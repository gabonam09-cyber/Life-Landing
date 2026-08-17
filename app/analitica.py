"""Recoleccion de metricas propias de la landing.

Todo lo que llega aqui viene del navegador, o sea de fuera: cada valor se acota
y se recorta antes de tocar la base. La sesion es un token aleatorio guardado en
una cookie propia; no se registra la IP ni ningun dato personal.
"""

from datetime import datetime, timedelta, timezone

from .models import Clic, SeccionVista, Sesion, VideoVista, db

# Topes defensivos: el endpoint es publico, asi que nada de listas infinitas.
MAX_CLICS_POR_ENVIO = 100
MAX_CLICS_POR_SESION = 400
MAX_SECCIONES = 40
UN_DIA_EN_SEG = 86400

DISPOSITIVOS = ("movil", "tablet", "escritorio")

# El origen se decide en el servidor a partir del referrer, no se le cree al cliente.
ORIGENES = {
    "whatsapp": ("whatsapp", "wa.me", "web.whatsapp"),
    "instagram": ("instagram", "ig.me", "l.instagram"),
    "facebook": ("facebook", "fb.com", "l.facebook", "m.facebook"),
    "google": ("google.", "googleusercontent"),
    "tiktok": ("tiktok",),
    "linkedin": ("linkedin", "lnkd.in"),
}


def _entero(valor, minimo, maximo, defecto=0):
    """Convierte a entero y lo deja dentro del rango; si no se puede, defecto."""
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return defecto
    return max(minimo, min(maximo, n))


def _decimal(valor, minimo, maximo, defecto=0.0):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return defecto
    if n != n:  # NaN: cualquier comparacion suya es falsa
        return defecto
    return max(minimo, min(maximo, n))


def _texto(valor, largo):
    if not isinstance(valor, str):
        return None
    limpio = valor.strip()[:largo]
    return limpio or None


def token_valido(token):
    """El token lo genera el navegador, asi que hay que comprobar su forma."""
    if not isinstance(token, str):
        return False
    token = token.strip()
    if not 8 <= len(token) <= 36:
        return False
    return all(c.isalnum() or c == "-" for c in token)


def clasificar_origen(referrer, propio_host=None):
    """Traduce el referrer a una etiqueta util: whatsapp, google, directo..."""
    if not referrer:
        return "directo"

    ref = referrer.lower()

    # Navegar dentro del propio sitio no es una fuente de trafico nueva.
    if propio_host and propio_host.lower() in ref:
        return "directo"

    for etiqueta, marcas in ORIGENES.items():
        if any(marca in ref for marca in marcas):
            return etiqueta

    return "otro"


def _dispositivo(valor, ancho):
    if valor in DISPOSITIVOS:
        return valor
    # Si el cliente manda cualquier cosa, se deduce del ancho de pantalla.
    if ancho and ancho < 768:
        return "movil"
    if ancho and ancho < 1024:
        return "tablet"
    return "escritorio"


def _obtener_o_crear_sesion(token, datos, es_interna, propio_host):
    sesion = Sesion.query.filter_by(token=token).first()
    if sesion:
        return sesion

    ancho = _entero(datos.get("ancho"), 200, 8000, defecto=0) or None
    referrer = _texto(datos.get("referrer"), 300)

    sesion = Sesion(
        token=token,
        referrer=referrer,
        origen=clasificar_origen(referrer, propio_host),
        dispositivo=_dispositivo(datos.get("dispositivo"), ancho),
        ancho=ancho,
        alto=_entero(datos.get("alto"), 200, 8000, defecto=0) or None,
        es_interna=bool(es_interna),
    )
    db.session.add(sesion)
    db.session.flush()  # necesitamos el id para las filas hijas
    return sesion


def _guardar_secciones(sesion, secciones):
    """Los segundos por seccion llegan acumulados: nos quedamos con el mayor."""
    if not isinstance(secciones, dict):
        return

    existentes = {s.seccion: s for s in sesion.secciones}

    for nombre, segundos in list(secciones.items())[:MAX_SECCIONES]:
        clave = _texto(nombre, 40)
        if not clave:
            continue

        valor = _entero(segundos, 0, UN_DIA_EN_SEG)
        fila = existentes.get(clave)

        if fila is None:
            fila = SeccionVista(sesion_id=sesion.id, seccion=clave, segundos=valor)
            db.session.add(fila)
            existentes[clave] = fila
        elif valor > (fila.segundos or 0):
            fila.segundos = valor


def _guardar_video(sesion, video):
    if not isinstance(video, dict):
        return

    fila = sesion.video
    if fila is None:
        # Los valores van explicitos: los "default" del modelo solo se aplican al
        # escribir en la base, y aqui hay que comparar contra ellos antes de eso.
        fila = VideoVista(sesion_id=sesion.id, dio_play=False,
                          segundos_vistos=0, pct_completado=0)
        db.session.add(fila)
        sesion.video = fila

    if video.get("dio_play"):
        fila.dio_play = True

    duracion = _entero(video.get("duracion_seg"), 0, UN_DIA_EN_SEG)
    if duracion:
        fila.duracion_seg = duracion

    vistos = _entero(video.get("segundos_vistos"), 0, UN_DIA_EN_SEG)
    if vistos > (fila.segundos_vistos or 0):
        fila.segundos_vistos = vistos

    pct = _entero(video.get("pct_completado"), 0, 100)
    if pct > (fila.pct_completado or 0):
        fila.pct_completado = pct

    # El punto de abandono es el ultimo conocido, no el mayor: si vuelve a
    # verlo desde el principio y lo deja antes, esa es la realidad mas reciente.
    if "abandono_seg" in video:
        fila.abandono_seg = _entero(video.get("abandono_seg"), 0, UN_DIA_EN_SEG)


def _guardar_clics(sesion, clics):
    if not isinstance(clics, list):
        return

    ya_tiene = Clic.query.filter_by(sesion_id=sesion.id).count()
    cupo = max(0, MAX_CLICS_POR_SESION - ya_tiene)
    if not cupo:
        return

    for crudo in clics[:min(MAX_CLICS_POR_ENVIO, cupo)]:
        if not isinstance(crudo, dict):
            continue

        ancho_ref = _entero(crudo.get("ancho_ref"), 200, 8000, defecto=0)
        if not ancho_ref:
            continue

        db.session.add(Clic(
            sesion_id=sesion.id,
            x_rel=_decimal(crudo.get("x_rel"), 0.0, 1.0),
            y_abs=_entero(crudo.get("y_abs"), 0, 200000),
            ancho_ref=ancho_ref,
            dispositivo=sesion.dispositivo,
            elemento=_texto(crudo.get("elemento"), 120),
            texto=_texto(crudo.get("texto"), 80),
        ))


def registrar_eventos(datos, es_interna=False, propio_host=None):
    """Guarda un lote de eventos. Devuelve True si se acepto el envio."""
    if not isinstance(datos, dict):
        return False

    token = datos.get("token")
    if not token_valido(token):
        return False
    token = token.strip()

    sesion = _obtener_o_crear_sesion(token, datos, es_interna, propio_host)

    # Duracion y scroll llegan acumulados desde el navegador: solo pueden crecer,
    # asi un envio que llegue tarde o desordenado no borra lo ya sabido.
    duracion = _entero(datos.get("duracion_seg"), 0, UN_DIA_EN_SEG)
    if duracion > (sesion.duracion_seg or 0):
        sesion.duracion_seg = duracion

    scroll = _entero(datos.get("scroll_max_pct"), 0, 100)
    if scroll > (sesion.scroll_max_pct or 0):
        sesion.scroll_max_pct = scroll

    sesion.ultima_actividad = datetime.now(timezone.utc)

    _guardar_secciones(sesion, datos.get("secciones"))
    _guardar_video(sesion, datos.get("video"))
    _guardar_clics(sesion, datos.get("clics"))

    db.session.commit()
    return True


# --- Lectura: lo que se muestra en el panel ---------------------------------

# Orden en que aparecen las secciones en la landing, para que el embudo se lea
# de arriba abajo igual que la pagina. Lo que no este aqui va al final.
ORDEN_SECCIONES = ["hero", "formacion", "insight", "sistema", "servicios",
                   "proceso", "nosotros", "faq", "contacto"]

ETIQUETAS_SECCIONES = {
    "hero": "Portada · titular y video",
    "formacion": "Formados en",
    "insight": "El error silencioso",
    "sistema": "Tácticas sueltas vs sistema",
    "servicios": "Los 3 sistemas",
    "proceso": "Proceso paso a paso",
    "nosotros": "Nosotros",
    "faq": "Preguntas frecuentes",
    "contacto": "Llamado final",
}


def _base_sesiones(dias, incluir_internas):
    consulta = Sesion.query
    if not incluir_internas:
        consulta = consulta.filter(Sesion.es_interna.is_(False))
    if dias:
        desde = datetime.now(timezone.utc) - timedelta(days=dias)
        consulta = consulta.filter(Sesion.creada_en >= desde)
    return consulta


def _porcentaje(parte, total):
    return round(parte * 100 / total) if total else 0


def resumen_metricas(dias=30, incluir_internas=False):
    """Arma todos los numeros del panel en una sola pasada por las sesiones."""
    sesiones = _base_sesiones(dias, incluir_internas).all()
    total = len(sesiones)

    resumen = {
        "total": total,
        "dias": dias,
        "incluir_internas": incluir_internas,
        "duracion_media": 0,
        "scroll_medio": 0,
        "origenes": [],
        "dispositivos": [],
        "secciones": [],
        "video": {"con_play": 0, "pct_play": 0, "retencion_media": 0,
                  "completaron": 0, "curva": []},
        "sin_datos": total == 0,
    }

    if not total:
        return resumen

    resumen["duracion_media"] = round(sum(s.duracion_seg or 0 for s in sesiones) / total)
    resumen["scroll_medio"] = round(sum(s.scroll_max_pct or 0 for s in sesiones) / total)

    # Origen y dispositivo: conteo simple, ordenado de mayor a menor.
    for campo, clave in (("origen", "origenes"), ("dispositivo", "dispositivos")):
        conteo = {}
        for s in sesiones:
            valor = getattr(s, campo) or "otro"
            conteo[valor] = conteo.get(valor, 0) + 1
        resumen[clave] = [
            {"nombre": k, "sesiones": v, "pct": _porcentaje(v, total)}
            for k, v in sorted(conteo.items(), key=lambda x: -x[1])
        ]

    # Embudo por seccion: cuantas visitas la vieron y cuanto aguantaron ahi.
    vistas = {}
    for s in sesiones:
        for sv in s.secciones:
            if sv.segundos <= 0:
                continue
            d = vistas.setdefault(sv.seccion, {"sesiones": 0, "segundos": 0})
            d["sesiones"] += 1
            d["segundos"] += sv.segundos

    def orden(nombre):
        return ORDEN_SECCIONES.index(nombre) if nombre in ORDEN_SECCIONES else 999

    resumen["secciones"] = [
        {
            "id": nombre,
            "etiqueta": ETIQUETAS_SECCIONES.get(nombre, nombre),
            "sesiones": d["sesiones"],
            "pct": _porcentaje(d["sesiones"], total),
            "segundos_medios": round(d["segundos"] / d["sesiones"]),
        }
        for nombre, d in sorted(vistas.items(), key=lambda x: orden(x[0]))
    ]

    # Video: cuantos le dan play, cuanto aguantan y donde lo dejan.
    con_video = [s.video for s in sesiones if s.video and s.video.dio_play]
    con_play = len(con_video)
    resumen["video"]["con_play"] = con_play
    resumen["video"]["pct_play"] = _porcentaje(con_play, total)

    if con_play:
        resumen["video"]["retencion_media"] = round(
            sum(v.pct_completado or 0 for v in con_video) / con_play
        )
        resumen["video"]["completaron"] = sum(
            1 for v in con_video if (v.pct_completado or 0) >= 90
        )

        # Curva de abandono: en que segundo se sale la gente, en 10 tramos.
        duracion = max((v.duracion_seg or 0) for v in con_video) or 0
        if duracion:
            tramos = 10
            ancho = max(1, round(duracion / tramos))
            cubos = [0] * tramos

            for v in con_video:
                seg = v.abandono_seg if v.abandono_seg is not None else v.segundos_vistos
                indice = min(tramos - 1, int((seg or 0) // ancho))
                cubos[indice] += 1

            resumen["video"]["curva"] = [
                {"desde": i * ancho,
                 "hasta": min(duracion, (i + 1) * ancho),
                 "sesiones": n,
                 "pct": _porcentaje(n, con_play)}
                for i, n in enumerate(cubos)
            ]

    return resumen


def clics_para_mapa(dias=30, dispositivo="escritorio", incluir_internas=False, limite=3000):
    """Clics de un tipo de pantalla. No se mezclan: las coordenadas no son comparables."""
    consulta = (Clic.query
                .join(Sesion, Clic.sesion_id == Sesion.id)
                .filter(Clic.dispositivo == dispositivo))

    if not incluir_internas:
        consulta = consulta.filter(Sesion.es_interna.is_(False))
    if dias:
        desde = datetime.now(timezone.utc) - timedelta(days=dias)
        consulta = consulta.filter(Sesion.creada_en >= desde)

    filas = consulta.order_by(Clic.id.desc()).limit(limite).all()

    return [
        {"x": round(c.x_rel, 4), "y": c.y_abs, "ancho_ref": c.ancho_ref,
         "elemento": c.elemento, "texto": c.texto}
        for c in filas
    ]


def reiniciar_metricas(solo_internas=False):
    """Borra las visitas registradas. Nunca toca los prospectos del formulario.

    Con solo_internas se limpian unicamente las visitas propias (las hechas con
    sesion de admin abierta), que son las que ensucian al estar probando.
    """
    consulta = Sesion.query
    if solo_internas:
        consulta = consulta.filter(Sesion.es_interna.is_(True))

    sesiones = consulta.all()
    if not sesiones:
        return {"sesiones": 0, "clics": 0}

    clics = sum(len(s.clics) for s in sesiones)

    for sesion in sesiones:
        db.session.delete(sesion)  # el cascade se lleva secciones, video y clics

    db.session.commit()
    return {"sesiones": len(sesiones), "clics": clics}


def purgar_analitica_vieja(dias=90):
    """Borra sesiones antiguas. Los clics son lo que mas crece con el tiempo."""
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    viejas = Sesion.query.filter(Sesion.creada_en < limite).all()

    if not viejas:
        return 0

    for sesion in viejas:
        db.session.delete(sesion)  # el cascade se lleva secciones, video y clics

    db.session.commit()
    return len(viejas)

/* Analitica propia de la landing.
 *
 * Mide lo que hace falta para saber que le falta a la pagina: de donde llega la
 * gente, hasta donde baja, cuanto aguanta cada seccion, si ve el video y donde
 * hace clic. No usa cookies de terceros ni guarda nada personal: el token es un
 * identificador aleatorio que vive solo en esta pestaña.
 */
(() => {
  'use strict';

  // Dentro de un iframe no se mide: el mapa de calor del panel carga la landing
  // ahi dentro, y si no, abrir el panel inventaria una visita cada vez.
  if (window.top !== window.self) return;

  // Solo la landing tiene hero: si no esta, esto no es la pagina a medir.
  const hero = document.querySelector('.hero');
  const wrap = document.querySelector('.wrap');
  if (!hero || !wrap) return;

  const ENDPOINT = '/api/eventos';
  const CADA_CUANTO_MS = 20000;   // envio periodico por si la persona se queda mucho rato
  const PRIMER_ENVIO_MS = 3000;   // un primer aviso pronto: si rebota, igual queda registrada
  const CLAVE_TOKEN = 'life_token_visita';

  // --- Token de la visita -------------------------------------------------
  const nuevoToken = () => {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'v-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  };

  let token;
  try {
    token = sessionStorage.getItem(CLAVE_TOKEN);
    if (!token) {
      token = nuevoToken();
      sessionStorage.setItem(CLAVE_TOKEN, token);
    }
  } catch (e) {
    // Modo privado o almacenamiento bloqueado: la visita se mide igual, pero
    // recargar la pagina contara como una visita nueva.
    token = nuevoToken();
  }

  // --- Estado que se va acumulando ----------------------------------------
  const estado = {
    duracion: 0,
    scrollMax: 0,
    secciones: {},       // nombre -> segundos en pantalla
    clics: [],           // se vacian al enviarlos
    video: { dio_play: false, segundos_vistos: 0, pct: 0, ultimo: 0, duracion: 0 },
  };

  let hayNovedades = true;   // el alta de la visita ya es novedad de por si

  const dispositivo = () => {
    const w = window.innerWidth;
    if (w < 768) return 'movil';
    if (w < 1024) return 'tablet';
    return 'escritorio';
  };

  // --- Secciones: cuanto tiempo estuvo cada una en pantalla ---------------
  // Se recorre una vez por segundo en vez de usar observadores: son nueve
  // bloques, sale barato, y asi el tiempo se cuenta solo con la pestaña activa.
  const secciones = [{ nombre: 'hero', el: hero }];
  document.querySelectorAll('section[id]').forEach((el) => {
    secciones.push({ nombre: el.id, el });
  });

  const contarSegundo = () => {
    if (document.visibilityState !== 'visible') return;

    estado.duracion += 1;
    const alto = window.innerHeight;

    secciones.forEach(({ nombre, el }) => {
      const r = el.getBoundingClientRect();
      const visible = Math.min(r.bottom, alto) - Math.max(r.top, 0);
      // Cuenta solo si de verdad esta ocupando pantalla, no si asoma una esquina.
      if (visible > 0 && visible >= Math.min(r.height, alto) * 0.4) {
        estado.secciones[nombre] = (estado.secciones[nombre] || 0) + 1;
        hayNovedades = true;
      }
    });
  };

  setInterval(contarSegundo, 1000);

  // --- Profundidad de scroll ---------------------------------------------
  let scrollPendiente = false;
  const medirScroll = () => {
    scrollPendiente = false;
    const alto = document.documentElement.scrollHeight;
    if (alto <= 0) return;

    const pct = Math.round(((window.scrollY + window.innerHeight) / alto) * 100);
    const acotado = Math.max(0, Math.min(100, pct));
    if (acotado > estado.scrollMax) {
      estado.scrollMax = acotado;
      hayNovedades = true;
    }
  };

  window.addEventListener('scroll', () => {
    if (scrollPendiente) return;
    scrollPendiente = true;
    requestAnimationFrame(medirScroll);
  }, { passive: true });
  medirScroll();

  // --- Video del hero -----------------------------------------------------
  const video = document.querySelector('.hero-video');
  if (video) {
    video.addEventListener('play', () => {
      estado.video.dio_play = true;
      hayNovedades = true;
    });

    video.addEventListener('timeupdate', () => {
      const t = video.currentTime || 0;
      estado.video.ultimo = t;
      if (t > estado.video.segundos_vistos) estado.video.segundos_vistos = t;

      if (video.duration && isFinite(video.duration)) {
        estado.video.duracion = video.duration;
        const pct = Math.round((estado.video.segundos_vistos / video.duration) * 100);
        if (pct > estado.video.pct) estado.video.pct = pct;
      }
      hayNovedades = true;
    });

    // Pausar o terminar marca el punto de abandono: es lo que dibuja la curva.
    ['pause', 'ended'].forEach((evento) => {
      video.addEventListener(evento, () => {
        estado.video.ultimo = video.currentTime || 0;
        hayNovedades = true;
      });
    });
  }

  // --- Clics --------------------------------------------------------------
  // La X se guarda como fraccion del ancho del contenido para que el mapa se
  // pueda repintar en cualquier pantalla; la Y va en pixeles desde el inicio.
  const describir = (el) => {
    if (!el || !el.tagName) return null;
    const tag = el.tagName.toLowerCase();
    if (el.id) return tag + '#' + el.id;
    const clase = (el.className && typeof el.className === 'string')
      ? el.className.trim().split(/\s+/)[0] : '';
    return clase ? tag + '.' + clase : tag;
  };

  document.addEventListener('click', (e) => {
    const r = wrap.getBoundingClientRect();
    if (r.width <= 0) return;

    // La posicion se calcula a mano desde clientX/clientY en vez de usar
    // pageX/pageY: el rectangulo tambien es relativo a la ventana, y asi la
    // cuenta no depende de como cada navegador rellene pageX en cada evento.
    const xDentro = (e.clientX - r.left) / r.width;

    estado.clics.push({
      x_rel: Math.max(0, Math.min(1, xDentro)),
      y_abs: Math.round(e.clientY + window.scrollY),
      ancho_ref: Math.round(r.width),
      elemento: describir(e.target),
      texto: (e.target.textContent || '').trim().slice(0, 80) || null,
    });
    hayNovedades = true;
  }, { capture: true, passive: true });

  // --- Envio --------------------------------------------------------------
  const armarPayload = () => ({
    token,
    referrer: document.referrer || '',
    dispositivo: dispositivo(),
    ancho: window.innerWidth,
    alto: window.innerHeight,
    duracion_seg: estado.duracion,
    scroll_max_pct: estado.scrollMax,
    secciones: estado.secciones,
    video: {
      dio_play: estado.video.dio_play,
      segundos_vistos: Math.round(estado.video.segundos_vistos),
      pct_completado: estado.video.pct,
      abandono_seg: Math.round(estado.video.ultimo),
      duracion_seg: Math.round(estado.video.duracion),
    },
    clics: estado.clics,
  });

  const enviar = (esCierre) => {
    if (!hayNovedades) return;

    const payload = armarPayload();
    const cuerpo = JSON.stringify(payload);
    // Los clics se dan por entregados: reintentarlos duplicaria el mapa.
    const enviados = estado.clics.length;
    estado.clics = [];
    hayNovedades = false;

    let entregado = false;

    if (navigator.sendBeacon) {
      try {
        entregado = navigator.sendBeacon(
          ENDPOINT, new Blob([cuerpo], { type: 'application/json' })
        );
      } catch (err) {
        entregado = false;
      }
    }

    if (!entregado) {
      // Al cerrar la pestaña solo keepalive tiene alguna posibilidad de salir.
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: cuerpo,
        keepalive: true,
      }).catch(() => {
        // Si de verdad no salio y aun estamos en la pagina, se reintenta luego.
        if (!esCierre && enviados) hayNovedades = true;
      });
    }
  };

  setTimeout(() => enviar(false), PRIMER_ENVIO_MS);
  setInterval(() => enviar(false), CADA_CUANTO_MS);

  // Cambiar de pestaña es el momento mas fiable para cerrar cuentas en movil,
  // donde el evento de descarga muchas veces no llega a dispararse.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') enviar(true);
  });
  window.addEventListener('pagehide', () => enviar(true));
})();

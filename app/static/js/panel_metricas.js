/* Mapa de clics del panel.
 *
 * Carga la landing dentro de un iframe del mismo origen y dibuja encima un punto
 * por cada clic. Como el iframe es del mismo sitio, se puede leer su interior y
 * colocar los puntos sobre el contenedor real en lugar de adivinar posiciones.
 */
(() => {
  'use strict';

  const mapa = document.getElementById('mapa');
  const datos = document.getElementById('datos-clics');
  if (!mapa || !datos) return;

  const marco = mapa.querySelector('.met-mapa-pagina');
  const capa = mapa.querySelector('.met-mapa-puntos');
  if (!marco || !capa) return;

  let clics = [];
  try {
    clics = JSON.parse(datos.textContent) || [];
  } catch (e) {
    return;
  }
  if (!clics.length) return;

  // Ancho al que se renderiza la landing dentro del iframe. Se busca que el
  // contenedor interno acabe midiendo lo mismo que cuando se hicieron los clics:
  // si la pagina se acomoda igual, las alturas coinciden y los puntos caen donde
  // deben. El contenedor mide min(tope del diseño, ancho de la ventana).
  const ANCHO_TOPE = Number(mapa.dataset.anchoBase) || 1320;

  const anchoDeReferencia = () => {
    const conteo = {};
    clics.forEach((c) => { conteo[c.ancho_ref] = (conteo[c.ancho_ref] || 0) + 1; });

    let mejor = null, masVisto = -1;
    Object.keys(conteo).forEach((ancho) => {
      if (conteo[ancho] > masVisto) { masVisto = conteo[ancho]; mejor = Number(ancho); }
    });

    const ref = mejor || ANCHO_TOPE;
    // Por debajo del tope, el contenedor ocupa toda la ventana: basta con igualarla.
    // A partir del tope hay que dejar sitio para los margenes laterales.
    const ventana = ref >= ANCHO_TOPE ? ref + 80 : ref;
    return Math.max(320, Math.min(2200, ventana));
  };

  const anchoVentana = anchoDeReferencia();
  marco.style.width = anchoVentana + 'px';
  capa.style.width = anchoVentana + 'px';

  const ajustarEscala = (altoPagina) => {
    // La landing se dibuja a su ancho real y luego se encoge para caber en el
    // panel; asi los puntos conservan su posicion relativa exacta.
    const disponible = mapa.clientWidth;
    const escala = Math.min(1, disponible / anchoVentana);

    [marco, capa].forEach((el) => {
      el.style.transform = 'scale(' + escala + ')';
      el.style.transformOrigin = 'top left';
    });

    mapa.style.height = (altoPagina * escala) + 'px';
  };

  const pintar = () => {
    let doc;
    try {
      doc = marco.contentDocument;
    } catch (e) {
      return;  // no deberia pasar siendo el mismo origen
    }
    if (!doc || !doc.body) return;

    // El formulario se abre solo al cargar y taparia la pagina entera.
    const cerrar = doc.querySelector('[data-close-modal]');
    if (cerrar) cerrar.click();

    // Las animaciones de entrada dejan las secciones invisibles hasta que se
    // hace scroll; aqui no hay scroll, asi que se muestran todas de golpe.
    doc.documentElement.classList.remove('js-anim');
    doc.querySelectorAll('[data-reveal], [data-hero-in]').forEach((el) => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    });

    const contenedor = doc.querySelector('.wrap');
    if (!contenedor) return;

    const r = contenedor.getBoundingClientRect();
    const izquierda = r.left + (doc.documentElement.scrollLeft || 0);
    const ancho = r.width;

    // Si algun clic viniera de una pantalla que dibujaba la pagina mas larga,
    // se estira el lienzo para que no quede recortado sin avisar.
    const alto = Math.max(
      doc.body.scrollHeight,
      doc.documentElement.scrollHeight,
      ...clics.map((c) => c.y + 40)
    );
    marco.style.height = alto + 'px';
    capa.style.height = alto + 'px';

    capa.innerHTML = '';
    const fragmento = doc.createDocumentFragment ? document.createDocumentFragment() : null;

    clics.forEach((c) => {
      const punto = document.createElement('span');
      punto.className = 'met-punto';
      punto.style.left = (izquierda + c.x * ancho) + 'px';
      punto.style.top = c.y + 'px';
      if (c.texto || c.elemento) {
        punto.title = (c.texto || c.elemento).slice(0, 60);
      }
      (fragmento || capa).appendChild(punto);
    });

    if (fragmento) capa.appendChild(fragmento);

    ajustarEscala(alto);
  };

  marco.addEventListener('load', () => {
    // Un respiro para que tipografias e imagenes terminen de acomodar la altura.
    setTimeout(pintar, 400);
  });

  let redibujar;
  window.addEventListener('resize', () => {
    clearTimeout(redibujar);
    redibujar = setTimeout(pintar, 200);
  });
})();

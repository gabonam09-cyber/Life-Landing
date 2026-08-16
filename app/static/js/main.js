document.addEventListener('DOMContentLoaded', () => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // --- Ventana modal del formulario de diagnostico ---
  // Va primero y sin depender de librerias externas: es el CTA del embudo, asi
  // que debe seguir funcionando aunque Lenis o GSAP no lleguen a cargar.
  const modal = document.getElementById('modal-diagnostico');
  let bloquearScroll = () => {};
  let liberarScroll = () => {};

  if (modal) {
    let ultimoFoco = null;

    const abrirModal = () => {
      ultimoFoco = document.activeElement;
      modal.hidden = false;
      bloquearScroll();
      const primero = modal.querySelector('input:not([type="hidden"]), textarea, button');
      if (primero) primero.focus();
    };

    const cerrarModal = () => {
      modal.hidden = true;
      liberarScroll();
      if (ultimoFoco) ultimoFoco.focus();
    };

    document.querySelectorAll('[data-open-modal]').forEach((el) => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        abrirModal();
      });
    });

    document.querySelectorAll('[data-close-modal]').forEach((el) => {
      el.addEventListener('click', cerrarModal);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) cerrarModal();
    });

    // Si el formulario volvio con errores de validacion, reabre el modal
    // para que la persona pueda corregir sin buscar el boton otra vez.
    if (document.querySelector('.flash-error')) abrirModal();
    // Al entrar a la pagina, el formulario aparece de inmediato.
    else abrirModal();
  }

  // --- Acordeon del FAQ: al abrir una pregunta se cierra la anterior ---
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach((item) => {
    item.addEventListener('toggle', () => {
      if (!item.open) return;
      faqItems.forEach((otro) => {
        if (otro !== item) otro.open = false;
      });
    });
  });

  // --- Barra de navegacion: se compacta en cuanto se baja del hero ---
  // Con listener propio (no ScrollTrigger) para que siga funcionando sin GSAP.
  const nav = document.querySelector('nav');
  if (nav) {
    const actualizarNav = () => {
      nav.classList.toggle('nav--scrolled', window.scrollY > 40);
    };
    actualizarNav();
    window.addEventListener('scroll', actualizarNav, { passive: true });
  }

  // --- Cursor personalizado (jaygood) ---
  // No depende de GSAP: va antes del corte de abajo. Solo con raton fino, para
  // no dibujar nada en tactil, y solo si no se pidio reducir movimiento.
  const punteroFino = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  if (punteroFino && !reduceMotion) {
    const halo = document.createElement('div');
    halo.className = 'cursor-ring';
    const punto = document.createElement('div');
    punto.className = 'cursor-dot';
    document.body.append(halo, punto);
    // solo ahora se oculta el cursor del sistema: si este bloque no corriera,
    // el usuario se quedaria sin puntero.
    document.documentElement.classList.add('has-cursor');

    let ratonX = window.innerWidth / 2, ratonY = window.innerHeight / 2;
    let haloX = ratonX, haloY = ratonY;

    const colocar = (el, x, y) => {
      el.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    };

    document.addEventListener('mousemove', (e) => {
      ratonX = e.clientX;
      ratonY = e.clientY;
      colocar(punto, ratonX, ratonY);   // el nucleo va pegado al puntero
    }, { passive: true });

    // el halo persigue al raton con retraso (interpolacion suave)
    const seguir = () => {
      haloX += (ratonX - haloX) * 0.18;
      haloY += (ratonY - haloY) * 0.18;
      colocar(halo, haloX, haloY);
      requestAnimationFrame(seguir);
    };
    seguir();

    // el halo se abre sobre cualquier cosa clickeable
    document.querySelectorAll('a, button, summary, .play-btn, input, textarea')
      .forEach((el) => {
        el.addEventListener('mouseenter', () => halo.classList.add('is-active'));
        el.addEventListener('mouseleave', () => halo.classList.remove('is-active'));
      });

    // si el raton sale de la ventana, el cursor no se queda flotando
    document.addEventListener('mouseleave', () => {
      halo.style.opacity = '0';
      punto.style.opacity = '0';
    });
    document.addEventListener('mouseenter', () => {
      halo.style.opacity = '';
      punto.style.opacity = '';
    });
  }

  // --- Scroll suave (opcional) ---
  let lenis = null;
  if (typeof Lenis !== 'undefined') {
    lenis = new Lenis({ duration: reduceMotion ? 0 : 1.1, smoothWheel: !reduceMotion });
    const raf = (time) => {
      lenis.raf(time);
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);

    bloquearScroll = () => lenis.stop();
    liberarScroll = () => lenis.start();
  } else {
    // Sin Lenis, se bloquea el scroll del documento a mano.
    bloquearScroll = () => { document.body.style.overflow = 'hidden'; };
    liberarScroll = () => { document.body.style.overflow = ''; };
  }

  // --- CTAs del hero: bajan al recuadro y arrancan el video ---
  const heroVideo = document.querySelector('.hero-video');
  const videoTarget = document.getElementById('video');

  if (heroVideo && videoTarget) {
    // Safari solo autoriza play() dentro del gesto que lo disparo, asi que va
    // antes del scroll: cualquier cosa que se haga primero puede invalidarlo.
    // Si aun asi lo rechaza, se reintenta sin sonido, que siempre esta permitido;
    // el visitante ve el video corriendo y sube el volumen si quiere.
    const reproducirHeroVideo = () => {
      const intento = heroVideo.play();
      if (!intento) return;

      intento.catch(() => {
        heroVideo.muted = true;
        heroVideo.play().catch(() => {});
      });
    };

    document.querySelectorAll('a[href="#video"]').forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        reproducirHeroVideo();

        if (lenis) {
          lenis.scrollTo(videoTarget, { offset: -90, immediate: reduceMotion });
        } else {
          videoTarget.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
        }
      });
    });
  }

  // --- Animaciones (opcionales) ---
  if (reduceMotion || typeof gsap === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);
  if (lenis) lenis.on('scroll', ScrollTrigger.update);

  // Solo ahora se ocultan los elementos animados: si GSAP no hubiera cargado,
  // la clase nunca se aplica y el contenido se ve normal.
  document.documentElement.classList.add('js-anim');

  // Las animaciones se reproducen en ambos sentidos del scroll: al bajar entran
  // y al subir se revierten, de modo que la pagina se siente viva en los dos
  // sentidos en vez de "gastarse" en la primera pasada.
  const AMBOS_SENTIDOS = 'play reverse play reverse';

  // Curva de jaygood (--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)): arranca
  // muy rapido y frena largo. Es lo que da la sensacion de "peso" al movimiento.
  const EASE = 'expo.out';

  // Entrada del hero al cargar
  gsap.fromTo('[data-hero-in]',
    { opacity: 0, y: 24 },
    { opacity: 1, y: 0, duration: 0.8, ease: EASE, stagger: 0.12, delay: 0.1 }
  );

  // Parallax del hero: el mockup de video se hunde un poco mas lento que el texto
  const heroMock = document.querySelector('.hero .video-mock');
  if (heroMock) {
    gsap.to(heroMock, {
      y: -60, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 0.6 },
    });
  }

  // Revelado progresivo de cada seccion, en los dos sentidos
  document.querySelectorAll('[data-reveal]').forEach((el) => {
    gsap.fromTo(el,
      { opacity: 0, y: 44 },
      {
        opacity: 1, y: 0, duration: 0.9, ease: EASE,
        scrollTrigger: { trigger: el, start: 'top 88%', end: 'bottom 12%', toggleActions: AMBOS_SENTIDOS },
      }
    );
  });

  // Tarjetas de sistemas: entrada escalonada
  gsap.fromTo('.system-card',
    { opacity: 0, y: 56 },
    {
      opacity: 1, y: 0, duration: 0.8, ease: EASE, stagger: 0.15,
      scrollTrigger: {
        trigger: '.systems-grid', start: 'top 82%', end: 'bottom 18%',
        toggleActions: AMBOS_SENTIDOS,
      },
    }
  );

  // Bullets de la comparativa: caen uno tras otro dentro de cada columna
  document.querySelectorAll('.compare-col').forEach((col) => {
    gsap.fromTo(col.querySelectorAll('.compare-item'),
      { opacity: 0, x: -18 },
      {
        opacity: 1, x: 0, duration: 0.5, ease: EASE, stagger: 0.09,
        scrollTrigger: {
          trigger: col, start: 'top 78%', end: 'bottom 22%',
          toggleActions: AMBOS_SENTIDOS,
        },
      }
    );
  });

  // Preguntas del FAQ: aparecen en cascada
  gsap.fromTo('.faq-item',
    { opacity: 0, y: 24 },
    {
      opacity: 1, y: 0, duration: 0.55, ease: EASE, stagger: 0.08,
      scrollTrigger: {
        trigger: '.faq-list', start: 'top 84%', end: 'bottom 16%',
        toggleActions: AMBOS_SENTIDOS,
      },
    }
  );

  // Los CTA laten suavemente al entrar en pantalla, para llamar el clic
  document.querySelectorAll('.cta-button').forEach((cta) => {
    gsap.fromTo(cta,
      { opacity: 0, scale: 0.94 },
      {
        opacity: 1, scale: 1, duration: 0.6, ease: EASE,
        scrollTrigger: { trigger: cta, start: 'top 90%', end: 'bottom 10%', toggleActions: AMBOS_SENTIDOS },
      }
    );
  });
});

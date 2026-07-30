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

  // --- Animaciones (opcionales) ---
  if (reduceMotion || typeof gsap === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);
  if (lenis) lenis.on('scroll', ScrollTrigger.update);

  // Entrada del hero al cargar
  gsap.fromTo('[data-hero-in]',
    { opacity: 0, y: 20 },
    { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', stagger: 0.12, delay: 0.1 }
  );

  // Revelado progresivo al hacer scroll
  document.querySelectorAll('[data-reveal]').forEach((el) => {
    gsap.fromTo(el,
      { opacity: 0, y: 32 },
      {
        opacity: 1, y: 0, duration: 0.9, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 85%' },
      }
    );
  });

  // Tarjetas de sistemas: entrada escalonada
  gsap.fromTo('.system-card',
    { opacity: 0, y: 40 },
    {
      opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', stagger: 0.15,
      scrollTrigger: { trigger: '.systems-grid', start: 'top 80%' },
    }
  );
});

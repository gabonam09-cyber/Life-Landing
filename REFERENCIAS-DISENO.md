# Análisis de referencias: colores y animaciones

Extraído de los estilos computados del DOM (no de capturas), el 1 de agosto de 2026.

- **momnt** — https://www.momntagency.com/vsl-447822
- **jaygood** — https://jaygood-agency.vercel.app

---

## 1. Colores

### momnt

| Uso | Color | Nota |
|---|---|---|
| Fondo dominante | `#000000` | negro puro, ~13.6M px² |
| Fondo secundario | `#050705` | negro con pizca de verde |
| **Bloque claro** | `#FAFAFA` | ~2.8M px², una sección clara entre tanto negro |
| **Acento** | `#B7FF12` | verde lima neón |
| Acento apagado | `#A3DC18` | variante para hover/bordes |
| Texto principal | `#F4F4EF` | crema, no blanco puro |
| Texto secundario | `#BBBBBB` | |
| Alarma (en keyframe) | `#EF233C` | rojo, solo en una variante del botón play |

Verde con transparencia para fondos sutiles: `rgba(183,255,18, 0.055 / 0.10 / 0.12)`.

Tipografías: **Inter** (cuerpo) + **Times** (serif, para énfasis) + Montserrat.

### jaygood

Declara solo cuatro variables en `:root` — paleta extremadamente disciplinada:

```css
--brand-dark: #030303;
--brand-lime: #ccff00;
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out-circ: cubic-bezier(0.85, 0, 0.15, 1);
```

Más blanco puro, una escala de grises (`#0A0A0A`, `#111111`, `#1A1A1A`) y overlays `rgba(255,255,255, 0.03 / 0.05 / 0.1)` para separar bloques sin usar bordes.

Tipografías: **Inter** + **Space Grotesk** (titulares condensados) + **monoespaciada** para detalles técnicos.

### El patrón que comparten

Los dos usan **la misma fórmula de tres colores**: casi negro + UN lima-neón + blanco. Ningún otro color. Sin azul, sin degradados de color, sin paleta multicolor.

---

## 2. Animaciones

### momnt — 100% CSS, sin GSAP ni librería alguna

| Animación | Duración | Qué hace |
|---|---|---|
| `momntPlayPulse` | infinita | Botón de play: ondas verdes que se expanden (box-shadow de 0 → 14px → 28px, opacidad 0.36 → 0) + escala 1 → 1.07 → 0.98 → 1 |
| `pulseGlow` | 2s ease-in-out | Halo que late en el botón CTA |
| `momntProgressGradient` | 4.8s | Barra de progreso con degradado que se desplaza sin parar |
| `momntOrbitSpinV9` | 12s y 19s linear | Dos anillos de puntos girando a distinta velocidad |
| `momntRingBreathV9` | 4.8s ease-in-out | Anillo que "respira" |
| `momntCoreBreathV9` | 2.8s | Núcleo central latiendo |
| `momntChipPulseV9` | 2.2s | Chips pulsando |
| `momntBadgeFloatV9` | 4.8s | Badges flotando |
| `momntHeroFadeUpV4` | 0.95s | Entrada del hero |
| `shiny-btn1` | — | Destello diagonal que barre el botón (scale 0 → 4 → 50, rotate 45°) |
| `rocking` | — | Balanceo de ±2° |

**Easing firma:** `cubic-bezier(0.2, 0.8, 0.2, 1)`
**Entradas:** 0.85–0.95s
**Transición más repetida:** `all 0.2s ease-in-out` (39 elementos)

Lo característico: casi todo es **infinito y sutil**. La página nunca está quieta.

### jaygood — scroll-driven por JS (Tailwind + bundle propio)

Solo dos keyframes CSS (`pulse`, `bounce`). Todo lo demás se mueve con el scroll:

- **5 elementos `position: sticky`** → secciones que se pegan mientras el contenido pasa por encima
- **Galería horizontal** dentro del scroll vertical (la sección "FEATURED WORK" se desplaza en X mientras bajas)
- **4 elementos con `mix-blend-mode`** → cursor personalizado que invierte lo que hay debajo
- 31 elementos con `transform` activo
- Página de 11.297px de alto
- Intercepta el scroll (`window.scrollTo` no funciona → hay interpolación propia)

**Easings:** `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out-expo: arranca rapidísimo, frena mucho — la firma del look "premium") y `cubic-bezier(0.85, 0, 0.15, 1)`.

Detalles de composición: titular en **dos capas** (palabra fantasma gris detrás, blanco delante), grid de líneas verticales sutiles de fondo, numeración `/01 /02 /03` en monoespaciada, reloj y temperatura en vivo en la barra superior.

---

## 3. Ideas aplicables a la landing de life

Ordenadas por relación esfuerzo/impacto.

1. **Animar la barra de progreso del modal.** Ya existe (`.contact-progress`, fija al 75%). momnt le mueve el degradado en bucle de 4.8s. Es el elemento con más carga psicológica del formulario: sensación de "ya casi".
2. **Ondas expansivas en el botón de play.** Hoy tiene un glow estático. momnt expande box-shadows de 0 a 28px con opacidad decreciente, más un latido de escala.
3. **Destello diagonal en el CTA** (`shiny-btn1`). Barre el botón cada varios segundos. Atrae la mirada sin ser una animación molesta.
4. **Cambiar el easing a `cubic-bezier(0.16, 1, 0.3, 1)`.** Hoy usa `power3.out`. El ease-out-expo es más dramático y es lo que separa visualmente un sitio premium de uno normal. Cambio de una línea en `main.js`.
5. **Sticky en la línea de tiempo de los 5 pasos.** Fijar el número del paso mientras su texto pasa al lado.
6. **Numeración monoespaciada** en pasos y FAQ (`/01`, `/02`). Los números ya están; es solo la fuente.
7. **Grid de líneas verticales** de fondo, muy tenue. Da profundidad al negro y evita que se vea plano.
8. **Titular del hero en dos capas** — una palabra fantasma detrás en gris muy oscuro.
9. **Un bloque claro de contraste.** momnt mantiene una sección `#FAFAFA` en medio del negro. Rompe la monotonía del scroll largo.
10. **Un dato en vivo** en la barra superior (hora de CDMX, cupos restantes). Señal de que el sitio "está vivo".

---

## 4. La decisión de color pendiente

**Las dos referencias usan lima-neón amarillento** (`#B7FF12`, `#CCFF00`) sobre negro, **sin azul**.

La landing hoy usa verde esmeralda `#33E661` + azul `#012F8A`. Son direcciones distintas:

- El **lima** de las referencias es más agresivo y "tech". Es casi el `#c6ff5e` que se descartó al principio del proyecto.
- El **esmeralda + azul** actual es más corporativo y menos genérico en el nicho de agencias — donde el lima sobre negro ya es un lugar común.

Ninguna es mejor por defecto. Pero conviene decidirlo a conciencia y no por inercia.

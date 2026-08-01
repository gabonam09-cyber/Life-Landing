# Copys de la landing de life

Reescritos el 1 de agosto de 2026 siguiendo el método de los apuntes
(hero con promesa y temporalidad → romper creencias → autoridad y storytelling
→ testimonios → FAQ que rompen objeciones).

🆕 = sección nueva · ⚠️ = necesita una decisión tuya

---

## 1. Navegación
life · SERVICIOS · NOSOTROS · CONTACTO

`app/templates/base.html`

---

## 2. Hero — Parte 1 del método

**Etiqueta:** DIAGNÓSTICO DIGITAL GRATUITO

**Titular:** ¿Tus ventas *no suben* como deberían?

**Promesa + temporalidad:**
> Tu negocio respondiendo y agendando solo, 24/7.
> **Sistema funcionando en 14 días**, sin cambiar tu equipo ni tus herramientas.

⚠️ **Confirma los 14 días.** Es la única cifra que promete un plazo, y ahora está
publicada. Si vuestro tiempo real de implementación es otro, cámbialo.

**Botones:** Agenda tu diagnóstico gratis · Ver los 3 sistemas

**Pie del vídeo:** MIRA CÓMO FUNCIONA EN 90 SEGUNDOS

`app/templates/index.html`

---

## 3. CTA principal (aparece dos veces)

**Título:** Solicita tu diagnóstico estratégico
**Subtítulo:** Primero analizamos tu negocio. Si vemos una oportunidad real de mejora, avanzamos.
**Nota:** No trabajamos con todos. Primero evaluamos si existe una oportunidad real para ayudar.

---

## 4. El error que casi nadie ve

**Titular:** Tu próximo cliente ya te escribió. Y sigue **esperando respuesta**
**Subtítulo:** No se fue porque otro fuera mejor. Se fue porque otro contestó primero.

> Antes decía "El 95% de los negocios en CDMX…". Se quitó la cifra: no tenía
> fuente y no se podía sostener si un prospecto la cuestionaba.

---

## 5. 🆕 Creencias que te frenan — Parte 2 del método

**Etiqueta:** LO QUE PROBABLEMENTE ESTÁS PENSANDO
**Titular:** Cuatro razones por las que hoy no harías nada

**"Ya publico todos los días, el problema es otro."**
Publicar atrae mensajes. El problema empieza después: cuando ese mensaje entra y tarda horas en recibir respuesta. Ahí es donde se cae la venta, no en el post.

**"La IA es para empresas grandes, no para mi negocio."**
Al contrario. Una empresa grande tiene un equipo entero para contestar. Un negocio de 3 o 10 personas es justo el que no puede estar pendiente del teléfono todo el día.

**"Mi negocio vive de recomendaciones, no lo necesito."**
La recomendación te trae al cliente. Pero antes de llamarte, te busca en Google y lee tus reseñas. Si ahí no apareces o apareces mal, la recomendación se enfría sola.

**"Ya tengo a alguien que contesta los mensajes."**
Y va a seguir contestando. La diferencia es que deja de responder lo repetitivo a las 11 de la noche, y entra en la conversación cuando ya hay una cita agendada.

`app/routes.py` → lista `CREENCIAS`

---

## 6. Comparativa (sin cambios)

**TÁCTICAS AISLADAS** vs **SISTEMA LIFE**, cuatro puntos cada columna.

---

## 7. Los 3 sistemas (sin cambios)

/01 Captación · /02 Respuesta · /03 Reputación

---

## 8. 🆕 Cómo se ve tu negocio después — el contrapeso al miedo

**Etiqueta:** A PARTIR DEL DÍA 14
**Titular:** Así se ve tu negocio cuando el sistema ya está trabajando

| Título | Texto |
|---|---|
| Abres el día con la agenda hecha | Las citas que se agendaron de madrugada ya están ahí cuando llegas. |
| Nadie se queda esperando | Cada mensaje recibe respuesta al momento, a la hora que entre y el día que sea. |
| Apareces cuando te buscan | Quien busca tu servicio en tu zona te encuentra a ti, no a quien está enfrente. |
| Tu calificación deja de bajar | Las reseñas se responden todas, y las buenas se piden solas después de cada visita. |
| Dejas de cargar con el teléfono | Tu equipo atiende a quien ya está decidido, en vez de repetir el mismo precio 40 veces. |
| Sabes qué está pasando | Cada semana ves cuántos escribieron, cuántos agendaron y dónde se quedó el resto. |

> Esta sección no existía. El sitio contaba ocho veces lo que se pierde y ninguna
> lo que se gana, justo al revés de "acercar al deseo y alejar del miedo".

`app/routes.py` → lista `RESULTADOS`

---

## 9. Proceso — los 5 pasos (sin cambios)

01 Diagnóstico inicial · 02 Auditoría comercial · 03 Detectamos la fuga ·
04 Diseñamos el sistema · 05 Seguimiento continuo

`app/routes.py` → lista `PASOS`

---

## 10. Nosotros — Parte 3: autoridad y storytelling

**Titular:** Empezamos por hartazgo

> Somos dos socios en Ciudad de México. Antes de montar life nos pasábamos el día
> revisando negocios: clínicas, talleres, spas, tiendas. Y en casi todos
> encontrábamos la misma escena.
>
> El dueño invirtiendo en anuncios y contenido. Los mensajes entrando. Y una
> bandeja de WhatsApp con veinte conversaciones sin responder desde el martes.
> Nadie era culpable: la persona que contestaba también atendía, cobraba y cerraba
> el local.
>
> Nos cansamos de ver negocios buenos perdiendo clientes por algo tan tonto como no
> alcanzar a contestar. Por eso life no vende campañas sueltas: montamos el sistema
> que responde, agenda y cuida tu reputación mientras tú haces tu trabajo.

⚠️ **Revisa que esta historia sea la vuestra.** La escribí a partir del problema que
ya afirmáis en el sitio. Si el origen real fue otro, cámbialo: una historia falsa se
nota en la primera llamada.

> Se quitó "Una agencia joven": decir "joven" resta autoridad justo en la sección
> que debe construirla.

---

## 11. Preguntas frecuentes — Parte 5: romper objeciones

Las seis anteriores explicaban el servicio. Estas atacan lo que de verdad frena la decisión.

**/01 — ¿Cuánto cuesta?**
Depende de qué sistemas necesites: no cuesta lo mismo resolver solo la respuesta por WhatsApp que montar captación, respuesta y reputación juntos. El número exacto sale del diagnóstico, y ahí te lo damos por escrito antes de que decidas nada.

**/02 — ¿En cuánto tiempo veo resultados?**
El sistema de respuesta queda funcionando en unos 14 días, y desde el primer día ningún mensaje se queda sin contestar. Captación y reputación tardan más en notarse: ahí hablamos de meses, porque dependen de posicionamiento y de reseñas acumuladas. Cualquiera que te prometa clientes en una semana te está vendiendo humo.

**/03 — ¿Y si no funciona en mi negocio?**
Por eso el diagnóstico va primero y es gratis. Si al revisar tu negocio no vemos una oportunidad clara, te lo decimos y no avanzamos: preferimos eso a cobrarte por algo que no te va a mover. Y una vez dentro, revisamos números cada semana, así que si algo no está funcionando se ve pronto, no a los seis meses.

**/04 — ¿La IA va a sonar como un robot con mis clientes?**
Se configura con tu forma de hablar, tus precios y tus servicios, y responde lo que se pregunta cien veces al día: horarios, ubicación, precios, disponibilidad. En cuanto la conversación se sale de ahí, o cuando ya hay intención de agendar, pasa a una persona de tu equipo.

**/05 — ¿Tengo que cambiar mis herramientas o mi equipo?**
No. El sistema se conecta al WhatsApp e Instagram que ya usas y a tu forma actual de agendar. Tu equipo sigue igual: lo único que cambia es que deja de contestar lo repetitivo y entra cuando la cita ya está en firme.

**/06 — ¿Me amarran a un contrato largo?**
No trabajamos con permanencias forzadas. La idea es que sigas porque los números te lo justifican cada mes, no porque firmaste algo hace un año.

⚠️ **Tres de estas comprometen condiciones comerciales**: que el precio se entrega
por escrito tras el diagnóstico, la revisión semanal de números, y que no hay
permanencia. Confirma que las tres son ciertas.

`app/routes.py` → lista `FAQS`

---

## 12. Formulario (modal)

**Titular:** Estás a un paso de dejar de *perder clientes*
**Subtítulo:** Agenda tu diagnóstico digital, sin costo.
**Campos:** Nombre completo · Correo · Teléfono (opcional) · ¿Qué necesita tu negocio?
**Botón:** Agendar mi diagnóstico
**Nota:** Te contactamos en menos de 24 horas.

---

## 13. Pie de página
LIFE — MARKETING + IA · CIUDAD DE MÉXICO

---

## Lo que se eliminó y por qué

**Barra "FORMADOS EN" (Udemy · Funnel School · UNAM).** Presentar cursos de Udemy
como credencial ante un dueño de clínica comunica formación de catálogo, no
experiencia en el sector. Restaba en la sección donde el método pide sumar
autoridad. Las tres imágenes de logos siguen en `static/img/` por si la recuperas.

**Sección "Casos de éxito" con tres tarjetas de "Próximamente".** Mostrar tres huecos
vacíos anuncia que no hay clientes. Mejor no tener la sección que tenerla vacía.

---

## Lo único que sigue sin cumplirse

**Parte 4 del método: testimonios y prueba social.** Es el hueco más caro y el único
que no puedo rellenar yo — inventar testimonios sería falsificar prueba social.

Con dos o tres que consigas, aunque sean en texto plano y sin foto, monto la sección
en el hueco que dejó "Casos de éxito". Pídeselos a vuestros primeros clientes
fundadores: basta una frase sobre qué cambió desde que trabajan con vosotros.

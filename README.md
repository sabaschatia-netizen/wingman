# Growth Wingman

Consulta de cartera por Farmer. Extracción reducida del módulo Brand Finder de
Growth OS — proyecto nuevo, no un fork de `app_glass.py`.

## Correr local

```bash
pip install -r requirements.txt
streamlit run wingmanapp.py
```


Paleta y logo propios de Wingman — ya no hereda los colores de Growth OS.

- **Logo**: extraído de `assets/`, dos versiones (`wingman_logo_full.png` con
  texto, `wingman_icon.png` solo el ícono), embebidos en `logo_asset.py`.
- **Paleta**: verde lima `#9CFB0A` (marca), carbón `#23272E`, gris `#5B5F66`
  — extraída por muestreo de píxeles del logo, no a ojo.
- **Modo**: dark mode. Fondo gris muy oscuro, cards más claras que el fondo
  (dan profundidad), sidebar y header en verde sólido.
- **Tipografía**: Poppins (antes DM Sans), coincide con la fuente del logo.
- **Semáforo de estado**: rojo/amarillo se mantienen para WATCH/ALERT. El
  verde de HEALTHY/Active es el mismo verde de marca — un solo verde en todo
  el sistema, por decisión explícita.

## Diseño (segundo rebrand)

Paleta y logo naranja/morado — reemplaza el rebrand verde/carbón anterior.

- **Logo**: wordmark "wingman" en `assets/`, fondo naranja sólido (no
  transparente — es parte del diseño). Embebido en `logo_asset.py`.
- **Paleta**: naranja `#F74D04` (sidebar, headers, marca), morado `#9A54F6`
  (hover, sombras), blanco `#FCFAF8` (texto sobre naranja) — extraída por
  muestreo de píxeles del logo.
- **Regla de color explícita**: sidebar y headers en naranja sólido. Hover de
  cualquier elemento interactivo en morado (no naranja, para no competir
  visualmente con los bordes de acento naranja que ya usan las cards).
  Sombras/profundidad también en morado.
- **Semáforo de estado** (HEALTHY/WATCH/ALERT): vuelve a ser verde/amarillo/
  rojo clásicos, independientes de la marca — con naranja como color de marca,
  ya no puede doblar como "alerta" al mismo tiempo.
- **Tipografía**: Poppins (sin cambios respecto al rebrand anterior).

## Login

Correo + contraseña. La contraseña es la parte del correo antes del `@`, en
minúsculas (ej. `sabas.ramirez@rappi.com` → contraseña `sabas.ramirez`).

**Aviso de seguridad:** esto es identificación, no autenticación fuerte —
cualquiera que sepa el correo de un Farmer puede calcular su contraseña. Sirve
para uso interno del equipo, pero si esto sale del equipo o necesita más
seguridad, conviene reemplazarlo por códigos reales vía `st.secrets`.

## Navegación

```
Login → Aterrizaje (tabla de prioridad + buscador) → Ficha de marca
                                                        (franja fija + 5 tabs)
```

El aterrizaje tiene 5 filtros por palanca (OPS / Menu / Markdown / MD PRO /
Ads) sobre la tabla de `PRIORITY DATA`. Al hacer clic en el nombre de una
marca (pill) o encontrarla por búsqueda, se muestra un telón de transición
(logo + barra deslizante, mismo lenguaje visual que Growth OS) y se abre la
ficha, con franja fija (nombre, ID, Churn, pills) y 5 tabs: Home, 360° Action,
Analytics, Campaign Designer, Outreach.

## Actualizar la data

Reemplazar `data/GROWTH_WINGMAN-ARG.xlsx` por la versión nueva. Hojas
requeridas: `ASIGNACION`, `ADS`, `AVA`, `MD`, `MD PRO`, `CVR%`, `TRAFFIC`,
`TOP PRODUCTS`, `MD NAMES`, `SEASONAL EVENTS`, `PRIORITY DATA`, `DETALLE`,
`PERFECT STORE`.

Las columnas **sí** pueden moverse de posición: todo se lee por nombre.

## Archivos

| Archivo | Qué hace |
|---|---|
| `wingmanapp.py` | UI: login, aterrizaje, ficha con tabs |
| `data_layer.py` | Loaders, normalización de IDs, cruces |
| `theme.py` | Paleta, tipografía, CSS y telón de transición |
| `logo_asset.py` | Logo G-Rocket en base64 |

## Decisiones cerradas

- **Filtro de cartera**: columna `BRAND_OWNER_EMAIL_NUEVO` de `ASIGNACION`.
- **Identidad**: correo + contraseña (ver aviso arriba).
- **País**: solo Argentina en v1. Cambiar `PAIS` en `data_layer.py` habilita UY.
- **Clave de marca**: `PAÍS + NÚMERO` (`AR16516`).
- **Read-only**: Wingman no escribe nada en el Excel.
- **LTOR Tier**: fuera de la ficha — se carga a mano en la fuente y no hay
  forma de confirmarlo automáticamente.
- **Bug heredado de Growth OS corregido**: la clasificación de palancas en
  Priority Data evaluaba "markdown" antes que "pro", así que **todas** las
  filas de "Promos Pro (Markdown Pro)" caían en el bucket MD normal y MD PRO
  siempre marcaba 0 cuentas. Se corrigió evaluando PRO primero.
- **Churn Status real**: hoja `CHURN` integrada. Trae varias semanas por marca
  (una fila por semana con riesgo activo) — se toma el estado de la semana
  MAS RECIENTE. Sin registro = "Disponible", no un dato faltante.
- **GMV/AOV con variación real vs mes anterior**: hoja `LAST GMV` (misma
  estructura que `DETALLE`) cruzada por Brand ID. Sin dato de mes anterior,
  no se fuerza una variación falsa.
- **ADS: fuente corregida a `EXPORT ADS`**, no la hoja `ADS` cruda —
  "Bookings Totales Corregidos" y "Revenue Real" son la medición oficial según
  Growth OS (ajustada por días de campaña inactiva). Esta hoja viene en USD:
  se convierte a ARS con `ARS_PER_USD = 1400` (misma referencia que Growth OS)
  directamente en el loader, antes de que la UI la use.
- **Búsqueda de Google sin teléfono**: Growth OS arma el query con nombre +
  categoría + país + teléfono. El teléfono tapa los resultados reales del
  restaurante con páginas de validación de número (bug conocido, sin corregir
  ahí). Wingman no lo replica: nombre + categoría + ciudad + Argentina.
- **Penetración MD/MD PRO calculada en vivo** (`MARKDOWN $ / GMV $`), no leída
  de una columna — mismo criterio que Growth OS, porque la columna de la hoja
  no siempre es consistente con los montos que la originan.
- **Nombres de campaña MD/MD PRO**: cruzados por nombre de marca contra
  `MD NAMES` (esa hoja no trae Brand ID). Una marca puede tener varias
  campañas; se muestran hasta 2, clasificadas como MD o MD PRO según si el
  texto contiene "pro"/"prime"/"exclusivo pro". Sin match = "-".
- **Bloque DEMANDA** (Conversión/CVR y Tráfico) movido de la tab Home a la tab
  Analytics.
- **360° Action reconstruido** con la misma lógica de negocio de Growth OS,
  traducida al español (el original mezcla inglés/español):
  - Card de contexto (gris, arriba): Coinversión MD, Teléfono, pills de
    palanca. Priority Score sacado a propósito.
  - Super-card con 4 tarjetas: OPS General, Menú, Markdown, Ads.
  - **OPS**: prioriza reclamos/cancelaciones/defectos/espera sobre
    disponibilidad pura cuando hay señal de riesgo, con las mismas fórmulas
    de Growth OS — reclamos con "el aliado absorbe 50%" del GMV en riesgo,
    cancelaciones con "absorbe el 100%", disponibilidad con upside
    proporcional al GMV real del mes. Requiere que `PRIORITY DATA` traiga
    una columna de descripción (texto con "% tasa") para calcular los montos
    de riesgo — hoy esa columna no existe en el export, así que sin ella el
    mensaje se muestra sin el monto estimado.
  - **Menú**: fotos y experiencia de compra con los mismos umbrales que
    Growth OS (90%/75%).
  - **Markdown**: mensaje según ROI (bajo <2, sano, alto >4) + nombre de
    campaña.
- **Analytics reconstruido** como una super-card: Funnel Tráfico & Conversión
  vs Benchmark arriba (con gráfico de embudo de 3 niveles y el mismo árbol de
  decisión de 6 ramas que Growth OS — sin datos, conversión fuerte sin
  tráfico medible, problema doble, problema de tráfico, problema de
  conversión, o ambas OK), y Dato Ancla + Benchmark abajo. Margen Neto/Orden
  y Punto de Equilibrio MD se sacaron de esta tab (confirmado: no van, falta
  comisión por marca para el primero). "Cómo decírselo al aliado" se sacó
  del funnel por ser redundante con el texto de arriba.
- **Bug corregido en Dato Ancla/Benchmark**: calculaban el percentil y el
  líder de categoría por **AOV**. Growth OS los calcula por **GMV**
  (`gmv_vals < brand_gmv` para el percentil, `idxmax()` de GMV para el
  líder) — se corrigió para usar la misma métrica. El mensaje de Dato Ancla
  ahora también tiene los 3 niveles de texto según el percentil (≥75%,
  50-74%, <50%), igual que el original.
- **Bug corregido en TRAFFIC**: la hoja trae el dato MENSUAL, no semanal.
  Growth OS lo trataba como semanal en varios lugares. Se corrige dividiendo
  entre 4 directamente en `load_traffic()`, así el resto de la app (Funnel de
  Analytics, Ads Plan) siempre recibe el valor semanal real sin tener que
  acordarse de la conversión en cada lugar que lo usa.
- **Campaign Designer construido**, reducido de las 4 cards de Growth OS a 2
  (Cross-Selling y Top 5 Products se eliminaron):
  - **Ads Plan · 12% Model** (ajustado de Growth OS, que usa 15% y CPC
    $1.000): presupuesto = 12% del GMV del mes anterior ÷ 4 semanas, modo
    Adquisición o Upselling según si ya hay Ads activo, con proyección
    completa (presupuesto ÷ CPC $950 = visitas → × CVR = pedidos
    incrementales → × AOV = GMV incremental).
  - **Markdown Plan**: regla nueva por tramo de conversión (reemplaza la
    regla de comisión+fotos+CVR de Growth OS, que no se puede replicar sin
    el dato de % de usuarios PRO por marca): CVR <10% → 25% OFF + 10% PRO;
    10-15% → 20% OFF + 5% PRO; ≥15% → 15% OFF + 5% PRO. Fusionado con los
    Top 3 Productos (antes era una card separada de Top 5), que se muestran
    siempre sin importar el tramo.
- **Home**: GMV y AOV ahora muestran el monto real de "Anterior" y "Actual"
  debajo del sparkline (antes solo se veía la línea, sin números). Att
  Revenue (ADS) y Penetración (Markdown/Markdown PRO) se movieron a un badge
  en la esquina superior derecha de cada card, coloreado por umbral: Att
  ≥90% verde / <90% rojo; Penetración ≥10% verde / <10% rojo. "Penet" pasó
  a decir "Penetración" completo.
- **Bug corregido en el gauge de Menú (360° Action)**: usaba `Global_Metric`
  de Perfect Store, un índice compuesto sin techo real (llega a 138.9% en
  la base — no es un porcentaje acotado). Corregido a `Perfect_Store_Pct`,
  que siempre va de 0 a 100.
- **360° Action — card de contexto**: se sacó el teléfono (ya está en la
  ficha de marca de arriba, era redundante). Queda solo Coinversión + pills
  de palanca.
- **Markdown y Ads en 360° Action — regla estricta**: si `PRIORITY DATA` no
  menciona esa palanca para la marca, el texto es solo "Seguimiento" (si ya
  hay campaña activa) o "Sin campaña aún" (si no hay) — sin el consejo
  largo de ROI. El consejo completo solo aparece cuando Priority Data sí
  trae la señal para esa palanca, igual que Growth OS.
- **Campaign Designer**: se sacó el texto pequeño de nota al pie de la card
  de Ads Plan ("Campaña nueva al modelo de presión...").
- **Home — Anterior/Actual**: el monto real se desbordaba y se pegaba
  visualmente (fuente 10px en negrita, ancho fijo de 96px). Corregido a
  fuente liviana (peso 400), 9.5px, con permiso de salto de línea si el
  número es largo.
- **Bug de "cero falso" corregido en el gauge de Menú (360° Action)**: dos
  capas del código trataban `0.0` como "sin dato" (`if pct else` y
  `if perfect_store_pct > 0`), cuando en realidad una marca puede tener
  legítimamente 0% de Perfect Store y aun así tener fotos/experiencia de
  compra reales (ej. "Sra Tabla": 77.5% de fotos, 0% de Perfect Store).
  Se corrigió para distinguir "sin ningún dato" (`None`) de "0% real" —
  confirmado que **1.036 de las 2.699 marcas del equipo (38%)** estaban
  afectadas, mostrando el consejo de fotos/compra sin ningún % visible.
- **Outreach reconstruido**: antes solo miraba disponibilidad (`< 90%`) y
  si no aplicaba, siempre caía en un texto genérico ("oportunidades de
  crecimiento activas") — nunca usaba las señales reales de Menú, Markdown
  o Ads. Se revisó el código real de Growth OS (`_first_priority_action`)
  y se replicó el mismo criterio de prioridad: OPS → Menú → Markdown → Ads,
  en ese orden, tomando la primera palanca que no esté estable. Texto corto
  y genérico por palanca (no el título largo de la card), según pedido
  explícito. Los 5 tipos de plantilla de Growth OS (Presentación/
  Seguimiento/Activación/No Contactado/Churn) y el "tono" del mensaje
  dependen de un `opportunity_status` de pipeline de negociación que no
  existe en nuestro Excel — no se replicaron; queda un solo tipo de mensaje
  (equivalente al "Seguimiento" genérico, que no depende de ese estado).
- **Markdown y Ads en 360° Action**: nunca llevan porcentaje (se pasaba `0`
  en vez de `None`, y con el fix de "cero falso" de la sesión anterior eso
  se mostraba indebidamente como "0%"). Corregido a `None` explícito — solo
  Menú y OPS General llevan %.
- **Bug real corregido en OPS General (360° Action)**: el % mostrado no
  correspondía al consejo que lo acompañaba. Cuando ganaba una señal como
  Churn, el título hablaba de Churn pero el % mostrado seguía siendo
  Disponibilidad — sin relación entre sí (caso real: "Chipa de Autor",
  Churn ganaba la prioridad, disponibilidad real 24% se mostraba sin que
  el texto la mencionara). Reglas corregidas: si gana Churn → 0% (no es
  comparable con un % real); si gana Disponibilidad → su % real; si gana
  reclamos/cancelaciones/defectos/espera → sin % propio, pero si ADEMÁS la
  disponibilidad está baja (<90%) se menciona como dato adicional en el
  detalle, para no perder ese hallazgo.
- **Outreach reescrito para listar TODOS los hallazgos**, no solo el
  primero. Nueva función `outreach_hallazgos()` (reemplaza
  `outreach_priority_frente()`) que recorre OPS/Menú/Markdown/Ads sin
  cortar en la primera señal — si una marca tiene 3 problemas reales, los
  3 aparecen numerados en el mensaje. Si no hay ningún hallazgo negativo,
  cae en un mensaje de "Seguimiento de tu marca", con matiz según si ya
  tiene campañas activas (sostener el ritmo) o no (proponer adquisición).
- **Menú (360° Action) — corregido a la fórmula real de Growth OS**, no
  la columna `Perfect_Store_Pct` cruda. Growth OS calcula un
  `menu_health` compuesto: `fotos×42% + compra×42% + perfect_bonus×16%`.
  Se replicó esa fórmula (adaptada a nuestras columnas 0-100, Growth OS
  las trae en 0-1), usando `Perfect_Store_Pct/100` como proxy del
  `perfect_bonus`. Antes, marcas con `Perfect_Store_Pct = 0` mostraban
  "0%" en el gauge aunque tuvieran fotos/experiencia de compra altas (caso
  real: 58% de experiencia de compra mostraba 0%). La penalización por
  `Missing_Products` de la fórmula original se sigue omitiendo — el rango
  real en nuestra base (3.5–223.5) no es la unidad chica que esa parte de
  la fórmula asume. Ahora también se listan ambos hallazgos (fotos Y
  compra) si los dos están bajos, no solo el peor.
- **OPS General (360° Action) — corregido para listar TODAS las señales
  activas**, no solo la de mayor valor. Bug real encontrado: una marca con
  3 señales simultáneas (reclamos, tiempo de espera, disponibilidad baja)
  solo mostraba una en la card — las otras dos se perdían aunque sí
  aparecían correctamente en el mensaje de Outreach (que ya recorría
  todas). Ahora la card lista el mismo conjunto completo que el Outreach.
- **Coinversión implementada en Markdown Plan**, con las reglas reales de
  Growth OS (`COINV_GROUPS`): 6 grupos con ratio Aliado:Rappi fijo (New
  Hunters 4:1, New Rest 2:1, Churn Prevention 2:3, Prioritized 2:1, Rest
  3:1; Churn es el único sin coinversión). Bug de fondo encontrado: nuestra
  columna de coinversión (`ASIGNACION`, columna sin nombre) solo trae el
  grupo (ej. "5. Prioritized"), sin el flag `SI`/`NO` de habilitación real
  que usa Growth OS. Se asumió, con confirmación explícita, que toda marca
  con grupo asignado (menos Churn) tiene coinversión potencialmente
  disponible. En nuestra base solo aparecen 2 de los 6 grupos: Prioritized
  (660 marcas) y Rest (1.193 marcas). Cuando hay coinversión, la campaña
  pasa a ser siempre **30% OFF + PRO** (5% o 10% según el mismo criterio de
  CVR), con el reparto Aliado:Rappi calculado sobre el **descuento total
  combinado** (30%+PRO), no por separado — pedido explícito. La
  recomendación por defecto (15/20/25% según CVR) queda como referencia en
  una pill debajo, sin desaparecer.
- **Navegación de 2 secciones agregada al sidebar**: Brand Finder (por
  defecto al entrar) y Management Dashboard, calcados de la estructura de
  Growth OS.
  - **Brand Finder simplificado**: se eliminó la tabla de "Prioridad de
    Contacto" (pills OPS/Menu/Markdown/MD PRO/Ads + ranking clickeable) —
    esa función ya vive en Smart Priority. Ahora solo queda la barra de
    búsqueda, y pasó de ser por **nombre** a ser por **ID**, con la misma
    lógica flexible de Growth OS (`brand_key()` ya normalizaba variantes
    como "AR97338", "97338" o "AR-97338" con basura alrededor a la misma
    clave canónica — se reusa esa función, no hubo que escribir nada nuevo).
  - **Management Dashboard nuevo**, con 2 cards apiladas:
    - **Brand Coverage · Live** (6 donuts): % de la cartera del Farmer con
      Ads activo, Markdown activo, Markdown PRO activo, y en riesgo PW1/
      PW2/Churn (según la hoja `CHURN`). PW2 hoy siempre da 0% — el export
      actual solo trae los estados PW1 y Churn, ningún caso real de PW2/PW3
      todavía; no es un bug, es que el dato no existe aún en la base.
    - **Contact Performance**: contactos efectivos desde el 1° del mes
      actual (mismo criterio que Growth OS), desglosados por canal —
      Amazon Connect, WhatsApp/Treble, Videoconferencia, y "No Contactado".
      Fuente: hoja nueva `PRODUCTIVITY` del Excel (trae `Farmer`, `Medio de
      Contacto`, `¿Contactado?`, `Date` por registro de contacto).
  - **Header naranja**: ya no muestra "X marcas en cartera" debajo del
    nombre del Farmer — ahora muestra el nombre de la sección activa
    ("Brand Finder" o "Management Dashboard").
  - **Botón "Salir"** anclado al final del sidebar (antes quedaba pegado
    justo debajo de la pill del Farmer).
- **Loader corregido para no tapar el sidebar**: antes usaba
  `position: fixed; inset: 0`, cubriendo toda la ventana del navegador.
  Ahora el overlay solo tapa el marco de contenido, dejando el sidebar
  visible siempre — ver el punto siguiente para el ajuste final de esta
  sesión.

- **Bug real corregido: Management Dashboard tumbaba toda la pantalla con
  `AttributeError`** en producción (no reproducible con el Excel local —
  el archivo real en el servidor difiere del usado en desarrollo, o hay
  una versión de pandas/Streamlit distinta ahí). Se blindaron
  `brand_coverage_for()` y `contact_performance_for()` con try/except real
  — probado forzando el fallo a propósito (`AttributeError` simulado): la
  primera versión del blindaje tenía un bug propio (el `except` volvía a
  llamar a la función que había fallado, y explotaba en cascada); corregido
  para devolver el estado base sin reintentar nada.
- **Botón "← Volver a la cartera" eliminado** de la ficha de marca.
  Reemplazado por una barra de búsqueda siempre visible arriba (misma
  lógica flexible de ID que Brand Finder) — el Farmer puede saltar directo
  de una marca a otra pegando el siguiente ID, sin fricción de volver
  atrás. Probado el flujo completo: entrar a una marca y saltar a otra
  distinta sin pasar por "Volver".
- **Loader: intento final para que no tape el sidebar.** El primer intento
  (`position:relative` en `[data-testid="stMain"]` + `absolute` en el
  overlay) seguía sin funcionar en producción — probablemente porque
  `requirements.txt` fija `streamlit>=1.32` sin techo, y el servidor instaló
  una versión con nombres de contenedor internos distintos a los probados
  en desarrollo local. Se descartó una alternativa con JavaScript (medir el
  sidebar con `getBoundingClientRect` y fijar el `left` del overlay
  dinámicamente): un `<script>` inyectado vía `st.markdown(unsafe_allow_html)`
  no tiene garantía de ejecutarse en el navegador. Solución final: CSS puro
  dando `position:relative` a **varios selectores candidatos a la vez**
  (`stMain`, `stAppViewContainer > div:nth-child(2)`,
  `stAppViewBlockContainer`, `.main`) — el que no exista en la versión
  activa simplemente no hace nada, sin romper nada. *Este punto no se pudo
  confirmar visualmente en un navegador real desde el entorno de
  desarrollo — si sigue sin funcionar tras esta versión, avisar para seguir
  ajustando con el nombre exacto del contenedor de esa versión de
  Streamlit.*
- **Bug real corregido: `load_top_products()` no reconocía el formato
  nuevo de la hoja `TOP PRODUCTS`.** En la sesión de filtrado del archivo
  de productos más vendidos, se armó con columnas nuevas (`Brand_ID`,
  `Brand_Name`, `Product_Name`, ya cruzado por marca), pero el loader
  seguía esperando el formato viejo (`COUNTRY_STORE_ID`, `NAME`, a nivel
  store, con cruce vía `AVA`) — se actualizó el dato sin actualizar el
  código que lo lee. Resultado en producción: aviso "Falta
  COUNTRY_STORE_ID o NAME" y Campaign Designer sin Top 3 Productos para
  ninguna marca. Corregido: `load_top_products()` ahora reconoce ambos
  formatos (nuevo primero, viejo como respaldo). Confirmado con el Excel
  real: 6.750 filas, 2.268 marcas mapeadas, cero avisos de datos.
- **Panel de "avisos de datos" eliminado del sidebar.** Era una ayuda de
  debugging agregada mientras se construía el proyecto (la que de hecho
  ayudó a diagnosticar el bug de `TOP PRODUCTS` de esta misma sesión) —
  correcta la decisión de sacarla: es información técnica que no debe
  verse en el uso diario de un Farmer. `dl.data_issues()` sigue existiendo
  por si hace falta diagnosticar algo puntual a futuro, solo se ocultó del
  render.
- **Brand Coverage: conteo absoluto de marcas debajo de cada donut.**
  `brand_coverage_for()` solo devolvía la fracción (0–1) de cada palanca;
  se agregaron las claves `*_n` con el conteo real (`ads_n`, `md_n`,
  `mdpro_n`, `pw1_n`, `pw2_n`, `churn_n`), mostradas en letra chica sin
  resaltar debajo de la etiqueta de cada donut — ej. "34% · Ads · 69
  marcas". Confirmado con datos reales.
- **Loader: diagnóstico correcto encontrado y corregido.** Los intentos
  anteriores (variar `position: absolute/fixed` y selectores CSS
  candidatos) atacaban la causa equivocada. La causa real, confirmada con
  capturas: `show_transition()` se llamaba a MITAD del script, después de
  que el header y el buscador de esa misma pasada ya se habían pintado —
  por eso quedaban visibles "detrás" del loader (no era un problema de
  z-index ni transparencia, era contenido pintado ANTES en el mismo
  flujo). Corregido con una bandera `pending_transition` en
  `session_state`, chequeada al principio absoluto del script, antes de
  pintar el sidebar. Cuando hay una transición pendiente, el loader se
  pinta como lo único que existe en esa pasada, y el script hace
  `st.rerun()` de inmediato sin pintar nada más. El CSS de `#gw-loading`
  ya no necesita `position: absolute/fixed` ni selectores candidatos —
  vive en su posición natural del flujo del documento.
- **Header perdido en la ficha de marca — corregido.** Al reemplazar el
  botón "Volver a la cartera" por la barra de búsqueda (sesión anterior),
  se olvidó volver a llamar a `header()` en esa vista. Ahora se muestra
  siempre, con el nombre de la marca activa como "sección" en el
  subtítulo.
- **Header invertido**: logo ahora a la derecha (`header-logo-right`,
  `margin-left:auto`), nombre del Farmer + sección activa ahora a la
  izquierda (`header-left`, alineado a la izquierda). Antes era al revés.
- **Bug real corregido: PDF Menu de Priority Data no se reflejaba en la
  card de Menú ni en Outreach.** `menu_tactical_card()` y
  `outreach_hallazgos()` solo miraban `photos_pct`/`purchase_pct`, nunca
  consultaban `signals_for_brand()` para la señal `menu_pdf` — una marca
  podía tener "PDF Menu" mencionado en la card de contexto de Priority
  Data (arriba) mientras la card de Menú decía "sin issues detectados"
  (abajo). Corregido en ambas funciones; confirmado con una marca real
  ("A la Tarta") que sí tiene esa señal.
- **Loader agregado al cambio de sección** (antes cambiaba de Buscador de
  Marcas a Gestión General, o viceversa, sin ninguna transición visual).
- **Renombres**: "Brand Finder" → **"Buscador de Marcas"**, "Management
  Dashboard" → **"Gestión General"**. Las keys internas del código
  (`section == "brand_finder"`, etc.) no cambiaron, solo las etiquetas
  visibles — no hizo falta tocar el resto de la lógica que compara contra
  esas keys.
- **Voseo argentino corregido a español neutro** en todos los textos
  visibles encontrados: login ("Ingresá"→"Ingresa", "Completá"→
  "Completa"), buscador ("Escribí"→"Escribe" ×2), Outreach ("Preferís"→
  "Prefieres"), y varios textos del diagnóstico de funnel en Analytics
  ("Activá"→"Activa" ×2, "perdés"→"pierdes", "llegás"→"llegas", "te estás
  perdiendo"→"se están perdiendo").
- **Loader reconstruido de raíz, calcado de la arquitectura real de
  Growth OS.** Los intentos anteriores (CSS `position:absolute/fixed` +
  selectores candidatos, luego una bandera `pending_transition` en
  `session_state` con `st.markdown()` + `time.sleep()` + `st.rerun()`
  manual) atacaban síntomas, no la causa real: confirmado con
  `AppTest` que `st.rerun()` sí corta la ejecución de inmediato (no era
  un problema de "el script sigue pintando después"), pero Streamlit no
  da ninguna garantía de sincronización entre "Python terminó de pintar
  un frame" y "el navegador terminó de renderizarlo" — con reruns
  manuales, ambos frames (loader viejo, contenido nuevo) podían quedar
  visibles a la vez de forma persistente (confirmado con capturas reales:
  logo del loader arriba, contenido de Management Dashboard ya
  renderizado y visible abajo, sin que fuera solo un instante de
  transición). Solución real: se copió la arquitectura completa que ya
  usa Growth OS (`_show_loading_overlay` / el bloque de JS de navegación
  en `app_glass.py`) — `st.components.v1.html()` en vez de `st.markdown()`
  (es la única forma de garantizar que el `<script>` se ejecute; el
  navegador no corre `<script>` insertado vía `innerHTML`), con un
  mecanismo que:
  - Escucha clics/teclas directamente en el navegador (sidebar y
    buscador de marca), mostrando el overlay al instante, sin esperar a
    que Python reciba el evento.
  - Detecta cuándo Streamlit realmente terminó de trabajar observando sus
    propios indicadores de estado en el DOM (`stStatusWidget`,
    `data-test-script-state`, `.stSpinner`, `stSkeleton`) más un
    `MutationObserver` que vigila si el DOM sigue mutando — no con un
    `time.sleep()` de duración fija adivinada.
  - Mide el sidebar en tiempo real (`getBoundingClientRect`) para calcular
    el `left` del overlay — el sidebar queda visible siempre.
  - Se re-engancha en cada ejecución del script (vive en
    `window.parent`, sobrevive a la destrucción de iframes).
  Ya no depende de banderas en `session_state` ni de reruns manuales para
  el loader — `render_loading_watcher()` se llama una sola vez, siempre,
  justo después del login.
- **Header: logo pegado al texto en vez de en la esquina — corregido.**
  Se agregó `width: 100%` explícito a `.app-header`: el contenedor que
  genera `st.markdown()` puede no expandirse automáticamente al ancho
  completo disponible en todas las versiones de Streamlit, lo que hacía
  que `margin-left: auto` del logo no tuviera "espacio extra" hacia el
  cual empujarse. *Este ajuste no se pudo confirmar visualmente en un
  navegador real desde el entorno de desarrollo — si el logo sigue
  viéndose pegado tras esta versión, avisar con otra captura para seguir
  ajustando.*
- **Header: logo seguía pegado tras el intento anterior (`width: 100%`)
  — segundo intento con un enfoque distinto.** Se reemplazó
  `margin-left: auto` (que depende de que el contenedor tenga espacio
  "extra" disponible de una forma específica) por
  `justify-content: space-between` en `.app-header` — el patrón CSS más
  directo para "un elemento en cada extremo", que reparte el espacio
  entre los elementos existentes sin importar el ancho real del
  contenedor. Se quitó el `gap: 14px` del padre (con `space-between` ya
  no hace falta, y competiría con la distribución). *Tampoco se pudo
  confirmar visualmente en un navegador real — si el problema persiste,
  puede hacer falta inspeccionar el HTML real con las herramientas de
  desarrollador del navegador para encontrar la causa exacta en vez de
  seguir probando por descarte.*
- **Brand Coverage rediseñado: Ads/Markdown/MD PRO "activo o no" (base
  marcas de la cartera) reemplazados por Conversión de Ads y Conversión
  de MD (base gestiones reales de `PRODUCTIVITY` ese mes)**, manteniendo
  PW1/PW2/Churn — queda en 5 donuts, no 6. Nueva función
  `conversion_for()`, y `load_productivity()` ampliada para traer también
  `Ads`, `Tipo Ads`, `Tipo Never Ads`, `Markdown`, `¿Se aceptó lo
  ofrecido?`.
  - **Markdown**: convierte si `Markdown="SI"` (se hizo la gestión) Y
    `¿Se aceptó lo ofrecido?="Sí"` (el aliado aceptó).
  - **Ads**: convierte si `Ads="SI"` y `Tipo Ads` es cualquier cosa
    distinta de "Never Ads"; si es "Never Ads", solo NO convierte cuando
    `Tipo Never Ads="No activo"` — "Con coinversión"/"Sin coinversión" SÍ
    cuentan como conversión (el aliado aceptó, con o sin apoyo de
    coinversión). Bug propio encontrado y corregido en el camino: la
    primera comparación usaba "Sin Coinversión" con mayúscula, pero el
    Excel real trae "Sin coinversión" con minúscula — se corrigió a
    comparación case-insensitive.
  - **Es acumulado del mes**, no un corte diario — se recalcula solo cada
    vez que `PRODUCTIVITY` trae datos nuevos (mismo filtro "desde el 1°
    del mes actual" que ya usa Contact Performance).
  - **Bases distintas conviven en la misma card**: Conversión Ads/MD mide
    % de gestiones ("50 de 73 convirtieron"), PW1/PW2/Churn mide % de
    marcas de la cartera ("12 marcas") — confirmado con Sabas que está
    bien así, con el texto de abajo de cada donut aclarando la base real.
  - **Hallazgo importante para el lanzamiento**: el filtro de fecha corta
    a cero si el Excel no tiene datos del mes calendario actual (ej. hoy
    es agosto y el Excel solo trae julio) — no es un bug nuevo, ya lo
    tenía Contact Performance desde antes sin que se hubiera notado.
    Actualizar el Excel con datos del mes vigente antes de compartir el
    link al equipo.

## Pendiente (sin fuente de datos todavía)

- **Margen Neto / Orden** (Analytics) — falta food cost y comisión por marca.
- **# Contacto (orden de marcado), Último Contacto, Vencida/Por vencer** —
  sin fuente en `PRIORITY DATA` (formato actual: `BID | Metric | Prioridad BD`,
  sin esas columnas). Se agregan solas en cuanto el Excel las traiga.
- **"Productos faltantes" de Perfect Store** (`menu_missing`) — el rango real
  observado es 12 a 214, no puede ser el porcentaje que Growth OS asume. Se
  omitió esta condición del catálogo hasta confirmar qué unidad es realmente.

## Cobertura de data por Farmer (aprox.)

| Fuente | Rango |
|---|---|
| ADS | 37-57% (normal: solo marcas con pauta activa) |
| Availability / MD / MD PRO | 53-99% |
| Priority Data | 88-100% |
| CVR / Traffic (cruzan por nombre) | 66-100% |
| DETALLE (GMV/AOV/Categoría) | 58-97% |
| PERFECT STORE (gauge Menu) | 61-97% |
| Top Products / LTOR-Categoría de `MD NAMES` | Solo cartera de Sabas — falta reexportar a nivel equipo |

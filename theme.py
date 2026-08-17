"""
Sistema de diseño de Growth Wingman v3 — dark mode, marca naranja/morado.

Segundo rebrand: reemplaza la paleta verde/carbon (v2) por naranja/morado,
extraida por muestreo de pixeles del logo nuevo (wordmark "wingman" blanco
sobre fondo naranja solido, con 3 puntos morados decorativos).

Reglas de color explicitas del usuario:
  - Sidebar y headers: naranja solido, texto blanco.
  - Hover (cualquier elemento interactivo): MORADO, no naranja — el naranja ya
    esta muy presente en superficies grandes y como color de "activo/marca",
    así que reusarlo en hover generaba demasiado ruido visual.
  - Sombras / profundidad de cards: morado.
  - Semaforo de estado (HEALTHY/WATCH/ALERT): vuelve a ser independiente de la
    marca — verde/amarillo/rojo clasicos. El naranja ya no puede significar
    "alerta" y "marca" al mismo tiempo, asi que se desacoplan.
"""

import base64
import io

from logo_asset import WINGMAN_ICON_B64, WINGMAN_LOGO_FULL_B64

# =========================
# PALETA — extraida por pixel del logo v2, mas dark mode
# =========================
COLORS = {
    # Marca (del logo)
    "brand_orange":     "#F74D04",   # naranja — sidebar, headers, marca
    "brand_orange_soft": "rgba(247,77,4,0.14)",
    "brand_purple":     "#9A54F6",   # morado — hover, sombras
    "brand_purple_soft": "rgba(154,84,246,0.16)",
    "brand_white":      "#FCFAF8",   # texto sobre naranja

    # Superficies (light mode)
    "bg":              "#F7F6F2",   # fondo general, blanco marfil/hueso tibio
    "card":            "#FFFFFF",   # cards, mas claras que el fondo (contraste)
    "card2":           "#EFEEE9",   # segundo plano (stat boxes, inputs)
    "sidebar":         "#F74D04",   # sidebar naranja solido

    # Texto
    "text":            "#23272E",   # texto principal, oscuro sobre fondo claro
    "muted":           "#6B7280",   # texto secundario
    "text_disabled":   "#9CA3AF",
    "sidebar_text":    "#FCFAF8",   # texto blanco sobre el sidebar naranja

    # Bordes
    "border":          "#E4E1D8",   # borde sutil, visible sobre fondo claro
    "border_hover":    "rgba(154,84,246,0.45)",   # hover = morado

    # Estado — semaforo clasico e independiente de la marca.
    "success":         "#22C55E",
    "success_soft":    "rgba(34,197,94,0.14)",
    "warning":         "#FBBF24",
    "warning_soft":    "rgba(251,191,36,0.16)",
    "danger":          "#EF4444",
    "danger_soft":     "rgba(239,68,68,0.16)",

    # Acentos por palanca (bordes izquierdos de las mini-cards)
    "accent":          "#F74D04",   # acento = marca (naranja)
    "blue":            "#6C9BD1",   # se mantiene para diferenciar MD de ADS visualmente
    "purple":          "#9A54F6",
    "info_bg":         "rgba(108,155,209,0.12)",
}

LOGO_FULL_URI = "data:image/png;base64," + WINGMAN_LOGO_FULL_B64
LOGO_ICON_URI = "data:image/png;base64," + WINGMAN_ICON_B64


def logo_img(size=40, radius=0, full=False):
    """<img> listo para inyectar. full=True usa el logo con texto 'wingman'."""
    uri = LOGO_FULL_URI if full else LOGO_ICON_URI
    return (
        f'<img src="{uri}" alt="Wingman" '
        f'style="height:{size}px;width:auto;max-width:none;flex-shrink:0;'
        f'border-radius:{radius}px;display:inline-block;object-fit:contain;"/>'
    )


def favicon():
    try:
        from PIL import Image

        return Image.open(io.BytesIO(base64.b64decode(WINGMAN_ICON_B64)))
    except Exception:
        return "🤝"


# =========================
# CSS
# =========================

def build_css(login=False):
    LOGIN_CSS = (
        f'[data-testid="stAppViewContainer"] {{'
        f'  background: {COLORS["brand_orange"]} !important;'
        f'  min-height: 100vh; overflow-x: hidden;'
        f'}}'
        f'[data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"] {{'
        f'  display: flex; align-items: center; min-height: 100vh; overflow-x: hidden;'
        f'}}'
        f'html, body {{ overflow-x: hidden !important; }}'
        if login else ""
    )
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

* {{ font-family: 'Poppins', sans-serif; }}

{LOGIN_CSS}

/* ── APP BACKGROUND — dark ── */
.stApp {{
    background: {COLORS["bg"]} !important;
    color: {COLORS["text"]};
}}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
    background: {COLORS["bg"]} !important;
}}

.block-container {{ padding-top: 2.2rem; max-width: 1500px; }}

/* ── SIDEBAR — naranja solido, FIJA (pedido explícito de Sabas, agosto
   2026, cuarto ajuste). Los intentos anteriores con la sidebar NATIVA de
   Streamlit fallaron (botón de colapsar imposible de neutralizar de
   forma confiable entre versiones). Se dejó de usar st.sidebar por
   completo -- la "sidebar" es la primera de dos st.columns() (ver
   wingmanapp.py, col_sidebar/col_main), con st.container(key=
   "wingman-sidebar") adentro para tener un selector estable.

   BUG REAL CORREGIDO (cuarto ajuste): pintar .st-key-wingman-sidebar
   directamente no alcanzaba -- ese elemento es un stVerticalBlock
   INTERNO, no la columna en sí. La columna real que Streamlit genera es
   un div[data-testid="stColumn"] que envuelve a
   .st-key-wingman-sidebar varios niveles más arriba (confirmado
   inspeccionando el DOM real con un navegador). Sin pintar ESE
   contenedor, el fondo naranja no cubre toda la columna -- se veía
   blanco/gris alrededor del contenido real.

   Se usa :has() (selector CSS estándar, soportado en navegadores
   modernos) para encontrar "el stColumn que contiene un descendiente
   con la clase .st-key-wingman-sidebar", sin depender de las clases
   auto-generadas de Streamlit (st-emotion-cache-...) que cambian entre
   builds y no son estables para apuntar con CSS.

   position: fixed (no sticky) para que la sidebar quede pegada al
   viewport real y NO se mueva al scrollear el contenido principal --
   left:0/top:0 la ancla al borde izquierdo real de la ventana, no al
   borde del layout centrado de Streamlit (que dejaba un margen blanco
   antes de la sidebar). El stMainBlockContainer se compensa con
   margin-left para que el contenido de la derecha no quede tapado
   debajo de la sidebar fija. */
div[data-testid="stColumn"]:has(.st-key-wingman-sidebar) {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    bottom: 0 !important;
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
    background: {COLORS["sidebar"]} !important;
    box-shadow: 2px 0 24px rgba(0,0,0,0.30) !important;
    z-index: 999 !important;
    overflow-y: auto !important;
}}
/* Compensar el contenido principal para que no quede tapado por la
   sidebar fija -- el layout de columnas de Streamlit normalmente pondría
   el contenido justo al lado, pero al sacar la sidebar del flujo normal
   (position:fixed la saca del flujo del documento) hay que correr el
   resto manualmente. */
section[data-testid="stMain"] .stMainBlockContainer {{
    margin-left: 260px !important;
}}
.st-key-wingman-sidebar {{
    background: {COLORS["sidebar"]} !important;
    padding: 14px 12px !important;
    display: flex !important; flex-direction: column !important; min-height: 100vh !important;
}}
.st-key-wingman-sidebar * {{ color: {COLORS["sidebar_text"]} !important; }}

.st-key-wingman-sidebar .stTextInput input {{
    background: rgba(252,250,248,0.14) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(252,250,248,0.30) !important;
    color: {COLORS["sidebar_text"]} !important;
}}
/* BUG REAL CORREGIDO (agosto 2026, quinto ajuste): estas reglas tenian
   la MISMA especificidad que la regla genérica .stButton button (mas
   abajo en la hoja) -- en un empate de especificidad, CSS le da la
   victoria a la que aparece despues en el archivo, sin importar
   !important de los dos lados (!important solo empata la CAPA de
   importancia; adentro de esa capa sigue rigiendo cascada normal). Los
   botones de la sidebar terminaban con el texto gris oscuro y fondo gris
   claro genericos del area principal, casi ilegibles sobre el fondo
   naranja. Se agrega ".stButton" al selector para que la especificidad
   sea mayor (2 clases + elemento, no 1 clase + elemento) y gane siempre,
   sin depender del orden de declaración en el archivo. */
.st-key-wingman-sidebar .stButton button {{
    background: rgba(252,250,248,0.14) !important;
    color: {COLORS["sidebar_text"]} !important;
    border: 1px solid rgba(252,250,248,0.30) !important;
    font-weight: 700 !important;
}}
.st-key-wingman-sidebar .stButton button:hover {{
    background: {COLORS["brand_purple"]} !important;
    border-color: {COLORS["brand_purple"]} !important;
    color: {COLORS["brand_white"]} !important;
}}

.logout-anchor {{ margin-top: auto; padding-top: 20px; }}

/* Navegación de 2 secciones (Management Dashboard / Brand Finder): texto
   alineado a la izquierda en los botones de nav. El resaltado del botón
   ACTIVO (fondo blanco/texto naranja) ya NO se resuelve acá -- dependía
   de un <div class="nav-btn-active"> wrapper que en Streamlit moderno
   queda vacío (cada elemento tiene su propio contenedor aislado, el div
   nunca envolvió al botón real). Se resuelve con CSS dinámico inyectado
   desde wingmanapp.py, apuntando directo al key del botón activo
   (.st-key-nav_management o .st-key-nav_brand_finder según
   st.session_state["section"]). */
.st-key-wingman-sidebar .stButton button {{
    text-align: left !important; justify-content: flex-start !important;
}}

/* ── INPUTS Y BOTONES (area principal) ── */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{
    background: {COLORS["card2"]} !important;
    color: {COLORS["text"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 10px !important;
}}
.stTextInput input::placeholder {{ color: {COLORS["text_disabled"]} !important; }}

.stButton button {{
    background: {COLORS["card2"]} !important;
    color: {COLORS["text"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
.stButton button:hover {{
    border-color: {COLORS["brand_purple"]} !important;
    color: {COLORS["brand_purple"]} !important;
}}
.stButton button[kind="primary"] {{
    background: {COLORS["brand_orange"]} !important;
    color: {COLORS["brand_white"]} !important;
    border: none !important;
    font-weight: 800 !important;
}}
.stButton button[kind="primary"]:hover {{
    background: {COLORS["brand_purple"]} !important;
    color: {COLORS["brand_white"]} !important;
}}

/* ── HEADER (area principal, naranja solido igual que sidebar) ── */
.app-header {{
    display: flex; align-items: center; justify-content: space-between;
    width: 100%;
    background: {COLORS["sidebar"]};
    border-radius: 18px;
    padding: 16px 22px;
    margin-bottom: 18px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.25);
}}
.app-header .header-title, .app-header .header-subtitle {{
    color: {COLORS["sidebar_text"]} !important;
}}
.header-left {{
    text-align: left;
}}
.header-logo-right {{
    display: flex; align-items: center;
}}
.header-title {{
    font-size: 21px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.15;
}}
.header-subtitle {{ font-size: 12.5px; font-weight: 600; opacity: 0.75; }}
.period-pill {{
    background: rgba(35,39,46,0.14);
    color: {COLORS["sidebar_text"]}; font-size: 11.5px; font-weight: 700;
    padding: 6px 13px; border-radius: 999px; white-space: nowrap;
}}

.section-title {{
    font-size: 13px; font-weight: 700; color: {COLORS["muted"]};
    letter-spacing: 0.3px; margin: 22px 0 10px 2px;
}}

/* ── CARDS — mas oscuras que el fondo, dan profundidad ── */
.glass-card, .metric-card, .brand-card, .info-card, .hero-card, .stack-card {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 4px 18px rgba(154,84,246,0.08);
    transition: border-color .18s, box-shadow .18s, transform .18s;
}}
.glass-card:hover, .metric-card:hover, .brand-card:hover,
.info-card:hover, .hero-card:hover, .stack-card:hover {{
    border-color: {COLORS["border_hover"]};
    box-shadow: 0 8px 26px rgba(154,84,246,0.22);
    transform: translateY(-1px);
}}

/* ── MINI CARDS POR PALANCA ── */
.business-card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
}}
.business-mini-card {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["border"]};
    border-radius: 14px;
    padding: 15px 17px;
    box-shadow: 0 2px 10px rgba(154,84,246,0.06);
    transition: border-color .18s, box-shadow .18s, transform .18s;
    position: relative;
}}
.business-mini-card:hover {{
    box-shadow: 0 8px 22px rgba(154,84,246,0.20);
    border-color: {COLORS["border_hover"]};
    transform: translateY(-1px);
}}
.business-mini-card.lever-ads   {{ border-left: 3px solid {COLORS["brand_orange"]} !important; }}
.business-mini-card.lever-md    {{ border-left: 3px solid {COLORS["blue"]} !important; }}
.business-mini-card.lever-pro   {{ border-left: 3px solid {COLORS["brand_purple"]} !important; }}
.business-mini-card.lever-menu  {{ border-left: 3px solid #6B7280 !important; }}

.corner-badge {{
    position: absolute; top: 12px; right: 14px;
    font-size: 11px; font-weight: 800;
    padding: 2px 9px; border-radius: 999px;
}}

.card-label {{
    font-size: 10.5px; font-weight: 700; color: {COLORS["muted"]};
    letter-spacing: 0.7px; text-transform: uppercase; margin-bottom: 5px;
}}
.card-value {{
    font-size: 22px; font-weight: 800; color: {COLORS["text"]};
    letter-spacing: -0.5px; line-height: 1.15;
}}
.card-copy {{ font-size: 11.5px; color: {COLORS["muted"]}; margin-top: 6px; line-height: 1.5; }}
.card-chip {{
    display: inline-block; font-size: 10.5px; font-weight: 700;
    padding: 3px 9px; border-radius: 999px; margin-left: 7px;
}}

/* ── PILLS DE CONTEXTO ── */
.pill-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 2px 0; }}
.ctx-pill {{
    font-size: 12px; font-weight: 600; padding: 8px 14px;
    border-radius: 12px; border: 1px solid {COLORS["border"]};
    background: {COLORS["card2"]}; color: {COLORS["text"]};
}}
.ctx-pill.warn   {{ background: {COLORS["warning_soft"]}; color: #FBBF24; border-color: rgba(251,191,36,0.30); }}
.ctx-pill.alert  {{ background: {COLORS["danger_soft"]};  color: #F0575A; border-color: rgba(240,87,90,0.30); }}
.ctx-pill.ok     {{ background: {COLORS["success_soft"]}; color: {COLORS["success"]}; border-color: rgba(34,197,94,0.30); }}
.ctx-pill.info   {{ background: {COLORS["info_bg"]};      color: {COLORS["blue"]}; border-color: rgba(108,155,209,0.30); }}

/* ── BRAND HEADER (franja fija) ── */
.brand-title {{
    font-size: 32px; font-weight: 800; color: {COLORS["text"]};
    letter-spacing: -0.8px; line-height: 1.1; margin-bottom: 4px;
}}
.brand-id {{
    font-size: 14px; font-weight: 700; color: {COLORS["text_disabled"]};
    letter-spacing: 0.5px;
}}
.stat-box {{
    background: {COLORS["card2"]}; border-radius: 12px;
    padding: 11px 15px; margin-bottom: 9px;
}}
.stat-label {{ font-size: 11px; color: {COLORS["muted"]}; font-weight: 600; }}
.stat-value {{ font-size: 15px; color: {COLORS["text"]}; font-weight: 700; margin-top: 2px; }}

/* ── GAUGE ── */
.gauge-wrap {{ display: flex; align-items: center; gap: 14px; }}
.gauge-pct  {{ font-size: 27px; font-weight: 800; letter-spacing: -0.6px; }}
.gauge-name {{ font-size: 13.5px; font-weight: 700; color: {COLORS["text"]}; margin-top: 1px; }}
.gauge-tag  {{
    display: inline-block; font-size: 10px; font-weight: 700;
    padding: 3px 9px; border-radius: 999px; margin-top: 6px; letter-spacing: 0.4px;
}}
.tag-healthy {{ background: {COLORS["success_soft"]}; color: {COLORS["success"]}; }}
.tag-watch   {{ background: {COLORS["warning_soft"]}; color: #FBBF24; }}
.tag-alert   {{ background: {COLORS["danger_soft"]};  color: #F0575A; }}
.tag-inactive {{ background: {COLORS["card2"]}; color: {COLORS["muted"]}; }}

/* ── PANTALLA DE ENTRADA ── */
/* Fondo naranja sólido de página completa (pedido explícito de Sabas,
   mismo tratamiento que ya se aplicó en Eagle con violeta): se activa
   solo con build_css(login=True), ver LOGIN_CSS arriba -- así el resto
   de la app (Gestión General, Buscador de Marcas, etc.) sigue con su
   fondo claro normal sin que este bloque se filtre ahí. */
.login-box {{ width: 100%; }}
.login-box [data-testid="stHorizontalBlock"] {{
    display: flex !important; align-items: center !important;
}}
.login-logo-col, .login-form-col {{ display: flex; flex-direction: column; justify-content: center; }}
.login-logo {{ display: flex; justify-content: flex-start; margin-bottom: 22px; max-width: 100%; }}
.login-logo img {{ max-width: 100%; height: auto; }}
.login-title {{
    font-size: 26px; font-weight: 800; color: {COLORS["brand_white"]};
    letter-spacing: -0.6px; margin-bottom: 6px; text-align: left;
}}
.login-sub {{ font-size: 15px; color: rgba(255,255,255,0.78); line-height: 1.6;
    margin-bottom: 4px; text-align: left; max-width: 380px; }}
.login-foot {{ font-size: 11.5px; color: rgba(255,255,255,0.55); margin-top: 18px; line-height: 1.5; }}
/* Inputs y botones sobre fondo naranja -- fondo translúcido blanco, no
   blanco sólido, para no competir visualmente con el logo (mismo
   criterio que ya usa el sidebar de Wingman con su propio naranja).
   Se agrandan (altura y tipografía) para que los campos tengan más
   presencia junto al logo grande, igual que en Eagle. */
.login-box .stTextInput input {{
    background: rgba(255,255,255,0.14) !important; color: {COLORS["brand_white"]} !important;
    border: 1px solid rgba(255,255,255,0.30) !important; border-radius: 10px !important;
    padding: 14px 16px !important; font-size: 16px !important;
}}
.login-box .stTextInput label {{ color: {COLORS["brand_white"]} !important; font-size: 14px !important; }}
.login-box .stButton button {{
    background: {COLORS["brand_white"]} !important; color: {COLORS["brand_orange"]} !important;
    border: none !important; font-weight: 700 !important;
    padding: 12px 0 !important; font-size: 16px !important;
}}
.login-box .stButton button:hover {{ background: {COLORS["card2"]} !important; }}
/* Los botones secundarios (type="secondary", el toggle Farmer/
   Supervisor cuando no está activo) necesitan su propio contraste --
   blanco translúcido, no blanco sólido, para distinguirse del botón
   primario "Entrar". */
.login-box .stButton button[kind="secondary"] {{
    background: rgba(255,255,255,0.14) !important; color: {COLORS["brand_white"]} !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
}}
.login-box [data-testid="stAlert"] {{
    background: rgba(255,255,255,0.14) !important; color: {COLORS["brand_white"]} !important;
}}

/* ── PILL DE SESIÓN EN SIDEBAR (estilo Growth OS) ── */
/* OJO: .st-key-wingman-sidebar * fuerza color blanco a TODO lo que hay
   adentro del sidebar (para que el texto directo sobre el naranja se lea
   bien). Esta pill tiene fondo BLANCO, asi que sus colores internos necesitan
   !important para ganarle a esa regla general -- si no, el nombre y el rol
   quedan blancos sobre blanco, invisibles. */
.session-pill {{
    display: flex; align-items: center; gap: 10px;
    background: {COLORS["brand_white"]};
    border-radius: 999px;
    padding: 8px 14px 8px 8px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.10);
}}
.session-avatar {{
    width: 40px; height: 40px; border-radius: 50%;
    background: {COLORS["brand_purple"]} !important;   /* morado fijo para todos los Farmers */
    color: {COLORS["brand_white"]} !important;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 800; letter-spacing: 0.3px;
    flex-shrink: 0;
}}
.session-text {{ min-width: 0; flex: 1 1 auto; overflow: hidden; }}
.session-name {{
    font-size: 13.5px; font-weight: 800; line-height: 1.2;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.session-role {{
    font-size: 11px; font-weight: 600; margin-top: 1px;
}}
/* Especificidad real: .st-key-wingman-sidebar * tiene mayor peso que
   una clase sola, incluso con !important de los dos lados (el !important solo
   empata la capa de importancia; adentro de esa capa gana la especificidad del
   selector, no el orden en la hoja). Por eso se repite el mismo selector
   completo aca, calificando la clase adentro del sidebar explicitamente. */
.st-key-wingman-sidebar .session-name {{ color: {COLORS["text"]} !important; }}
.st-key-wingman-sidebar .session-role {{ color: {COLORS["muted"]} !important; }}

/* ── TABLA DE PRIORIDAD (aterrizaje) ── */
.lever-filter-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 4px 0 18px 0; }}

.pr-table-head {{
    display: grid; grid-template-columns: 44px 90px 1fr 90px 150px 1.6fr;
    gap: 12px; padding: 0 15px 8px 15px; font-size: 10.5px; font-weight: 700;
    color: {COLORS["muted"]}; letter-spacing: 0.4px; text-transform: uppercase;
}}
.pr-row {{
    display: grid; grid-template-columns: 44px 90px 1fr 90px 150px 1.6fr;
    gap: 12px; align-items: center; padding: 12px 15px; border-radius: 13px;
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    margin-bottom: 7px; font-size: 12.5px;
}}
.pr-rank {{ color: {COLORS["text_disabled"]}; font-weight: 700; }}
.pr-id   {{ color: {COLORS["text_disabled"]}; font-weight: 600; font-size: 11.5px; }}
.pr-score {{ font-weight: 800; color: {COLORS["brand_orange"]}; }}
.pr-signal {{ color: {COLORS["text"]}; font-weight: 600; font-size: 11.5px; }}
.pr-signals {{ color: {COLORS["muted"]}; font-size: 11px; }}

.brand-pill-btn button {{
    background: {COLORS["brand_orange_soft"]} !important;
    color: {COLORS["brand_orange"]} !important;
    border: 1px solid rgba(247,77,4,0.30) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    text-align: left !important;
    padding: 6px 12px !important;
}}
.brand-pill-btn button:hover {{
    background: {COLORS["brand_purple_soft"]} !important;
    border-color: {COLORS["brand_purple"]} !important;
    color: {COLORS["brand_purple"]} !important;
}}

/* El CSS del telón de carga (#gw-loading) ya NO vive acá -- se inyecta
   completo desde JS en render_loading_watcher() (wingmanapp.py), junto
   con el resto de la arquitectura de detección de eventos/fin de carga.
   Ver el docstring de esa función para el porqué de este cambio. */

/* ── FRANJA FIJA DE MARCA ── */
.brand-sticky {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 18px; padding: 20px 24px; margin-bottom: 14px;
    box-shadow: 0 4px 18px rgba(154,84,246,0.10);
    transition: border-color .18s, box-shadow .18s;
}}
.brand-sticky:hover {{
    border-color: {COLORS["border_hover"]};
    box-shadow: 0 8px 26px rgba(154,84,246,0.24);
}}
.back-link button {{
    background: transparent !important; border: none !important;
    color: {COLORS["muted"]} !important; font-weight: 600 !important;
    padding: 0 !important; font-size: 12.5px !important;
}}
.back-link button:hover {{ color: {COLORS["brand_purple"]} !important; }}

/* ── CAMPAIGN DESIGNER: Ads Plan + Markdown Plan (2 cards) ── */
.campaign-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.campaign-card {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["border"]}; border-radius: 18px;
    padding: 20px 22px; box-shadow: 0 4px 18px rgba(154,84,246,0.08);
}}
.campaign-card.lever-ads {{ border-left: 3px solid {COLORS["brand_orange"]}; }}
.campaign-card.lever-md  {{ border-left: 3px solid {COLORS["blue"]}; }}
.campaign-mode {{ font-size: 11px; font-weight: 800; text-transform: uppercase; margin-top: 8px; }}
.campaign-headline {{ font-size: 26px; font-weight: 800; color: {COLORS["text"]}; line-height: 1.1; margin-top: 4px; }}
.campaign-sub {{ font-size: 12px; color: {COLORS["muted"]}; margin-top: 6px; line-height: 1.55; }}
.campaign-projection {{
    background: {COLORS["info_bg"]}; border: 1px solid rgba(108,155,209,0.18);
    border-radius: 12px; padding: 12px 14px; margin-top: 12px;
}}
.campaign-projection-label {{ font-size: 10px; font-weight: 800; text-transform: uppercase; color: {COLORS["blue"]}; margin-bottom: 6px; }}
.campaign-projection-line {{ font-size: 12px; color: {COLORS["text"]}; line-height: 1.9; }}
.campaign-projection-total {{ font-size: 13px; font-weight: 800; color: {COLORS["blue"]}; margin-top: 8px; }}
.md-ladder {{ margin-top: 10px; }}
.md-ladder-pill {{
    display: inline-block; width: 34px; text-align: center; border-radius: 8px;
    padding: 4px 0; font-size: 11px; font-weight: 800; margin-right: 4px;
    background: {COLORS["card2"]}; color: {COLORS["text_disabled"]};
}}
.md-ladder-pill.active {{ background: {COLORS["blue"]}; color: {COLORS["brand_white"]}; }}
.coinv-block {{
    background: {COLORS["info_bg"]}; border: 1px solid rgba(108,155,209,0.22);
    border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;
}}
.coinv-badge {{
    display: inline-flex; align-items: center; gap: 5px;
    background: {COLORS["blue"]}22; color: {COLORS["blue"]};
    font-size: 11px; font-weight: 800; border-radius: 999px; padding: 3px 10px;
}}
.coinv-split {{ display: flex; gap: 14px; margin-top: 8px; }}
.coinv-split-item {{ flex: 1; }}
.coinv-split-label {{ font-size: 9.5px; color: {COLORS["muted"]}; text-transform: uppercase; font-weight: 700; }}
.coinv-split-value {{ font-size: 16px; font-weight: 800; color: {COLORS["text"]}; }}
.default-plan-pill {{
    background: {COLORS["card2"]}; border-radius: 10px; padding: 8px 12px;
    font-size: 11px; color: {COLORS["muted"]}; margin-bottom: 12px;
}}
.top3-row {{
    display: grid; grid-template-columns: 30px 1fr 130px; gap: 10px; align-items: center;
    padding: 9px 12px; border-radius: 10px; background: {COLORS["card2"]}; margin-bottom: 6px;
}}

/* ── MANAGEMENT DASHBOARD: Brand Coverage (6 donuts) + Contact Performance ── */
.mgmt-card {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 18px; padding: 24px 26px; box-shadow: 0 4px 18px rgba(154,84,246,0.08);
    margin-bottom: 18px;
}}
.mgmt-card-title {{
    font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;
    color: {COLORS["muted"]}; margin-bottom: 18px;
}}
/* Brand Coverage · Live: 5 donuts (agosto 2026, vigésima vuelta -- se
   eliminó PW2, pedido explícito de Sabas; antes 6: Adquisición Ads +
   Upselling Ads + Conversión MD + PW1 + PW2 + Churn). grid-template-
   columns pasa de repeat(6,1fr) a repeat(5,1fr) -- con 6 columnas
   fijas, el 5to donut quedaba corrido y dejaba un hueco vacío en la
   6ta posición en vez de repartir el ancho parejo entre los 5 reales. */
.donut-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; justify-items: center; }}
.donut-item {{ display: flex; flex-direction: column; align-items: center; gap: 8px; }}
.donut-wrap {{ position: relative; width: 82px; height: 82px; }}
.donut-pct {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    font-size: 15px; font-weight: 800; text-align: center;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    line-height: 1.1;
}}
/* Emoji de ritmo dentro del donut, centrado y debajo del % (agosto 2026,
   séptima vuelta -- pedido explícito de Sabas): solo aparece en las 3
   métricas medidas en pace (Adquisición/Upselling Ads, Conversión MD),
   mismo emoji que ya usa la tabla Rendimiento País/Farmer por color de
   ritmo (ver _RENDIMIENTO_EMOJI en wingmanapp.py). display:flex +
   align-items:center en el padre (.donut-pct) es lo que centra el
   emoji simétrico respecto al número, sin necesidad de margin/padding
   manual por caso. */
.donut-emoji {{ font-size: 13px; margin-top: 2px; line-height: 1; }}
.donut-label {{ font-size: 11px; font-weight: 700; color: {COLORS["text"]}; text-align: center; }}
.donut-count {{ font-size: 10px; font-weight: 500; color: {COLORS["muted"]}; text-align: center; margin-top: 1px; }}
.donut-sub {{ font-size: 9.5px; color: {COLORS["muted"]}; }}

.cp-total {{ font-size: 30px; font-weight: 900; color: {COLORS["brand_orange"]}; }}
.cp-total-label {{ font-size: 13px; font-weight: 700; color: {COLORS["muted"]}; }}
.cp-target-row {{ margin: 6px 0 4px; }}
.cp-target-label {{ font-size: 12.5px; font-weight: 600; color: {COLORS["muted"]}; margin-bottom: 4px; }}
.cp-target-bar-track {{ height: 8px; border-radius: 999px; background: {COLORS["card2"]}; overflow: hidden; width: 100%; }}
.cp-target-bar-fill {{ height: 100%; border-radius: 999px; transition: width .2s ease; }}
.cp-bar {{ display: flex; height: 26px; border-radius: 999px; overflow: hidden; width: 100%; margin: 14px 0; }}
.cp-bar-seg {{ display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 800; color: #fff; white-space: nowrap; overflow: hidden; }}
.cp-legend {{ display: flex; gap: 18px; flex-wrap: wrap; }}
.cp-legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; }}
.cp-legend-dot {{ width: 11px; height: 11px; border-radius: 3px; flex-shrink: 0; }}

/* ── ANALYTICS: super-card con funnel + dato ancla + benchmark ── */
.analytics-supercard {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 18px; padding: 20px; box-shadow: 0 4px 18px rgba(154,84,246,0.08);
}}
.funnel-card {{
    background: {COLORS["card2"]}; border-radius: 14px; padding: 18px 20px;
    margin-bottom: 14px;
}}
.funnel-label {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; color: {COLORS["muted"]}; margin-bottom: 8px; }}
.funnel-headline {{ font-size: 16px; font-weight: 800; margin-bottom: 12px; }}
.funnel-texto {{ font-size: 11.5px; color: {COLORS["muted"]}; line-height: 1.55; margin-bottom: 10px;
    border-top: 1px solid {COLORS["border"]}; padding-top: 10px; }}
.funnel-pitch-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase;
    color: {COLORS["muted"]}; margin-bottom: 4px; }}
.funnel-pitch {{ font-size: 11.5px; color: {COLORS["muted"]}; line-height: 1.55; font-style: italic; }}

.analytics-mini-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}

/* ── 360° ACTION: card de contexto + super-card de 4 palancas ── */
.action-context-card {{
    background: {COLORS["card2"]};
    border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
}}
.action-context-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
}}
.action-mini-label {{ font-size: 10.5px; font-weight: 700; color: {COLORS["muted"]}; text-transform: uppercase; letter-spacing: 0.4px; }}
.action-mini-value {{ font-size: 14px; font-weight: 700; color: {COLORS["text"]}; margin-top: 2px; }}
.action-lever-pill {{
    display: inline-block; font-size: 11.5px; font-weight: 600;
    background: {COLORS["info_bg"]}; color: {COLORS["blue"]};
    border-radius: 999px; padding: 5px 11px; margin: 8px 6px 0 0;
}}

/* Tabla de farmers del Supervisor (Gestión General por país): pills de
   colores en vez de texto plano, mismo estilo visual que las pills de
   prioridad de Growth OS -- correo en un color, resto de columnas en el
   color contrario (pedido explícito de Sabas, agosto 2026). */
.sup-table {{
    width: 100%; table-layout: fixed; border-collapse: separate; border-spacing: 0 8px;
}}
.sup-table th {{
    font-size: 11px; font-weight: 700; color: {COLORS["muted"]};
    text-transform: uppercase; letter-spacing: 0.4px; text-align: left;
    padding: 0 8px 6px 8px; overflow: hidden;
}}
/* Anchos por columna (9 columnas fijas de Rendimiento País, agosto
   2026, cuarta vuelta -- se agregó Upselling Ads como columna 4,
   corriendo MD/Bookings/Revenue/MD Full/MD PRO un puesto y agregando
   MD PRO como 9na columna, que antes no tenía ancho explícito y por eso
   se cortaba en el borde del contenedor). Farmer y Contactos Efectivos
   con espacio moderado; Adquisición/Upselling/Conversión MD y los 2
   Objetivo Ads (contenido corto, "112% 🔥") bien angostas; MD Full/PRO
   mas anchas porque su contenido es mas largo ("6,76% / 7,69% - 88%").
   NO se busca que las 9 columnas se vean completas en el ancho normal
   del contenedor -- para eso está el botón de pantalla completa (ver
   sup-table-fullscreen); aquí el criterio es que ninguna columna quede
   sin ancho definido (eso es lo que las corta), no que quepan todas. */
.sup-table th:nth-child(1), .sup-table td:nth-child(1) {{ width: 13%; }}
.sup-table th:nth-child(2), .sup-table td:nth-child(2) {{ width: 11%; }}
.sup-table th:nth-child(3), .sup-table td:nth-child(3) {{ width: 9%; }}
.sup-table th:nth-child(4), .sup-table td:nth-child(4) {{ width: 9%; }}
.sup-table th:nth-child(5), .sup-table td:nth-child(5) {{ width: 8%; }}
.sup-table th:nth-child(6), .sup-table td:nth-child(6) {{ width: 8%; }}
.sup-table th:nth-child(7), .sup-table td:nth-child(7) {{ width: 8%; }}
.sup-table th:nth-child(8), .sup-table td:nth-child(8) {{ width: 17%; }}
.sup-table th:nth-child(9), .sup-table td:nth-child(9) {{ width: 17%; }}

/* Tablas de "Trabajables" (agosto 2026, vigésima tercera vuelta --
   pedido explícito de Sabas: "esa columna y celda de # está demasiado
   ancha, busca la forma de hacer la tabla simétrica"). Reusan la clase
   base .sup-table (mismo look de pills/spacing) pero heredaban los
   anchos por nth-child pensados para Rendimiento País (9 columnas fijas,
   la 1ra pensada para el correo largo del Farmer -- 13%) -- acá la
   columna 1 es solo "#" (1-2 dígitos), así que ese 13% la dejaba
   desproporcionada. .sup-table-trab GANA por especificidad (dos clases
   combinadas pesan más que una) sobre las reglas de arriba, sin tocar
   la tabla de Rendimiento País. "#" bien angosta (suficiente para "10"),
   "Marca" con la mayor parte del espacio (nombre + ID, lo más largo de
   la fila), el resto del espacio se reparte parejo entre las columnas
   de datos restantes vía flex en vez de porcentajes fijos por posición
   -- el número de columnas varía por tab (4 a 7), así que un ancho fijo
   por nth-child no sirve igual de bien para los 4 tabs a la vez. */
.sup-table.sup-table-trab {{ table-layout: auto; }}
.sup-table.sup-table-trab th:nth-child(1),
.sup-table.sup-table-trab td:nth-child(1) {{ width: 40px; }}
.sup-table.sup-table-trab th:nth-child(2),
.sup-table.sup-table-trab td:nth-child(2) {{ width: auto; min-width: 220px; }}
.sup-table.sup-table-trab th:nth-child(n+3),
.sup-table.sup-table-trab td:nth-child(n+3) {{ width: auto; white-space: nowrap; }}
/* Tab Churn: "#" sigue en columna 1, pero "Categoría" pasa a ser la 2da
   columna (angosta, solo "Churn"/"PW1") y "Marca" se corre a la 3ra --
   se sobreescribe puntualmente con una clase extra en el <table> de ese
   tab en vez de intentar detectar el contenido por CSS. */
.sup-table.sup-table-trab.sup-table-trab-churn th:nth-child(2),
.sup-table.sup-table-trab.sup-table-trab-churn td:nth-child(2) {{ width: 90px; min-width: 0; }}
.sup-table.sup-table-trab.sup-table-trab-churn th:nth-child(3),
.sup-table.sup-table-trab.sup-table-trab-churn td:nth-child(3) {{ width: auto; min-width: 220px; }}

/* Tabla interactiva (Rendimiento País/Farmer): resize de columnas
   arrastrando el borde derecho del header, y ordenar de mayor a menor /
   menor a mayor haciendo click en el header -- pedido explícito de Sabas
   (agosto 2026). El resize y el sort en si corren via JS (ver
   _render_table_interactivity en wingmanapp.py) porque el resize:
   horizontal nativo de CSS no es confiable en celdas de tabla entre
   navegadores -- este bloque solo da el cursor visual y el indicador de
   columna ordenada. */
.sup-table-interactive th {{ position: relative; }}
.sup-table-interactive th .sup-resize-handle {{
    position: absolute; right: 0; top: 0; bottom: 0; width: 6px;
    cursor: col-resize; z-index: 5;
}}
/* Botón de ordenar dedicado (agosto 2026, quinta vuelta): ANTES el click
   en cualquier parte del <th> disparaba el sort -- esto hacía que un
   intento de arrastrar el resize-handle que no arrancara EXACTO sobre el
   handle (un pixel de margen) se interpretara como click normal y
   reordenara toda la tabla de golpe, quedando híper sensible ("medio
   movimiento" cerca del header ya cambiaba el orden, pedido explícito de
   Sabas). Fix: el header YA NO tiene cursor:pointer ni listener de click
   -- el único trigger de sort es este botón chiquito (⇅) al lado del
   texto, así resize y sort quedan completamente separados en el espacio
   de la UI, sin superposición de gestos. */
.sup-sort-btn {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 16px; height: 16px; margin-left: 4px; border-radius: 4px;
    cursor: pointer; font-size: 10px; opacity: 0.55; vertical-align: middle;
    background: transparent; border: none; color: inherit; padding: 0;
}}
.sup-sort-btn:hover {{ opacity: 1; background: rgba(154,84,246,0.12); }}
.sup-sort-btn.active {{ opacity: 1; color: {COLORS["brand_purple"]}; }}

/* Modal nativo de st.dialog (Rendimiento País/Farmer en pantalla
   completa, agosto 2026, decimosexta vuelta -- "esa fullscreen
   simplemente no tiene sentido, no es fullscreen si se ve recortado"):
   el intento anterior apuntaba a data-testid="stDialogContent", un
   selector INVENTADO que no existe en el bundle real de Streamlit --
   confirmado inspeccionando directamente el JS compilado del frontend
   instalado (streamlit/static/static/js/index.*.js) en vez de suponer
   el nombre. La estructura real: el contenedor con
   data-testid="stDialog" envuelve un panel interno (componente styled
   con una prop $dialogWidth aplicada como estilo INLINE de React, no
   como clase CSS) -- ese estilo inline tiene prioridad muy alta y
   pisaba silenciosamente cualquier regla externa que no usara
   !important sobre el selector correcto. width="large" en Python solo
   pide el techo nativo de Streamlit (small/medium/large, no hay "full"
   en la API), que sigue sin alcanzar para 9 columnas.

   Fix: el selector apunta al PRIMER DIV HIJO DIRECTO de
   [data-testid="stDialog"] (ahí es donde React aplica el estilo inline
   de ancho) con !important -- esto gana por especificidad/orden sobre
   el estilo inline de la prop $dialogWidth. Se fuerza a 96vw con
   !important en width, max-width Y min-width (el componente real
   también fija un min-width vía calc(), que sin cubrir los 3 poeda
   quedar más angosto de lo esperado en pantallas grandes). */
div[data-testid="stDialog"] > div {{
    width: 96vw !important;
    max-width: 96vw !important;
    min-width: 96vw !important;
}}
div[data-testid="stDialog"] {{
    overflow-x: auto;
}}

/* Tabla en modo fullscreen: auto en vez de fixed, cada columna a su
   ancho natural, pill centrada en la celda con padding parejo (nada
   pegado a bordes) -- pedido explícito de Sabas. */
.sup-table-fullscreen {{ table-layout: auto; width: auto; }}
.sup-table-fullscreen th, .sup-table-fullscreen td {{ width: auto !important; white-space: nowrap; }}
.sup-table-fullscreen th {{ padding: 0 20px 10px 20px; text-align: center; }}
.sup-table-fullscreen th:first-child {{ text-align: left; }}
.sup-table-fullscreen td {{ padding: 6px 20px; text-align: center; }}
.sup-table-fullscreen td:first-child {{ text-align: left; }}
.sup-table-fullscreen .sup-pill {{ display: inline-flex; align-items: center; justify-content: center; }}

/* Rendimiento Farmer (una sola fila, no 16+ como Rendimiento País): con
   table-layout: fixed y los % de arriba, cada columna quedaba con mucho
   aire vacío o con texto cortado porque esos anchos estaban calculados
   para repartir el espacio entre muchas filas, no para una sola (ajuste
   de simetria, agosto 2026, segunda vez). auto deja que el navegador
   ajuste cada columna a su contenido real. */
/* Rendimiento Farmer (una sola fila): con table-layout auto + nowrap en
   el header, el TITULO largo ("OBJETIVO ADS BOOKINGS") forzaba el ancho
   de toda la columna aunque la pill adentro fuera corta -- quedaba una
   pill chica con mucho aire alrededor (ajuste de simetria, agosto 2026,
   tercera vez). Fix: el header SI puede quebrar en 2 lineas (sin nowrap),
   así no manda el ancho de la columna; el contenido de la celda queda
   centrado con padding parejo a los lados, ajustado al tamaño real de la
   pill. */
.sup-table-single {{ table-layout: auto; }}
.sup-table-single th {{
    width: auto; white-space: normal; text-align: center; line-height: 1.3;
    max-width: 90px;
}}
.sup-table-single th:first-child {{ text-align: left; max-width: none; }}
.sup-table-single td {{ width: 1%; white-space: nowrap; text-align: center; padding: 4px 10px; }}
.sup-table-single td:first-child {{ text-align: left; width: auto; }}

.sup-table td {{ padding: 4px 4px; vertical-align: middle; overflow: hidden; }}
.sup-pill {{
    display: inline-block; font-size: 12.5px; font-weight: 700;
    border-radius: 999px; padding: 6px 12px; white-space: nowrap;
    letter-spacing: 0.1px; max-width: 100%; overflow: hidden; text-overflow: ellipsis;
}}
/* Correo del Farmer: el texto puede truncarse con "..." si no entra
   (ej. luisfernando.hernandez@rappi.com, el mas largo del equipo) en vez
   de forzar el ancho de toda la fila y desbordar el contenedor --
   auditoria de simetria, agosto 2026. Se mantiene inline-block+ellipsis
   arriba (comun a toda pill) mas un max-width explicito aca para forzar
   el corte incluso dentro de la celda de ancho fijo. */
.sup-pill-farmer {{ max-width: 100%; display: inline-block; vertical-align: middle; }}
.sup-pill-orange {{ background: {COLORS["brand_orange_soft"]}; color: {COLORS["brand_orange"]}; }}
.sup-pill-purple {{ background: {COLORS["brand_purple_soft"]}; color: {COLORS["brand_purple"]}; }}
.sup-pill-red    {{ background: rgba(239,68,68,0.10);  color: #C4483F; }}
.sup-pill-green  {{ background: rgba(34,197,94,0.12);  color: #3E9160; }}
.sup-pill-yellow {{ background: rgba(251,191,36,0.16); color: #A97A1E; }}
.sup-pill-blue   {{ background: rgba(108,155,209,0.14); color: #4C7CAD; }}
.sup-pill-gray   {{ background: rgba(107,114,128,0.10); color: {COLORS["muted"]}; }}

.action-supercard {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 18px; padding: 20px; box-shadow: 0 4px 18px rgba(154,84,246,0.08);
}}
.action-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}}
.action-card {{
    background: {COLORS["card2"]}; border-radius: 14px; padding: 16px;
}}
.action-card-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.action-card-pct {{ font-size: 24px; font-weight: 800; }}
.action-card-name {{ font-size: 12.5px; font-weight: 700; color: {COLORS["text"]}; margin-top: 2px; }}
.action-card-title {{ font-size: 12px; font-weight: 700; color: {COLORS["text"]}; margin-top: 10px; line-height: 1.4; }}
.action-card-detail {{ font-size: 11px; color: {COLORS["muted"]}; margin-top: 6px; line-height: 1.5; }}
.action-card-item {{ font-size: 11.5px; font-weight: 600; color: {COLORS["text"]}; margin-top: 8px; line-height: 1.4; }}

/* ── TABS (Home / 360 Action / Analytics / Campaign Designer / Outreach) ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px; border-bottom: 1px solid {COLORS["border"]};
}}
.stTabs [data-baseweb="tab"] {{
    color: {COLORS["muted"]} !important;
}}
.stTabs [aria-selected="true"] {{
    color: {COLORS["brand_purple"]} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: {COLORS["brand_purple"]} !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    background-color: {COLORS["border"]} !important;
}}

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
"""

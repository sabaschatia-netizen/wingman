"""
Growth Wingman — consulta de cartera por Farmer.

Extraccion reducida del modulo Brand Finder de Growth OS. Cada Farmer entra con
su correo + contraseña y ve unicamente sus marcas.

Navegacion: Login -> Aterrizaje (tabla de prioridad filtrable por palanca,
+ buscador libre) -> Ficha de marca (franja fija + 5 tabs: Home, 360 Action,
Analytics, Campaign Designer, Outreach).
"""

import html as html_lib
import json
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components

import data_layer as dl
from theme import COLORS, build_css, favicon, logo_img

st.set_page_config(
    page_title="Wingman",
    page_icon=favicon(),
    layout="wide",
    initial_sidebar_state="expanded",
)
# NOTA: build_css() se movió más abajo, después del gate de login (ver
# `if "farmer" not in st.session_state: render_login(); st.stop()`).
# Antes se llamaba acá arriba SIEMPRE, incondicional -- con el login
# ahora inyectando su propio build_css(login=True) más abajo, quedaban
# dos bloques <style> compitiendo (fondo claro normal + fondo naranja
# de login) al mismo tiempo, y cuál "ganaba" dependía del orden de
# aplicación en el DOM, no de una regla explícita. Ahora solo se carga
# UN build_css() por render: el de login mientras no hay sesión, el
# normal una vez adentro -- igual que ya se resolvió en Eagle.


# =========================
# RENDER HELPERS
# =========================

def _copy_button_html(texto, label="📋", tamano="chico"):
    """
    Devuelve SOLO el <button> (sin onclick) para insertar dentro de un
    st.markdown -- el onclick se ata aparte, ver _render_copy_script.

    BUG REAL CORREGIDO (agosto 2026, segunda vuelta): un onclick puesto
    directo en el HTML de st.markdown no se disparaba de forma confiable
    ("lo oprimo y no copia nada", sin error visible). Se investigó como
    resuelve esto Growth OS (app_glass.py) y usa un patrón de DOS PASOS,
    no un onclick inline:
      1) El botón se pinta con st.markdown, con un id, SIN onclick.
      2) Aparte, un st_components.html() inyecta un <script> que busca
         el boton en window.parent.document (el documento REAL del
         navegador -- st_components.html corre en su propio iframe pero
         SI puede alcanzar window.parent) y le asigna btn.onclick desde
         ahi. Ese patrón es el que ya usa render_loading_watcher() en
         este mismo archivo para el loader -- se replica igual acá.

    Este helper es el paso 1 (el botón visual). Se necesita SIEMPRE
    junto con una llamada a _render_copy_script(texto, mismo_id) para que
    el click funcione -- no sirve solo.
    """
    btn_id = f"copy-{abs(hash(texto))}"
    if tamano == "grande":
        style = (
            f"background:{COLORS['brand_purple_soft']};color:{COLORS['brand_purple']};"
            "border:none;border-radius:8px;padding:6px 12px;font-size:12px;font-weight:700;"
            "cursor:pointer;white-space:nowrap;"
        )
    else:
        style = (
            "background:transparent;border:none;cursor:pointer;font-size:13px;"
            "padding:0 0 0 6px;vertical-align:middle;opacity:0.6;"
        )
    return btn_id, f'<button id="{btn_id}" style="{style}" title="Copiar">{label}</button>'


def _render_copy_script(texto, btn_id, label_original="📋"):
    """
    Paso 2 del botón de copiar: st_components.html() que busca el botón
    por su id en window.parent.document y le asigna el onclick real
    (navigator.clipboard.writeText con fallback a execCommand('copy'),
    igual que Growth OS). Se llama SIEMPRE junto a _copy_button_html.
    """
    texto_js = json.dumps(str(texto))
    label_js = json.dumps(str(label_original))
    st_components.html(
        f"""
        <script>
        (function() {{
          var texto = {texto_js};
          var labelOriginal = {label_js};
          function findBtn() {{
            try {{
              var btn = window.parent.document.getElementById({json.dumps(btn_id)});
              if (!btn) return;
              btn.onclick = function() {{
                function marcarCopiado() {{
                  btn.innerHTML = '✅';
                  setTimeout(function() {{ btn.innerHTML = labelOriginal; }}, 1500);
                }}
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                  navigator.clipboard.writeText(texto).then(marcarCopiado).catch(function() {{
                    var ta = window.parent.document.createElement('textarea');
                    ta.value = texto;
                    window.parent.document.body.appendChild(ta);
                    ta.select();
                    try {{ window.parent.document.execCommand('copy'); }} catch(e) {{}}
                    window.parent.document.body.removeChild(ta);
                    marcarCopiado();
                  }});
                }} else {{
                  var ta = window.parent.document.createElement('textarea');
                  ta.value = texto;
                  window.parent.document.body.appendChild(ta);
                  ta.select();
                  try {{ window.parent.document.execCommand('copy'); }} catch(e) {{}}
                  window.parent.document.body.removeChild(ta);
                  marcarCopiado();
                }}
              }};
            }} catch(e) {{}}
          }}
          findBtn();
          setTimeout(findBtn, 400);
        }})();
        </script>
        """,
        height=0,
    )


def _render_table_interactivity(table_id):
    """
    Script que activa, en la tabla con id=table_id (dentro de
    window.parent.document): (1) resize de columnas arrastrando el borde
    derecho del header, (2) ordenar de mayor a menor / menor a mayor
    haciendo click en un BOTÓN dedicado (⇅) dentro del header -- pedido
    explícito de Sabas (agosto 2026), aplicado tanto a Rendimiento País
    (Supervisor) como Rendimiento Farmer (una fila).

    Resize: se agrega un <div class="sup-resize-handle"> a cada <th> (si
    no existe ya) y se escucha mousedown/mousemove/mouseup sobre
    window.parent.document para ajustar el width del header en tiempo
    real (position:relative en el th + handle absoluto a la derecha,
    mismo patrón que un resizer de spreadsheet).

    Sort: cada click en un botón dedicado (⇅) dentro del header ordena
    las filas del <tbody> comparando el atributo data-sort de la celda
    correspondiente de cada fila -- NUMÉRICO si el valor parsea como
    número, TEXTO si no (la columna Farmer, alfabético). Un segundo
    click invierte el orden.

    BUG REAL CORREGIDO (agosto 2026, decimoquinta vuelta -- "me quedo en
    Argentina y cargaba bien, pasé a Chile y ya ningún botón servía, me
    devolví a Argentina y tampoco, solo se arregla con F5"): el patrón
    anterior marcaba table.dataset.wingmanInteractive='1' en el elemento
    DOM real para "no duplicar listeners" y cortaba ahí -- pero ese flag
    vive en el nodo del navegador, no en Python/session_state. Streamlit
    reutiliza (diffea) el iframe de st_components.html() entre reruns
    cuando el contenido del script es igual salvo por variables --
    exactamente el caso acá, donde el ÚNICO cambio entre el script de AR
    y el de CL es el valor de table_id dentro del JSON, el resto del
    string es idéntico caracter por caracter. Si Streamlit decide
    reciclar el mismo iframe físico en vez de crear uno nuevo, el
    closure de setup() de ESE iframe reciclado puede quedar apuntando a
    un table_id viejo, o el dataset de la tabla vieja (si Streamlit
    también reusa el nodo <table> al re-renderizar el markdown) sigue
    marcado en '1' de una carga anterior -- bloqueando CUALQUIER
    reenganche futuro, tanto de resize como de sort, hasta que un F5
    fuerza un WebSocket nuevo y destruye todo el estado del navegador de
    punta a punta (lo único que garantiza iframes y nodos 100% limpios).

    Fix: se elimina el flag dataset.wingmanInteractive por completo.
    setup() ahora es IDEMPOTENTE por diseño -- antes de agregar cualquier
    resize-handle o sort-btn a un <th>, revisa si ESE <th> puntual ya
    tiene uno (querySelector local, no un flag global en la tabla) y lo
    salta si ya existe, en vez de cortar toda la función por un flag
    único a nivel tabla. Esto significa que setup() puede correr las
    veces que Streamlit decida (con el mismo tableId o con uno distinto,
    reciclando el iframe o no) sin duplicar nada y sin depender de que
    ningún estado sobreviva "por las buenas" en el DOM -- si el th ya
    tiene su handle/botón, no hace nada; si no lo tiene (tabla nueva,
    tabla reciclada sin sus hijos, lo que sea), lo agrega.
    """
    st_components.html(
        f"""
        <script>
        (function() {{
          var tableId = {json.dumps(table_id)};

          function setup() {{
            try {{
              var table = window.parent.document.getElementById(tableId);
              if (!table) return;

              var ths = table.querySelectorAll('thead th');
              var sortState = {{ col: -1, asc: true }};

              ths.forEach(function(th, idx) {{
                // ── Resize: solo agrega el handle si ESTE th todavía
                //    no tiene uno (idempotente por elemento, no por
                //    flag global de la tabla) ──
                if (!th.querySelector('.sup-resize-handle')) {{
                  var handle = window.parent.document.createElement('div');
                  handle.className = 'sup-resize-handle';
                  th.appendChild(handle);
                  var startX, startWidth;
                  handle.addEventListener('mousedown', function(e) {{
                    startX = e.pageX;
                    startWidth = th.offsetWidth;
                    table.style.tableLayout = 'fixed';
                    function onMove(e2) {{
                      var newWidth = Math.max(50, startWidth + (e2.pageX - startX));
                      th.style.width = newWidth + 'px';
                    }}
                    function onUp() {{
                      window.parent.document.removeEventListener('mousemove', onMove);
                      window.parent.document.removeEventListener('mouseup', onUp);
                    }}
                    window.parent.document.addEventListener('mousemove', onMove);
                    window.parent.document.addEventListener('mouseup', onUp);
                    e.stopPropagation();
                    e.preventDefault();
                  }});
                }}

                // ── Sort: idem, solo agrega el botón si falta. Si ya
                //    existe, lo REENGANCHA (clone+replace) para que el
                //    listener siempre quede atado al `ths`/`table` de
                //    ESTA pasada de setup(), nunca a un closure viejo
                //    de un iframe reciclado con datos obsoletos ──
                var existingBtn = th.querySelector('.sup-sort-btn');
                var btn = existingBtn ? existingBtn.cloneNode(true) : window.parent.document.createElement('span');
                if (existingBtn) {{
                  existingBtn.parentNode.replaceChild(btn, existingBtn);
                }} else {{
                  btn.className = 'sup-sort-btn';
                  btn.textContent = '⇅';
                  btn.title = 'Ordenar';
                  th.appendChild(btn);
                }}

                btn.addEventListener('click', function(e) {{
                  e.stopPropagation();
                  e.preventDefault();
                  var asc = (sortState.col === idx) ? !sortState.asc : true;
                  sortState = {{ col: idx, asc: asc }};

                  ths.forEach(function(t) {{
                    var b = t.querySelector('.sup-sort-btn');
                    if (b) b.classList.remove('active');
                  }});
                  btn.classList.add('active');
                  btn.textContent = asc ? '↑' : '↓';

                  var tbody = table.querySelector('tbody');
                  var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
                  rows.sort(function(r1, r2) {{
                    var c1 = r1.children[idx].getAttribute('data-sort') || '';
                    var c2 = r2.children[idx].getAttribute('data-sort') || '';
                    var n1 = parseFloat(c1), n2 = parseFloat(c2);
                    var cmp;
                    if (!isNaN(n1) && !isNaN(n2)) {{
                      cmp = n1 - n2;
                    }} else {{
                      cmp = c1.localeCompare(c2);
                    }}
                    return asc ? cmp : -cmp;
                  }});
                  rows.forEach(function(r) {{ tbody.appendChild(r); }});
                }});
              }});
            }} catch(e) {{}}
          }}

          setup();
          setTimeout(setup, 400);
          setTimeout(setup, 1200);
        }})();
        </script>
        """,
        height=0,
    )


def header(farmer_name, section_name, pill=""):
    # Orden invertido por pedido explícito: nombre del Farmer + sección
    # activa ahora a la IZQUIERDA (antes a la derecha), logo ahora a la
    # DERECHA (antes a la izquierda, siempre primero). El texto pasa de
    # alinearse a la derecha a alinearse a la izquierda para que quede
    # prolijo en su nuevo lugar.
    pill_html = f'<div class="period-pill">{pill}</div>' if pill else ""
    st.markdown(
        f'<div class="app-header">'
        f'<div class="header-left">'
        f'<div class="header-title">{farmer_name}</div>'
        f'<div class="header-subtitle">{section_name}</div>'
        f"</div>"
        f"{pill_html}"
        f'<div class="header-logo-right">{logo_img(44, full=True)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def mini_card(label, value, copy="", lever="", chip="", chip_color="", corner_badge=None):
    chip_html = (
        f'<span class="card-chip" style="background:{chip_color}22;color:{chip_color};">{chip}</span>'
        if chip else ""
    )
    badge_html = ""
    if corner_badge:
        b_text, b_color = corner_badge
        badge_html = f'<span class="corner-badge" style="background:{b_color}22;color:{b_color};">{b_text}</span>'
    return (
        f'<div class="business-mini-card lever-{lever}">'
        f"{badge_html}"
        f'<div class="card-label">{label}</div>'
        f'<div class="card-value">{value}{chip_html}</div>'
        f'<div class="card-copy">{copy}</div></div>'
    )


def gauge_card(pct, name, tag, sub=""):
    tag_class = {"HEALTHY": "tag-healthy", "WATCH": "tag-watch", "ALERT": "tag-alert"}[tag]
    color = {"HEALTHY": COLORS["success"], "WATCH": COLORS["warning"], "ALERT": COLORS["danger"]}[tag]
    return (
        f'<div class="glass-card"><div class="gauge-wrap"><div>'
        f'<div class="gauge-pct" style="color:{color};">{pct:.0f}%</div>'
        f'<div class="gauge-name">{name}</div>'
        f'<span class="gauge-tag {tag_class}">{tag}</span>'
        f'<div class="card-copy">{sub}</div>'
        f"</div></div></div>"
    )


def _trend_sparkline(prev, curr):
    """Mini grafico SVG de 2 puntos: Anterior -> Actual. Mismo lenguaje visual
    que Growth OS (linea con puntos), pero con solo 2 periodos reales -- no se
    inventa un tercer punto ("Mayo") que no existe en la data disponible."""
    prev, curr = max(prev, 0), max(curr, 0)
    top = max(prev, curr, 1)
    y_prev = 34 - (prev / top) * 24
    y_curr = 34 - (curr / top) * 24
    color = COLORS["brand_orange"]
    return (
        f'<svg width="96" height="44" viewBox="0 0 96 44" style="overflow:visible;">'
        f'<line x1="14" y1="{y_prev:.1f}" x2="82" y2="{y_curr:.1f}" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        f'<circle cx="14" cy="{y_prev:.1f}" r="3" fill="{color}"/>'
        f'<circle cx="82" cy="{y_curr:.1f}" r="3" fill="{color}"/>'
        f'</svg>'
    )


def metric_trend_card(icon, label, value_ars, delta_frac, sub_left, prev_ars=0, currency="ARS", es_ritmo=False):
    """
    Card de GMV/AOV al estilo Growth OS: icono + label arriba, monto grande
    (en la moneda nativa del farmer -- currency), % de variacion vs mes
    anterior, y sparkline Anterior->Actual a la derecha (solo si hay dato
    de mes anterior).

    El "USD $ X" de referencia chiquito que antes iba debajo del monto se
    elimino (pedido explicito de Sabas, agosto 2026): dependia de una tasa
    fija pensada solo para ARS, que no tenia sentido para otras monedas
    (UYU) a medida que el equipo crece a Cono Sur.

    es_ritmo=True (GMV): delta_frac ya viene como RITMO -- el GMV acumulado
    del mes en curso PROYECTADO a mes completo (por dias calendario)
    contra el GMV real del mes anterior -- no la variacion cruda del
    acumulado (bug real corregido, agosto 2026: comparar 2-3 dias de
    agosto contra 31 dias de julio sin ajustar daba caidas falsas de
    -80/-90%). El texto dice "ritmo vs mes anterior" en vez de solo
    "vs mes anterior" para que quede claro que es una proyeccion, no lo
    ya vendido. es_ritmo=False (AOV, default): variacion directa de
    siempre -- el AOV es un promedio, no un acumulado, no hace falta
    proyectarlo.
    """
    delta_html = ""
    if delta_frac:
        color = COLORS["success"] if delta_frac > 0 else COLORS["danger"]
        arrow = "▲" if delta_frac > 0 else "▼"
        texto_comparacion = "ritmo vs mes anterior" if es_ritmo else "vs mes anterior"
        delta_html = (
            f'<span style="color:{color};font-weight:700;font-size:12.5px;">'
            f"{arrow} {abs(delta_frac) * 100:.0f}%</span> "
            f'<span style="color:{COLORS["muted"]};font-size:11.5px;">{texto_comparacion}</span>'
        )
    trend_html = ""
    if prev_ars > 0:
        trend_html = (
            '<div style="text-align:center;min-width:120px;">'
            f'{_trend_sparkline(prev_ars, value_ars)}'
            f'<div style="display:flex;justify-content:space-between;width:110px;margin:0 auto;'
            f'font-size:9px;color:{COLORS["muted"]};margin-top:2px;">'
            f"<span>Anterior</span><span>Actual</span></div>"
            f'<div style="display:flex;justify-content:space-between;width:110px;margin:2px auto 0;'
            f'font-size:9.5px;font-weight:400;color:{COLORS["muted"]};line-height:1.35;">'
            f'<span style="max-width:52px;white-space:normal;word-break:break-word;">{dl.fmt_money(prev_ars, currency)}</span>'
            f'<span style="max-width:52px;white-space:normal;word-break:break-word;">{dl.fmt_money(value_ars, currency)}</span></div>'
            "</div>"
        )
    return (
        f'<div class="glass-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div style="flex:1;">'
        f'<div class="card-label">{icon} {label}</div>'
        f'<div class="card-value">{dl.fmt_money(value_ars, currency)}</div>'
        f'<div style="margin-top:8px;">{delta_html}</div>'
        f'<div class="card-copy" style="margin-top:4px;">{sub_left}</div>'
        f"</div>{trend_html}</div></div>"
    )


def state_text(active):
    return ("Active 🚀", COLORS["success"]) if active else ("Inactive 💤", COLORS["text_disabled"])


def watch_alert_tag(pct, good=95, ok=85):
    return "HEALTHY" if pct >= good else ("WATCH" if pct >= ok else "ALERT")


def cvr_tag(brand_cvr, bench):
    if not bench:
        return "WATCH"
    if brand_cvr >= bench:
        return "HEALTHY"
    return "WATCH" if brand_cvr >= bench * 0.7 else "ALERT"


def render_conosur_map():
    """
    Mapa clickeable del Cono Sur (AR/CL/UY) para la Gestión General del
    Supervisor. No es un contorno geográfico real -- serían paths SVG
    demasiado complejos para trazar a mano con precisión y no aportan nada
    funcional sobre 3 bloques posicionados aproximadamente como el mapa
    real (Chile angosto a la izquierda, Argentina grande al centro,
    Uruguay chico abajo a la derecha). Hover morado (brand_purple, mismo
    tono que el resto de Wingman) al pasar el mouse; el país seleccionado
    queda resaltado con el mismo morado, sólido.

    Usa botones nativos de Streamlit (no JS/SVG custom) para el click,
    posicionados con columnas para simular la geografía -- más robusto que
    intentar hacer que un SVG le hable de vuelta a Streamlit.
    """
    pais_actual = st.session_state.get("supervisor_pais", "AR")
    purple = COLORS["brand_purple"]

    st.markdown(
        f"""
        <style>
        div[data-testid="stHorizontalBlock"] .conosur-btn button {{
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: all .15s ease !important;
        }}
        div[data-testid="stHorizontalBlock"] .conosur-btn button:hover {{
            background: {purple} !important;
            border-color: {purple} !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="mgmt-card" style="padding-bottom:8px;">'
        '<div class="mgmt-card-title" style="margin-bottom:12px;">🗺️ Cono Sur — elegí un país</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Layout aproximado: Chile (angosto, izquierda) | Argentina (grande,
    # centro) | Uruguay (chico, derecha-abajo, mismo ancho relativo que
    # tiene en el mapa real comparado con Argentina).
    c_cl, c_ar, c_uy = st.columns([1, 2, 1])
    columnas = {"CL": c_cl, "AR": c_ar, "UY": c_uy}

    for pais_info in dl.PAISES_CONO_SUR:
        code = pais_info["code"]
        with columnas[code]:
            st.markdown('<div class="conosur-btn">', unsafe_allow_html=True)
            es_actual = code == pais_actual
            if st.button(
                pais_info["label"],
                key=f"mapa_{code}",
                type="primary" if es_actual else "secondary",
                use_container_width=True,
            ):
                st.session_state["supervisor_pais"] = code
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


# =========================
# RENDIMIENTO (helpers compartidos entre vista Supervisor -por país- y
# vista Farmer -su propia fila-, agosto 2026)
# =========================

# Pill SIEMPRE gris de fondo (pedido explicito de Sabas, agosto 2026,
# segundo ajuste): lo que antes era el color de FONDO de la pill ahora es
# el color del TEXTO adentro -- la logica de que color corresponde a cada
# rango de valor no cambia, solo cambia DONDE se aplica ese color.
_RENDIMIENTO_TEXT_COLOR = {
    "red": "#C4483F", "green": "#3E9160", "yellow": "#A97A1E",
    "blue": "#4C7CAD", "purple": COLORS["brand_purple"],
    "orange": COLORS["brand_orange"], "gray": COLORS["muted"],
    "farmer": COLORS["text"],
}
_RENDIMIENTO_EMOJI = {"blue": "⚡", "green": "🏆", "red": "🟥", "purple": "🔥", "yellow": "⚠️"}


def _rend_pill(valor, color):
    text_color = _RENDIMIENTO_TEXT_COLOR.get(color, COLORS["muted"])
    return f'<span class="sup-pill sup-pill-gray" style="color:{text_color};">{valor}</span>'


def _rend_pill_a(valor, color):
    emoji = _RENDIMIENTO_EMOJI.get(color, "")
    return _rend_pill(f"{valor} {emoji}".strip(), color)


def _trab_pill(valor, color):
    """
    Pill de la sección "Trabajables" (agosto 2026, vigésima segunda
    vuelta -- pedido explícito de Sabas): a diferencia de _rend_pill (que
    SIEMPRE fuerza fondo gris y solo cambia el color del texto), esta
    pill deja que el FONDO cambie de color según `color` -- "el fondo de
    la pill también cambia de color, fondo pastel + texto oscuro encima,
    mismo estilo visual que el resto de pills de Wingman". Reusa las
    clases sup-pill-{color} que ya existían en theme.py (orange/purple/
    gray/red/yellow), no hace falta CSS nuevo.
    """
    return f'<span class="sup-pill sup-pill-{color}">{valor}</span>'


def _rend_color_conversion(pct):
    if pct < 10:
        return "red"
    if pct <= 20:
        return "blue"
    if pct <= 30:
        return "green"
    return "purple"


def _rend_color_bookings(pct):
    # Objetivo Ads Bookings: rojo <90, azul 90-95, verde >95, morado >105.
    if pct < 90:
        return "red"
    if pct <= 95:
        return "blue"
    if pct <= 105:
        return "green"
    return "purple"


def _rend_color_revenue_pace(pct):
    # Objetivo Ads Revenue (ritmo): rojo <80, amarillo 80-89, azul
    # 90-99, verde >=100, morado >=105.
    if pct < 80:
        return "red"
    if pct < 90:
        return "yellow"
    if pct < 100:
        return "blue"
    if pct < 105:
        return "green"
    return "purple"


def _rend_color_md(att_pct):
    # Objetivo MD Full/PRO: rojo <80, azul 80-90, verde >90, morado >100.
    if att_pct < 80:
        return "red"
    if att_pct <= 90:
        return "blue"
    if att_pct <= 100:
        return "green"
    return "purple"


def _correo_corto(email):
    """
    "alejandro.guerrero@rappi.com" -> "alejandro.guerrero@..." -- pedido
    explícito de Sabas (agosto 2026): con que se vea el usuario y el
    arroba alcanza, no hace falta el dominio completo. Se usa en
    Rendimiento Farmer/País en vez de mostrar el correo entero (que
    forzaba el ancho de toda la fila con correos largos como
    luisfernando.hernandez@rappi.com).
    """
    usuario = str(email).split("@")[0]
    return f"{usuario}@..."


def _fila_rendimiento_html(row):
    """
    Construye el <tr> de rendimiento para UNA fila (un Farmer). Reusada
    tanto por render_tabla_farmers_supervisor (una fila por Farmer del
    país) como por render_rendimiento_farmer (una sola fila, la propia).
    `row` es cualquier objeto con los atributos que trae
    tabla_farmers_por_pais: farmer, contactos_efectivos, target,
    cumplimiento_pct, ads_n, ads_total, ads_pct, ups_n, ups_total,
    ups_pct, md_n, md_total, md_pct.

    ads_n/ads_total/ads_pct (agosto 2026, segunda vuelta): ya NO son
    "Conversión Ads" -- son "Adquisición Ads" (adquisicion_ads_for). ads_n
    = Never Ads convertidos este mes, ads_total = camino más corto para
    cerrar el gap real (con piso de días hábiles del mes -- ver
    _camino_mas_corto en data_layer.py), ads_pct = RITMO/PACE ya en
    escala 0-100 (no multiplicar por 100 de nuevo, a diferencia de md_pct
    que sí viene en fracción 0-1). Se pinta con dl.pace_color_ads_upsell
    -- rojo/azul/verde/morado (agosto 2026, octava vuelta: semáforo
    propio de 4 niveles, DISTINTO al pace_color de 3 niveles que usa
    Contactos Efectivos -- pedido explícito de Sabas), no con
    _rend_color_conversion (esa sigue solo para la pill de MD). ups_n/
    ups_total/ups_pct (Upselling Ads) usan exactamente el mismo criterio
    y la misma función de color.

    ups_n/ups_total/ups_pct (agosto 2026, tercera vuelta): "Upselling
    Ads", columna hermana de Adquisición Ads (upselling_ads_for). Mismo
    denominador tipo camino-más-corto/piso días hábiles, pero para
    marcas tipo upsell. NUMERADOR AÚN NO DEFINIDO (pendiente hoja
    alimentadora nueva, confirmado por Sabas) -- ups_n siempre llega en
    0 por ahora, la pill se ve como "0 / N - 0%" hasta que se conecte.
    """
    if row.target > 0:
        cumpl = round(row.cumplimiento_pct)
        color_ef = dl.pace_color(cumpl)
        efectivos_pill = _rend_pill_a(
            f"{row.contactos_efectivos:.0f} / {row.target:.0f} - {cumpl}%", color_ef
        )
        sort_efectivos = cumpl
    else:
        efectivos_pill = _rend_pill(f"{row.contactos_efectivos:.0f}", "purple")
        sort_efectivos = row.contactos_efectivos

    ads_pct_val = row.ads_pct
    ads_pill = _rend_pill_a(
        f"{row.ads_n} / {row.ads_total} - {ads_pct_val:.0f}%",
        dl.pace_color_ads_upsell(ads_pct_val),
    )
    ups_pct_val = row.ups_pct
    ups_pill = _rend_pill_a(
        f"{row.ups_n} / {row.ups_total} - {ups_pct_val:.0f}%",
        dl.pace_color_ads_upsell(ups_pct_val),
    )
    md_pct_val = row.md_pct * 100
    md_pill = _rend_pill_a(
        f"{row.md_n} / {row.md_total} - {md_pct_val:.0f}%",
        _rend_color_conversion(md_pct_val),
    )

    ads_kam = dl.ads_kam_for(row.farmer)
    if ads_kam["att_bookings_pct"] is not None:
        bookings_val = ads_kam["att_bookings_pct"]
        bookings_pill = _rend_pill_a(f"{bookings_val:.0f}%", _rend_color_bookings(bookings_val))
    else:
        bookings_pill = _rend_pill("Sin dato", "gray")
        bookings_val = -1

    if ads_kam["revenue_pace_pct"] is not None:
        revenue_val = ads_kam["revenue_pace_pct"]
        # Formato "Att real% / Att esperado% - Pace%" (agosto 2026,
        # decimoctava vuelta -- pedido explícito de Sabas): en vez de
        # mostrar solo el pace final ("69%"), se muestra el Att% real de
        # hoy sobre el Att% que correspondería a este punto del mes --
        # así el farmer ve "18% / 21%" y entiende que va casi al día, no
        # solo un número aislado que puede confundir como "voy bien"
        # sin referencia del punto del mes. Si por algún motivo no hay
        # att_revenue_esperado_pct (mes cerrado, dias_transcurridos=None
        # -- ver _dias_calendario_mes), cae al formato viejo de solo el
        # pace, para no mostrar "None%".
        att_real = ads_kam.get("att_revenue_pct")
        att_esperado = ads_kam.get("att_revenue_esperado_pct")
        if att_real is not None and att_esperado is not None:
            revenue_pill = _rend_pill_a(
                f"{att_real:.0f}% / {att_esperado:.0f}% - {revenue_val:.0f}%",
                _rend_color_revenue_pace(revenue_val),
            )
        else:
            revenue_pill = _rend_pill_a(f"{revenue_val:.0f}%", _rend_color_revenue_pace(revenue_val))
    else:
        revenue_pill = _rend_pill("Sin dato", "gray")
        revenue_val = -1

    md_kam = dl.md_kam_for(row.farmer)
    if md_kam["att_md_total_pct"] is not None:
        att = md_kam["att_md_total_pct"] * 100
        md_full_pill = _rend_pill_a(
            f"{md_kam['md_total_pct']*100:.2f}% / {md_kam['tgt_md_total_pct']*100:.2f}% - {att:.0f}%",
            _rend_color_md(att),
        )
        md_full_val = att
    else:
        md_full_pill = _rend_pill("Sin dato", "gray")
        md_full_val = -1

    if md_kam["att_md_pro_pct"] is not None:
        att_pro = md_kam["att_md_pro_pct"] * 100
        md_pro_pill = _rend_pill_a(
            f"{md_kam['md_pro_pct']*100:.2f}% / {md_kam['tgt_md_pro_pct']*100:.2f}% - {att_pro:.0f}%",
            _rend_color_md(att_pro),
        )
        md_pro_val = att_pro
    else:
        md_pro_pill = _rend_pill("Sin dato", "gray")
        md_pro_val = -1

    # data-sort en cada <td>: valor numérico crudo, usado por el script de
    # ordenamiento de la tabla (pedido explícito de Sabas, agosto 2026) --
    # el texto visible de la pill trae emoji/formato, no sirve para
    # comparar; el correo (primera columna) ordena alfabético (data-sort
    # = el string tal cual, comparado como texto).
    return (
        "<tr>"
        f'<td data-sort="{html_lib.escape(row.farmer)}"><span class="sup-pill sup-pill-gray sup-pill-farmer" style="color:{COLORS["text"]};">{_correo_corto(row.farmer)}</span></td>'
        f'<td data-sort="{sort_efectivos}">{efectivos_pill}</td>'
        f'<td data-sort="{ads_pct_val:.2f}">{ads_pill}</td>'
        f'<td data-sort="{ups_pct_val:.2f}">{ups_pill}</td>'
        f'<td data-sort="{md_pct_val:.2f}">{md_pill}</td>'
        f'<td data-sort="{bookings_val:.2f}">{bookings_pill}</td>'
        f'<td data-sort="{revenue_val:.2f}">{revenue_pill}</td>'
        f'<td data-sort="{md_full_val:.2f}">{md_full_pill}</td>'
        f'<td data-sort="{md_pro_val:.2f}">{md_pro_pill}</td>'
        "</tr>"
    )


_RENDIMIENTO_THEAD = (
    "<thead><tr>"
    "<th>Farmer</th><th>Contactos Efectivos</th><th>Adquisición Ads</th>"
    "<th>Upselling Ads</th>"
    "<th>Conversión MD</th><th>Objetivo Ads Bookings</th><th>Objetivo Ads Revenue</th>"
    "<th>Objetivo MD Full</th><th>Objetivo MD PRO</th>"
    "</tr></thead>"
)


def _tabla_fullscreen_dialog(pais, fs_flag_key):
    """
    Modal nativo de Streamlit (st.dialog) con la tabla de Rendimiento
    País/Farmer agrandada -- REEMPLAZA el intento anterior de "pantalla
    completa" via botón HTML + JS custom en un iframe de
    st_components.html() (agosto 2026, duodécima vuelta -- "carga solo 1
    y luego se queda pegado con el cambio de país").

    BUG REAL DE RAÍZ #1 (por qué se abandona el enfoque JS por completo):
    las tres vueltas anteriores (novena, décima, undécima) intentaron
    distintas variantes de "un botón HTML dentro de un <div>, con JS en
    un iframe de st_components.html() que lo engancha" -- MutationObserver,
    delegación de eventos a nivel documento, reenganche con
    cloneNode/replaceChild, reintentos con setInterval/setTimeout. Ninguna
    funcionó de forma confiable al cambiar de país. La causa de fondo es
    estructural: el botón vive en el DOM principal de Streamlit, pero el
    JS que lo controla vive en un iframe EFÍMERO que Streamlit crea y
    destruye en cada rerun.

    BUG REAL DE RAÍZ #2 (agosto 2026, decimotercera vuelta -- "los
    botones funcionan una sola vez y se quedan pegados"): la duodécima
    vuelta invocaba st.dialog() DIRECTO dentro del `if st.button(...)`
    en render_tabla_farmers_supervisor. Documentación oficial de
    Streamlit confirma el mecanismo exacto: "st.dialog inherits behavior
    from st.fragment. When a user interacts with an input widget created
    inside a dialog function, Streamlit only reruns the dialog function
    instead of the full script" -- es decir, cualquier interacción
    DENTRO del modal (o su cierre) NO vuelve a correr el script completo,
    por lo que el `if st.button(...)` de afuera nunca se re-evalúa a
    True de nuevo, y st.dialog() deja de re-invocarse -- el modal de
    Streamlit queda "pegado" a medio camino. Fix: la apertura/cierre del
    dialog se controla con una bandera de session_state (fs_flag_key)
    que SIEMPRE se revisa al final de render_tabla_farmers_supervisor
    (fuera del `if` del botón), y esta función apaga la bandera por DOS
    caminos: (a) el parámetro on_dismiss='rerun' + callback _on_dismiss,
    que Streamlit invoca automáticamente cuando el usuario cierra con la
    X, clic afuera, o Esc; (b) un botón "Cerrar" explícito dentro del
    modal, para el caso en que el usuario prefiera un botón visible en
    vez de la X. Ambos dejan la bandera en False, así el próximo click
    del botón de afuera vuelve a abrir el modal desde cero.

    Dentro del modal, la tabla se re-renderiza con la clase
    sup-table-fullscreen (table-layout:auto, pill centrada, sin cortes).
    No es un clon del HTML ya pintado -- se reconstruye la fila HTML de
    nuevo, así siempre refleja el estado actual de los datos.
    """
    def _on_dismiss():
        # Se dispara cuando el usuario cierra el modal con la X, clic
        # afuera, o tecla Esc (on_dismiss='rerun' abajo) -- apaga la
        # bandera para que el modal no se reabra solo en el próximo
        # rerun, y para que el botón de afuera pueda volver a abrirlo.
        st.session_state[fs_flag_key] = False

    @st.dialog(f"📊 Rendimiento País — {pais}", width="large", on_dismiss=_on_dismiss)
    def _dialog():
        tabla = dl.tabla_farmers_por_pais(pais)
        if tabla.empty:
            st.info("No hay farmers activos en este país todavía.")
        else:
            filas_html = [_fila_rendimiento_html(row) for row in tabla.itertuples()]
            st.markdown(
                f'<table class="sup-table sup-table-fullscreen">'
                f"{_RENDIMIENTO_THEAD}"
                f"<tbody>{''.join(filas_html)}</tbody>"
                "</table>",
                unsafe_allow_html=True,
            )
        # Botón de cierre explícito DENTRO del modal, además de la X
        # nativa -- ambos caminos apagan la bandera (este vía el mismo
        # patrón que _on_dismiss, la X vía el callback de on_dismiss).
        if st.button("Cerrar", key=f"fs-close-{fs_flag_key}"):
            st.session_state[fs_flag_key] = False
            st.rerun()

    _dialog()


def _farmer_fullscreen_dialog(farmer_email, fila_html, fs_flag_key):
    """
    Misma idea que _tabla_fullscreen_dialog pero para Rendimiento Farmer
    (una sola fila) -- ver esa función para el detalle completo del bug
    de raíz (session_state como bandera persistente en vez de invocar el
    dialog directo dentro del `if st.button`) y por qué se abandonó el
    enfoque JS.
    """
    def _on_dismiss():
        st.session_state[fs_flag_key] = False

    @st.dialog("📊 Rendimiento Farmer", width="large", on_dismiss=_on_dismiss)
    def _dialog():
        st.markdown(
            f'<table class="sup-table sup-table-single sup-table-fullscreen">'
            f"{_RENDIMIENTO_THEAD}"
            f"<tbody>{fila_html}</tbody>"
            "</table>",
            unsafe_allow_html=True,
        )
        if st.button("Cerrar", key=f"fs-close-{fs_flag_key}"):
            st.session_state[fs_flag_key] = False
            st.rerun()

    _dialog()


def render_tabla_farmers_supervisor(pais):
    """
    Tabla "Rendimiento País", debajo de Brand Coverage + Contact
    Performance -- pedido explícito de Sabas (agosto 2026), con sistema
    de semáforo de colores por columna (ver _fila_rendimiento_html para
    el detalle de umbrales de cada columna).

    Interactiva (pedido explícito, agosto 2026): columnas redimensionables
    arrastrando el borde del header, y ordenables (mayor↔menor) mediante
    un botón dedicado (⇅) en cada header -- ver _render_table_interactivity.
    También tiene botón de pantalla completa (⛶) para ver las 9 columnas
    a su ancho natural, sin cortes -- vía st.dialog nativo.

    BUG REAL CORREGIDO (agosto 2026, decimotercera vuelta -- "los botones
    de esa tabla funcionan una sola vez y se quedan pegados"): la
    duodécima vuelta invocaba _tabla_fullscreen_dialog() DIRECTO dentro
    del `if st.button(...)`. Streamlit reruns TODO el script en cada
    interacción -- incluida cualquier interacción DENTRO del propio
    modal, o el cierre del modal con la X. En ese rerun posterior, el
    usuario no volvió a hacer click físico en el botón, así que
    st.button() vuelve a evaluar False -- el bloque `if` no vuelve a
    ejecutarse y por lo tanto el dialog() tampoco se vuelve a invocar en
    ese rerun. Streamlit SÍ tiene una forma soportada de mantener un
    dialog abierto a través de reruns (re-invocando la función del
    dialog en cada script run mientras una bandera de session_state siga
    en True), pero invocarlo solo una vez dentro del `if` del botón NO
    la cumple -- de ahí que "funcionaba la primera vez" (el rerun
    inmediato al click SÍ traía el st.button()==True) y se "quedaba
    pegado" después (cualquier rerun subsiguiente, el botón ya no estaba
    en True y el dialog dejaba de re-invocarse, pero Streamlit lo
    consideraba trabado a medio camino en su propio manejo interno de
    diálogos).

    Fix: el click del botón SOLO setea una bandera en session_state
    (dl.FULLSCREEN_PAIS_KEY). La apertura real del dialog() se evalúa
    SIEMPRE al final de la función, leyendo esa bandera -- así en CADA
    rerun (sea por el click original, por una interacción dentro del
    modal, o por el cierre con la X) el código vuelve a preguntar "¿la
    bandera sigue en True?" y re-invoca st.dialog() de forma consistente,
    en vez de depender de que st.button() vuelva a dar True en un rerun
    donde nadie volvió a hacer click.

    Una fila por Farmer del país. Para la version de un solo Farmer (su
    propia fila en Gestión General), ver render_rendimiento_farmer.
    """
    tabla = dl.tabla_farmers_por_pais(pais)
    if tabla.empty:
        st.info("No hay farmers activos en este país todavía.")
        return

    filas_html = [_fila_rendimiento_html(row) for row in tabla.itertuples()]
    table_id = f"rend-pais-{pais}"
    wrapper_id = f"rend-pais-wrap-{pais}"
    fs_flag_key = f"fs_open_pais_{pais}"

    st.markdown(
        '<div class="mgmt-card-title" style="margin:18px 0 8px;">📊 Rendimiento País</div>',
        unsafe_allow_html=True,
    )
    if st.button("⛶ Pantalla completa", key=f"fs-btn-{pais}"):
        st.session_state[fs_flag_key] = True
    st.markdown(
        f'<div class="mgmt-card" id="{wrapper_id}">'
        f'<table id="{table_id}" class="sup-table sup-table-interactive">'
        f"{_RENDIMIENTO_THEAD}"
        f"<tbody>{''.join(filas_html)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )
    _render_table_interactivity(table_id)

    # Se evalúa SIEMPRE (no solo en el rerun del click) -- ver docstring.
    if st.session_state.get(fs_flag_key):
        _tabla_fullscreen_dialog(pais, fs_flag_key)


# =========================
# SECCIÓN: TRABAJABLES (agosto 2026, vigésima segunda vuelta)
# =========================
# 4 tabs con el top 10 de marcas priorizadas por gap/oportunidad para
# cada palanca (Adquisición Ads, Upselling Ads, Adquisición MD,
# Recuperación Churn) -- pedido explícito de Sabas, construido sobre las
# 4 funciones de data_layer.py ya validadas a mano en el chat para
# sabas.ramirez antes de convertirlas en feature. Vista Farmer: solo SUS
# marcas. Vista Supervisor: TODAS las marcas del país agregadas en un
# solo ranking competitivo, con columna "Farmer" mostrando el dueño.

_TRAB_THEAD_ADQ_ADS = (
    "<thead><tr><th>#</th><th>Marca</th><th>Gap (USD)</th><th>Budget semanal (ARS)</th></tr></thead>"
)
_TRAB_THEAD_ADQ_ADS_SUP = (
    "<thead><tr><th>#</th><th>Marca</th><th>Farmer</th><th>Gap (USD)</th><th>Budget semanal (ARS)</th></tr></thead>"
)
_TRAB_THEAD_UPS_ADS = (
    "<thead><tr><th>#</th><th>Marca</th><th>Real actual</th><th>Target</th>"
    "<th>Gap (USD)</th><th>Upsell semanal (ARS)</th></tr></thead>"
)
_TRAB_THEAD_UPS_ADS_SUP = (
    "<thead><tr><th>#</th><th>Marca</th><th>Farmer</th><th>Real actual</th><th>Target</th>"
    "<th>Gap (USD)</th><th>Upsell semanal (ARS)</th></tr></thead>"
)
_TRAB_THEAD_ADQ_MD = (
    "<thead><tr><th>#</th><th>Marca</th><th>Store Status</th></tr></thead>"
)
_TRAB_THEAD_ADQ_MD_SUP = (
    "<thead><tr><th>#</th><th>Marca</th><th>Farmer</th><th>Store Status</th></tr></thead>"
)
_TRAB_THEAD_CHURN = (
    "<thead><tr><th>#</th><th>Categoría</th><th>Marca</th><th>Contacto</th></tr></thead>"
)
_TRAB_THEAD_CHURN_SUP = (
    "<thead><tr><th>#</th><th>Categoría</th><th>Marca</th><th>Farmer</th><th>Contacto</th></tr></thead>"
)


def _trab_num_pill(n):
    return _trab_pill(str(n), "orange")


def _trab_marca_pill(brand):
    return _trab_pill(html_lib.escape(str(brand)), "purple")


def render_trabajables_adquisicion_ads(farmer_or_list, is_supervisor):
    """Tab "Adquisición Ads" de Trabajables -- ver trabajables_adquisicion_ads en data_layer.py."""
    df = dl.trabajables_adquisicion_ads(farmer_or_list)
    if df.empty:
        st.info("No hay marcas de adquisición pendientes ahora mismo. 🎉")
        return

    filas = []
    for i, row in enumerate(df.itertuples(), 1):
        farmer_td = f'<td>{_trab_pill(html_lib.escape(row.farmer), "gray")}</td>' if is_supervisor else ""
        filas.append(
            "<tr>"
            f"<td>{_trab_num_pill(i)}</td>"
            f"<td>{_trab_marca_pill(row.brand)}</td>"
            f"{farmer_td}"
            f'<td>{_trab_pill(f"${row.gap_usd:,.2f}".replace(",", "."), "gray")}</td>'
            f'<td>{_trab_pill(dl.fmt_money(row.budget_semanal_ars, "ARS"), "gray")}</td>'
            "</tr>"
        )
    thead = _TRAB_THEAD_ADQ_ADS_SUP if is_supervisor else _TRAB_THEAD_ADQ_ADS
    st.markdown(
        f'<div class="mgmt-card"><table class="sup-table sup-table-trab">{thead}<tbody>{"".join(filas)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_trabajables_upselling_ads(farmer_or_list, is_supervisor):
    """Tab "Upselling Ads" de Trabajables -- ver trabajables_upselling_ads en data_layer.py."""
    df = dl.trabajables_upselling_ads(farmer_or_list)
    if df.empty:
        st.info("No hay marcas de upselling pendientes ahora mismo. 🎉")
        return

    filas = []
    for i, row in enumerate(df.itertuples(), 1):
        farmer_td = f'<td>{_trab_pill(html_lib.escape(row.farmer), "gray")}</td>' if is_supervisor else ""
        filas.append(
            "<tr>"
            f"<td>{_trab_num_pill(i)}</td>"
            f"<td>{_trab_marca_pill(row.brand)}</td>"
            f"{farmer_td}"
            f'<td>{_trab_pill(dl.fmt_money(row.real_actual, "USD"), "gray")}</td>'
            f'<td>{_trab_pill(dl.fmt_money(row.target, "USD"), "gray")}</td>'
            f'<td>{_trab_pill(dl.fmt_money(row.gap_usd, "USD"), "gray")}</td>'
            f'<td>{_trab_pill(dl.fmt_money(row.upsell_semanal_ars, "ARS"), "gray")}</td>'
            "</tr>"
        )
    thead = _TRAB_THEAD_UPS_ADS_SUP if is_supervisor else _TRAB_THEAD_UPS_ADS
    st.markdown(
        f'<div class="mgmt-card"><table class="sup-table sup-table-trab">{thead}<tbody>{"".join(filas)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_trabajables_adquisicion_md(farmer_or_list, is_supervisor):
    """
    Tab "Adquisición MD" de Trabajables -- ver trabajables_adquisicion_md
    en data_layer.py. La columna GMV se ORDENA por (mayor oportunidad
    primero) pero ya NO se MUESTRA en la tabla (pedido explícito de
    Sabas, agosto 2026, vigésima tercera vuelta) -- el orden de las filas
    sigue siendo por GMV descendente, solo se quitó la columna visible.
    """
    df = dl.trabajables_adquisicion_md(farmer_or_list)
    if df.empty:
        st.info("No hay marcas sin Markdown activo ahora mismo. 🎉")
        return

    filas = []
    for i, row in enumerate(df.itertuples(), 1):
        farmer_td = f'<td>{_trab_pill(html_lib.escape(row.farmer), "gray")}</td>' if is_supervisor else ""
        filas.append(
            "<tr>"
            f"<td>{_trab_num_pill(i)}</td>"
            f"<td>{_trab_marca_pill(row.brand)}</td>"
            f"{farmer_td}"
            f'<td>{_trab_pill(html_lib.escape(row.store_status), "gray")}</td>'
            "</tr>"
        )
    thead = _TRAB_THEAD_ADQ_MD_SUP if is_supervisor else _TRAB_THEAD_ADQ_MD
    st.markdown(
        f'<div class="mgmt-card"><table class="sup-table sup-table-trab">{thead}<tbody>{"".join(filas)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_trabajables_recuperacion_churn(farmer_or_list, is_supervisor):
    """
    Tab "Recuperación Churn" de Trabajables -- ver
    trabajables_recuperacion_churn en data_layer.py. Única tab con
    colores de categoría propios: pill de "Churn" en ROJO, pill de "PW1"
    en AMARILLO (pedido explícito de Sabas: "a excepto de las categorías
    de churn que esas llevan su color rojo y amarillo correspondiente"
    -- el resto de columnas de este tab sí van grises, igual que los
    otros 3 tabs). Columna GMV: se ORDENA por ella (Churn siempre
    primero, luego mayor GMV) pero ya NO se MUESTRA (pedido explícito de
    Sabas, agosto 2026, vigésima tercera vuelta).
    """
    df = dl.trabajables_recuperacion_churn(farmer_or_list)
    if df.empty:
        st.info("No hay marcas en Churn o PW1 ahora mismo. 🎉")
        return

    filas = []
    for i, row in enumerate(df.itertuples(), 1):
        cat_color = "red" if row.categoria == "Churn" else "yellow"
        farmer_td = f'<td>{_trab_pill(html_lib.escape(row.farmer), "gray")}</td>' if is_supervisor else ""
        filas.append(
            "<tr>"
            f"<td>{_trab_num_pill(i)}</td>"
            f"<td>{_trab_pill(row.categoria, cat_color)}</td>"
            f"<td>{_trab_marca_pill(row.brand)}</td>"
            f"{farmer_td}"
            f'<td>{_trab_pill(html_lib.escape(row.contacto), "gray")}</td>'
            "</tr>"
        )
    thead = _TRAB_THEAD_CHURN_SUP if is_supervisor else _TRAB_THEAD_CHURN
    st.markdown(
        f'<div class="mgmt-card"><table class="sup-table sup-table-trab sup-table-trab-churn">{thead}<tbody>{"".join(filas)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_trabajables(farmer_or_list, is_supervisor):
    """
    Sección "Trabajables" completa: 4 tabs con st.tabs nativo de
    Streamlit -- pedido explícito de Sabas. `farmer_or_list` es un email
    (vista Farmer) o una lista de emails (vista Supervisor, agregando
    todo el país en un solo ranking competitivo por tab).
    """
    st.markdown('<div class="mgmt-card-title">🛠️ Trabajables</div>', unsafe_allow_html=True)
    tab_adq_ads, tab_ups_ads, tab_adq_md, tab_churn = st.tabs(
        ["Adquisición Ads", "Upselling Ads", "Adquisición MD", "Recuperación Churn"]
    )
    with tab_adq_ads:
        render_trabajables_adquisicion_ads(farmer_or_list, is_supervisor)
    with tab_ups_ads:
        render_trabajables_upselling_ads(farmer_or_list, is_supervisor)
    with tab_adq_md:
        render_trabajables_adquisicion_md(farmer_or_list, is_supervisor)
    with tab_churn:
        render_trabajables_recuperacion_churn(farmer_or_list, is_supervisor)


def render_login_tracker_supervisor():
    """
    Tabla de login/logout de TODO el equipo (28 farmers, no filtrada por
    país) -- pedido explícito de Sabas (agosto 2026): 4 columnas (Farmer,
    Última entrada, Tiempo de uso, Última salida), con SOLO el último
    valor conocido por farmer (no historial acumulado). Dentro de un
    st.expander colapsado por defecto ("una opción desplegable... para no
    saturar"), debajo de la tabla de Rendimiento País.

    Ver load_login_log/registrar_login/registrar_logout en data_layer.py
    para el mecanismo de persistencia (GitHub via API, porque el disco
    de Streamlit Cloud se resetea en cada redeploy).
    """
    if not dl._github_configurado():
        # Sin secretos de GitHub configurados, el tracking está inactivo
        # -- se avisa una sola vez, sin ruido visual si nadie lo necesita
        # (colapsado dentro del expander).
        with st.expander("🕒 Actividad del equipo (login/logout)"):
            st.info(
                "El registro de actividad no está configurado todavía. "
                "Hace falta un Personal Access Token de GitHub guardado como "
                "secreto de Streamlit Cloud (GITHUB_TOKEN, GITHUB_REPO)."
            )
        return

    log = dl.load_login_log()
    activos = set(dl.list_farmers_activos())

    with st.expander("🕒 Actividad del equipo (login/logout)"):
        if log.empty:
            st.info("Todavía no hay registros de actividad -- van a aparecer a medida que el equipo entre a Wingman.")
            return

        # Se muestra TODO el equipo activo, tengan o no registro todavía
        # (los que nunca entraron aparecen con "—" en sus 3 columnas) --
        # así el supervisor ve de un vistazo quién no ha usado la
        # herramienta en absoluto, no solo quién sí.
        log_idx = log.set_index("farmer")
        filas = []
        for email in sorted(activos):
            if email in log_idx.index:
                row = log_idx.loc[email]
                entrada = row["ultima_entrada"] if pd.notna(row["ultima_entrada"]) else "—"
                salida = row["ultima_salida"] if pd.notna(row["ultima_salida"]) else "—"
                tiempo = f'{row["tiempo_uso_min"]:.0f} min' if pd.notna(row["tiempo_uso_min"]) else "—"
            else:
                entrada = salida = tiempo = "—"
            filas.append({
                "Farmer": _correo_corto(email),
                "Última entrada": entrada,
                "Tiempo de uso": tiempo,
                "Última salida": salida,
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


def render_rendimiento_farmer(farmer_email):
    """
    "Rendimiento Farmer": la misma tabla/pills que Rendimiento País del
    Supervisor, pero con UNA sola fila -- la del propio Farmer. Va debajo
    de Contact Performance en su Gestión General (pedido explícito de
    Sabas, agosto 2026).

    Se arma la fila directamente (no via tabla_farmers_por_pais, que
    calcula y ordena TODO el país) para no cargar el resto del equipo
    solo para mostrar un renglón.
    """
    cp = dl.contact_performance_for(farmer_email)
    bc = dl.brand_coverage_for(farmer_email)
    conv = dl.conversion_for(farmer_email)
    adq = dl.adquisicion_ads_for(farmer_email)
    ups = dl.upselling_ads_for(farmer_email)
    target = dl.target_for(farmer_email)
    # BUG REAL CORREGIDO (agosto 2026): usaba el acumulado crudo
    # (total_effective/target*100) en vez del RITMO (pace_pct) que
    # contact_performance_for ya calcula -- mismo bug que se corrigió en
    # tabla_farmers_por_pais (vista Supervisor) la sesión pasada, pero
    # esta función arma la fila directamente sin pasar por ahí (para no
    # cargar todo el país solo para una fila), así que tenía su propia
    # copia del cálculo sin corregir. Ahora ambas vistas (Supervisor y
    # Farmer) usan el mismo criterio.
    if target > 0 and cp.get("pace_pct") is not None:
        cumplimiento = cp["pace_pct"]
    elif target > 0:
        cumplimiento = cp["total_effective"] / target * 100
    else:
        cumplimiento = -1

    class _Fila:
        pass

    row = _Fila()
    row.farmer = farmer_email
    row.contactos_efectivos = cp["total_effective"]
    row.target = target
    row.cumplimiento_pct = cumplimiento
    row.ads_pct, row.ads_n, row.ads_total = adq["adq_pct"], adq["adq_n"], adq["adq_target"]
    row.ups_pct, row.ups_n, row.ups_total = ups["ups_pct"], ups["ups_n"], ups["ups_target"]
    row.md_pct, row.md_n, row.md_total = conv["md_pct"], conv["md_conv"], conv["md_total"]

    fila_html = _fila_rendimiento_html(row)
    table_id = f"rend-farmer-{abs(hash(farmer_email))}"
    wrapper_id = f"rend-farmer-wrap-{abs(hash(farmer_email))}"
    fs_flag_key = f"fs_open_farmer_{abs(hash(farmer_email))}"

    st.markdown(
        '<div class="mgmt-card-title" style="margin:18px 0 8px;">📊 Rendimiento Farmer</div>',
        unsafe_allow_html=True,
    )
    if st.button("⛶ Pantalla completa", key=f"fs-btn-{table_id}"):
        st.session_state[fs_flag_key] = True
    st.markdown(
        f'<div class="mgmt-card" id="{wrapper_id}">'
        f'<table id="{table_id}" class="sup-table sup-table-single sup-table-interactive">'
        f"{_RENDIMIENTO_THEAD}"
        f"<tbody>{fila_html}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )
    _render_table_interactivity(table_id)

    # Se evalúa SIEMPRE (no solo en el rerun del click) -- mismo patrón
    # que render_tabla_farmers_supervisor, ver _tabla_fullscreen_dialog
    # para el detalle completo del bug de raíz.
    if st.session_state.get(fs_flag_key):
        _farmer_fullscreen_dialog(farmer_email, fila_html, fs_flag_key)

    _render_comision_ads_proyectada(farmer_email)


def _render_comision_ads_proyectada(farmer_email):
    """
    Proyección de comisión Revenue Share ADS -- pedido explícito de Sabas
    (agosto 2026, séptimo ajuste), debajo de Rendimiento Farmer. Ver
    comision_ads_proyectada_for en data_layer.py para el modelo completo
    (3 buckets, replica de Growth OS, con proyección "piso" al 91% del
    target cuando el ritmo real da menos, y notas de bloqueo separadas
    por Bookings/Revenue/MD/Contactos -- se muestran TODAS las que
    apliquen, no solo la peor).
    """
    r = dl.comision_ads_proyectada_for(farmer_email)
    if r is None:
        return  # sin target de Ads o de Contactos disponible, no hay nada que proyectar

    # Todas las notas de bloqueo juntas -- Ads (Bookings/Revenue) +
    # Contactos/MD (pedido explícito: "si los dos están rotos se
    # muestran las dos notas", y "el mínimo posible siempre son 3 cosas").
    notas_bloqueo = list(r.get("bloqueos_ads", []))
    if r["metricas_flojas"]:
        metricas_txt = " y ".join(r["metricas_flojas"])
        notas_bloqueo.append(f"Tu {metricas_txt} está por debajo del 90% de ritmo")

    alerta_html = ""
    if notas_bloqueo:
        items_html = "".join(f"<div>⚠️ {n}</div>" for n in notas_bloqueo)
        alerta_html = (
            '<div style="margin-top:10px;padding:10px 12px;border-radius:10px;'
            f'background:rgba(251,191,36,0.14);color:#A97A1E;font-size:12.5px;font-weight:600;'
            f'line-height:1.6;">{items_html}'
            f"<div style='margin-top:4px;font-weight:500;'>Afiná ahí para poder tomar esta plata de la mesa.</div>"
            f"</div>"
        )

    cap_html = ""
    if r["topeado_por_cap"]:
        cap_html = (
            f'<div style="font-size:11.5px;color:{COLORS["muted"]};margin-top:4px;">'
            f'Antes del tope mensual de USD $2.000: USD ${r["total_usd_uncapped"]:,.0f}</div>'.replace(",", ".")
        )

    buckets_html = "".join(
        f'<span class="sup-pill sup-pill-gray" style="margin-right:6px;color:{COLORS["muted"]};">'
        f'{label}: {dl.fmt_money(valor, "USD")}</span>'
        for label, valor in [
            ("Bucket 1 (90-100%, 10%)", r["bucket1_usd"]),
            ("Bucket 2 (100-120%, 20%)", r["bucket2_usd"]),
            ("Bucket 3 (>120%, 30%)", r["bucket3_usd"]),
        ]
    )

    # Indicador de que el número mostrado es la proyección PISO (al 91%
    # del target), no el resultado del ritmo real actual -- pedido
    # explícito de Sabas: siempre mostrar como mínimo lo que se ganaría
    # llegando al 91%, aclarando que es una meta alcanzable, no lo que ya
    # se está ganando hoy.
    piso_html = ""
    if r["es_piso"]:
        piso_html = (
            f'<div style="font-size:11.5px;color:{COLORS["brand_purple"]};font-weight:700;margin-top:2px;">'
            f"🎯 Esto es lo que ganarías llegando al 91% del target — con tu ritmo actual "
            f"({r['revenue_pace_pct']:.0f}%) todavía no se desbloquea.</div>"
        )

    st.markdown(
        '<div class="mgmt-card" style="margin-top:14px;">'
        '<div class="mgmt-card-title">💵 Comisión Ads proyectada · al ritmo actual</div>'
        f'<div style="font-size:11.5px;color:{COLORS["muted"]};margin-bottom:8px;">'
        f'Revenue proyectado: {dl.fmt_money(r["revenue_pace_result"], "USD")} de '
        f'{dl.fmt_money(r["target_revenue"], "USD")} target ({r["revenue_pace_pct"]:.0f}% de ritmo)</div>'
        f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">'
        f'<div style="font-size:28px;font-weight:900;color:{COLORS["brand_orange"]};">'
        f'{dl.fmt_money(r["total_usd"], "USD")}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{COLORS["brand_purple"]};">'
        f'≈ {dl.fmt_money(r["total_cop"], "COP")}</div>'
        "</div>"
        f"{piso_html}"
        f'<div style="margin-top:8px;">{buckets_html}</div>'
        f"{cap_html}"
        f"{alerta_html}"
        "</div>",
        unsafe_allow_html=True,
    )


def render_loading_watcher():
    """
    Telón de carga -- arquitectura calcada del mecanismo real de Growth OS
    (page_management_dashboard / la función que arma el overlay 'gos-loading'),
    NO reinventada: los intentos anteriores con st.markdown() + time.sleep()
    + st.rerun() manual fallaban porque Streamlit no da ninguna garantía de
    cuándo el navegador terminó de pintar el frame anterior antes de que el
    siguiente rerun empiece a mutar el DOM -- el resultado real (confirmado
    con capturas) era el overlay y el contenido nuevo visibles a la vez,
    de forma persistente, no solo un instante de transición.

    La diferencia real de este enfoque:
    - Se usa st.components.v1.html() (NO st.markdown()) -- es la única forma
      de garantizar que el <script> se ejecute; st.markdown(unsafe_allow_html)
      inserta el HTML vía innerHTML, y los navegadores no ejecutan <script>
      insertado así.
    - El JS se inyecta en CADA ejecución del script (sin condición ninguna),
      y vive en window.parent (el documento real de la pestaña, no el iframe
      aislado de components.html) -- se re-engancha en cada rerun.
    - El overlay se muestra al INSTANTE del clic/Enter, desde el propio
      listener de JS -- no espera a que Python reciba el evento y decida
      mostrar nada.
    - Se oculta solo cuando el JS detecta que Streamlit realmente terminó de
      trabajar (querySelectors de status/spinner/skeleton de Streamlit +
      MutationObserver que vigila si el DOM sigue cambiando), no con un
      time.sleep() de duración fija adivinada.
    - position:fixed con "left" calculado en tiempo real midiendo el ancho
      real del sidebar (getBoundingClientRect) -- el sidebar queda visible
      siempre, el overlay solo tapa el área de contenido.
    """
    from theme import LOGO_ICON_URI
    import json

    logo_js = json.dumps(LOGO_ICON_URI)
    bg = COLORS["bg"]
    txt = COLORS["muted"]
    track = COLORS["card2"]

    st_components.html(
        f"""
        <script>
        (function() {{
          var W, D;
          try {{ W = window.parent; D = W.document; }} catch (e) {{ return; }}
          if (!D || !D.body) return;

          try {{
            var s = D.getElementById('gw-loading-style');
            if (!s) {{ s = D.createElement('style'); s.id = 'gw-loading-style'; D.head.appendChild(s); }}
            s.textContent = `
              #gw-loading {{ position: fixed; z-index: 2147483200; display: flex;
                align-items: center; justify-content: center; background: {bg};
                font-family: 'Poppins', sans-serif; animation: gw-fade-in .12s ease-out; }}
              #gw-loading .gw-box {{ display: flex; flex-direction: column; align-items: center; gap: 16px; }}
              #gw-loading .gw-logo {{ height: 46px; width: auto; animation: gw-pulse 1.6s ease-in-out infinite; }}
              #gw-loading .gw-txt {{ font-size: 15px; font-weight: 700; color: {txt}; }}
              #gw-loading .gw-bar {{ width: 230px; height: 6px; border-radius: 999px; background: {track}; overflow: hidden; }}
              #gw-loading .gw-bar-fill {{ height: 100%; width: 38%; border-radius: 999px;
                background: {COLORS["brand_orange"]}; animation: gw-slide 1.1s ease-in-out infinite; }}
              @keyframes gw-slide {{ 0% {{ transform: translateX(-130%); }} 100% {{ transform: translateX(360%); }} }}
              @keyframes gw-fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
              @keyframes gw-pulse {{ 0%,100% {{ transform: scale(1); opacity: .92; }} 50% {{ transform: scale(1.06); opacity: 1; }} }}
            `;
          }} catch (e) {{}}

          var LOGO = {logo_js};
          var S = W.__gwNavState = W.__gwNavState || {{ sawBusy: false, shownAt: 0, lastAct: 0 }};

          function buildOverlay(label) {{
            var el = D.getElementById('gw-loading');
            if (!el) {{ el = D.createElement('div'); el.id = 'gw-loading'; D.body.appendChild(el); }}
            var safe = String(label == null ? '' : label)
              .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            el.innerHTML = '<div class="gw-box">' +
              '<img class="gw-logo" src="' + LOGO + '" alt="Wingman"/>' +
              '<div class="gw-txt">Cargando ' + safe + '…</div>' +
              '<div class="gw-bar"><div class="gw-bar-fill"></div></div></div>';
            el.style.display = 'flex';

            var left = 0;
            try {{
              var sb = D.querySelector('.st-key-wingman-sidebar');
              if (sb) {{
                var r = sb.getBoundingClientRect();
                if (r.width > 2 && r.right > 2 && r.right < 600) left = r.right;
              }}
            }} catch (e) {{}}
            el.style.left = left + 'px';
            el.style.top = '0px';
            el.style.right = '0px';
            el.style.bottom = '0px';

            try {{ W.clearTimeout(W.__gwLoadingKill); }} catch (e) {{}}
            W.__gwLoadingKill = W.setTimeout(removeOverlay, 25000);
          }}

          function removeOverlay() {{
            var el = D.getElementById('gw-loading');
            if (el) el.remove();
            try {{ W.clearTimeout(W.__gwLoadingKill); }} catch (e) {{}}
            W.__gwPendingNav = false;
            S.sawBusy = false;
          }}

          function startNav(label) {{
            W.__gwPendingNav = true;
            S.sawBusy = false;
            S.shownAt = Date.now();
            S.lastAct = S.shownAt;
            buildOverlay(label);
          }}

          function onNavClick(ev) {{
            try {{
              var btn = ev.target && ev.target.closest ? ev.target.closest('button') : null;
              if (!btn) return;
              var sidebar = D.querySelector('.st-key-wingman-sidebar');
              if (!sidebar || !sidebar.contains(btn)) return;
              // Ya no existe el componente sidebar nativo de Streamlit (es una
              // columna de layout normal), así que no debería haber ningún
              // botón de colapsar/expandir -- estos filtros quedan como
              // respaldo de bajo costo, por si algún otro control nativo de
              // Streamlit apareciera ahí en el futuro con un texto técnico
              // sin renderizar (ej. nombre crudo de ícono).
              var testid = btn.getAttribute('data-testid') || '';
              if (testid.indexOf('Sidebar') !== -1 || testid.indexOf('Collapse') !== -1) return;
              var ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
              if (ariaLabel.indexOf('sidebar') !== -1) return;
              var label = ((btn.innerText || btn.textContent) || '').trim();
              if (!label) return;
              // Cualquier texto en snake_case/sin espacios que parezca nombre
              // de ícono técnico (ej. "keyboard_double_arrow_left") tampoco es
              // una acción real -- filtro de respaldo por si el testid/aria
              // cambia de nombre en otra versión de Streamlit.
              if (/^[a-z_]+$/.test(label) && label.indexOf('_') !== -1) return;
              if (label.indexOf('Salir') !== -1) return;
              startNav(label.replace(/^[^\\w]+/, '').trim());
            }} catch (e) {{}}
          }}

          function isBrandSearchInput(t) {{
            if (!t || t.tagName !== 'INPUT') return false;
            var lbl = (t.getAttribute('aria-label') || '') + ' ' + (t.getAttribute('placeholder') || '');
            return /id de marca|otro id de marca/i.test(lbl);
          }}
          function onBrandKey(ev) {{
            try {{
              if (ev.key !== 'Enter') return;
              if (!isBrandSearchInput(ev.target)) return;
              var v = (ev.target.value || '').trim();
              if (!v) return;
              if (ev.target.__gwLastSearched === v) return;
              ev.target.__gwLastSearched = v;
              startNav('marca ' + v);
            }} catch (e) {{}}
          }}
          function onBrandFocusIn(ev) {{
            try {{ if (isBrandSearchInput(ev.target)) ev.target.__gwV0 = ev.target.value; }} catch (e) {{}}
          }}
          function onBrandFocusOut(ev) {{
            try {{
              var t = ev.target;
              if (!isBrandSearchInput(t)) return;
              var v = (t.value || '').trim();
              if (!v || t.__gwV0 === t.value) return;
              if (t.__gwLastSearched === v) return;
              t.__gwLastSearched = v;
              startNav('marca ' + v);
            }} catch (e) {{}}
          }}

          function streamlitBusy() {{
            try {{
              if (D.querySelector('[data-testid="stStatusWidget"]')) return true;
              if (D.querySelector('.stApp[data-test-script-state="running"]')) return true;
              if (D.querySelector('[data-test-script-state="running"]')) return true;
              if (D.querySelector('.stSpinner')) return true;
              if (D.querySelector('[data-testid="stSkeleton"]')) return true;
            }} catch (e) {{}}
            return false;
          }}

          function navTick() {{
            if (!W.__gwPendingNav) return;
            var now = Date.now();
            if (streamlitBusy()) {{ S.sawBusy = true; S.lastAct = now; return; }}
            if (now - S.shownAt < 450) return;
            if (now - S.lastAct < 650) return;
            if (!S.sawBusy && now - S.shownAt < 5000) return;
            W.__gwPendingNav = false;
            W.requestAnimationFrame(function() {{
              W.requestAnimationFrame(function() {{ W.setTimeout(removeOverlay, 60); }});
            }});
          }}

          try {{
            var old = W.__gwNavHandlers;
            if (old) {{
              D.removeEventListener('click', old.click, true);
              D.removeEventListener('keydown', old.key, true);
              D.removeEventListener('focusin', old.fin, true);
              D.removeEventListener('focusout', old.fout, true);
            }}
          }} catch (e) {{}}
          var H = {{ click: onNavClick, key: onBrandKey, fin: onBrandFocusIn, fout: onBrandFocusOut }};
          W.__gwNavHandlers = H;
          D.addEventListener('click', H.click, true);
          D.addEventListener('keydown', H.key, true);
          D.addEventListener('focusin', H.fin, true);
          D.addEventListener('focusout', H.fout, true);

          try {{ if (W.__gwNavMO) W.__gwNavMO.disconnect(); }} catch (e) {{}}
          try {{
            var mo = new W.MutationObserver(function() {{
              if (W.__gwPendingNav) S.lastAct = Date.now();
            }});
            var root = D.querySelector('[data-testid="stAppViewContainer"]') ||
                       D.querySelector('.stApp') || D.body;
            mo.observe(root, {{ childList: true, subtree: true }});
            W.__gwNavMO = mo;
          }} catch (e) {{}}

          try {{ if (W.__gwNavTick) W.clearInterval(W.__gwNavTick); }} catch (e) {{}}
          W.__gwNavTick = W.setInterval(navTick, 80);
        }})();
        </script>
        """,
        height=0,
    )


# =========================
# PANTALLA DE ENTRADA
# =========================
# Identificacion con correo + contraseña (password = usuario en minusculas).
# No es autenticacion fuerte -- ver nota en README -- pero ya no es un simple
# selector donde se ve al equipo completo.
#
# list_farmers_activos() (no list_farmers()) porque el equipo real quedo
# desincronizado de ASIGNACION: Arnold y Claudia salieron (se les quita el
# acceso aunque sigan en ASIGNACION) y los 6 de Fabian entraron (se les da
# acceso aunque aun no tengan fila en ASIGNACION).

VALID_EMAILS = set(dl.list_farmers_activos())
if not VALID_EMAILS:
    st.error("No pude cargar la asignación. Revisá que el workbook esté en `data/`.")
    st.stop()


def render_login():
    st.markdown(build_css(login=True), unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        col_logo, col_form = st.columns([1.15, 1], gap="large")

        with col_logo:
            st.markdown(
                f'<div class="login-logo-col">'
                f'<div class="login-logo">{logo_img(320, full=True)}</div>'
                f'<div class="login-sub">Ingresa con tu correo y contraseña<br>de Rappi para ver tu cartera.</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        with col_form:
            st.markdown('<div class="login-form-col">', unsafe_allow_html=True)

            # Selector de rol (agosto 2026): Fabián es supervisor de todo Cono
            # Sur (AR+CL+UY juntos, ver SUPERVISOR_EMAILS), y solo entra como
            # Supervisor -- no necesita tambien ver una cartera individual de
            # Farmer (pedido explicito de Sabas). El resto del equipo solo ve
            # el boton Farmer.
            st.session_state.setdefault("login_role", "farmer")
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("👤 Farmer", use_container_width=True,
                             type="primary" if st.session_state["login_role"] == "farmer" else "secondary"):
                    st.session_state["login_role"] = "farmer"
                    st.rerun()
            with rc2:
                if st.button("🧭 Supervisor", use_container_width=True,
                             type="primary" if st.session_state["login_role"] == "supervisor" else "secondary"):
                    st.session_state["login_role"] = "supervisor"
                    st.rerun()

            role = st.session_state["login_role"]

            if role == "farmer":
                email = st.text_input("Correo", placeholder="nombre.apellido@rappi.com")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••")
                entrar = st.button("Entrar", type="primary", use_container_width=True)

                if entrar:
                    clean = email.strip().lower()
                    if not clean or not password:
                        st.warning("Completa correo y contraseña para continuar.")
                    elif clean not in VALID_EMAILS:
                        st.error("Correo o contraseña incorrectos.")
                    elif not dl.check_password(clean, password):
                        st.error("Correo o contraseña incorrectos.")
                    else:
                        st.session_state["farmer"] = clean
                        st.session_state["role"] = "farmer"
                        st.session_state["view"] = "landing"
                        dl.registrar_login(clean)
                        st.rerun()
            else:
                # Supervisor: un solo correo autorizado (SUPERVISOR_EMAILS), sin
                # selector libre de email -- evita que alguien intente entrar
                # como "supervisor" con otro correo del equipo.
                st.markdown(
                    '<div style="font-size:12.5px;color:rgba(255,255,255,0.65);margin:-4px 0 10px;">'
                    "Acceso de supervisor · todo Cono Sur (AR · CL · UY)</div>",
                    unsafe_allow_html=True,
                )
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="sup_pw")
                entrar_sup = st.button("Entrar como Supervisor", type="primary", use_container_width=True)

                if entrar_sup:
                    sup_email = next(iter(dl.SUPERVISOR_EMAILS))
                    if not password:
                        st.warning("Completa la contraseña para continuar.")
                    elif not dl.check_password(sup_email, password):
                        st.error("Contraseña incorrecta.")
                    else:
                        st.session_state["farmer"] = sup_email
                        st.session_state["role"] = "supervisor"
                        st.session_state["view"] = "landing"
                        dl.registrar_login(sup_email)
                        st.rerun()

            st.markdown(
                f'<div class="login-foot">'
                f"{len(VALID_EMAILS)} Farmers con cartera activa · Datos de julio 2026</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


if "farmer" not in st.session_state:
    render_login()
    st.stop()

st.markdown(build_css(), unsafe_allow_html=True)

selected = st.session_state["farmer"]
st.session_state.setdefault("view", "landing")

# Rol de sesion (agosto 2026): Fabián es el unico supervisor, ve todo Cono
# Sur. Se define acá arriba (antes del sidebar) porque el sidebar ya
# necesita saber si mostrar "Supervisor" o el nombre de un Farmer.
IS_SUPERVISOR = st.session_state.get("role") == "supervisor"

# Moneda nativa del farmer en sesion (default ARS; ver FARMER_PAIS_OVERRIDE
# en data_layer.py -- hoy solo Maria/UY difiere). Sin conversion cruzada:
# cada quien ve su GMV/Ads/Markdown en su propia moneda.
CURRENCY = dl.farmer_moneda(selected)

# ── Telón de carga: se re-engancha en CADA ejecución del script ──
# Arquitectura calcada de Growth OS -- ver el docstring completo de
# render_loading_watcher() más arriba para el diagnóstico detallado de
# por qué el enfoque anterior (bandera en session_state + st.markdown +
# time.sleep + st.rerun manual) no era confiable: Streamlit no da ninguna
# garantía de timing entre "Python terminó de pintar" y "el navegador
# terminó de renderizar" -- el JS de acá abajo resuelve eso escuchando
# los propios indicadores de estado de Streamlit en el DOM real.
render_loading_watcher()

# =========================
# SIDEBAR
# =========================

col_sidebar, col_main = st.columns([1, 5.2], gap="small")

with col_sidebar:
    with st.container(key="wingman-sidebar"):
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:center;'
            f'width:100%;padding:10px 2px 20px 2px;">'
            f'{logo_img(64, full=True)}</div>'
            f'<div class="session-pill">'
            f'<div class="session-avatar">{dl.farmer_initials(selected)}</div>'
            f'<div class="session-text">'
            f'<div class="session-name">{"Supervisor" if IS_SUPERVISOR else dl.farmer_display(selected)}</div>'
            f'<div class="session-role">{"Cono Sur" if IS_SUPERVISOR else "Farmer"}</div>'
            f"</div></div>",
            unsafe_allow_html=True,
        )

        # ── Navegación de 2 secciones: Gestión General / Buscador de Marcas ──
        # Buscador de Marcas es la seccion por defecto (ya la trae
        # st.session_state con setdefault mas abajo). Cambiar de seccion
        # resetea la vista a "landing" dentro de esa seccion (nunca deja a
        # alguien parado en una ficha de marca de otra seccion). Las keys
        # internas (brand_finder / management) NO cambiaron -- solo la
        # etiqueta visible -- para no tener que tocar el resto del código que
        # ya compara contra esas keys.
        st.session_state.setdefault("section", "management")
        NAV_SECTIONS = [
            ("brand_finder", "🔍 Buscador de Marcas"),
            ("management",   "📊 Gestión General"),
            ("trabajables",  "🛠️ Trabajables"),
        ]
        for sec_key, sec_label in NAV_SECTIONS:
            active = st.session_state["section"] == sec_key
            # BUG REAL CORREGIDO (agosto 2026, sexto ajuste): el patrón viejo
            # st.markdown('<div class="...">') + st.button(...) + st.markdown
            # ('</div>') NO envuelve el botón en Streamlit moderno -- cada
            # elemento (markdown, button) crea su propio stElementContainer
            # AISLADO, así que el <div> quedaba vacío y el botón real vivía
            # en un contenedor HERMANO, no adentro. El selector CSS
            # .nav-btn-active button nunca encontraba nada (confirmado
            # inspeccionando el DOM real: el div existía pero sin hijos).
            # Fix: el propio key del botón ya genera una clase CSS estable
            # (.st-key-nav_management / .st-key-nav_brand_finder) que
            # Streamlit aplica al stElementContainer real -- no hace falta
            # ningún div wrapper manual. La clase "active_class" se agrega
            # como marcador extra vía CSS custom (ver theme.py, selector por
            # key exacto) en vez de por wrapper.
            if st.button(sec_label, key=f"nav_{sec_key}", use_container_width=True):
                st.session_state["section"] = sec_key
                st.session_state["view"] = "landing"
                st.rerun()

        # Resaltar el botón de la sección ACTIVA con fondo blanco/texto
        # naranja -- inyectado como CSS dinámico apuntando al key exacto
        # del botón activo (st.session_state["section"] cambia en cada
        # rerun, así que no puede resolverse con CSS estático en
        # theme.py).
        #
        # BUG REAL CORREGIDO: la regla .st-key-wingman-sidebar * (theme.py)
        # fuerza texto blanco a TODO descendiente, sin importar la
        # profundidad -- eso incluye el <p> interno que Streamlit anida
        # dentro del <button> (button > div > span > div > p). Poner el
        # color naranja solo en ".stButton button" no alcanza porque esa
        # regla no aplica al <p> anidado mas adentro; la regla universal
        # seguía ganando ahí y el texto quedaba blanco sobre fondo blanco,
        # invisible. Se agrega el mismo selector "*" acá para cubrir
        # cualquier profundidad de anidación.
        active_key = f"nav_{st.session_state['section']}"
        st.markdown(
            f"""<style>
            .st-key-{active_key} .stButton button,
            .st-key-{active_key} .stButton button * {{
                background: {COLORS["brand_white"]} !important;
                color: {COLORS["brand_orange"]} !important;
                border-color: {COLORS["brand_white"]} !important;
            }}
            </style>""",
            unsafe_allow_html=True,
        )

        # Panel de "avisos de datos" ELIMINADO por pedido explícito: era una
        # ayuda de debugging (útil mientras construíamos, sirvió para detectar
        # el bug real de TOP PRODUCTS en la sesión anterior), pero es
        # información técnica que no debe verse en el uso diario del Farmer.
        # dl.data_issues() sigue existiendo -- si hace falta diagnosticar algo
        # a futuro, se puede volver a mostrar puntualmente sin tocar nada más.

        # Botón Salir SIEMPRE al final del sidebar (logout-anchor + margin-top:auto
        # en el CSS empuja este bloque hasta el fondo, sin importar cuánto
        # contenido haya arriba).
        st.markdown('<div class="logout-anchor">', unsafe_allow_html=True)
        if st.button("Salir", use_container_width=True):
            dl.registrar_logout(st.session_state.get("farmer"))  # antes de borrar el session_state
            for k in ("farmer", "view", "active_brand", "section"):
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

col_main.__enter__()


# Carga PEREZOSA de la cartera (auditoria de rendimiento agosto 2026).
#
# Antes, portfolio / benchmarks / pmap / tpmap se cargaban SIEMPRE, en cada
# rerun de Streamlit, incluso cuando el usuario estaba en Gestión General
# -- que no usa ninguno de los cuatro (esa vista corre sobre
# farmers_por_pais + brand_coverage_for). Para el supervisor era lo peor:
# portfolio_supervisor() concatena la cartera de los 27 farmers (4.98s con
# hojas ya cacheadas, ~43s en frio) para nada.
#
# get_portfolio() se llama solo donde de verdad hace falta: el Buscador de
# Marcas y la ficha de marca. Gestión General ya no lo toca.
def get_portfolio():
    """Cartera del usuario en sesion. Supervisor: TODAS las marcas de los
    27 farmers (puede buscar cualquiera). Farmer: solo la suya."""
    if "_portfolio_cache" not in st.session_state:
        st.session_state["_portfolio_cache"] = (
            dl.portfolio_supervisor() if IS_SUPERVISOR else dl.portfolio_for(selected)
        )
    return st.session_state["_portfolio_cache"]


def go_to_brand(key):
    st.session_state["active_brand"] = key
    st.session_state["view"] = "ficha"
    st.rerun()


def go_to_landing():
    st.session_state["view"] = "landing"
    st.rerun()


def render_brand_coverage_and_contact(farmer_or_list):
    """
    Cards de Brand Coverage · Live (5 donuts) + Contact Performance.
    farmer_or_list: un email (Farmer normal) o una lista de emails (vista
    de Supervisor, agregado por país) -- brand_coverage_for/conversion_for/
    contact_performance_for ya soportan ambos casos (ver data_layer.py).
    Extraída a función para reusar el mismo render en ambas vistas sin
    duplicar el HTML/SVG de los donuts.
    """
    cov = dl.brand_coverage_for(farmer_or_list)
    conv = dl.conversion_for(farmer_or_list)
    cp = dl.contact_performance_for(farmer_or_list)
    adq = dl.adquisicion_ads_for(farmer_or_list)
    ups = dl.upselling_ads_for(farmer_or_list)

    # ── Card 1: Brand Coverage · Live (5 donuts) ──
    # Se sacaron Ads/Markdown/MD PRO "activo o no" (base: marcas de la
    # cartera) -- pedido explícito de Sabas: esa info ya se puede ver
    # en el Home de cada marca, y no aportaba tanto como conversión
    # real. Se agregó Conversión de MD (base: GESTIONES registradas en
    # PRODUCTIVITY ese mes, no marcas de la cartera -- confirmado con
    # Sabas que está bien mezclar bases distintas en la misma card, con
    # el conteo de abajo aclarando cada una).
    #
    # "Conversión Ads" reemplazada por "Adquisición Ads" + "Upselling
    # Ads" (agosto 2026, sexta vuelta -- pedido explícito de Sabas, mismo
    # cambio de criterio ya aplicado a la tabla Rendimiento País/Farmer):
    # ya no es "gestiones que convirtieron sobre gestiones ofrecidas"
    # (PRODUCTIVITY), sino "conversiones reales de CHECKOUT sobre la meta
    # de camino más corto" (adquisicion_ads_for/upselling_ads_for, mismas
    # funciones que alimentan la tabla -- así el donut y la tabla nunca
    # muestran números distintos para el mismo concepto). Con
    # farmer_or_list como LISTA (vista Supervisor por país/equipo), ambas
    # funciones ya suman numerador y denominador de cada farmer
    # automáticamente, mismo patrón que brand_coverage_for/conversion_for.
    #
    # Color por RITMO + emoji dentro del donut (agosto 2026, séptima
    # vuelta, actualizado en la octava): Adquisición Ads, Upselling Ads
    # y Conversión MD son las 3 métricas que se miden en ritmo/pace (ver
    # adquisicion_ads_for/upselling_ads_for/conversion_for) -- para esas
    # 3, el color del anillo y el emoji debajo del % salen de una función
    # de pace, con _RENDIMIENTO_EMOJI para el símbolo. IMPORTANTE (octava
    # vuelta): Adquisición y Upselling YA NO comparten semáforo con
    # Conversión MD -- Adquisición/Upselling usan pace_color_ads_upsell
    # (rojo<80% / azul 81-90% / verde 91-105% / morado >105%, un cuarto
    # nivel que el otro semáforo no tiene), Conversión MD sigue con
    # pace_color (rojo<90% / azul 90-94% / verde>94%), mismo criterio que
    # ya usa Contactos Efectivos y la tabla Rendimiento País/Farmer para
    # esas columnas -- así el color de un farmer o equipo nunca
    # contradice entre el donut y la fila de la tabla para la métrica que
    # corresponda. Nota: md_pct de conversion_for es un % de conversión
    # simple (no está en escala de pace 0-100+ como adq_pct/ups_pct),
    # pero pace_color() solo necesita el número en escala 0-100 para
    # decidir el color, así que se le pasa md_pct*100 igual -- el color
    # resultante es razonable aunque el significado de fondo (tasa vs
    # ritmo) sea distinto, coherente con que la card ya mezcla bases
    # distintas (ver nota más arriba). PW1/Churn NO son ritmo (son % de
    # cartera) -- mantienen su color fijo de warning/danger, sin emoji.
    #
    # PW2 eliminado (agosto 2026, vigésima vuelta -- pedido explícito de
    # Sabas): quedan 5 donuts en vez de 6.
    donut_specs = [
        ("adq_pct",   "Adquisición Ads", None),
        ("ups_pct",   "Upselling Ads",   None),
        ("md_pct",    "Conversión MD",   None),
        ("pw1",       "PW1",            COLORS["warning"]),
        ("churn",     "Churn",          COLORS["danger"]),
    ]

    def _donut_svg(pct, color, size=82, stroke=10):
        import math as _m
        r = (size - stroke) / 2
        circ = 2 * _m.pi * r
        filled = round(circ * pct, 1)
        gap = round(circ - filled, 1)
        cx = cy = size / 2
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{COLORS["card2"]}" stroke-width="{stroke}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-dasharray="{filled} {gap}" stroke-dashoffset="{circ * 0.25}" stroke-linecap="round"/>'
            f"</svg>"
        )

    def _donut_count_text(k):
        # Adquisición/Upselling Ads: base = meta de camino más corto
        # ("18 de 617 necesarias"). Conversión MD: base = gestiones ("39
        # de 130 convirtieron"). PW1/PW2/Churn: base = marcas de la
        # cartera ("125 marcas").
        if k == "adq_pct":
            return f'{adq["adq_n"]} de {adq["adq_target"]} necesarias'
        if k == "ups_pct":
            return f'{ups["ups_n"]} de {ups["ups_target"]} necesarias'
        if k == "md_pct":
            return f'{conv["md_conv"]} de {conv["md_total"]} convirtieron'
        n = cov[f"{k}_n"]
        return f'{n} marca{"s" if n != 1 else ""}'

    def _donut_pct(k):
        if k == "adq_pct":
            return min(adq["adq_pct"] / 100, 1.0)
        if k == "ups_pct":
            return min(ups["ups_pct"] / 100, 1.0)
        return conv[k] if k == "md_pct" else cov[k]

    def _donut_pct_raw(k):
        # Valor de pace SIN topar a 100%, en escala 0-100 -- usado SOLO
        # para decidir el color/emoji, nunca para dibujar el círculo
        # (_donut_pct sí topa a 1.0, porque el SVG no puede rellenar más
        # de una vuelta completa). Usar el valor topado acá sería un bug
        # real: nunca podría alcanzarse "morado >105%" si el número ya
        # viene cortado en 100.
        if k == "adq_pct":
            return adq["adq_pct"]
        if k == "ups_pct":
            return ups["ups_pct"]
        return conv[k] * 100 if k == "md_pct" else cov[k] * 100

    def _donut_color_and_emoji(k, fixed_color):
        # Adquisición/Upselling Ads: semáforo propio de 4 niveles
        # (pace_color_ads_upsell -- rojo<80/azul81-90/verde91-105/
        # morado>105, agosto 2026, octava vuelta, pedido explícito de
        # Sabas). Conversión MD (agosto 2026, vigésima primera vuelta --
        # CORREGIDO, pedido explícito de Sabas: "la donut debe llevar la
        # misma regla de coloración que su columna de la tabla"): antes
        # usaba pace_color (rojo<90/azul90-94/verde>94), una escala
        # pensada para métricas de RITMO -- pero la columna "Conversión
        # MD" de la tabla Rendimiento País/Farmer siempre usó
        # _rend_color_conversion (rojo<10/azul10-20/verde20-30/
        # morado>30, escala calibrada para valores TÍPICAMENTE bajos de
        # conversión de Markdown, muy distinta de una escala de ritmo).
        # Con esas dos escalas distintas, un mismo % podía verse rojo en
        # el donut y verde/morado en la tabla para el mismo farmer --
        # ahora ambas usan _rend_color_conversion, así nunca contradicen
        # entre sí. PW1/Churn: color fijo, sin emoji.
        if k in ("adq_pct", "ups_pct"):
            raw_pct = _donut_pct_raw(k)
            pace_name = dl.pace_color_ads_upsell(raw_pct)
            return _RENDIMIENTO_TEXT_COLOR[pace_name], _RENDIMIENTO_EMOJI.get(pace_name, "")
        if k == "md_pct":
            raw_pct = _donut_pct_raw(k)
            pace_name = _rend_color_conversion(raw_pct)
            return _RENDIMIENTO_TEXT_COLOR[pace_name], _RENDIMIENTO_EMOJI.get(pace_name, "")
        return fixed_color, ""

    donuts_html_parts = []
    for k, label, fixed_color in donut_specs:
        color, emoji = _donut_color_and_emoji(k, fixed_color)
        emoji_html = f'<div class="donut-emoji">{emoji}</div>' if emoji else ""
        donuts_html_parts.append(
            f'<div class="donut-item">'
            f'<div class="donut-wrap">{_donut_svg(_donut_pct(k), color)}'
            f'<div class="donut-pct" style="color:{color};">{_donut_pct(k) * 100:.0f}%{emoji_html}</div></div>'
            f'<div class="donut-label">{label}</div>'
            f'<div class="donut-count">{_donut_count_text(k)}</div>'
            f"</div>"
        )
    donuts_html = "".join(donuts_html_parts)
    st.markdown(
        '<div class="mgmt-card">'
        f'<div class="mgmt-card-title">🎯 Brand Coverage · Live ({cov["total"]} marcas en cartera)</div>'
        f'<div class="donut-grid">{donuts_html}</div>'
        "</div>".format(cov=cov),
        unsafe_allow_html=True,
    )

    # ── Card 2: Contact Performance (desde el 1° del mes) ──
    total_universe = max(cp["total_effective"] + cp["not_contacted"], 1)
    calls_pct = round(cp["calls"] / total_universe * 100)
    chats_pct = round(cp["chats"] / total_universe * 100)
    meets_pct = round(cp["meets"] / total_universe * 100)
    ghost_pct = round(cp["not_contacted"] / total_universe * 100)

    # Antes hardcodeado al 1° del mes calendario actual (siempre decía
    # "Desde 01 Aug" aunque los datos mostrados fueran de julio, por el
    # fallback de mes en contact_performance_for). Ahora usa la fecha
    # real que la data_layer efectivamente usó como corte.
    month_label = cp["period_label"]

    # Efectivos vs Target (pedido explícito de Sabas, agosto 2026): sale de
    # PROD TARGET (target_for), suma automáticamente si farmer_or_list es
    # una lista (vista de Supervisor por país). Sin dato de target
    # disponible (target=0, ej. si PROD TARGET no trae ese mes/farmer
    # todavía) no se muestra la barra -- mejor omitirla que mostrar un 0%
    # o una división por cero engañosa.
    target = dl.target_for(farmer_or_list)
    target_html = ""
    if target > 0:
        # BUG REAL CORREGIDO (agosto 2026): la barra usaba el cumplimiento
        # ACUMULADO crudo (total_effective/target*100) en vez del RITMO
        # que contact_performance_for ya calculaba y devolvía
        # (pace_pct) -- con solo 1-2 días cargados del mes, el acumulado
        # crudo da un % muy chico (ej. 23/4599 = 5%) que parece un
        # desastre, cuando el RITMO real (proyectando esos mismos 2 días
        # a mes completo) puede estar en 79%, mucho mas representativo de
        # cómo va el farmer en realidad. Al sacar la pill "Ritmo X%" en
        # la sesión anterior (porque "ya se ve en la barra"), la barra en
        # sí NUNCA había mostrado el ritmo -- mostraba el acumulado desde
        # el principio, quedó sin corregir por error.
        pace_pct = cp.get("pace_pct")
        pct_mostrado = pace_pct if pace_pct is not None else min(round(cp["total_effective"] / target * 100), 999)
        barra_color = COLORS["success"] if pct_mostrado >= 100 else (
            COLORS["warning"] if pct_mostrado >= 70 else COLORS["danger"]
        )
        target_html = (
            '<div class="cp-target-row">'
            f'<div class="cp-target-label">🎯 Target del mes: '
            f'<b>{cp["total_effective"]:.0f} / {target:.0f}</b> '
            f'<span style="color:{barra_color};font-weight:800;">({pct_mostrado:.0f}% ritmo)</span>'
            f"</div>"
            '<div class="cp-target-bar-track">'
            f'<div class="cp-target-bar-fill" style="width:{min(pct_mostrado, 100)}%;background:{barra_color};"></div>'
            "</div></div>"
        )

    def _cp_seg(pct, color):
        txt = f"{pct}%" if pct >= 7 else ""
        return f'<div class="cp-bar-seg" style="width:{pct}%;background:{color};">{txt}</div>'

    cp_bar_html = (
        '<div class="cp-bar">'
        + _cp_seg(calls_pct, COLORS["brand_purple"])
        + _cp_seg(chats_pct, COLORS["success"])
        + _cp_seg(meets_pct, COLORS["blue"])
        + _cp_seg(ghost_pct, COLORS["danger"])
        + "</div>"
    )
    legend_items = [
        ("📞 Amazon Connect", cp["calls"], calls_pct, COLORS["brand_purple"]),
        ("💬 WhatsApp", cp["chats"], chats_pct, COLORS["success"]),
        ("🖥️ Meet", cp["meets"], meets_pct, COLORS["blue"]),
        ("👻 No Contactado", cp["not_contacted"], ghost_pct, COLORS["danger"]),
    ]
    legend_html = "".join(
        f'<div class="cp-legend-item"><div class="cp-legend-dot" style="background:{color};"></div>'
        f'<span style="color:{color};">{label}</span>'
        f'<span style="color:{COLORS["muted"]};font-weight:600;">{n} · {pct}%</span></div>'
        for label, n, pct, color in legend_items
    )
    st.markdown(
        '<div class="mgmt-card">'
        f'<div class="mgmt-card-title">📞 Contact Performance · desde {month_label}</div>'
        f'<div class="cp-total">{cp["total_effective"]} <span class="cp-total-label">contactos efectivos</span></div>'
        f"{target_html}"
        f"{cp_bar_html}"
        f'<div class="cp-legend">{legend_html}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # "Rendimiento Farmer": misma tabla/pills de Rendimiento País, pero con
    # una sola fila (pedido explícito de Sabas, agosto 2026). Solo cuando
    # farmer_or_list es un email individual -- cuando es el agregado por
    # país (vista de Supervisor), esa vista ya muestra la tabla completa
    # aparte (render_tabla_farmers_supervisor), no hace falta repetirla.
    if isinstance(farmer_or_list, str):
        render_rendimiento_farmer(farmer_or_list)


# =========================================================
# PANTALLA A — ATERRIZAJE
# =========================================================

if st.session_state["view"] == "landing":
    section = st.session_state["section"]
    section_label = {
        "brand_finder": "Buscador de Marcas",
        "trabajables": "Trabajables",
    }.get(section, "Gestión General")
    header_name = "Supervisor" if IS_SUPERVISOR else dl.farmer_display(selected)
    header(header_name, section_label, "")

    # =====================================================
    # SECCIÓN: BRAND FINDER — solo búsqueda por ID
    # =====================================================
    # La tabla de Prioridad de Contacto (con las pills OPS/Menu/Markdown/
    # MD PRO/Ads y el ranking clickeable) se eliminó por pedido explícito:
    # esa función ya vive en Smart Priority. Acá solo queda el buscador,
    # y ahora es por ID (no por nombre), con la misma lógica flexible de
    # Growth OS: brand_key() normaliza "AR97338", "97338", "AR-97338" o
    # cualquier variante con basura alrededor, a la misma clave canónica.
    if section == "brand_finder":
        query = st.text_input(
            "Buscar por ID", placeholder="ID de marca (ej. AR97338 o 97338)…",
            label_visibility="collapsed",
        )
        if query.strip():
            qkey = dl.brand_key(query.strip())
            if qkey:
                _pf = get_portfolio()
                match = _pf[_pf["key"] == qkey]
                if len(match) == 1:
                    go_to_brand(match.iloc[0]["key"])
                else:
                    donde = "en el equipo" if IS_SUPERVISOR else "en tu cartera"
                    st.info(f"No encontré ninguna marca con el ID {qkey} {donde}.")
            else:
                st.info("Escribe un ID válido (ej. AR97338 o simplemente 97338).")

    # =====================================================
    # SECCIÓN: TRABAJABLES (agosto 2026, vigésima segunda vuelta)
    # =====================================================
    elif section == "trabajables":
        if IS_SUPERVISOR:
            # Vista Supervisor: mismo selector de país que Gestión
            # General (reusa supervisor_pais de session_state, así que
            # si el usuario ya eligió un país en Gestión General, se
            # respeta acá también) -- top 10 agregado de TODOS los
            # farmers de ese país, con columna Farmer mostrando el dueño
            # de cada marca (pedido explícito de Sabas).
            st.session_state.setdefault("supervisor_pais", "AR")
            render_conosur_map()
            pais_actual = st.session_state["supervisor_pais"]
            farmers_pais = dl.farmers_por_pais(pais_actual)
            render_trabajables(farmers_pais, is_supervisor=True)
        else:
            render_trabajables(selected, is_supervisor=False)

    # =====================================================
    # SECCIÓN: MANAGEMENT DASHBOARD — Brand Coverage + Contact Performance
    # =====================================================
    else:
        if IS_SUPERVISOR:
            # Vista de Supervisor: mapa del Cono Sur clickeable arriba de
            # todo. Al elegir un país, se recalculan Brand Coverage +
            # Contact Performance con SOLO los farmers de ese país (no de
            # todo el equipo), y debajo aparece la tabla de farmers
            # ordenada por Contactos Efectivos -- pedido explícito de
            # Sabas (agosto 2026).
            st.session_state.setdefault("supervisor_pais", "AR")
            render_conosur_map()

            pais_actual = st.session_state["supervisor_pais"]
            pais_label = next(
                (p["label"] for p in dl.PAISES_CONO_SUR if p["code"] == pais_actual), pais_actual
            )
            st.markdown(
                f'<div style="font-size:13px;font-weight:800;color:{COLORS["brand_purple"]};'
                f'margin:4px 0 14px;text-transform:uppercase;letter-spacing:.04em;">'
                f"📍 {pais_label}</div>",
                unsafe_allow_html=True,
            )

            farmers_pais = dl.farmers_por_pais(pais_actual)
            render_brand_coverage_and_contact(farmers_pais)
            render_tabla_farmers_supervisor(pais_actual)
            render_login_tracker_supervisor()
        else:
            render_brand_coverage_and_contact(selected)

    st.stop()


# =========================================================
# PANTALLA B — FICHA DE MARCA
# =========================================================

active_key = st.session_state.get("active_brand")
portfolio = get_portfolio()
match = portfolio[portfolio["key"] == active_key]
if match.empty:
    go_to_landing()

# Mapas auxiliares: solo se usan en esta pantalla (360 Action, Analytics,
# Campaign Designer), no en el aterrizaje ni en Gestión General -- por eso
# se cargan aca abajo y no a nivel de modulo (auditoria agosto 2026).
benchmarks = dl.category_benchmarks()
pmap = dl.priority_map()
tpmap = dl.top_products_map(limit=3)
row = match.iloc[0]

# Para el supervisor, la moneda de la ficha depende de a QUÉ farmer
# pertenece la marca que está viendo (portfolio_supervisor trae la columna
# farmer_moneda por fila) -- no la moneda default de Fabián (ARS), que no
# tiene sentido si está mirando una marca de Chile o Uruguay. Para un
# Farmer normal, CURRENCY ya viene bien definida arriba (todas sus marcas
# son de un solo país).
if IS_SUPERVISOR and "farmer_moneda" in row.index:
    CURRENCY = row.farmer_moneda

# Header naranja SIEMPRE visible, también en la ficha de marca -- se había
# perdido en la sesión anterior al reemplazar el botón "Volver" por la
# barra de búsqueda de acá abajo. Muestra el nombre de la marca activa
# como "sección" (en vez de "Buscador de Marcas"/"Gestión General"), para
# que el Farmer sepa en qué ficha está parado. Para el supervisor, el
# encabezado usa "Supervisor" en vez del nombre de un Farmer individual.
header_name = "Supervisor" if IS_SUPERVISOR else dl.farmer_display(selected)
header(header_name, row.brand_name, "")

# ── Barra de búsqueda SIEMPRE visible arriba de la ficha (reemplaza el botón
# "Volver a la cartera") -- pedido explícito de Sabas: el Farmer no debe
# tener que volver atrás para saltar de una marca a otra, solo pega el
# siguiente ID acá mismo y salta directo. Misma lógica flexible que
# Buscador de Marcas (brand_key() normaliza "AR97338", "97338", basura
# alrededor, etc).
ficha_query = st.text_input(
    "Buscar otra marca", placeholder="Otro ID de marca (ej. AR97338 o 97338)…",
    label_visibility="collapsed", key="ficha_search",
)
if ficha_query.strip():
    fqkey = dl.brand_key(ficha_query.strip())
    if fqkey and fqkey != active_key:
        fmatch = portfolio[portfolio["key"] == fqkey]
        if len(fmatch) == 1:
            go_to_brand(fmatch.iloc[0]["key"])
        else:
            donde = "en el equipo" if IS_SUPERVISOR else "en tu cartera"
            st.info(f"No encontré ninguna marca con el ID {fqkey} {donde}.")
    elif not fqkey:
        st.info("Escribe un ID válido (ej. AR97338 o simplemente 97338).")

# ── Franja fija: Nombre, ID, Contacto (texto plano estilo Growth OS) + Pills (Churn/Ranking) ──
search_url = dl.google_search_url(row.brand_name, row.categoria, row.ciudad)
tel_btn_id, telefono_copy = (_copy_button_html(row.telefono) if row.telefono else (None, ""))
mail_btn_id, mail_copy = (_copy_button_html(row.mail) if row.mail else (None, ""))
contact_html = (
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:14px;">'
    f'<div><div class="stat-label">TELÉFONO</div><div class="stat-value">{row.telefono or "?"}{telefono_copy}</div></div>'
    f'<div><div class="stat-label">CORREO</div><div class="stat-value" style="font-size:13px;">{row.mail or "?"}{mail_copy}</div></div>'
    f'<div><div class="stat-label">CATEGORÍA</div><div class="stat-value">{row.categoria or "?"}</div></div>'
    f'<div><div class="stat-label">LOCAL</div><div class="stat-value">'
    f'<a href="{search_url}" target="_blank" rel="noopener noreferrer" '
    f'style="color:{COLORS["brand_purple"]};text-decoration:none;font-weight:700;">🔎 Buscar</a>'
    "</div></div>"
    "</div>"
)

# Pills reales: Churn Status (con color segun severidad). Ranking por GMV
# se quitó -- pedido explícito de Sabas (agosto 2026).
churn_class = {
    "Disponible": "ok", "PW1": "warn", "PW2": "warn", "PW3": "alert", "Churn": "alert",
}.get(row.churn_status, "info")
churn_icon = "✅" if row.churn_status == "Disponible" else "⚠️"

status_pills_html = (
    '<div class="pill-row">'
    f'<span class="ctx-pill {churn_class}">{churn_icon} Estado de Churn: {row.churn_status}</span>'
    "</div>"
)

st.markdown(
    f'<div class="brand-sticky">'
    f'<div class="brand-title">{row.brand_name}</div>'
    f'<div class="brand-id">{row.brand_id}</div>'
    f"{status_pills_html}"
    f"{contact_html}"
    f"</div>",
    unsafe_allow_html=True,
)
if tel_btn_id:
    _render_copy_script(row.telefono, tel_btn_id)
if mail_btn_id:
    _render_copy_script(row.mail, mail_btn_id)

tab_home, tab_action, tab_analytics, tab_campaign, tab_outreach = st.tabs(
    ["🏠 Home", "🎯 360° Action", "📊 Analytics", "🚀 Campaign Designer", "📧 Outreach"]
)


# ── TAB: HOME ──
with tab_home:
    if row.gmv > 0:
        g1, g2 = st.columns(2)
        with g1:
            ordenes_sub = f'📦 {row.ordenes:,.0f} órdenes'.replace(",", ".")
            st.markdown(
                metric_trend_card("📈", "GMV (mes)", row.gmv, row.gmv_delta,
                                   ordenes_sub, prev_ars=row.gmv_last, currency=CURRENCY, es_ritmo=True),
                unsafe_allow_html=True,
            )
        with g2:
            st.markdown(
                metric_trend_card("🛒", "AOV", row.aov, row.aov_delta,
                                   "Ticket promedio", prev_ars=row.aov_last, currency=CURRENCY),
                unsafe_allow_html=True,
            )
    else:
        st.caption("Sin datos de GMV/AOV para esta marca en el período.")

    st.markdown('<div class="section-title">PALANCAS</div>', unsafe_allow_html=True)

    ads_txt, _ = state_text(row.bookings > 0)
    ads_copy = (
        f"Booking {dl.fmt_money(row.bookings, CURRENCY)} · Revenue {dl.fmt_money(row.revenue, CURRENCY)}"
        if row.bookings > 0 else "Sin pauta activa este mes"
    )
    ads_chip = f"{dl.fmt_roi(row.roas)}" if row.roas > 0 else ""
    ads_badge = None
    # Att% de la card de Palancas (agosto 2026, decimonovena vuelta --
    # pedido explícito de Sabas): antes comparaba el Att% acumulado de
    # la marca contra un umbral fijo (90%), sin tener en cuenta el punto
    # del mes -- mismo problema ya resuelto en Objetivo Ads Revenue de
    # la tabla. Ahora se compara contra el Att% ESPERADO hoy según
    # calendario (att_esperado_hoy_pct, mismo cálculo que ya usa
    # ads_kam_for para el agregado del farmer, aplicado aquí a una marca
    # puntual). Tres estados (no dos):
    #   - RITMO BAJO (rojo): Att real < Att esperado -- va atrasado.
    #   - RITMO SANO (verde): Att esperado <= Att real <= 2x Att esperado.
    #   - RITMO ACELERADO CON RIESGO (amarillo): Att real > 2x Att
    #     esperado -- pedido explícito de Sabas: un ritmo MUY por encima
    #     de lo esperado tampoco es necesariamente bueno (podría ser
    #     sobre-gasto o un dato atípico), así que se marca como
    #     advertencia en vez de premiarlo como "sano" sin más.
    # El signo (> o <) en el texto compara real vs esperado
    # automáticamente, no está hardcodeado.
    if row.bookings > 0 and row.att_revenue > 0:
        att_real = row.att_revenue * 100
        firma_email_ads = row.farmer_owner if (IS_SUPERVISOR and "farmer_owner" in row.index) else selected
        att_esperado = dl.att_esperado_hoy_pct(firma_email_ads)
        if att_esperado is not None and att_esperado > 0:
            signo = ">" if att_real >= att_esperado else "<"
            if att_real < att_esperado:
                estado, att_color = "Ritmo bajo", COLORS["danger"]
            elif att_real > att_esperado * 2:
                estado, att_color = "Ritmo acelerado con riesgo", COLORS["warning"]
            else:
                estado, att_color = "Ritmo sano", COLORS["success"]
            ads_badge = (
                f"{estado} Att {att_real:.0f}% {signo} {att_esperado:.0f}%",
                att_color,
            )
        else:
            # Sin PRODUCTIVITY para calcular el esperado (mes cerrado o
            # sin gestiones) -- cae al criterio viejo de umbral fijo,
            # mismo fallback que ads_kam_for usa para revenue_pace_pct.
            att_color = COLORS["success"] if row.att_revenue >= 0.90 else COLORS["danger"]
            ads_badge = (f"Att {att_real:.0f}%", att_color)

    md_txt, _ = state_text(row.markdown_md > 0)
    md_camp = row.campaign_md if row.campaign_md and row.campaign_md != "-" else ""
    md_copy = f"Campaign {md_camp or '-'}" if row.markdown_md > 0 else "Campaign —"
    md_badge = None
    if row.markdown_md > 0:
        pen_color = COLORS["success"] if row.penetracion_md >= 0.10 else COLORS["danger"]
        md_badge = (f"Penetración {row.penetracion_md * 100:.1f}%", pen_color)

    pro_txt, _ = state_text(row.markdown_mdpro > 0)
    pro_camp = row.campaign_mdpro if row.campaign_mdpro and row.campaign_mdpro != "-" else ""
    pro_copy = f"Campaign {pro_camp or '-'}" if row.markdown_mdpro > 0 else "Campaign —"
    pro_badge = None
    if row.markdown_mdpro > 0:
        pen_color = COLORS["success"] if row.penetracion_mdpro >= 0.10 else COLORS["danger"]
        pro_badge = (f"Penetración {row.penetracion_mdpro * 100:.1f}%", pen_color)

    st.markdown(
        '<div class="business-card-grid">'
        + mini_card("ADS", ads_txt, ads_copy,
                    "ads", ads_chip, COLORS["accent"], corner_badge=ads_badge)
        + mini_card("MARKDOWN", md_txt, md_copy, "md",
                    dl.fmt_roi(row.roi_md) if row.roi_md > 0 else "", COLORS["blue"], corner_badge=md_badge)
        + mini_card("MARKDOWN PRO", pro_txt, pro_copy, "pro",
                    dl.fmt_roi(row.roi_mdpro) if row.roi_mdpro > 0 else "", COLORS["success"], corner_badge=pro_badge)
        + "</div>",
        unsafe_allow_html=True,
    )


# ── TAB: 360° ACTION ──
with tab_action:
    # ── Card de contexto (gris, arriba): Coinversión + pills de palanca ──
    # Teléfono sacado: ya está en la ficha de marca de arriba, no hace falta
    # repetirlo acá. "# Contacto" (orden de marcado), "Último Contacto" y
    # "Vencida/Por vencer" siguen sin fuente propia en Wingman -- existen en
    # PRIORITY DATA pero, por pedido explícito de Sabas (agosto 2026), no
    # se incorporan a esta card.
    #
    # coinv_md_label (no row.coinversion): row.coinversion es el texto crudo
    # de ASIGNACION ("5. Prioritized"), que mostraba el grupo SIN chequear
    # si la marca realmente tiene coinversión de Markdown activa -- bug real
    # detectado por Sabas viendo ¡hey Pizza! marcado "5. Prioritized" en
    # Growth OS cuando su Coinversion MD real es blanco/No. La lógica
    # correcta sale de PRIORITY DATA (ver load_coinversion_md): "No" si
    # Coinversion MD != "SI" exacto; si es "SI", ahí sí se muestra el grupo
    # real (Prioritized/Rest/Churn Prevention/etc.) leído de STATUS Brand.
    #
    # BUG REAL CORREGIDO (agosto 2026, decimoséptima vuelta): el [:4] de
    # acá cortaba silenciosamente las pills de palanca a un máximo de 4,
    # aunque PRIORITY DATA trajera más métricas para esa marca (hasta 9
    # en el export actual) -- pedido explícito de Sabas: "las palancas
    # que deben mencionarse ahí deben ser TODAS las que mencione [la
    # marca] en priority data, sea 1 palanca o sean 20". El [:4] SÍ sigue
    # existiendo (y debe seguir así) en las 4 CARDS TÁCTICAS de abajo
    # (OPS/Menú/Markdown/Ads, ver ops_tactical_card/menu_tactical_card/
    # md_tactical_card/ads_tactical_card) -- esas 4 son categorías fijas
    # de negocio, no un listado de PRIORITY DATA, así que no aplica el
    # mismo cambio ahí. Esta pill_list (pmap.get(row.key, [])) es un
    # concepto DISTINTO: el listado completo y sin recortar de todas las
    # métricas con prioridad para esta marca puntual.
    lever_pills = "".join(
        f'<span class="action-lever-pill">{lb} · {v:.2f}</span>'
        for lb, v in pmap.get(row.key, [])
    )
    st.markdown(
        f'<div class="action-context-card">'
        f'<div class="action-context-grid" style="grid-template-columns:1fr;">'
        f'<div><div class="action-mini-label">Coinversión MD</div>'
        f'<div class="action-mini-value">{row.coinv_md_label}</div></div>'
        f"</div>"
        f"{lever_pills}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Super-card: OPS · Menú · Markdown · Ads ──
    # md_tactical_card y ads_tactical_card ya resuelven solas la Descripción
    # real de Priority Data (Adquisición/Optimización/Upselling) -- no hace
    # falta chequear has_md_signal/has_ads_signal acá, quedó todo adentro
    # de data_layer.py para no duplicar lógica de negocio en la UI.
    ops = dl.ops_tactical_card(row.key, row.availability, row.lost_hours, row.gmv, row.aov, row.ordenes)
    menu = dl.menu_tactical_card(row.key, row.perfect_store_pct, row.menu_photos, row.menu_purchase, row.menu_missing)
    md_c = dl.md_tactical_card(row.key, row.markdown_md > 0, row.roi_md, row.campaign_md)
    ads_c = dl.ads_tactical_card(row.key, row.bookings > 0, row.roas, row.bookings, CURRENCY)

    def _tag_color(tag):
        return {
            "HEALTHY": COLORS["success"], "WATCH": COLORS["warning"],
            "ALERT": COLORS["danger"], "INACTIVE": COLORS["muted"],
        }[tag]

    def _tag_bg(tag):
        # Fondo pastel de la card completa segun estado -- pedido
        # explícito de Sabas (agosto 2026): antes las 4 cards eran
        # siempre grises, ahora toman el color del estado (mismo estilo
        # suave que ya usamos en Rendimiento País).
        return {
            "HEALTHY": COLORS["success_soft"], "WATCH": COLORS["warning_soft"],
            "ALERT": COLORS["danger_soft"], "INACTIVE": COLORS["card2"],
        }[tag]

    def _action_mini(icon, name, pct, tag, title, detail, items=None):
        color = _tag_color(tag)
        bg = _tag_bg(tag)
        pct_html = f'<div class="action-card-pct" style="color:{color};">{pct:.0f}%</div>' if pct is not None else ""
        tag_class = {
            "HEALTHY": "tag-healthy", "WATCH": "tag-watch",
            "ALERT": "tag-alert", "INACTIVE": "tag-inactive",
        }[tag]
        # Si hay "items" (lista de bullets de OPS/Menú), se renderiza uno
        # por línea (un <div> por ítem) en vez del párrafo corrido de
        # "detail" -- pedido explícito de Sabas (agosto 2026): las 4
        # señales de OPS/Menú deben verse una debajo de la otra, no
        # unidas con " · " en un solo bloque de texto.
        if items:
            cuerpo_html = "".join(
                f'<div class="action-card-item">{item}</div>' for item in items
            )
        else:
            cuerpo_html = f'<div class="action-card-title">{title}</div><div class="action-card-detail">{detail}</div>'
        return (
            f'<div class="action-card" style="background:{bg};">'
            f'<div class="action-card-head">{icon}</div>'
            f"{pct_html}"
            f'<div class="action-card-name">{name}</div>'
            f'<span class="gauge-tag {tag_class}">{tag}</span>'
            f"{cuerpo_html}"
            f"</div>"
        )

    st.markdown(
        '<div class="action-supercard"><div class="action-grid">'
        + _action_mini("⚙️", "OPS General", ops["pct"], ops["tag"], ops["title"], ops["detail"], items=ops.get("items"))
        + _action_mini("🍔", "Menú", menu["pct"], menu["tag"], menu["title"], menu["detail"], items=menu.get("items"))
        + _action_mini("🏷️", "Markdown", None, md_c["tag"], md_c["title"], md_c["detail"])
        + _action_mini("🚀", "Ads", None, ads_c["tag"], ads_c["title"], ads_c["detail"])
        + "</div></div>",
        unsafe_allow_html=True,
    )


# ── TAB: ANALYTICS ──
with tab_analytics:
    bench_cvr, bench_traffic = benchmarks.get(row.categoria, (0, 0))
    diag = dl.funnel_diagnosis(row.cvr, row.traffic, row.aov, row.gmv, bench_cvr, bench_traffic, row.ordenes)

    # ── Funnel SVG: 3 niveles (Traffic benchmark / Traffic marca / Conversión) ──
    # Ajuste de color/mensaje por baldosa (agosto 2026, séptima vuelta,
    # pedido explícito de Sabas):
    #  - Baldosa 1 (Tráfico benchmark categoría): naranja -> MORADO fijo
    #    (color de marca, ver COLORS["brand_purple"]) -- es la referencia
    #    del benchmark, no un resultado que pueda estar bien o mal, así
    #    que no necesita semáforo, solo un color distintivo de las otras
    #    dos.
    #  - Baldosa 2 (Tráfico de la marca): antes SIEMPRE azul fijo, sin
    #    reflejar el resultado real (mismo problema que tenía antes la
    #    baldosa de Conversión) -- ahora ROJO + "Tráfico bajo" si el
    #    tráfico real está por debajo del benchmark de categoría, VERDE +
    #    "Tráfico sano" si está en o por encima (ver
    #    traffic_above_bench en funnel_diagnosis, data_layer.py).
    #  - Baldosa 3 (Conversión de la marca): se mantenía gris + "CR baja"
    #    cuando está por debajo del benchmark (sin cambio); cuando está en
    #    o por encima, pasa de VERDE a AZUL, y el texto de "CR sana" pasa
    #    a "CR% sana" (y "CR baja" -> "CR% baja") para diferenciarla
    #    visualmente de la baldosa 2 (que ahora sí usa verde) y dejar el
    #    verde como color exclusivo de "tráfico sano".
    cvr_ok_real = diag.get("cvr_above_bench", False)
    conv_color = COLORS["blue"] if cvr_ok_real else COLORS["muted"]
    conv_texto_baldosa = "CR% sana" if cvr_ok_real else "CR% baja"
    conv_label_color = COLORS["text"] if cvr_ok_real else COLORS["danger"]

    traffic_ok_real = diag.get("traffic_above_bench", False)
    traffic_color = COLORS["success"] if traffic_ok_real else COLORS["danger"]
    traffic_texto_baldosa = "Tráfico sano" if traffic_ok_real else "Tráfico bajo"

    levels = [
        ("Tráfico benchmark categoría", diag["bench_traffic_disp"] + "/sem", COLORS["brand_purple"], 100, None),
        ("Tráfico de la marca", diag["traffic_disp"] + "/sem", traffic_color, 68, traffic_texto_baldosa),
        ("Conversión de la marca", diag["cvr_disp"], conv_color, 40, conv_texto_baldosa),
    ]
    funnel_svg_parts = ['<svg viewBox="0 0 320 130" width="100%" height="130" style="max-width:280px;">']
    y = 4
    level_h = 34
    for i, (label, val, color, width_pct, texto_interno) in enumerate(levels):
        w = 280 * (width_pct / 100)
        x = (280 - w) / 2 + 20
        next_w = 280 * (levels[i + 1][3] / 100) if i + 1 < len(levels) else w * 0.7
        next_x = (280 - next_w) / 2 + 20
        funnel_svg_parts.append(
            f'<polygon points="{x:.0f},{y} {x + w:.0f},{y} {next_x + next_w:.0f},{y + level_h} '
            f'{next_x:.0f},{y + level_h}" fill="{color}" opacity="0.9"/>'
        )
        if texto_interno:
            cx = 20 + 280 / 2
            cy = y + level_h / 2 + 4
            funnel_svg_parts.append(
                f'<text x="{cx:.0f}" y="{cy:.0f}" text-anchor="middle" '
                f'font-size="11" font-weight="700" fill="white">{texto_interno}</text>'
            )
        y += level_h
    funnel_svg_parts.append("</svg>")
    funnel_svg = "".join(funnel_svg_parts)

    funnel_legend = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{color};display:inline-block;"></span>'
        f'<span style="font-size:10.5px;color:{conv_label_color if label == "Conversión de la marca" else COLORS["muted"]};">'
        f'{label}: <b style="color:{conv_label_color if label == "Conversión de la marca" else COLORS["text"]};">{val}</b></span>'
        f"</div>"
        for label, val, color, _, _ in levels
    )

    # ── Dato Ancla + Benchmark: se calculan por GMV, no por AOV (mismo criterio
    # que Growth OS: percentil = cuantas marcas de la cartera tienen menos GMV;
    # benchmark = la marca con mayor GMV de la categoria). ──
    ancla_html = ""
    if row.gmv > 0 and row.categoria:
        cat_brands = portfolio[portfolio["categoria"] == row.categoria]
        cat_brands = cat_brands[cat_brands["gmv"] > 0]
        if len(cat_brands) > 1:
            percentil = (cat_brands["gmv"] < row.gmv).mean() * 100
            leader = cat_brands.loc[cat_brands["gmv"].idxmax()]

            if percentil >= 75:
                ancla_texto = f"Estás en el percentil {percentil:.0f}% de {row.categoria}. Ya sos de las marcas que más venden en tu categoría."
                ancla_color = COLORS["success"]
            elif percentil >= 50:
                ancla_texto = f"Estás en el percentil {percentil:.0f}% de {row.categoria}. Estás por encima de la mitad — hay espacio real para subir."
                ancla_color = COLORS["brand_orange"]
            else:
                ancla_texto = f"Estás en el percentil {percentil:.0f}% de {row.categoria}. Hay marcas similares vendiendo mucho más con la palanca correcta."
                ancla_color = COLORS["brand_orange"]

            ancla_html = (
                '<div class="analytics-mini-grid">'
                + f'<div class="glass-card"><div class="card-label">DATO ANCLA</div>'
                  f'<div class="card-value" style="color:{ancla_color};">Percentil {percentil:.0f}%</div>'
                  f'<div class="card-copy">{ancla_texto}</div></div>'
                + f'<div class="glass-card"><div class="card-label">BENCHMARK</div>'
                  f'<div class="card-value" style="color:{COLORS["brand_orange"]};">{dl.fmt_money(leader["gmv"], CURRENCY)}</div>'
                  f'<div class="card-copy">El líder de {row.categoria} es {leader["brand_name"]} con '
                  f'{dl.fmt_money(leader["gmv"], CURRENCY)}. Ese es el benchmark real.</div></div>'
                + "</div>"
            )
        else:
            ancla_html = '<div class="card-copy">No hay suficientes marcas de tu cartera en esta categoría para comparar.</div>'
    else:
        ancla_html = '<div class="card-copy">Sin GMV/categoría para calcular Dato Ancla y Benchmark.</div>'

    st.markdown(
        f'<div class="analytics-supercard">'
        f'<div class="funnel-card">'
        f'<div class="funnel-label">🔍 Funnel Tráfico &amp; Conversión vs Benchmark</div>'
        f'<div class="funnel-headline" style="color:{diag["color"]};">{diag["headline"]}</div>'
        f'<div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">'
        f'<div>{funnel_svg}</div><div>{funnel_legend}</div>'
        f"</div>"
        f'<div class="funnel-texto">{diag["texto"]}</div>'
        f"</div>"
        f"{ancla_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── TAB: CAMPAIGN DESIGNER ──
with tab_campaign:
    # ── ADS PLAN (agosto 2026, septimo ajuste -- reescrito por completo,
    #    pedido explicito de Sabas). Ya no hay distincion Adquisicion/
    #    Upselling: siempre se muestra el presupuesto recomendado completo.
    #    dias_transcurridos_mes_actual() es la misma logica ya validada
    #    que usa gmv_delta en Home, extraida como funcion reutilizable. ──
    plan = dl.ads_plan(row.gmv_last, row.gmv, dl.dias_transcurridos_mes_actual(), row.cvr, row.aov)

    if row.gmv_last <= 0:
        ads_card_html = (
            '<div class="campaign-card lever-ads">'
            '<div class="card-label">📣 Ads Plan</div>'
            '<div class="campaign-sub" style="margin-top:8px;">Sin GMV del mes anterior para calcular el modelo.</div>'
            "</div>"
        )
    else:
        pct_label = f'{plan["pct"] * 100:.0f}%'
        minis = (
            f'<div class="glass-card"><div class="card-label">ROAS 1 SEMANA</div>'
            f'<div class="card-value">{plan["roas_1sem"]:.2f}x</div></div>'
            f'<div class="glass-card"><div class="card-label">ROAS 4 SEMANAS</div>'
            f'<div class="card-value">{plan["roas_4sem"]:.2f}x</div></div>'
            f'<div class="glass-card"><div class="card-label">VENTA INCREMENTAL · 1 SEM</div>'
            f'<div class="card-value">{dl.fmt_money(plan["gmv_inc_1sem"], CURRENCY)}</div>'
            f'<div class="card-copy">{plan["pedidos_inc_1sem"]:,.0f} pedidos</div></div>'.replace(",", ".")
            + f'<div class="glass-card"><div class="card-label">VENTA INCREMENTAL · 4 SEM</div>'
            f'<div class="card-value">{dl.fmt_money(plan["gmv_inc_4sem"], CURRENCY)}</div>'
            f'<div class="card-copy">{plan["pedidos_inc_4sem"]:,.0f} pedidos</div></div>'.replace(",", ".")
        )
        ads_card_html = (
            '<div class="campaign-card lever-ads">'
            '<div class="card-label">📣 Ads Plan</div>'
            f'<div class="campaign-headline">{dl.fmt_money(plan["presupuesto_semana1"], CURRENCY)}<span style="font-size:14px;font-weight:600;"> /semana</span></div>'
            f'<div class="campaign-sub">Inversión recomendada: el {pct_label} del GMV de la última semana '
            f'({dl.fmt_money(plan["gmv_semana"], CURRENCY)})</div>'
            f'<div class="analytics-mini-grid" style="margin-top:14px;">{minis}</div>'
            "</div>"
        )

    # ── MARKDOWN PLAN · coinversión primero (si aplica) + descuento por tramo de CVR + Top 3 productos ──
    md = dl.markdown_plan_by_cvr(row.cvr)
    coinv_plan = dl.coinversion_markdown_plan(row.cvr, row.coinv_group_key)

    ladder_html = "".join(
        f'<span class="md-ladder-pill{" active" if pct == md["discount"] else ""}">{pct}%</span>'
        for pct in (20, 25, 30)
    )
    tops = tpmap.get(row.key, [])
    medals = ["🥇", "🥈", "🥉"]
    if tops:
        tops_html = "".join(
            f'<div class="top3-row"><span style="font-size:16px;">{medals[i]}</span>'
            f'<span class="pf-name">{p}</span>'
            f'<span class="pf-meta">VPD {v:,.0f} · CVR {c * 100:.1f}%</span></div>'.replace(",", ".")
            for i, (p, v, c) in enumerate(tops)
        )
    else:
        tops_html = '<div class="card-copy">Sin productos rankeados para esta marca.</div>'

    if coinv_plan:
        # Con coinversión: la campaña principal es 30% + PRO, con el desglose
        # del ratio Aliado:Rappi sobre el descuento total combinado. La regla
        # por defecto (15/20/25 según CVR) queda como pill debajo, no como
        # recomendación principal -- pedido explicito de Sabas.
        coinv_html = (
            '<div class="coinv-block">'
            f'<span class="coinv-badge">{coinv_plan["grupo_icon"]} Coinversión activa · {coinv_plan["grupo_label"]} · ratio {coinv_plan["ratio"]}</span>'
            f'<div class="campaign-headline" style="font-size:26px;margin-top:8px;">'
            f'{coinv_plan["discount"]}% OFF <span style="font-size:15px;color:{COLORS["success"]};">+ {coinv_plan["pro_extra"]}% PRO</span></div>'
            f'<div class="coinv-split">'
            f'<div class="coinv-split-item"><div class="coinv-split-label">Pone el aliado</div>'
            f'<div class="coinv-split-value">{coinv_plan["pct_aliado"]:.1f}%</div></div>'
            f'<div class="coinv-split-item"><div class="coinv-split-label">Pone Rappi</div>'
            f'<div class="coinv-split-value" style="color:{COLORS["blue"]};">{coinv_plan["pct_rappi"]:.1f}%</div></div>'
            f"</div></div>"
        )
        default_pill_html = (
            '<div class="default-plan-pill">'
            f'Sin coinversión, la recomendación por defecto sería: '
            f'<b>{md["discount"]}% OFF + {md["pro_extra"]}% PRO</b> ({md["tramo"]}, CVR {row.cvr * 100:.1f}%).'
            "</div>"
        )
        md_card_html = (
            '<div class="campaign-card lever-md">'
            '<div class="card-label">🏷️ Markdown Plan</div>'
            f'<div style="margin-top:10px;">{coinv_html}</div>'
            f"{default_pill_html}"
            '<div class="section-title" style="margin:14px 0 8px 0;">TOP 3 PRODUCTOS</div>'
            f"{tops_html}"
            "</div>"
        )
    else:
        md_card_html = (
            '<div class="campaign-card lever-md">'
            '<div class="card-label">🏷️ Markdown Plan</div>'
            f'<div class="campaign-headline" style="font-size:26px;">'
            f'{md["discount"]}% OFF <span style="font-size:15px;color:{COLORS["success"]};">+ {md["pro_extra"]}% PRO</span></div>'
            f'<div class="md-ladder">{ladder_html}</div>'
            f'<div class="campaign-sub">{md["tramo"]} (CVR {row.cvr * 100:.1f}%)</div>'
            '<div class="section-title" style="margin:14px 0 8px 0;">TOP 3 PRODUCTOS</div>'
            f"{tops_html}"
            "</div>"
        )

    st.markdown(
        f'<div class="campaign-grid">{ads_card_html}{md_card_html}</div>',
        unsafe_allow_html=True,
    )


# ── TAB: OUTREACH ──
with tab_outreach:
    # El email/WhatsApp debe firmarlo el Farmer REAL dueño de esta marca
    # (row.farmer_owner, columna que solo existe en portfolio_supervisor),
    # no el supervisor logueado -- el aliado espera que le hable su Farmer
    # asignado, no Fabián. Para un Farmer normal, selected YA es el dueño.
    firma_email = row.farmer_owner if (IS_SUPERVISOR and "farmer_owner" in row.index) else selected
    farmer_name = dl.farmer_display(firma_email)
    hallazgos = dl.outreach_hallazgos(
        row.key, row.availability, row.perfect_store_pct, row.menu_photos, row.menu_purchase,
        row.markdown_md > 0, row.bookings > 0,
    )

    if hallazgos:
        items_num = "\n".join(f"{i+1}) {h.capitalize()}" for i, h in enumerate(hallazgos))
        items_inline = "; ".join(f"{i+1}) {h}" for i, h in enumerate(hallazgos))
        frente_intro = f"hoy tenemos {len(hallazgos)} frente{'s' if len(hallazgos) > 1 else ''} que conviene mover ya"
        cierre = "Cada día que pasa sin resolverlo es visibilidad y pedidos que la marca cede frente a su categoría."
        wa_cierre = "Son definiciones rápidas y cada día que pasa nos cuesta pedidos."
    else:
        # Sin hallazgos negativos: seguimiento simple. Si ya tiene campañas
        # activas, el enfoque es sostener; si no tiene ninguna, es adquisición.
        tiene_campanas = row.markdown_md > 0 or row.bookings > 0
        items_num = (
            "1) Seguimiento de tu marca — mantener el buen desempeño de las campañas activas"
            if tiene_campanas else
            "1) Seguimiento de tu marca — ver cómo podemos activar adquisición (Ads/Markdown)"
        )
        items_inline = items_num.split(") ", 1)[1]
        frente_intro = "quiero hacer seguimiento de cómo viene la marca"
        cierre = "La idea es no perder el buen ritmo y seguir sumando oportunidades."
        wa_cierre = "Quiero ver si hay algo puntual para ajustar o seguimos sumando."

    email_body = (
        f"Hola Equipo de {row.brand_name},\n\n"
        f"Hablas con {farmer_name}, especialista en crecimiento de marcas digitales en Rappi. "
        f"Te escribo porque {frente_intro}:\n\n"
        f"{items_num}\n\n"
        f"{cierre}\n\n"
        f"¿Prefieres que te llame hoy mismo o seguimos por WhatsApp? Quedo atento.\n\n"
        f"{farmer_name}\nRappi Farmer"
    )
    whatsapp_body = (
        f"Hola Equipo de {row.brand_name},\n\n"
        f"Hablas con {farmer_name} de Rappi. Hoy quiero resolver contigo: {items_inline}. "
        f"{wa_cierre} "
        f"¿Tienes 10 minutos ahora para cerrarlo?"
    )

    oc1, oc2 = st.columns(2)
    with oc1:
        email_btn_id, email_copy_btn = _copy_button_html(email_body, label="📋 Copiar", tamano="grande")
        st.markdown(
            f'<div class="glass-card"><div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div class="card-label">📧 EMAIL</div>{email_copy_btn}</div>'
            f'<div style="margin-top:10px;font-size:12.5px;white-space:pre-wrap;line-height:1.6;">{email_body}</div></div>',
            unsafe_allow_html=True,
        )
        _render_copy_script(email_body, email_btn_id, label_original="📋 Copiar")
    with oc2:
        st.markdown(
            f'<div class="glass-card"><div class="card-label">💬 WHATSAPP</div>'
            f'<div style="margin-top:10px;font-size:12.5px;white-space:pre-wrap;line-height:1.6;">{whatsapp_body}</div></div>',
            unsafe_allow_html=True,
        )

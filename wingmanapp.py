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
import re
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components

import data_layer as dl
from theme import (
    COLORS,
    ICON_ADS_LEVER,
    ICON_ADS_PLAN,
    ICON_AOV,
    ICON_BILLETE,
    ICON_BULLET_CHECK,
    ICON_BULLET_EYE,
    ICON_BULLET_WARNING,
    ICON_CARRITO_MD,
    ICON_CHAT,
    ICON_CLIPBOARD,
    ICON_COINV_CHURN,
    ICON_COINV_CHURN_PREVENTION,
    ICON_COINV_NEW_HUNTERS,
    ICON_COINV_NEW_REST,
    ICON_COINV_PRIORITIZED,
    ICON_COINV_REST,
    ICON_CONVERSION,
    ICON_CORONA,
    ICON_CUADRADO,
    ICON_ENVELOPE,
    ICON_FANTASMA,
    ICON_FUEGO,
    ICON_FUNNEL,
    ICON_GMV,
    ICON_GOOGLE,
    ICON_MARKDOWN,
    ICON_MARKDOWN_LEVER,
    ICON_MAPA,
    ICON_MD_PLAN,
    ICON_MEDALLA,
    ICON_MENU,
    ICON_MONITOR,
    ICON_OJO,
    ICON_OPS,
    ICON_ORDENES,
    ICON_PIN,
    ICON_RAPPI,
    ICON_RAYO,
    ICON_RENDIMIENTO,
    ICON_TELEFONO,
    ICON_TENDENCIA,
    ICON_TRAFICO,
    ICON_TROFEO,
    build_css,
    favicon,
    icon_categoria_for,
    icon_medalla_numero,
    logo_img,
)

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

def _copy_button_html(texto, label=None, tamano="chico"):
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

    label (novena vuelta, pedido explícito de Sabas): default None usa
    el ícono de portapapeles SVG monocromático (ICON_CLIPBOARD) en vez
    del emoji 📋 -- pasar un label explícito (ej. el botón "grande" con
    texto "Copiar") sigue funcionando igual que antes.
    """
    btn_id = f"copy-{abs(hash(texto))}"
    if label is None:
        label = f'<span class="lever-icon" style="margin:0;">{ICON_CLIPBOARD}</span>'
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


def _render_copy_script(texto, btn_id, label_original=None):
    """
    Paso 2 del botón de copiar: st_components.html() que busca el botón
    por su id en window.parent.document y le asigna el onclick real
    (navigator.clipboard.writeText con fallback a execCommand('copy'),
    igual que Growth OS). Se llama SIEMPRE junto a _copy_button_html.

    label_original / ícono de confirmación (novena vuelta, pedido
    explícito de Sabas): el emoji ✅ de "copiado" que antes iba
    hardcodeado en el JS pasa a ICON_BULLET_CHECK (SVG monocromático);
    label_original default None usa el mismo ICON_CLIPBOARD que
    _copy_button_html para que el botón vuelva a su ícono normal tras
    el timeout.
    """
    if label_original is None:
        label_original = f'<span class="lever-icon" style="margin:0;">{ICON_CLIPBOARD}</span>'
    check_html_js = json.dumps(f'<span class="lever-icon" style="margin:0;color:{COLORS["success"]};">{ICON_BULLET_CHECK}</span>')
    texto_js = json.dumps(str(texto))
    label_js = json.dumps(str(label_original))
    st_components.html(
        f"""
        <script>
        (function() {{
          var texto = {texto_js};
          var labelOriginal = {label_js};
          var checkHtml = {check_html_js};
          function findBtn() {{
            try {{
              var btn = window.parent.document.getElementById({json.dumps(btn_id)});
              if (!btn) return;
              btn.onclick = function() {{
                function marcarCopiado() {{
                  btn.innerHTML = checkHtml;
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


def mini_card(label, value, copy="", lever="", chip="", chip_color="", corner_badge=None, active=False):
    chip_html = (
        f'<span class="card-chip" style="background:{chip_color}22;color:{chip_color};">{chip}</span>'
        if chip else ""
    )
    badge_html = ""
    if corner_badge:
        b_text, b_color = corner_badge
        badge_html = f'<span class="corner-badge" style="background:{b_color}22;color:{b_color};">{b_text}</span>'
    # Ícono de palanca (morado si activa, gris si inactiva) -- rediseño
    # septiembre 2026, pedido explícito de Sabas: reemplaza el label de
    # texto suelto por un ícono circular chico + el nombre de la palanca.
    # Corrección (segunda vuelta, mismo pedido): el ícono es específico
    # por palanca -- megáfono para ADS, círculo-con-% para Markdown y
    # Markdown Pro (ambas comparten glifo, solo cambia el color) -- no un
    # rayo genérico como se había puesto antes.
    icon_svg = ICON_ADS_LEVER if lever == "ads" else ICON_MARKDOWN_LEVER
    icon_class = "lever-icon icon-purple" if active else "lever-icon"
    icon_html = f'<span class="{icon_class}">{icon_svg}</span>'
    # Card "apagada" cuando la palanca está inactiva -- tercera vuelta,
    # pedido explícito de Sabas: la card entera pasa a fondo gris (no
    # blanco brillante), sin borde lateral de color, y el corner-badge
    # también se desatura (ver .is-inactive en theme.py, con !important
    # para ganarle al color inline del badge).
    card_class = "business-mini-card lever-{}".format(lever) if active else "business-mini-card lever-{} is-inactive".format(lever)
    return (
        f'<div class="{card_class}">'
        f"{badge_html}"
        f'<div class="card-label">{icon_html}{label}</div>'
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


def _trend_sparkline(prev2, prev, curr):
    """
    Mini grafico SVG de 3 puntos: hace-2-meses -> mes-pasado -> mes-en-curso.
    Mismo lenguaje visual que Growth OS (linea con puntos huecos + area
    sombreada degradada debajo). Reemplaza al sparkline viejo de 2 puntos
    (Anterior/Actual) -- ahora son 3 meses reales, ya no 2 periodos
    genericos (pedido explicito de Sabas, septiembre 2026, hoja PREVIOUS
    GMV nueva en el Excel).

    Fix (septiembre 2026, segunda vuelta -- pedido explícito de Sabas):
    los puntos deben ser HUECOS (relleno blanco/card, borde naranja), no
    sólidos, y debe haber un área sombreada con degradado por debajo de
    la línea (se desvanece hacia abajo) -- antes faltaban ambos detalles,
    esto es lo que se ve en la referencia visual de Growth OS.

    Achicado (septiembre 2026, cuarta vuelta -- pedido explícito de
    Sabas): viewBox 250->170 de ancho, ahora hay 3 cards por fila
    (Órdenes/AOV/GMV) en vez de 2, menos ancho disponible por card;
    width="100%" (ya no fijo) para que escale con el contenedor.
    """
    prev2, prev, curr = max(prev2, 0), max(prev, 0), max(curr, 0)
    top = max(prev2, prev, curr, 1)
    y_prev2 = 34 - (prev2 / top) * 24
    y_prev = 34 - (prev / top) * 24
    y_curr = 34 - (curr / top) * 24
    color = COLORS["brand_orange"]
    fill_id = f"sparkfill-{abs(hash((prev2, prev, curr))) % 100000}"
    return (
        f'<svg width="100%" height="40" viewBox="0 0 170 44" style="overflow:visible;display:block;">'
        f'<defs><linearGradient id="{fill_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<path d="M13,{y_prev2:.1f} L85,{y_prev:.1f} L157,{y_curr:.1f} L157,44 L13,44 Z" '
        f'fill="url(#{fill_id})" stroke="none"/>'
        f'<line x1="13" y1="{y_prev2:.1f}" x2="85" y2="{y_prev:.1f}" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="85" y1="{y_prev:.1f}" x2="157" y2="{y_curr:.1f}" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
        f'<circle cx="13" cy="{y_prev2:.1f}" r="3.5" fill="{COLORS["card"]}" stroke="{color}" stroke-width="2.2"/>'
        f'<circle cx="85" cy="{y_prev:.1f}" r="3.5" fill="{COLORS["card"]}" stroke="{color}" stroke-width="2.2"/>'
        f'<circle cx="157" cy="{y_curr:.1f}" r="3.5" fill="{COLORS["card"]}" stroke="{color}" stroke-width="2.2"/>'
        f'</svg>'
    )


def metric_trend_card(icon, label, value, delta_frac, sub_left, prev=0, prev2=0,
                       currency="ARS", es_ritmo=False, fmt_fn=None, fmt_spark_fn=None):
    """
    Card de GMV/AOV/Órdenes al estilo Growth OS: icono + label arriba,
    valor grande (moneda nativa del farmer -- currency -- salvo que
    fmt_fn diga lo contrario), % de variacion vs mes anterior, y
    sparkline de 3 meses reales a la derecha (solo si hay dato de mes
    anterior).

    fmt_fn (nuevo, septiembre 2026, cuarta vuelta -- pedido explícito de
    Sabas: "Órdenes" pasa a tener su propia card, con el mismo sparkline
    de 3 meses que GMV/AOV, pero mostrando un CONTEO ("73 órdenes"), no
    un monto en ARS): funcion opcional value -> str que reemplaza a
    dl.fmt_money() en el valor grande. None (default) mantiene el
    comportamiento de siempre (fmt_money con currency) -- GMV/AOV no
    cambian su firma de llamada.

    fmt_spark_fn (nuevo, quinta vuelta -- pedido explícito de Sabas): el
    formateador de los 3 puntos chicos del pie del sparkline puede ser
    DISTINTO del de arriba -- ej. GMV muestra "ARS $ 4.028.558" arriba
    pero "$4,0M" abajo (dl.fmt_money_compact, abrevia a K/M porque con 3
    cards por fila el monto completo no entra legible); Órdenes muestra
    "73 órdenes" arriba pero solo "73" abajo (sin la palabra, para que
    quepa). None (default) usa el mismo formateador que el valor grande
    (fmt_fn o fmt_money).

    prev/prev2 (renombrados de prev_ars/prev2_ars en esta misma vuelta,
    ya no son necesariamente ARS): dato de mes anterior y de hace DOS
    meses (hoja LAST GMV / PREVIOUS GMV), para completar la comparativa
    de 3 meses reales -- antes el sparkline solo tenia 2 puntos
    genericos ("Anterior"/"Actual"); ahora son 3 meses nombrados por su
    mes calendario real (ej. Jul/Ago/Sep), que rota solo cada mes via
    dl.etiquetas_3_meses() -- pedido explicito de Sabas: que el proximo
    mes (octubre) el grafico se actualice solo, sin tocar codigo, para
    mostrar Ago/Sep/Oct.

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
    ya vendido. es_ritmo=False (AOV/Órdenes, default): variacion directa
    de siempre -- ninguno de los dos es un acumulado que haga falta
    proyectar (AOV es promedio, Órdenes ya viene sumada completa del mes
    en DETALLE, no parcial por dia).
    """
    _fmt = fmt_fn if fmt_fn else (lambda v: dl.fmt_money(v, currency))
    _fmt_spark = fmt_spark_fn if fmt_spark_fn else _fmt
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
    if prev > 0:
        mes_prev2, mes_prev, mes_curr = dl.etiquetas_3_meses()
        trend_html = (
            '<div style="text-align:center;flex:1;min-width:150px;max-width:220px;">'
            f'{_trend_sparkline(prev2, prev, value)}'
            f'<div style="display:flex;gap:8px;width:100%;margin:4px auto 0;">'
            f'<div style="flex:1;text-align:left;min-width:0;">'
            f'<div style="font-size:9px;color:{COLORS["muted"]};">{mes_prev2}</div>'
            f'<div style="font-size:10px;font-weight:600;color:{COLORS["muted"]};line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_fmt_spark(prev2)}</div>'
            f'</div>'
            f'<div style="flex:1;text-align:center;min-width:0;">'
            f'<div style="font-size:9px;color:{COLORS["muted"]};">{mes_prev}</div>'
            f'<div style="font-size:10px;font-weight:600;color:{COLORS["muted"]};line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_fmt_spark(prev)}</div>'
            f'</div>'
            f'<div style="flex:1;text-align:right;min-width:0;">'
            f'<div style="font-size:9px;color:{COLORS["muted"]};">{mes_curr}</div>'
            f'<div style="font-size:10px;font-weight:600;color:{COLORS["muted"]};line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_fmt_spark(value)}</div>'
            f'</div>'
            f'</div>'
            "</div>"
        )
    return (
        f'<div class="glass-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">'
        f'<div style="flex:1;min-width:0;">'
        f'<div class="card-label"><span class="lever-icon">{icon}</span>{label}</div>'
        f'<div class="card-value">{_fmt(value)}</div>'
        f'<div style="margin-top:8px;">{delta_html}</div>'
        f'<div class="card-copy" style="margin-top:4px;">{sub_left}</div>'
        f"</div>{trend_html}</div></div>"
    )


def state_text(active):
    # Sin emoji al lado de Active/Inactive -- pedido explícito de Sabas
    # (septiembre 2026, tercera vuelta): antes llevaba 🚀/💤, ahora solo
    # la palabra (el color y, si corresponde, el corner-badge/pill ya
    # comunican el estado).
    return ("Active", COLORS["success"]) if active else ("Inactive", COLORS["text_disabled"])


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
        f'<div class="mgmt-card-title" style="margin-bottom:12px;"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_MAPA}</span>Cono Sur — elegí un país</div>'
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

# _RENDIMIENTO_BG_COLOR: paleta PASTEL de las pills de Rendimiento
# Farmer/País -- fondo suave + texto/ícono del mismo tono, más saturado
# (ver _RENDIMIENTO_TEXT_COLOR). Vuelve a pastel (pedido explícito de
# Sabas, mockup aprobado) después de un paso intermedio por fondo
# ELÉCTRICO/sólido (_RENDIMIENTO_SOLID_COLOR, que queda sin uso acá pero
# se mantiene por si se reutiliza en otro lado -- sigue siendo la que
# pintan los 5 donuts de Brand Coverage). "red" comparte el mismo rojo
# coral que el segmento "Rechazado" del funnel de Rendimiento Comercial
# (COLORS["coral_soft"]/["coral_text"]), para que ambos contextos usen
# idéntico tono.
_RENDIMIENTO_BG_COLOR = {
    "red": COLORS["coral_soft"], "green": COLORS["success_soft"],
    "yellow": COLORS["warning_soft"], "blue": "rgba(108,155,209,0.16)",
    "purple": COLORS["brand_purple_soft"], "orange": COLORS["brand_orange_soft"],
    "gray": "rgba(107,114,128,0.10)",
}
_RENDIMIENTO_TEXT_COLOR = {
    "red": COLORS["coral_text"], "green": "#3E9160",
    "yellow": "#A97A1E", "blue": "#4C7CAD",
    "purple": COLORS["brand_purple"], "orange": COLORS["brand_orange"],
    "gray": COLORS["muted"],
}
_RENDIMIENTO_ICON = {"blue": ICON_RAYO, "green": ICON_TROFEO, "red": ICON_CUADRADO, "purple": ICON_FUEGO, "yellow": ICON_BULLET_WARNING}
# Color SÓLIDO/eléctrico -- usado por los 5 donuts de Brand Coverage
# (ver render_brand_coverage_and_contact). Ya no lo usan las pills de
# Rendimiento País/Farmer (ver _RENDIMIENTO_BG_COLOR arriba).
_RENDIMIENTO_SOLID_COLOR = {
    "red": COLORS["danger"], "green": COLORS["success"], "yellow": "#A97A1E",
    "blue": COLORS["blue"], "purple": COLORS["brand_purple"],
    "orange": COLORS["brand_orange"], "gray": COLORS["muted"],
}


def _rend_pill(valor, color):
    # Pill pastel (pedido explícito de Sabas, mockup aprobado): fondo
    # suave (_RENDIMIENTO_BG_COLOR) + texto/ícono del mismo tono, más
    # saturado (_RENDIMIENTO_TEXT_COLOR) -- el ícono hereda el color de
    # texto vía currentColor, no hace falta tocarlo aparte.
    bg_color = _RENDIMIENTO_BG_COLOR.get(color, "rgba(107,114,128,0.10)")
    text_color = _RENDIMIENTO_TEXT_COLOR.get(color, COLORS["muted"])
    return f'<span class="sup-pill" style="background:{bg_color};color:{text_color};">{valor}</span>'


def _rend_pill_a(valor, color):
    # Vuelta a pill pastel (pedido explícito de Sabas, mockup aprobado):
    # el ícono va del mismo color de texto que el resto de la pill
    # (_RENDIMIENTO_TEXT_COLOR), no blanco fijo -- blanco solo tenía
    # sentido cuando el fondo era el color eléctrico sólido. Color
    # explícito en el style inline igual que antes, para ganar por
    # especificidad sobre el gris fijo de la clase .lever-icon.
    icon_svg = _RENDIMIENTO_ICON.get(color, "")
    text_color = _RENDIMIENTO_TEXT_COLOR.get(color, COLORS["muted"])
    icon_html = (
        f'<span class="lever-icon" style="margin-left:4px;width:13px;height:13px;'
        f'vertical-align:-2px;color:{text_color};">{icon_svg}</span>'
        if icon_svg else ""
    )
    return _rend_pill(f"{valor}{icon_html}", color)


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
    "alejandro.guerrero@rappi.com" -> "alejandro.guerrero" -- pedido
    explícito de Sabas (segunda vuelta, septiembre 2026): antes se
    mostraba "usuario@..." (arroba + puntos suspensivos); ahora se
    corta directo en el "@", sin dejar rastro del dominio ni del
    símbolo. Se usa en Rendimiento Farmer/País en vez de mostrar el
    correo entero (que forzaba el ancho de toda la fila con correos
    largos como luisfernando.hernandez@rappi.com).
    """
    return str(email).split("@")[0]


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

    @st.dialog(f"Rendimiento País — {pais}", width="large", icon=":material/bar_chart:", on_dismiss=_on_dismiss)
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

    @st.dialog("Rendimiento Farmer", width="large", icon=":material/bar_chart:", on_dismiss=_on_dismiss)
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
        f'<div class="mgmt-card-title" style="margin:18px 0 8px;"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_RENDIMIENTO}</span>Rendimiento País</div>',
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

def render_login_tracker_supervisor():
    """
    Tabla de login/logout de TODO el equipo (28 farmers, no filtrada por
    país) -- pedido explícito de Sabas (agosto 2026, ajustada vigésima
    cuarta vuelta): 6 columnas (Farmer, Estado, Hora, Última entrada,
    Última salida, Tiempo de uso), con SOLO el último valor conocido por
    farmer (no historial acumulado -- confirmado explícitamente que se
    mantiene así, no se pasa a un historial de eventos). Dentro de un
    st.expander colapsado por defecto ("una opción desplegable... para no
    saturar"), debajo de la tabla de Rendimiento País.

    "Estado" es una pill semáforo (verde "Acceso" / rojo "Salida" / gris
    "Sin datos"), derivada de cuál de las 2 marcas de tiempo es más
    reciente -- el sistema no guarda un booleano explícito de "está
    adentro ahora". "Hora" muestra la marca de tiempo que corresponde a
    ese estado (la entrada si está en verde, la salida si está en rojo).

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
        # Diagnóstico temporal (vigésima cuarta vuelta, pedido explícito
        # de Sabas: "ya duré 2 minutos logueado y sigue diciendo que no
        # hay registros"): _github_get_file() atrapa CUALQUIER excepción
        # silenciosamente (token sin permisos, repo/rama mal escrito,
        # timeout, etc.) y devuelve un log vacío sin avisar nada en
        # pantalla -- solo queda registrado en session_state (data_issues,
        # ver data_layer.py), que hoy no se mostraba en ningún lado de la
        # UI. Se expone acá el detalle real del error (si lo hay) para
        # diagnosticar sin tener que adivinar la causa a ciegas.
        issues = dl.data_issues()
        if "login_log (leer)" in issues:
            st.error(f"Error real al leer el registro de GitHub: {issues['login_log (leer)']}")
        if "login_log (escribir)" in issues:
            st.error(f"Error real al escribir el registro de GitHub: {issues['login_log (escribir)']}")

        if log.empty:
            st.info("Todavía no hay registros de actividad -- van a aparecer a medida que el equipo entre a Wingman.")
            return

        # Se muestra TODO el equipo activo, tengan o no registro todavía
        # (los que nunca entraron aparecen con "—" en sus 3 columnas) --
        # así el supervisor ve de un vistazo quién no ha usado la
        # herramienta en absoluto, no solo quién sí.
        # Semáforo + Tipo de movimiento (vigésima cuarta vuelta, pedido
        # explícito de Sabas): el sistema NO guarda un booleano explícito
        # de "está adentro ahora" -- se deriva comparando cuál de las 2
        # marcas de tiempo es más reciente. VERDE + "Acceso" si la
        # última entrada es más reciente que la última salida (o si
        # nunca salió después de entrar); ROJO + "Salida" si ya salió y
        # no volvió a entrar. Farmer sin ningún registro aún -> gris,
        # "Sin datos".
        log_idx = log.set_index("farmer")
        filas_html = []
        for email in sorted(activos):
            if email in log_idx.index:
                row = log_idx.loc[email]
                entrada_raw = row["ultima_entrada"] if pd.notna(row["ultima_entrada"]) else None
                salida_raw = row["ultima_salida"] if pd.notna(row["ultima_salida"]) else None
                tiempo = f'{row["tiempo_uso_min"]:.0f} min' if pd.notna(row["tiempo_uso_min"]) else "—"
            else:
                entrada_raw = salida_raw = None
                tiempo = "—"

            entrada_ts = pd.to_datetime(entrada_raw, errors="coerce") if entrada_raw else None
            salida_ts = pd.to_datetime(salida_raw, errors="coerce") if salida_raw else None

            if entrada_ts is None and salida_ts is None:
                estado_color, estado_texto, hora_mostrada = "gray", "Sin datos", "—"
            elif entrada_ts is not None and (salida_ts is None or entrada_ts > salida_ts):
                estado_color, estado_texto, hora_mostrada = "green", "Acceso", entrada_raw
            else:
                estado_color, estado_texto, hora_mostrada = "red", "Salida", salida_raw

            entrada_fmt = entrada_raw or "—"
            salida_fmt = salida_raw or "—"

            filas_html.append(
                "<tr>"
                f'<td>{html_lib.escape(_correo_corto(email))}</td>'
                f'<td>{_rend_pill(html_lib.escape(estado_texto), estado_color)}</td>'
                f'<td>{html_lib.escape(str(hora_mostrada))}</td>'
                f'<td>{html_lib.escape(str(entrada_fmt))}</td>'
                f'<td>{html_lib.escape(str(salida_fmt))}</td>'
                f'<td>{html_lib.escape(str(tiempo))}</td>'
                "</tr>"
            )

        tabla_html = (
            '<table class="sup-table">'
            "<thead><tr>"
            "<th>Farmer</th><th>Estado</th><th>Hora</th>"
            "<th>Última entrada</th><th>Última salida</th><th>Tiempo de uso</th>"
            "</tr></thead>"
            f'<tbody>{"".join(filas_html)}</tbody>'
            "</table>"
        )
        st.markdown(tabla_html, unsafe_allow_html=True)


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
        f'<div class="mgmt-card-title" style="margin:18px 0 8px;"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_RENDIMIENTO}</span>Rendimiento Farmer</div>',
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
        items_html = "".join(
            f'<div><span class="lever-icon" style="width:12px;height:12px;margin-right:5px;vertical-align:-2px;color:{COLORS["brand_orange"]};">{ICON_BULLET_WARNING}</span>{n}</div>'
            for n in notas_bloqueo
        )
        # Solo gris y naranja (pedido explícito de Sabas, mockup
        # aprobado): la caja de aviso deja el fondo/texto amarillo-ámbar
        # y pasa a fondo gris muy claro (card2) con ícono y título en
        # naranja (brand_orange) y el texto en gris (muted).
        alerta_html = (
            '<div style="margin-top:10px;padding:10px 12px;border-radius:10px;'
            f'background:{COLORS["card2"]};color:{COLORS["brand_orange"]};font-size:12.5px;font-weight:600;'
            f'line-height:1.6;">{items_html}'
            f'<div style="margin-top:4px;font-weight:500;color:{COLORS["muted"]};">Afiná ahí para poder tomar esta plata de la mesa.</div>'
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
    # se está ganando hoy. Solo gris y naranja (mockup aprobado): el "91%
    # del target" pasa de morado a naranja, el resto del texto en gris.
    piso_html = ""
    if r["es_piso"]:
        piso_html = (
            f'<div style="font-size:11.5px;color:{COLORS["muted"]};font-weight:700;margin-top:2px;">'
            f'<span class="lever-icon" style="width:12px;height:12px;margin-right:5px;vertical-align:-2px;color:{COLORS["brand_orange"]};">{ICON_CONVERSION}</span>'
            f'Esto es lo que ganarías llegando al <span style="color:{COLORS["brand_orange"]};">91% del target</span> — con tu ritmo actual '
            f"({r['revenue_pace_pct']:.0f}%) todavía no se desbloquea.</div>"
        )

    st.markdown(
        '<div class="mgmt-card" style="margin-top:14px;">'
        f'<div class="mgmt-card-title"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_BILLETE}</span>Comisión Ads proyectada · al ritmo actual</div>'
        f'<div style="font-size:11.5px;color:{COLORS["muted"]};margin-bottom:8px;">'
        f'Revenue proyectado: {dl.fmt_money(r["revenue_pace_result"], "USD")} de '
        f'{dl.fmt_money(r["target_revenue"], "USD")} target ({r["revenue_pace_pct"]:.0f}% de ritmo)</div>'
        f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">'
        f'<div style="font-size:28px;font-weight:900;color:{COLORS["brand_orange"]};">'
        f'{dl.fmt_money(r["total_usd"], "USD")}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{COLORS["muted"]};">'
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
    from theme import LOGO_AZUL_URI
    import json

    logo_js = json.dumps(LOGO_AZUL_URI)
    bg = COLORS["bg"]
    ring_track = "rgba(18,62,74,0.10)"
    ring_fill = COLORS["brand_orange"]

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
                font-family: 'Plus Jakarta Sans', sans-serif; animation: gw-fade-in .12s ease-out; }}
              #gw-loading .gw-ring-wrap {{ position: relative; width: 150px; height: 150px;
                display: flex; align-items: center; justify-content: center; }}
              #gw-loading .gw-ring-svg {{ position: absolute; top: 0; left: 0; }}
              #gw-loading .gw-ring-arc {{ animation: gw-ring-cycle 2.4s cubic-bezier(.4,0,.2,1) infinite; }}
              #gw-loading .gw-logo {{ width: 88px; height: auto; position: relative; }}
              @keyframes gw-ring-cycle {{
                0% {{ stroke-dashoffset: 389.6; }}
                50% {{ stroke-dashoffset: 0; }}
                100% {{ stroke-dashoffset: 389.6; }}
              }}
              @keyframes gw-fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            `;
          }} catch (e) {{}}

          var LOGO = {logo_js};
          var S = W.__gwNavState = W.__gwNavState || {{ sawBusy: false, shownAt: 0, lastAct: 0 }};

          // buildOverlay ya NO recibe ni muestra ningún texto ("Cargando
          // X...") -- pedido explícito de Sabas (décima novena vuelta,
          // aprobado primero como mockup animado antes de tocar código): el
          // loader es siempre el mismo sin importar a dónde se navegue --
          // el logo completo de Wingman (en azul petróleo, para verse sobre
          // el fondo claro del área de contenido) quieto en el centro, con
          // un anillo tipo dona alrededor que se llena y se vacía en bucle
          // continuo (color naranja de marca). El parámetro `label` se
          // conserva sin usar en la firma para no tener que tocar las 3
          // llamadas a startNav(label) que lo siguen pasando -- simplemente
          // ya no se renderiza en ningún lado.
          // buildOverlay(label, anchorSelector) -- pedido explícito de
          // Sabas (trigésima vuelta): "cambiar tab Ads/MD", "cambiar
          // país del Supervisor" y "cambiar Farmer del Supervisor" usan
          // el MISMO overlay visual (logo + anillo), pero acotado a la
          // franja de abajo, SIN tapar el control que el usuario acaba
          // de tocar -- a diferencia del overlay global (click en ID de
          // marca / botón Volver), que sigue tapando toda el área de
          // contenido igual que siempre (anchorSelector null/omitido).
          //
          // anchorSelector, cuando se pasa, es el contenedor real
          // (st.container(key=...) -> ".st-key-<key>") que marca DÓNDE
          // empieza la zona a tapar: se mide su borde inferior
          // (getBoundingClientRect().bottom) y el overlay arranca ahí,
          // no en top:0 -- así el control disparador (botones Ads/MD,
          // mapa de país, selector de Farmer) queda siempre visible y
          // usable por fuera del overlay.
          function buildOverlay(label, anchorSelector) {{
            var el = D.getElementById('gw-loading');
            if (!el) {{ el = D.createElement('div'); el.id = 'gw-loading'; D.body.appendChild(el); }}
            el.innerHTML = '<div class="gw-ring-wrap">' +
              '<svg class="gw-ring-svg" width="150" height="150" viewBox="0 0 150 150">' +
                '<circle cx="75" cy="75" r="62" fill="none" stroke="{ring_track}" stroke-width="6"/>' +
                '<circle class="gw-ring-arc" cx="75" cy="75" r="62" fill="none" stroke="{ring_fill}" ' +
                  'stroke-width="6" stroke-linecap="round" stroke-dasharray="389.6" ' +
                  'stroke-dashoffset="389.6" transform="rotate(-90 75 75)"/>' +
              '</svg>' +
              '<img class="gw-logo" src="' + LOGO + '" alt="Wingman"/>' +
              '</div>';
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
            el.style.right = '0px';

            var top = 0;
            if (anchorSelector) {{
              try {{
                var anchor = D.querySelector(anchorSelector);
                if (anchor) {{
                  var ar = anchor.getBoundingClientRect();
                  if (ar.bottom > 0) top = ar.bottom;
                }}
              }} catch (e) {{}}
            }}
            el.style.top = top + 'px';
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

          function startNav(label, anchorSelector) {{
            W.__gwPendingNav = true;
            S.sawBusy = false;
            S.shownAt = Date.now();
            S.lastAct = S.shownAt;
            buildOverlay(label, anchorSelector);
          }}

          // Botón "← Volver a Rendimiento Comercial" / "← Volver a Ficha
          // de Marca" (pedido explícito de Sabas, trigésima vuelta: "ese
          // es el mismo [overlay global] que debe cargar al volver al
          // rendimiento comercial") -- vive en la Ficha de Marca, fuera
          // del sidebar, así que necesita su propio chequeo por key
          // igual que brandRowWrap.
          var VOLVER_KEY = 'btn_volver_comercial';

          // Triggers de loader LOCAL (pedido explícito de Sabas,
          // trigésima vuelta): cambiar tab Ads/MD, cambiar país del
          // Supervisor y cambiar Farmer del Supervisor NO deben tapar
          // pantalla completa -- cada uno tapa solo la franja de abajo
          // de su propio anchor, dejando visible el control recién
          // tocado. anchorKey es el st.container(key=...) cuyo borde
          // inferior marca dónde arranca la zona tapada.
          var LOCAL_TRIGGERS = [
            {{ btnKey: 'comercial_tab_btn_ads', anchorKey: 'comercial_tabs_anchor' }},
            {{ btnKey: 'comercial_tab_btn_md', anchorKey: 'comercial_tabs_anchor' }},
            // 'mapa_' (pedido explícito de Sabas, trigésima tercera
            // vuelta: "elegir Farmer primero, como ya funciona en
            // Rendimiento Comercial") -- el mismo botón físico de
            // render_conosur_map() ahora se monta dentro de DOS anchors
            // distintos según la sección activa (comercial_mapa_anchor
            // en Rendimiento Comercial, smartpri_mapa_anchor en Ficha de
            // Marca), nunca los dos a la vez -- anchorKeys (plural) se
            // resuelve probando cada uno con closest() y usando el que
            // de verdad envuelve al botón clickeado.
            {{ btnKeyPrefix: 'mapa_', anchorKeys: ['comercial_mapa_anchor', 'smartpri_mapa_anchor'] }},
            {{ containerKeyPrefix: 'st-key-comercial_blk_', anchorKey: 'comercial_tabs_anchor' }},
            // Fila de Smart Priorities (Ficha de Marca) -- mismo
            // mecanismo que 'st-key-comercial_row_' de Rendimiento
            // Comercial (ver isVolver/brandRowWrap en onNavClick):
            // dispara el overlay GLOBAL, no local, así que no lleva
            // entrada acá -- se resuelve más abajo junto a brandRowWrap.
          ];

          function resolveAnchorSelector(btn, trig) {{
            if (trig.anchorKey) return '.st-key-' + trig.anchorKey;
            if (trig.anchorKeys) {{
              for (var i = 0; i < trig.anchorKeys.length; i++) {{
                var sel = '.st-key-' + trig.anchorKeys[i];
                if (btn.closest(sel)) return sel;
              }}
            }}
            return null;
          }}

          function matchLocalTrigger(btn) {{
            for (var i = 0; i < LOCAL_TRIGGERS.length; i++) {{
              var t = LOCAL_TRIGGERS[i];
              if (t.btnKey && btn.closest('div[class*="st-key-' + t.btnKey + '"]')) return t;
              if (t.btnKeyPrefix) {{
                var wrap = btn.closest('div[class*="st-key-' + t.btnKeyPrefix + '"]');
                if (wrap) return t;
              }}
              if (t.containerKeyPrefix) {{
                var cwrap = btn.closest('div[class*="' + t.containerKeyPrefix + '"]');
                if (cwrap) return t;
              }}
            }}
            return null;
          }}

          function onNavClick(ev) {{
            try {{
              var btn = ev.target && ev.target.closest ? ev.target.closest('button') : null;
              if (!btn) return;
              var sidebar = D.querySelector('.st-key-wingman-sidebar');
              var inSidebar = sidebar && sidebar.contains(btn);
              // ID de marca clickeado en una tabla de ranking clicable --
              // Rendimiento Comercial (st-key-comercial_row_) y ahora
              // también Smart Priorities en Ficha de Marca (pedido
              // explícito de Sabas, trigésima tercera vuelta: "cuando yo
              // presione en el nombre de la marca o en el ID... me mande
              // a la ficha de la marca... tener los loaders claramente
              // entre cada cambio de página" -- st-key-smartpri_row_,
              // mismo contrato que comercial_row_, mismo overlay
              // GLOBAL). Ambos viven fuera del sidebar, así que
              // necesitan su propio chequeo aparte del filtro de arriba.
              var brandRowWrap = btn.closest('div[class*="st-key-comercial_row_"]') ||
                                  btn.closest('div[class*="st-key-smartpri_row_"]');
              var isVolver = !!btn.closest('div[class*="st-key-' + VOLVER_KEY + '"]');
              var localTrigger = matchLocalTrigger(btn);
              if (!inSidebar && !brandRowWrap && !isVolver && !localTrigger) return;
              if (brandRowWrap || isVolver) {{ startNav((btn.innerText || btn.textContent || '').trim()); return; }}
              if (localTrigger) {{
                startNav((btn.innerText || btn.textContent || '').trim(), resolveAnchorSelector(btn, localTrigger));
                return;
              }}
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
              // BUG REAL CORREGIDO (décima novena vuelta, pedido explícito de
              // Sabas -- "el loader sigue sin arreglarse", vio "Cargando
              // bar_chart Rendimiento General..."): desde que los botones de
              // navegación llevan icon=":material/...:" (Material Symbols),
              // Streamlit los renderiza como un <span data-testid=
              // "stIconMaterial"> cuyo TEXTO LITERAL es el nombre crudo del
              // ícono (ej. "bar_chart") -- la fuente de íconos lo convierte
              // visualmente en el glifo correcto, pero btn.innerText sigue
              // leyendo ese nombre técnico concatenado con el label real
              // ("bar_chart" + salto de línea + "Rendimiento General",
              // confirmado inspeccionando el DOM real). El filtro viejo de "todo el label es puro
              // snake_case" nunca lo atajaba porque el label completo no es
              // SOLO snake_case, es el ícono pegado al texto real. Fix: se
              // clona el botón, se le quita el <span data-testid=
              // "stIconMaterial"> ANTES de leer el texto, así el label nunca
              // incluye el nombre del ícono, sin importar cuál sea.
              var btnClone = btn.cloneNode(true);
              var iconSpan = btnClone.querySelector('[data-testid="stIconMaterial"]');
              if (iconSpan) iconSpan.remove();
              var label = ((btnClone.innerText || btnClone.textContent) || '').trim();
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

          // Selector de Farmer del Supervisor (st.selectbox) -- pedido
          // explícito de Sabas, trigésima vuelta (extendido en la
          // trigésima tercera a Smart Priorities / Ficha de Marca, que
          // usa el mismo patrón con su propio anchor): mismo loader
          // LOCAL que el cambio de país, acotado a la franja debajo del
          // mapa. Un st.selectbox de Streamlit no es un <select> nativo:
          // es un combobox armado con un input de solo-lectura + listbox
          // desplegable, así que no dispara 'change' -- se escucha
          // 'click' sobre las opciones del listbox (role="option"), que
          // Streamlit monta en un portal al final del <body>, fuera del
          // propio contenedor del selectbox.
          //
          // FARMER_COMBOS (plural) -- dos combos de Farmer distintos
          // pueden existir en el DOM según la sección activa
          // (comercial_farmer_anchor en Rendimiento Comercial,
          // smartpri_farmer_anchor en Ficha de Marca), nunca los dos a
          // la vez. Se guarda CUÁL combo se abrió (su mapAnchor) en el
          // atributo del body, para saber a qué overlay anclar cuando
          // se elige una opción -- antes solo existía un combo, así que
          // el anchor de cierre estaba hardcodeado.
          var FARMER_COMBOS = [
            {{ comboKey: 'comercial_farmer_anchor', mapAnchor: 'comercial_mapa_anchor' }},
            {{ comboKey: 'smartpri_farmer_anchor', mapAnchor: 'smartpri_mapa_anchor' }},
          ];
          function isFarmerSelectOption(t) {{
            try {{
              var opt = t && t.closest ? t.closest('[role="option"]') : null;
              if (!opt) return false;
              // El listbox del selectbox de Farmer es el único que este
              // watcher necesita distinguir -- se valida contra el combo
              // actualmente abierto en vez de inspeccionar el texto de
              // la opción (evita falsos positivos con otro selectbox que
              // pudiera existir en la página).
              return !!D.body.getAttribute('data-gw-farmer-combo-open');
            }} catch (e) {{ return false; }}
          }}
          function onFarmerComboClick(ev) {{
            try {{
              for (var i = 0; i < FARMER_COMBOS.length; i++) {{
                var fc = FARMER_COMBOS[i];
                var combo = ev.target && ev.target.closest
                  ? ev.target.closest('.st-key-' + fc.comboKey) : null;
                if (combo) {{ D.body.setAttribute('data-gw-farmer-combo-open', fc.mapAnchor); return; }}
              }}
              if (isFarmerSelectOption(ev.target)) {{
                var mapAnchor = D.body.getAttribute('data-gw-farmer-combo-open');
                D.body.removeAttribute('data-gw-farmer-combo-open');
                startNav('Farmer', '.st-key-' + mapAnchor);
              }}
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

          // Timings del watcher (pedido explícito de Sabas, trigésima
          // primera vuelta: "si con el caché el tiempo disminuye,
          // recorta los loaders parciales -- actualmente están en
          // 0.4s") -- recortados de 450/650ms a 250/350ms tras meter
          // @st.cache_data en rendimiento_comercial_ads_for/md_for
          // (ver data_layer.py): con cache-hit, el trabajo real que
          // Streamlit hace en un click de Rendimiento Comercial (cambiar
          // de bloque/tab/país/Farmer) pasa de recorrer 5 hojas con
          // iterrows a devolver un resultado ya calculado, así que el
          // margen de seguridad ya no necesita ser tan generoso. No se
          // toca el 5000ms de más abajo -- ese es el respaldo para el
          // caso RARO en que Streamlit termine tan rápido que el
          // polling de 80ms ni lo detecte "busy" (cache-miss real, TTL
          // vencido a las 24h, o cualquier otro trigger de la app fuera
          // de Rendimiento Comercial que use este mismo watcher) -- 
          // acortar ESE número sí arriesga cerrar el overlay antes de
          // tiempo en esos casos, que es justo lo que este watchdog
          // existe para evitar.
          function navTick() {{
            if (!W.__gwPendingNav) return;
            var now = Date.now();
            if (streamlitBusy()) {{ S.sawBusy = true; S.lastAct = now; return; }}
            if (now - S.shownAt < 250) return;
            if (now - S.lastAct < 350) return;
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
              D.removeEventListener('click', old.farmerCombo, true);
              D.removeEventListener('keydown', old.key, true);
              D.removeEventListener('focusin', old.fin, true);
              D.removeEventListener('focusout', old.fout, true);
            }}
          }} catch (e) {{}}
          var H = {{ click: onNavClick, farmerCombo: onFarmerComboClick, key: onBrandKey, fin: onBrandFocusIn, fout: onBrandFocusOut }};
          W.__gwNavHandlers = H;
          D.addEventListener('click', H.click, true);
          D.addEventListener('click', H.farmerCombo, true);
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
                f'<div class="login-logo">{logo_img(160, full=True)}</div>'
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
                if st.button("👤 Farmer", use_container_width=True, key="login_toggle_farmer",
                             type="primary" if st.session_state["login_role"] == "farmer" else "secondary"):
                    st.session_state["login_role"] = "farmer"
                    st.rerun()
            with rc2:
                if st.button("🧭 Supervisor", use_container_width=True, key="login_toggle_supervisor",
                             type="primary" if st.session_state["login_role"] == "supervisor" else "secondary"):
                    st.session_state["login_role"] = "supervisor"
                    st.rerun()

            role = st.session_state["login_role"]

            if role == "farmer":
                email = st.text_input("Correo", placeholder="nombre.apellido@rappi.com")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••")
                entrar = st.button("Entrar", type="primary", use_container_width=True, key="login_submit")

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
                entrar_sup = st.button("Entrar como Supervisor", type="primary", use_container_width=True, key="login_submit_sup")

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

        # ── Navegación de 2 secciones: Rendimiento General / Ficha de Marca ──
        # RENOMBRADAS (décima octava vuelta, pedido explícito de Sabas):
        # "Buscador de Marcas" -> "Ficha de Marca", "Gestión General" ->
        # "Rendimiento General" -- y el orden se invierte (antes Ficha de
        # Marca/brand_finder arriba, ahora Rendimiento General/management
        # arriba). Los emojis Unicode a color (🔍/📊) pasan al parámetro
        # icon= nativo de st.button con Material Symbols
        # (":material/search:"/":material/bar_chart:") -- mismo mecanismo
        # ya usado en st.dialog (ver _tabla_fullscreen_dialog): st.button
        # es un componente nativo de Streamlit que NO acepta HTML/SVG en
        # su label (confirmado en vueltas anteriores), pero SÍ tiene su
        # propio parámetro icon con soporte de Material Symbols, que
        # resuelve esto sin la técnica de "botón HTML + JS enganchado"
        # que el propio código ya documentó como poco confiable
        # (ver el comentario de BUG REAL CORREGIDO más arriba en este
        # archivo, sobre _tabla_fullscreen_dialog). Rendimiento General
        # es ahora la sección por defecto (setdefault) porque quedó
        # primera en el nuevo orden. Cambiar de sección resetea la vista
        # a "landing" dentro de esa sección (nunca deja a alguien parado
        # en una ficha de marca de otra sección). Las keys internas
        # (brand_finder / management) NO cambiaron -- solo la etiqueta
        # visible y el orden -- para no tener que tocar el resto del
        # código que ya compara contra esas keys.
        #
        # "trabajables" ELIMINADA por completo (décima vuelta, pedido
        # explícito de Sabas): la sección completa -- las 4 tabs
        # (Adquisición Ads, Upselling Ads, Adquisición MD, Recuperación
        # Churn) y sus funciones render_trabajables* -- sale del
        # producto. El sidebar vuelve a los 2 ítems originales.
        st.session_state.setdefault("section", "management")
        NAV_SECTIONS = [
            ("management",   "Rendimiento General", ":material/bar_chart:"),
            ("brand_finder", "Ficha de Marca", ":material/search:"),
            ("comercial",    "Rendimiento Comercial", ":material/emoji_events:"),
        ]
        for sec_key, sec_label, sec_icon in NAV_SECTIONS:
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
            if st.button(sec_label, key=f"nav_{sec_key}", icon=sec_icon, use_container_width=True):
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
# =====================================================
# SECCIÓN: RENDIMIENTO COMERCIAL — funnel Ads + Markdown, ambos reales
# =====================================================
# Pedido explícito de Sabas (vigésima quinta a vigésima octava
# vuelta): 3ra sección del sidebar, con 2 tabs (Ads/MD), cada uno con
# su propio funnel Base -> Contactados -> Cierre. Ads: OPP START +
# PRODUCTIVITY + ADS COMERCIAL + CHECKOUT (ver
# rendimiento_comercial_ads_for). MD: MD START + PRODUCTIVITY (ver
# rendimiento_comercial_md_for) -- sin target por marca ni fila de
# Total (pedido explícito: "en las tablas de MD no hay target...
# con la sola pill del status basta", "la fila Total solo aplica a
# Ads").
def _render_funnel_comercial(kind, farmer_para_funnel):
    """
    kind: "ads" o "md". Dibuja el funnel de 3 bloques + tabla al
    lado, con click-en-bloque, ID clickeable a la Ficha de Marca
    (con botón Volver que recuerda tab+bloque), loader acotado solo
    al cuadro de la tabla, y fila de Total en Cierre (solo Ads).
    """
    vista_key = f"comercial_{kind}_vista"
    st.session_state.setdefault(vista_key, "base")

    if kind == "ads":
        datos = dl.rendimiento_comercial_ads_for(farmer_para_funnel)
    else:
        datos = dl.rendimiento_comercial_md_for(farmer_para_funnel)
    c = datos["counts"]

    if c["base"] == 0:
        st.info("Sin datos de Rendimiento Comercial disponibles para este Farmer.")
        return

    pct_contactado = round(c["contactado"] / c["base"] * 100, 1) if c["base"] else 0
    pct_no_cont = round(c["no_contactado"] / c["base"] * 100, 1) if c["base"] else 0
    pct_sin_gest = round(c["sin_gestionar"] / c["base"] * 100, 1) if c["base"] else 0
    pct_rechazado = round(c["rechazado"] / c["contactado"] * 100, 1) if c["contactado"] else 0
    pct_pnm = round(c["palanca_no_mencionada"] / c["contactado"] * 100, 1) if c["contactado"] else 0
    pct_cerrado = round(c["cerrado"] / c["contactado"] * 100, 1) if c["contactado"] else 0
    pct_cierre_base = round(c["cerrado"] / c["base"] * 100, 1) if c["base"] else 0
    win_rate = pct_cerrado

    # Colores (pedido explícito, vigésima octava vuelta): "los
    # bloques ahora serán de color azul de la sidebar, y las letras
    # blancas" (antes morado) -- eso libera COLORS["blue"] (el azul
    # claro que usaba "Palanca no mencionada"), que ahora pasa a
    # GRIS ("eso te hará cambiar el azul de contactados, entonces
    # ese azul ahora ponlo gris que es palancas no mencionadas").
    color_principal = COLORS["sidebar"]  # brand_blue #123E4A
    color_principal_soft = "rgba(18,62,74,0.16)"
    color_pnm = COLORS["muted"]

    etiqueta_base = "Prospectados" if kind == "ads" else "Prospectados · MD"
    etiqueta_cierre = "Adquiridos" if kind == "ads" else "Adquiridos · MD"

    col_funnel, col_tabla = st.columns([1, 1])
    with col_funnel:
        activo = st.session_state[vista_key]
        # Fondo AZUL COMPLETO en los 3 bloques (pedido explícito,
        # confirmado 2 veces: "el FONDO COMPLETO de la card... con TODO
        # el texto en blanco... los 3 bloques quedan con el mismo fondo
        # azul sólido") -- antes solo la barra de progreso interna
        # cambiaba de color, el resto de la card seguía blanca/gris.
        # El bloque activo (el que está siendo visto en la tabla) se
        # distingue con un borde blanco más grueso, ya que un borde
        # morado/verde no se notaría sobre el mismo azul de fondo.
        borde_base = "2px solid white" if activo == "base" else f"1px solid {color_principal}"
        borde_contactado = "2px solid white" if activo == "contactado" else f"1px solid {color_principal}"
        borde_cierre = "2px solid white" if activo == "cierre" else f"1px solid {color_principal}"

        def _leyenda(items):
            chips = "".join(
                '<div class="cp-legend-item" style="font-size:10.5px;gap:5px;color:white;">'
                f'<div class="cp-legend-dot" style="width:8px;height:8px;background:{color};border:1px solid rgba(255,255,255,0.4);"></div>'
                f'<span>{label} · {valor}</span></div>'
                for label, valor, color in items
            )
            return f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">{chips}</div>'

        with st.container(key=f"comercial_blk_base_{kind}"):
            base_html = (
                f'<div class="comercial-blk-visual" style="width:100%;background:{color_principal};border:{borde_base};border-radius:16px 16px 0 0;padding:16px 24px;box-sizing:border-box;">'
                f'<div style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.75);">{etiqueta_base} (inicio de mes)</div>'
                f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:2px;">'
                f'<span style="font-size:26px;font-weight:800;color:white;">{c["base"]}</span>'
                f'<span style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.75);">100%</span></div>'
                '<div style="display:flex;height:16px;border-radius:6px;overflow:hidden;margin-top:8px;background:rgba(255,255,255,0.15);">'
                f'<div style="width:{pct_contactado}%;background:white;"></div>'
                f'<div style="width:{pct_no_cont}%;background:rgba(255,255,255,0.45);"></div>'
                '<div style="background:transparent;"></div>'
                "</div>"
                + _leyenda([
                    ("Contactado", c["contactado"], "white"),
                    ("No Contactado", c["no_contactado"], "rgba(255,255,255,0.45)"),
                    ("Sin Gestionar", c["sin_gestionar"], "rgba(255,255,255,0.15)"),
                ])
                + "</div>"
            )
            st.markdown(base_html, unsafe_allow_html=True)
            if st.button(" ", key=f"comercial_blk_base_btn_{kind}"):
                st.session_state[vista_key] = "base"
                st.rerun()

        st.markdown(
            '<div style="display:flex;justify-content:center;">'
            f'<div style="width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:9px solid {color_principal};"></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        with st.container(key=f"comercial_blk_contactado_{kind}"):
            contactado_html = (
                f'<div class="comercial-blk-visual" style="width:100%;background:{color_principal};border:{borde_contactado};border-top:none;padding:14px 22px;box-sizing:border-box;">'
                f'<div style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.75);">Contactados</div>'
                f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:2px;">'
                f'<span style="font-size:20px;font-weight:800;color:white;">{c["contactado"]}</span>'
                f'<span style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.75);">{pct_contactado}% de la base</span></div>'
                '<div style="display:flex;height:16px;border-radius:6px;overflow:hidden;margin-top:8px;">'
                f'<div style="width:{pct_rechazado}%;background:{COLORS["coral_solid"]};"></div>'
                f'<div style="width:{pct_pnm}%;background:rgba(255,255,255,0.45);"></div>'
                f'<div style="width:{pct_cerrado}%;background:{COLORS["success"]};"></div>'
                "</div>"
                + _leyenda([
                    ("Rechazado", c["rechazado"], COLORS["coral_solid"]),
                    ("Palanca no mencionada", c["palanca_no_mencionada"], "rgba(255,255,255,0.45)"),
                    ("Cerrado", c["cerrado"], COLORS["success"]),
                ])
                + "</div>"
            )
            st.markdown(contactado_html, unsafe_allow_html=True)
            if st.button(" ", key=f"comercial_blk_contactado_btn_{kind}"):
                st.session_state[vista_key] = "contactado"
                st.rerun()

        st.markdown(
            '<div style="display:flex;justify-content:center;">'
            f'<div style="width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:9px solid {color_principal};"></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        with st.container(key=f"comercial_blk_cierre_{kind}"):
            fuente_cierre = "Ads Comercial" if kind == "ads" else "Productivity"
            cierre_html = (
                f'<div class="comercial-blk-visual" style="width:100%;background:{color_principal};border:{borde_cierre};border-top:none;border-radius:0 0 16px 16px;padding:14px 20px;box-sizing:border-box;box-shadow:0 4px 14px rgba(18,62,74,0.25);">'
                f'<div style="font-size:10.5px;font-weight:700;color:rgba(255,255,255,0.75);">{etiqueta_cierre} ({fuente_cierre})</div>'
                f'<div style="display:flex;align-items:baseline;gap:7px;margin-top:2px;">'
                f'<span style="font-size:20px;font-weight:800;color:white;">{c["cerrado"]}</span>'
                f'<span style="font-size:9.5px;font-weight:700;color:rgba(255,255,255,0.75);">{pct_cierre_base}% base · {win_rate}% de contactados</span></div>'
                f'<div style="margin-top:8px;"><span style="background:{COLORS["success"]};color:white;font-size:11px;font-weight:800;padding:4px 12px;border-radius:999px;">Win rate {win_rate}%</span></div>'
                "</div>"
            )
            st.markdown(cierre_html, unsafe_allow_html=True)
            if st.button(" ", key=f"comercial_blk_cierre_btn_{kind}"):
                st.session_state[vista_key] = "cierre"
                st.rerun()

    with col_tabla:
        vista = st.session_state[vista_key]
        color_estado = {
            "Contactado": (color_principal, "white"),
            "No Contactado": (color_principal_soft, COLORS["text"]),
            "Sin Gestionar": (COLORS["card2"], COLORS["muted"]),
            "Rechazado": (COLORS["coral_solid"], "white"),
            "Palanca no mencionada": (color_pnm, "white"),
            "Cerrado": (COLORS["success"], "white"),
        }

        def _pill_gris(valor):
            return (
                f'<span style="background:{COLORS["card2"]};color:{COLORS["muted"]};'
                f'font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;'
                f'display:inline-block;white-space:nowrap;">{html_lib.escape(str(valor))}</span>'
            )

        def _pill_estado(valor):
            bg, fg = color_estado.get(valor, (COLORS["card2"], COLORS["muted"]))
            return (
                f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:800;'
                f'padding:3px 10px;border-radius:999px;display:inline-block;white-space:nowrap;">{html_lib.escape(str(valor))}</span>'
            )

        # ID clickeable → Ficha de Marca, con botón Volver (pedido
        # explícito de Sabas, vigésima octava vuelta) -- un
        # st.button real por fila (no HTML puro, para poder disparar
        # go_to_brand), disfrazado de pill azul clickeable vía CSS
        # ".comercial-id-btn" (mismo mecanismo de re-skin que ya usa
        # el resto de la app, no position:absolute esta vez porque
        # acá el botón SÍ debe verse, no cubrir un bloque entero).
        titulos = {"base": etiqueta_base.split(" (")[0].split(" · ")[0], "contactado": "Contactados", "cierre": etiqueta_cierre.split(" (")[0].split(" · ")[0]}
        titulo = titulos.get(vista, "")

        # Loader del CLICK EN BLOQUE (pedido explícito de Sabas, trigésima
        # vuelta) -- ya NO es este st.spinner() de Python: el cálculo real
        # y pesado (datos = rendimiento_comercial_*_for arriba, sin cache,
        # con iterrows sobre 5 hojas) ya terminó ANTES de llegar acá, así
        # que un spinner puesto en este punto siempre llega tarde --
        # cubre el momento en que ya no hay nada lento por esperar. El
        # overlay LOCAL (mismo logo+anillo del global, acotado con
        # buildOverlay(label, anchorSelector)) ahora se dispara desde JS
        # al instante del click en el bloque (ver LOCAL_TRIGGERS /
        # containerKeyPrefix 'st-key-comercial_blk_' en
        # render_loading_watcher), que sí alcanza a cubrir el cálculo
        # real. El time.sleep(0.4) artificial que existía acá se retira
        # por el mismo motivo: corría en CADA ejecución de esta función
        # (entrar desde el sidebar, cambiar de tab, volver de la Ficha),
        # no solo al cambiar de bloque, sumando 0.4s a cargas que el
        # overlay global ya cubre por su cuenta.
        tabla_placeholder = st.empty()
        with tabla_placeholder.container():
                if vista == "base":
                    filas = datos["base"]
                elif vista == "contactado":
                    filas = [f for f in datos["contactado"] if f["estado"] != "Cerrado"]
                else:
                    filas = datos["cierre"]

                st.markdown(f'<div style="font-size:13px;font-weight:800;color:{COLORS["text"]};margin-bottom:8px;">{titulo} · {len(filas)} marcas</div>', unsafe_allow_html=True)

                if not filas:
                    st.info("Sin marcas en esta vista.")
                else:
                    # Anchos de columna equilibrados (pedido explícito:
                    # "ajusta también el tamaño de las celdas para que
                    # queden equilibradas, mira que ID se corta y baja
                    # a dos líneas") -- ID más ancho (90px, cabe
                    # "AR104180" sin cortar), Target más angosto en MD
                    # (no existe esa columna en absoluto).
                    con_target = kind == "ads" and vista != "cierre"
                    # Mismas proporciones que row_cols (st.columns) de
                    # abajo, expresadas como fracciones CSS Grid (fr) --
                    # así el header y las filas quedan alineados en vez
                    # de usar números de píxel independientes que podían
                    # desalinearse sutilmente contra los ratios reales.
                    if vista == "cierre" and kind == "ads":
                        cols_css = "1.4fr 3.2fr 1.3fr"
                    elif con_target:
                        cols_css = "1.4fr 3.2fr 1fr 1.6fr"
                    else:
                        cols_css = "1.4fr 3.2fr 1.6fr"

                    tabla_key = f"comercial_tabla_scroll_{kind}_{vista}"

                    # BUG REAL EVITADO antes de entregar (mismo problema
                    # que ya peleamos con los bloques del funnel): un
                    # st.markdown() que abre un <div style="overflow-y:
                    # auto"> y otro st.markdown() que lo cierra, con
                    # st.columns()/st.button() en medio, NO envuelve nada
                    # de verdad -- son elementos DOM hermanos, no padre-
                    # hijo, así que el scroll interno nunca funcionaría.
                    # Fix: TODO (header + filas) va dentro de un único
                    # st.container(key=...) real, y el overflow se aplica
                    # vía CSS al [data-testid="stVerticalBlock"] interno
                    # de ESE contenedor -- eso sí es un <div> de verdad
                    # que contiene a todos los hijos.
                    #
                    # BUG REAL CORREGIDO (confirmado por Sabas: "la tabla
                    # se está mostrando completa... no una tabla gigante
                    # que tuve que bajar toda la página"). El CSS custom
                    # (max-height + overflow-y en el data-testid interno)
                    # no se estaba aplicando de forma confiable -- la
                    # documentación oficial de Streamlit confirma que
                    # st.container(height=N) es el mecanismo NATIVO para
                    # esto exacto: "si el contenido es más grande que la
                    # altura especificada, el scroll se activa
                    # automáticamente" -- mucho más confiable que CSS
                    # custom sobre un data-testid interno cuya estructura
                    # exacta puede variar según los widgets anidados
                    # adentro (st.columns() dentro del container).
                    st.markdown(
                        f"""
                        <style>
                        div[class*="st-key-comercial_row_"] {{ display: grid !important; grid-template-columns: 1fr !important; }}
                        div[class*="st-key-comercial_row_"] [data-testid="stElementContainer"] {{ grid-column: 1 !important; grid-row: 1 !important; margin: 0 !important; padding: 0 !important; }}
                        div[class*="st-key-comercial_row_"] .stButton button {{
                            width: 100%; text-align: left; background: transparent !important; border: none !important;
                            padding: 0 !important; margin: 0 !important; box-shadow: none !important; color: {color_principal} !important;
                            font-weight: 700 !important; font-size: 11px !important; text-decoration: underline;
                            white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    header_cols = ["ID", "Nombre", "Valor"] if (vista == "cierre" and kind == "ads") else (
                        ["ID", "Nombre", "Target", "Estado"] if con_target else ["ID", "Nombre", "Estado"]
                    )
                    header_html = (
                        f'<div style="display:grid;grid-template-columns:{cols_css};gap:8px;padding:0 4px 6px;'
                        f'font-size:10px;font-weight:700;color:{COLORS["muted"]};text-transform:uppercase;">'
                        + "".join(f"<span>{h}</span>" for h in header_cols) + "</div>"
                    )
                    st.markdown(
                        f'<div style="border:1px solid {COLORS["card2"]};border-radius:12px 12px 0 0;'
                        f'border-bottom:none;padding:10px 12px 0;">{header_html}</div>',
                        unsafe_allow_html=True,
                    )

                    total_valor = 0.0
                    with st.container(key=tabla_key, height=440, border=True):
                        for idx, f in enumerate(filas):
                            row_cols = st.columns([1.4, 3.2, 1, 1.6] if con_target else ([1.4, 3.2, 1.3] if (vista == "cierre" and kind == "ads") else [1.4, 3.2, 1.6]))
                            with row_cols[0]:
                                if f["id"] != "—":
                                    with st.container(key=f"comercial_row_{kind}_{vista}_{idx}"):
                                        if st.button(f["id"], key=f"comercial_row_btn_{kind}_{vista}_{idx}"):
                                            go_to_brand(
                                                f["id"],
                                                volver_a={
                                                    "tab": st.session_state.get("comercial_tab_activo", "ads"),
                                                    "vista_ads": st.session_state.get("comercial_ads_vista", "base"),
                                                    "vista_md": st.session_state.get("comercial_md_vista", "base"),
                                                },
                                            )
                                else:
                                    st.markdown(_pill_gris("—"), unsafe_allow_html=True)
                            with row_cols[1]:
                                st.markdown(f'<div style="font-size:12px;padding-top:2px;">{html_lib.escape(f["nombre"])}</div>', unsafe_allow_html=True)
                            if vista == "cierre" and kind == "ads":
                                with row_cols[2]:
                                    if f["valor"] != "—":
                                        total_valor += float(f["valor"].replace("$", "").replace(",", ""))
                                    st.markdown(f'<div style="font-size:12px;font-weight:800;color:{COLORS["success"]};padding-top:2px;">{html_lib.escape(f["valor"])}</div>', unsafe_allow_html=True)
                            elif con_target:
                                with row_cols[2]:
                                    st.markdown(f'<div style="padding-top:2px;">{_pill_gris(f["target"])}</div>', unsafe_allow_html=True)
                                with row_cols[3]:
                                    st.markdown(f'<div style="padding-top:2px;">{_pill_estado(f["estado"])}</div>', unsafe_allow_html=True)
                            else:
                                with row_cols[2]:
                                    st.markdown(f'<div style="padding-top:2px;">{_pill_estado(f["estado"])}</div>', unsafe_allow_html=True)

                    # Fila de Total (pedido explícito, solo Ads en
                    # Cierre: "añade una fila de total en cierre, que
                    # sume todo lo adquirido si hay reporte" -- "la
                    # fila Total solo aplica a la tabla de Cierre de
                    # Ads"). "si hay reporte" -> si al menos una fila
                    # tiene valor real (no todas son relleno "—").
                    if vista == "cierre" and kind == "ads" and total_valor > 0:
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;padding:10px 4px 0;'
                            f'margin-top:6px;border-top:2px solid {COLORS["text"]};font-size:12.5px;font-weight:800;">'
                            f'<span>Total adquirido</span><span style="color:{COLORS["success"]};">${total_valor:,.0f}</span></div>',
                            unsafe_allow_html=True,
                        )

st.session_state.setdefault("comercial_tab_activo", "ads")



def get_portfolio():
    """Cartera del usuario en sesion. Supervisor: TODAS las marcas de los
    27 farmers (puede buscar cualquiera). Farmer: solo la suya."""
    if "_portfolio_cache" not in st.session_state:
        st.session_state["_portfolio_cache"] = (
            dl.portfolio_supervisor() if IS_SUPERVISOR else dl.portfolio_for(selected)
        )
    return st.session_state["_portfolio_cache"]


def go_to_brand(key, volver_a=None):
    st.session_state["active_brand"] = key
    st.session_state["view"] = "ficha"
    # "volver_a" (pedido explícito de Sabas, vigésima octava vuelta:
    # "un botón de volver, para volver a rendimiento comercial a ver la
    # siguiente marca") -- guarda de dónde vino el click para que el
    # botón Volver de la Ficha de Marca sepa restaurar EXACTAMENTE ese
    # estado (section, tab Ads/MD, y bloque del funnel activo), en vez
    # de usar go_to_landing() genérico que siempre resetea a la pantalla
    # de aterrizaje sin memoria de dónde estaba el usuario.
    if volver_a is not None:
        st.session_state["volver_a"] = volver_a
    else:
        st.session_state.pop("volver_a", None)
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
    # Color por RITMO + ícono dentro del donut (agosto 2026, séptima
    # vuelta, actualizado en la octava; ícono SVG monocromático en vez
    # de emoji Unicode desde la segunda vuelta de septiembre): Adquisición
    # Ads, Upselling Ads y Conversión MD son las 3 métricas que se miden
    # en ritmo/pace (ver adquisicion_ads_for/upselling_ads_for/
    # conversion_for) -- para esas 3, el color del anillo y el ícono
    # debajo del % salen de una función de pace, con _RENDIMIENTO_ICON
    # para el símbolo. IMPORTANTE (octava vuelta): Adquisición y
    # Upselling YA NO comparten semáforo con Conversión MD -- Adquisición/
    # Upselling usan pace_color_ads_upsell
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
        # Rediseño Rendimiento General (pedido explícito de Sabas, mockup
        # aprobado): la card pasa a fondo azul petróleo -- el track de
        # fondo del donut ya no puede ser card2 (gris claro pensado para
        # fondo blanco, invisible/roto sobre azul petróleo); pasa a un
        # blanco translúcido tenue. El relleno de progreso ya no lleva el
        # color eléctrico por métrica (rojo/verde/azul/morado) -- ahora es
        # blanco sólido fijo para las 5 donas, coherente con "las donas se
        # rellenan de blanco" del mockup.
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.16)" stroke-width="{stroke}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{COLORS["brand_white"]}" stroke-width="{stroke}" '
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
            return _RENDIMIENTO_SOLID_COLOR[pace_name], _RENDIMIENTO_ICON.get(pace_name, "")
        if k == "md_pct":
            raw_pct = _donut_pct_raw(k)
            pace_name = _rend_color_conversion(raw_pct)
            return _RENDIMIENTO_SOLID_COLOR[pace_name], _RENDIMIENTO_ICON.get(pace_name, "")
        return fixed_color, ""

    donuts_html_parts = []
    for k, label, fixed_color in donut_specs:
        color, icon_svg = _donut_color_and_emoji(k, fixed_color)
        # Rediseño Rendimiento General (pedido explícito de Sabas, mockup
        # aprobado): con la card en fondo azul petróleo, el ícono de
        # ritmo (antes gris fijo, pensado para fondo blanco) pasa a
        # blanco -- mismo criterio que el resto de la card ("todo el
        # progreso se ve en blanco"). El color eléctrico por métrica
        # (_donut_color_and_emoji) ya no se usa para pintar nada acá --
        # se sigue calculando (queda disponible si se necesita en otro
        # lado) pero el % y el ícono dentro del donut ahora son blancos
        # fijos, no color.
        icon_html = (
            f'<div class="donut-emoji"><span class="lever-icon" style="width:14px;height:14px;color:{COLORS["brand_white"]};">{icon_svg}</span></div>'
            if icon_svg else ""
        )
        donuts_html_parts.append(
            f'<div class="donut-item">'
            f'<div class="donut-wrap">{_donut_svg(_donut_pct(k), color)}'
            f'<div class="donut-pct" style="color:{COLORS["brand_white"]};">{_donut_pct(k) * 100:.0f}%{icon_html}</div></div>'
            f'<div class="donut-label">{label}</div>'
            f'<div class="donut-count">{_donut_count_text(k)}</div>'
            f"</div>"
        )
    donuts_html = "".join(donuts_html_parts)
    st.markdown(
        '<div class="mgmt-card mgmt-card-dark">'
        f'<div class="mgmt-card-title"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_CONVERSION}</span>Brand Coverage · Live ({cov["total"]} marcas en cartera)</div>'
        f'<div class="donut-grid">{donuts_html}</div>'
        "</div>",
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
            f'<div class="cp-target-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_CONVERSION}</span>Target del mes: '
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

    # Pasteles dedicados de Contact Performance (pedido explícito de
    # Sabas, mockup aprobado) -- ver COLORS["cp_*"] en theme.py.
    cp_bar_html = (
        '<div class="cp-bar">'
        + _cp_seg(calls_pct, COLORS["cp_calls"])
        + _cp_seg(chats_pct, COLORS["cp_chats"])
        + _cp_seg(meets_pct, COLORS["cp_meets"])
        + _cp_seg(ghost_pct, COLORS["cp_ghost"])
        + "</div>"
    )
    legend_items = [
        (ICON_TELEFONO, "Amazon Connect", cp["calls"], calls_pct, COLORS["cp_calls"]),
        (ICON_CHAT, "WhatsApp", cp["chats"], chats_pct, COLORS["cp_chats"]),
        (ICON_MONITOR, "Meet", cp["meets"], meets_pct, COLORS["cp_meets"]),
        (ICON_FANTASMA, "No Contactado", cp["not_contacted"], ghost_pct, COLORS["cp_ghost"]),
    ]
    # Con la card en fondo azul petróleo (pedido explícito de Sabas,
    # mockup aprobado), el ícono y el conteo de cada ítem ya no pueden
    # ir en gris muted (pensado para fondo claro, invisible sobre azul
    # petróleo) -- pasan a blanco apagado. El nombre del ítem sigue
    # llevando su color pastel propio (cp_calls/cp_chats/cp_meets/
    # cp_ghost), que es lo que distingue cada segmento en la leyenda.
    legend_html = "".join(
        f'<div class="cp-legend-item"><div class="cp-legend-dot" style="background:{color};"></div>'
        f'<span class="lever-icon" style="margin-right:5px;vertical-align:-2px;width:13px;height:13px;color:rgba(252,250,248,0.75);">{icon_svg}</span>'
        f'<span style="color:{color};">{label}</span>'
        f'<span style="color:rgba(252,250,248,0.75);font-weight:600;">{n} · {pct}%</span></div>'
        for icon_svg, label, n, pct, color in legend_items
    )
    st.markdown(
        '<div class="mgmt-card mgmt-card-dark">'
        f'<div class="mgmt-card-title"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_TELEFONO}</span>Contact Performance · desde {month_label}</div>'
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
        "brand_finder": "Ficha de Marca",
        "comercial": "Rendimiento Comercial",
    }.get(section, "Rendimiento General")
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

        # Tabla Smart Priorities -- pedido explícito de Sabas (trigésima
        # tercera vuelta): "que esa primera ficha lleve el orden exacto
        # de Smart Priorities para cada uno de los farmers... brand ID,
        # brand name y el puntaje de prioridad... organizado en orden
        # descendente". Ver smart_priorities_for en data_layer.py para
        # de dónde sale el puntaje (fila Total de PRIORITY DATA, no un
        # cálculo propio -- el panel de pesos editable vive en otro
        # Excel fuera de este Wingman).
        #
        # Selector de Farmer para Supervisor (pedido explícito: "elegir
        # Farmer primero, como ya funciona en Rendimiento Comercial") --
        # mismo patrón de loader LOCAL ya usado en la sección comercial:
        # el selectbox va dentro de su propio st.container(key=...) para
        # que el JS pueda anclar el overlay parcial a su borde inferior
        # (ver LOCAL_TRIGGERS / onFarmerComboClick en
        # render_loading_watcher, extendido más abajo para reconocer
        # también "smartpri_farmer_anchor").
        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        if IS_SUPERVISOR:
            st.session_state.setdefault("supervisor_pais", "AR")
            with st.container(key="smartpri_mapa_anchor"):
                render_conosur_map()
            pais_smartpri = st.session_state["supervisor_pais"]
            farmers_pais = dl.farmers_por_pais(pais_smartpri)
            farmer_labels = {f: dl.farmer_display(f) for f in farmers_pais}
            if not farmers_pais:
                st.info("No hay Farmers con cartera activa en este país.")
                st.stop()
            with st.container(key="smartpri_farmer_anchor"):
                farmer_para_smartpri = st.selectbox(
                    "Farmer", farmers_pais, format_func=lambda f: farmer_labels.get(f, f),
                    key="smartpri_farmer_select",
                )
        else:
            farmer_para_smartpri = selected

        with st.container(key="smartpri_zona_tapable"):
            filas_sp = dl.smart_priorities_for(farmer_para_smartpri)
            st.markdown(
                '<div class="mgmt-card-title" style="margin:14px 0 8px;">'
                f'<span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_RENDIMIENTO}</span>'
                'Smart Priorities</div>',
                unsafe_allow_html=True,
            )
            if not filas_sp:
                st.info("No hay marcas con puntaje de Smart Priorities disponible para este Farmer.")
            else:
                # 7 columnas -- pedido explícito de Sabas (trigésima
                # cuarta vuelta, "el ID, el nombre, el puntaje, Ads,
                # Markdown y Churn", ampliado en la trigésima sexta:
                # "la última columna debe ser último contacto con la
                # fecha"). Ver smart_priorities_for en data_layer.py
                # para el criterio exacto de cada pill.
                cols_css = "1.2fr 2.4fr 0.8fr 1fr 1fr 1fr 1fr"
                header_html = (
                    f'<div style="display:grid;grid-template-columns:{cols_css};gap:8px;'
                    f'padding:0 4px 6px;font-size:10px;font-weight:700;color:{COLORS["muted"]};'
                    'text-transform:uppercase;">'
                    '<span>ID</span><span>Nombre</span><span>Puntaje</span>'
                    '<span>Ads</span><span>Markdown</span><span>Churn</span>'
                    '<span>Último contacto</span></div>'
                )
                st.markdown(
                    f'<div style="border:1px solid {COLORS["card2"]};border-radius:12px 12px 0 0;'
                    f'border-bottom:none;padding:10px 12px 0;">{header_html}</div>',
                    unsafe_allow_html=True,
                )
                # Lista liviana (solo id+nombre) para armar el botón "ver
                # también" de la siguiente marca en la Ficha de Marca
                # (pedido explícito, misma vuelta: "en la otra esquina...
                # el ID y el nombre de la siguiente marca... me voy
                # preparando para ver cuál es la marca que sigue") -- va
                # en volver_a en vez de recalcular smart_priorities_for
                # de nuevo dentro de la Ficha, y sin duplicar puntaje/
                # ads/md/churn ahí, que la Ficha no necesita mostrar.
                orden_ids = [{"id": f["id"], "nombre": f["nombre"]} for f in filas_sp]

                # Pills de estado -- función LOCAL propia (no
                # _pill_estado de _render_funnel_comercial: esa vive
                # anidada en el scope de esa función, con su propio
                # color_estado mapeado SOLO a los 6 estados del funnel
                # comercial -- Contactado/Cerrado/etc; ninguno de esos
                # nombres coincide con Adquisición/Upselling/Reajuste/
                # Seguimiento/PW1/Churn/Tienda activa de esta tabla, así
                # que reusarla habría caído siempre en su gris por
                # defecto). Semántica de color: Adquisición = oportunidad
                # (acento marca), Upselling/Reajuste/PW1 = atención
                # (warning), Churn = riesgo (danger), Seguimiento/Tienda
                # activa = neutro/positivo.
                _smartpri_colores = {
                    "Adquisición": (COLORS["brand_orange_soft"], COLORS["brand_orange"]),
                    "Upselling": (COLORS["warning_soft"], "#92650A"),
                    "Reajuste": (COLORS["warning_soft"], "#92650A"),
                    "PW1": (COLORS["warning_soft"], "#92650A"),
                    "PW2": (COLORS["warning_soft"], "#92650A"),
                    "PW3": (COLORS["warning_soft"], "#92650A"),
                    "Churn": (COLORS["danger_soft"], COLORS["danger"]),
                    "Tienda activa": (COLORS["success_soft"], "#15803D"),
                    "Seguimiento": (COLORS["card2"], COLORS["muted"]),
                }

                def _pill_smartpri(valor):
                    bg, fg = _smartpri_colores.get(valor, (COLORS["card2"], COLORS["muted"]))
                    return (
                        f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:800;'
                        f'padding:3px 10px;border-radius:999px;display:inline-block;white-space:nowrap;">'
                        f'{html_lib.escape(str(valor))}</span>'
                    )

                with st.container(key="smartpri_tabla", height=520, border=True):
                    for idx, f in enumerate(filas_sp):
                        row_cols = st.columns([1.2, 2.4, 0.8, 1, 1, 1, 1])
                        with row_cols[0]:
                            with st.container(key=f"smartpri_row_{idx}"):
                                if st.button(f["id"], key=f"smartpri_row_btn_{idx}"):
                                    go_to_brand(
                                        f["id"],
                                        volver_a={
                                            "section": "brand_finder",
                                            "orden": orden_ids,
                                            "pos": idx,
                                        },
                                    )
                        with row_cols[1]:
                            st.markdown(
                                f'<div style="font-size:12px;padding-top:2px;">{html_lib.escape(f["nombre"])}</div>',
                                unsafe_allow_html=True,
                            )
                        with row_cols[2]:
                            st.markdown(
                                f'<div style="font-size:12px;font-weight:800;padding-top:2px;">{f["puntaje"]:,.0f}</div>'.replace(",", "."),
                                unsafe_allow_html=True,
                            )
                        with row_cols[3]:
                            st.markdown(f'<div style="padding-top:2px;">{_pill_smartpri(f["ads"])}</div>', unsafe_allow_html=True)
                        with row_cols[4]:
                            st.markdown(f'<div style="padding-top:2px;">{_pill_smartpri(f["md"])}</div>', unsafe_allow_html=True)
                        with row_cols[5]:
                            st.markdown(f'<div style="padding-top:2px;">{_pill_smartpri(f["churn"])}</div>', unsafe_allow_html=True)
                        with row_cols[6]:
                            st.markdown(
                                f'<div style="font-size:12px;color:{COLORS["muted"]};padding-top:2px;">{html_lib.escape(f["ultimo_contacto"])}</div>',
                                unsafe_allow_html=True,
                            )

    elif section == "comercial":
        # Selector de Farmer para Supervisor -- mismo patrón que ya usa
        # Rendimiento General (render_conosur_map + farmers_por_pais).
        #
        # Anchors de loader LOCAL (pedido explícito de Sabas, trigésima
        # vuelta): "cambiar tab Ads/MD", "cambiar país del Supervisor" y
        # "cambiar Farmer del Supervisor" NO deben disparar el overlay de
        # pantalla completa (ese se reserva para click en ID de marca y
        # el botón Volver) -- deben tapar solo la franja de abajo, sin
        # cubrir el control que el usuario acaba de tocar. Se envuelve
        # cada control disparador en su propio st.container(key=...) para
        # que el JS pueda medir su borde inferior real (mismo mecanismo
        # que ya usa el sidebar completo vía getBoundingClientRect), y
        # TODO lo que debe quedar tapado (desde ese punto hacia abajo)
        # vive dentro de comercial_zona_tapable, un único contenedor real
        # que el overlay local usa como referencia de ancho/alto/left.
        if IS_SUPERVISOR:
            st.session_state.setdefault("supervisor_pais", "AR")
            with st.container(key="comercial_mapa_anchor"):
                render_conosur_map()

        with st.container(key="comercial_zona_tapable"):
            if IS_SUPERVISOR:
                pais_comercial = st.session_state["supervisor_pais"]
                farmers_pais = dl.farmers_por_pais(pais_comercial)
                farmer_labels = {f: dl.farmer_display(f) for f in farmers_pais}
                if not farmers_pais:
                    st.info("No hay Farmers con cartera activa en este país.")
                    st.stop()
                with st.container(key="comercial_farmer_anchor"):
                    farmer_para_funnel = st.selectbox(
                        "Farmer", farmers_pais, format_func=lambda f: farmer_labels.get(f, f),
                        key="comercial_farmer_select",
                    )
            else:
                farmer_para_funnel = selected

            # Tabs propios con botones, NO st.tabs() nativo -- st.tabs() no
            # expone un key que persista cuál está activo entre reruns, y
            # necesitamos recordarlo para el botón Volver de la Ficha de
            # Marca (pedido explícito: "que quede en el MISMO bloque del
            # funnel que tenía antes").
            with st.container(key="comercial_tabs_anchor"):
                tcol1, tcol2 = st.columns(2)
                with tcol1:
                    if st.button("Ads", key="comercial_tab_btn_ads", use_container_width=True,
                                 type="primary" if st.session_state["comercial_tab_activo"] == "ads" else "secondary"):
                        st.session_state["comercial_tab_activo"] = "ads"
                        st.rerun()
                with tcol2:
                    if st.button("Markdown", key="comercial_tab_btn_md", use_container_width=True,
                                 type="primary" if st.session_state["comercial_tab_activo"] == "md" else "secondary"):
                        st.session_state["comercial_tab_activo"] = "md"
                        st.rerun()

            st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)

            with st.container(key="comercial_funnel_zona"):
                if st.session_state["comercial_tab_activo"] == "ads":
                    _render_funnel_comercial("ads", farmer_para_funnel)
                else:
                    _render_funnel_comercial("md", farmer_para_funnel)


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
                f'<span class="lever-icon" style="width:13px;height:13px;margin-right:5px;vertical-align:-2px;">{ICON_PIN}</span>{pais_label}</div>',
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

# ── Franja fija: Nombre, ID centrados + los 5 datos (Teléfono, Correo,
# Categoría, Buscar en Google, Estado de conexión) en una sola fila
# centrada -- rediseño décima primera/segunda vuelta, pedido explícito
# de Sabas, aprobado como mockup visual antes de escribir el código: el
# Estado de Churn (ahora "Estado de conexión") deja de ser una pill
# aparte arriba de los datos de contacto y pasa a ser un dato más de la
# misma fila. Segunda vuelta: más espacio entre columnas, título/ID más
# grandes, ID con guión separando letras de números, "Local" renombrado
# a "Buscar en Google" con solo el ícono de lupa como link (antes decía
# "Buscar" en texto). ──
tel_btn_id, telefono_copy = (_copy_button_html(row.telefono) if row.telefono else (None, ""))

# ID con guión + microzonas -- pedido explícito de Sabas (vigésima
# segunda vuelta): "AR16516" -> "AR-16516", y ahora se le agregan las
# microzonas de todas las tiendas de la marca, limpias y deduplicadas,
# unidas con "/" ("AR-16516 / Balvanera/Once"). Si la marca no tiene
# ninguna microzona conocida (no está en PITCHDATA), se muestra solo el
# ID, igual que antes.
_id_match = re.match(r"^([A-Za-z]+)(\d+)$", str(row.brand_id or "").strip())
brand_id_display = f"{_id_match.group(1)}-{_id_match.group(2)}" if _id_match else row.brand_id

pitch_info = dl.pitchdata_for_brand(row.key)
if pitch_info["microzonas_texto"]:
    brand_id_display = f'{brand_id_display} / {pitch_info["microzonas_texto"]}'

# Estado de conexión (antes "Estado de Churn") -- mismo criterio de
# color por severidad que ya existía, solo cambia el label visible y el
# lugar donde se muestra.
churn_class = {
    "Disponible": "ok", "PW1": "warn", "PW2": "warn", "PW3": "alert", "Churn": "alert",
}.get(row.churn_status, "info")
churn_icon = "✅" if row.churn_status == "Disponible" else "⚠️"

# Cabecera de 6 ítems (antes 5) -- pedido explícito de Sabas (vigésima
# segunda vuelta):
#   1. Estado de Conexión -- sin cambios.
#   2. Teléfono -- sin cambios (sigue siendo el de ASIGNACION).
#   3. ENCARGADO (nuevo, reemplaza a Correo) -- nombre de contacto de la
#      tienda de referencia (ver pitchdata_for_brand/tienda_referencia_for).
#      El correo de ASIGNACION NO desaparece del todo -- se muda a la
#      barra de Outreach junto con los correos/teléfonos adicionales.
#   4. Categoría -- sin cambios.
#   5. CONEXIÓN / ÓRDENES (nuevo) -- ✅ si <72h, 🚨 si >72h, "-" sin dato,
#      de la tienda de referencia.
#   6. GOOGLE / RAPPI (reemplaza a "Buscar en Google") -- 🔎 abre Google
#      (igual que antes), 🔗 abre el Link Tienda de la tienda de
#      referencia (si no hay link, el ícono no es clickeable).
search_url = dl.google_search_url(row.brand_name, row.categoria, row.ciudad)
link_rappi = pitch_info["link"]
# Íconos SVG propios (G de Google, R de Rappi) en vez de los emojis
# nativos 🔎/🔗 -- pedido explícito de Sabas, mockup aprobado: mismo
# lenguaje visual que el resto de la app, no depende del render del
# emoji por dispositivo/SO. vertical-align:middle centra el ícono
# respecto al "/" separador y al resto del texto de la fila.
_icon_link_style = "display:inline-flex;vertical-align:middle;width:18px;height:18px;"
link_html = (
    f'<a href="{link_rappi}" target="_blank" rel="noopener noreferrer" '
    f'title="Abrir en Rappi" aria-label="Abrir en Rappi" '
    f'style="text-decoration:none;{_icon_link_style}">{ICON_RAPPI}</a>'
    if link_rappi else
    f'<span style="opacity:0.3;{_icon_link_style}" title="Sin link disponible">{ICON_RAPPI}</span>'
)
google_html = (
    f'<a href="{search_url}" target="_blank" rel="noopener noreferrer" '
    f'title="Buscar en Google" aria-label="Buscar en Google" '
    f'style="text-decoration:none;{_icon_link_style}">{ICON_GOOGLE}</a>'
)

contact_html = (
    '<div class="brand-stats-row">'
    f'<div><div class="stat-label">ESTADO DE CONEXIÓN</div>'
    f'<div class="conn-status-pill {churn_class}">{churn_icon} {row.churn_status}</div></div>'
    f'<div><div class="stat-label">TELÉFONO</div><div class="stat-value">{row.telefono or "?"}{telefono_copy}</div></div>'
    f'<div><div class="stat-label">ENCARGADO</div><div class="stat-value" style="font-size:13px;">{pitch_info["encargado"] or "?"}</div></div>'
    f'<div><div class="stat-label">CATEGORÍA</div><div class="stat-value">{row.categoria or "?"}</div></div>'
    f'<div><div class="stat-label">CONEXIÓN / ÓRDENES</div><div class="stat-value">'
    f'{pitch_info["conexion_icono"]} / {pitch_info["ordenes_icono"]}</div></div>'
    f'<div><div class="stat-label">GOOGLE / RAPPI</div><div class="stat-value">'
    f'{google_html} / {link_html}</div></div>'
    "</div>"
)

# Botón "Volver" -- pedido explícito de Sabas (vigésima octava vuelta
# para Rendimiento Comercial, extendido en la trigésima tercera vuelta a
# Smart Priorities / Ficha de Marca: "seleccionar la segunda, vuelvo a
# ficha de marca, luego vuelvo"): solo aparece si se llegó acá desde una
# tabla con volver_a (go_to_brand) -- al presionarlo, restaura la
# SECCIÓN Y EL ESTADO exactos que tenía antes del click en el ID, no
# solo vuelve a la pantalla de aterrizaje genérica como go_to_landing().
# "section" en volver_a decide a cuál de las dos restaurar -- el llamado
# ya existente en _render_funnel_comercial no manda "section" (siempre
# fue comercial), así que el default aquí preserva ese comportamiento
# sin tocar ese llamado.
#
# El botón espejo de "siguiente marca" que existió acá (esquina derecha,
# "AR123 · Nombre →") se RETIRÓ por pedido explícito de Sabas (trigésima
# quinta vuelta: "en la parte de Home, elimina ese botón... dejémoslo
# solo en el volver a ficha de marca, solamente ese botón") -- go_to_brand
# sigue aceptando "orden"/"pos" en volver_a (lo manda smart_priorities al
# armar cada fila) por si se retoma más adelante, pero ya no se lee ni se
# renderiza nada con esas dos claves.
_volver_a = st.session_state.get("volver_a")
if _volver_a:
    _volver_section = _volver_a.get("section", "comercial")
    if _volver_section == "brand_finder":
        if st.button("← Volver a Ficha de Marca", key="btn_volver_comercial"):
            st.session_state["view"] = "landing"
            st.session_state["section"] = "brand_finder"
            st.session_state.pop("volver_a", None)
            st.rerun()
    else:
        if st.button("← Volver a Rendimiento Comercial", key="btn_volver_comercial"):
            st.session_state["view"] = "landing"
            st.session_state["section"] = "comercial"
            st.session_state["comercial_tab_activo"] = _volver_a.get("tab", "ads")
            st.session_state["comercial_ads_vista"] = _volver_a.get("vista_ads", "base")
            st.session_state["comercial_md_vista"] = _volver_a.get("vista_md", "base")
            st.session_state.pop("volver_a", None)
            st.rerun()

# Ícono de categoría como "primera letra" del título -- rediseño décima
# tercera vuelta, pedido explícito de Sabas, aprobado como mockup visual
# antes de escribir el código: el círculo con el dibujo de la categoría
# (Peruana, Asado, Sushi, etc. -- ver icon_categoria_for en theme.py) ya
# no va junto al dato "CATEGORÍA" de la fila de abajo (que ahora es solo
# texto plano) -- pasa a ir INMEDIATAMENTE antes del nombre de la marca,
# ambos centrados como un solo bloque, como si el ícono fuera la
# primera letra del título.
#
# Último contacto (pedido explícito de Sabas, trigésima quinta vuelta:
# "en la esquina superior derecha de la carta de cabecera... en
# chiquitico en gris... 9 de septiembre del 2026") -- se arma como una
# tercera columna dentro de la misma fila flex que ya centraba
# ícono+título (antes solo 1 bloque centrado; ahora ese bloque central
# convive con un espaciador a la izquierda y el texto de la fecha a la
# derecha, para no romper el centrado del título). Se omite el bloque
# entero (ver fmt_fecha_es) si la marca no tiene ninguna fecha
# registrada en Priority Data -- nunca se muestra la etiqueta con un
# valor vacío al lado.
_ultimo_contacto_txt = dl.fmt_fecha_es(dl.ultimo_contacto_for(row.key))
_ultimo_contacto_html = (
    f'<div style="font-size:11px;color:rgba(252,250,248,0.65);white-space:nowrap;">'
    f'Último contacto: {_ultimo_contacto_txt}</div>'
    if _ultimo_contacto_txt else ""
)

brand_title_html = (
    '<div style="display:flex;align-items:center;">'
    '<div style="flex:1;"></div>'
    '<div style="display:flex;align-items:center;justify-content:center;gap:16px;">'
    f'<div style="width:52px;height:52px;border-radius:50%;background:{COLORS["brand_orange"]};color:{COLORS["brand_white"]};'
    f'display:flex;align-items:center;justify-content:center;flex-shrink:0;padding:11px;box-sizing:border-box;">'
    f'{icon_categoria_for(row.categoria)}'
    f'</div>'
    f'<div class="brand-title" style="margin-bottom:0;">{row.brand_name}</div>'
    f'</div>'
    f'<div style="flex:1;display:flex;justify-content:flex-end;align-items:center;">{_ultimo_contacto_html}</div>'
    f'</div>'
)

st.markdown(
    f'<div class="brand-sticky">'
    f"{brand_title_html}"
    f'<div class="brand-id">{brand_id_display}</div>'
    f"{contact_html}"
    f"</div>",
    unsafe_allow_html=True,
)
if tel_btn_id:
    _render_copy_script(row.telefono, tel_btn_id)

tab_home, tab_action, tab_analytics, tab_campaign, tab_outreach = st.tabs(
    ["Home", "360° Action", "Analytics", "Campaign Designer", "Outreach"]
)


# ── TAB: HOME ──
with tab_home:
    if row.gmv > 0:
        # 3 cards -- Órdenes, AOV, GMV, en ese orden (pedido explícito de
        # Sabas, septiembre 2026, cuarta vuelta: antes "Órdenes" era una
        # sub-línea dentro de la card de GMV; ahora tiene su propia card
        # con el mismo sparkline de 3 meses reales que GMV/AOV, usando
        # ordenes_last/ordenes_prev2 -- misma hoja LAST GMV/PREVIOUS GMV,
        # que ya traía la columna Ordenes sin usarla desde acá).
        g1, g2, g3 = st.columns(3)
        with g1:
            fmt_ordenes = lambda v: f'{v:,.0f} órdenes'.replace(",", ".")
            # fmt_spark_fn solo-número (sin la palabra "órdenes") -- pedido
            # explícito de Sabas (septiembre 2026, quinta vuelta): el pie
            # del sparkline necesita quedar corto para que quepa en 1/3
            # de card.
            fmt_ordenes_spark = lambda v: f'{v:,.0f}'.replace(",", ".")
            st.markdown(
                metric_trend_card(ICON_ORDENES, "ÓRDENES", row.ordenes, row.ordenes_delta,
                                   "Órdenes del mes", prev=row.ordenes_last, prev2=row.ordenes_prev2,
                                   fmt_fn=fmt_ordenes, fmt_spark_fn=fmt_ordenes_spark, es_ritmo=True),
                unsafe_allow_html=True,
            )
        with g2:
            st.markdown(
                metric_trend_card(ICON_AOV, "AOV", row.aov, row.aov_delta,
                                   "Ticket promedio", prev=row.aov_last, prev2=row.aov_prev2,
                                   currency=CURRENCY,
                                   fmt_spark_fn=lambda v: dl.fmt_money_compact(v, CURRENCY)),
                unsafe_allow_html=True,
            )
        with g3:
            st.markdown(
                metric_trend_card(ICON_GMV, "GMV (mes)", row.gmv, row.gmv_delta,
                                   "Facturación bruta del mes", prev=row.gmv_last, prev2=row.gmv_prev2,
                                   currency=CURRENCY, es_ritmo=True,
                                   fmt_spark_fn=lambda v: dl.fmt_money_compact(v, CURRENCY)),
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
    md_copy = f"Campaign {md_camp or '-'}" if row.markdown_md > 0 else "Sin promo activa este mes"
    md_badge = None
    if row.markdown_md > 0:
        pen_color = COLORS["success"] if row.penetracion_md >= 0.10 else COLORS["danger"]
        md_badge = (f"Penetración {row.penetracion_md * 100:.1f}%", pen_color)

    pro_txt, _ = state_text(row.markdown_mdpro > 0)
    pro_camp = row.campaign_mdpro if row.campaign_mdpro and row.campaign_mdpro != "-" else ""
    pro_copy = f"Campaign {pro_camp or '-'}" if row.markdown_mdpro > 0 else "Sin promo activa este mes"
    pro_badge = None
    if row.markdown_mdpro > 0:
        pen_color = COLORS["success"] if row.penetracion_mdpro >= 0.10 else COLORS["danger"]
        pro_badge = (f"Penetración {row.penetracion_mdpro * 100:.1f}%", pen_color)

    st.markdown(
        '<div class="business-card-grid">'
        + mini_card("ADS", ads_txt, ads_copy,
                    "ads", ads_chip, COLORS["accent"], corner_badge=ads_badge, active=row.bookings > 0)
        + mini_card("MARKDOWN", md_txt, md_copy, "md",
                    dl.fmt_roi(row.roi_md) if row.roi_md > 0 else "", COLORS["blue"], corner_badge=md_badge, active=row.markdown_md > 0)
        + mini_card("MARKDOWN PRO", pro_txt, pro_copy, "pro",
                    dl.fmt_roi(row.roi_mdpro) if row.roi_mdpro > 0 else "", COLORS["success"], corner_badge=pro_badge, active=row.markdown_mdpro > 0)
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
        f'<span class="action-lever-pill">{lb} <span class="action-lever-pill-value">{v:.2f}</span></span>'
        for lb, v in pmap.get(row.key, [])
    )
    # Top Res movido acá (vigésima tercera vuelta, pedido explícito de
    # Sabas): antes eran 2 líneas dentro de la card de OPS General, ahora
    # es UNA pill en la esquina derecha de esta barra de contexto (mismo
    # estilo que las pills de palanca), con los 2 meses apilados uno
    # encima del otro DENTRO de la misma pill blanca -- no 2 pills
    # separadas. margin-left:auto empuja esta pill sola hasta el borde
    # derecho de la card, separada del resto de pills de palanca.
    _top_res = pitch_info["top_res"]
    top_res_pill = (
        '<span class="action-lever-pill" style="margin-left:auto;flex-direction:column;'
        'align-items:flex-start;gap:2px;line-height:1.5;">'
        f'<span>{_top_res["icono_anterior"]} TOP RES {_top_res["mes_anterior"] or "ANT."}: '
        f'<span class="action-lever-pill-value">{_top_res["tier_anterior"]}</span></span>'
        f'<span>{_top_res["icono_actual"]} TOP RES {_top_res["mes_actual"] or "ACT."}: '
        f'<span class="action-lever-pill-value">{_top_res["tier_actual"]}</span></span>'
        "</span>"
    )
    st.markdown(
        f'<div class="action-context-card">'
        f'<div class="action-context-label-block">'
        f'<div class="action-mini-label">Coinversión MD</div>'
        f'<div class="action-mini-value">{row.coinv_md_label}</div></div>'
        f'<div class="action-context-pills">{lever_pills}</div>'
        f"{top_res_pill}"
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

    def _tag_border_class(tag):
        # Clase de la barra superior de la card segun estado -- rediseño
        # septiembre 2026, pedido explícito de Sabas: las 4 cards pasan
        # de fondo pastel completo a fondo blanco + barra superior de
        # color (mismo semáforo que antes, ahora solo como acento).
        return {
            "HEALTHY": "action-card-healthy", "WATCH": "action-card-watch",
            "ALERT": "action-card-alert", "INACTIVE": "action-card-inactive",
        }[tag]

    def _bullet_icon_for_estado(estado):
        # Ícono dentro del bullet según estado -- séptima vuelta, pedido
        # explícito de Sabas: ALERT -> triángulo de warning, WATCH -> ojo,
        # HEALTHY -> chulito.
        #
        # Fix (misma sesión, octava vuelta -- pedido explícito de Sabas):
        # estado None ("Cancelaciones — sin alerta presente", "Tiempo de
        # espera — sin alerta presente") también lleva CHULITO, no el
        # punto simple -- confirmado explícitamente: "sin alerta
        # presente" ES estar sano (no hay fila en Priority Data para esa
        # métrica, pero eso significa que no hay problema reportado, así
        # que cuenta como saludable). El punto simple queda sin uso real
        # hoy (ningún estado actual lo dispara), pero se mantiene el
        # fallback por si en el futuro aparece un estado genuinamente
        # distinto de los 3 conocidos.
        if estado == "ALERT":
            return ICON_BULLET_WARNING
        if estado == "WATCH":
            return ICON_BULLET_EYE
        if estado in ("HEALTHY", None):
            return ICON_BULLET_CHECK
        return None

    def _bullet_html(estado, icon_purple):
        base_class = "action-bullet icon-purple" if icon_purple else "action-bullet"
        icon_svg_bullet = _bullet_icon_for_estado(estado)
        if icon_svg_bullet:
            return f'<span class="{base_class} has-icon">{icon_svg_bullet}</span>'
        return f'<span class="{base_class}"></span>'

    def _action_mini(icon_svg, name, pct, tag, title, detail, items=None, icon_purple=False, top_res_html="", extra_items=None):
        color = _tag_color(tag)
        border_class = _tag_border_class(tag)
        icon_class = "action-card-icon icon-purple" if icon_purple else "action-card-icon"
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
        #
        # Bullet circular (sexta vuelta, pedido explícito de Sabas): cada
        # item de OPS/Menú y el title de Markdown/Ads llevan un bullet
        # circular monocromático (gris u "icon_purple" según la card),
        # reemplazando el emoji Unicode que antes iba concatenado al
        # texto en data_layer.py.
        #
        # Negrita condicional (séptima vuelta, pedido explícito de
        # Sabas): cada item ahora es (texto, estado) en vez de solo
        # texto -- ALERT/WATCH van en negrita ("action-card-item-alert",
        # lo importante), HEALTHY/None (sin alerta, "sin alerta
        # presente"/"Métrica sana y competitiva") van en texto normal
        # ("action-card-item-normal"), igual peso que el Insight de
        # Markdown/Ads.
        #
        # Ícono dentro del bullet (séptima vuelta, misma sesión, pedido
        # explícito de Sabas): el punto simple se reemplaza por
        # warning/eye/check según el estado -- tanto en cada item de
        # OPS/Menú como en el bullet único de Markdown/Ads (ahí no hay
        # "items", se usa el `tag` general de la card completa).
        if items:
            item_divs = []
            for item_texto, item_estado in items:
                peso_class = (
                    "action-card-item-alert"
                    if item_estado in ("ALERT", "WATCH")
                    else "action-card-item-normal"
                )
                item_divs.append(
                    f'<div class="action-card-item {peso_class}">'
                    f'{_bullet_html(item_estado, icon_purple)}{item_texto}</div>'
                )
            cuerpo_html = "".join(item_divs)
        else:
            cuerpo_html = (
                f'<div class="action-card-title">{_bullet_html(tag, icon_purple)}{title}</div>'
                f'<div class="action-card-detail">{detail}</div>'
            )
            # extra_items (pedido explícito de Sabas, trigésima sexta
            # vuelta, corrigiendo el diseño anterior: "promos por vencer
            # debe ser otro ítem también, no debe ser un ítem completo
            # para las dos... lo único que va en negrita es el título...
            # los números de los códigos van en gris normal, sin
            # negrita"): lista de ítems EXTRA debajo del title/detail
            # normal de Markdown, SIN reemplazarlos (a diferencia de
            # "items", que sí reemplaza -- ese mecanismo es el que ya
            # usan OPS/Menú, donde no hay title/detail separados que
            # conservar). Cada ítem es (titulo, contenido, estado) -- 3
            # elementos, no 2 -- porque acá el peso SIEMPRE difiere
            # dentro del mismo ítem (título en negrita, contenido en
            # normal), a diferencia del resto de la app donde todo el
            # texto del ítem entra o sale de negrita junto según su
            # estado. El bullet (warning/ojo/chulito) usa el estado de
            # ESE ítem puntual, no el tag general de la card.
            if extra_items:
                for item_titulo, item_contenido, item_estado in extra_items:
                    contenido_html = f': {item_contenido}' if item_contenido else ''
                    cuerpo_html += (
                        f'<div class="action-card-item">'
                        f'{_bullet_html(item_estado, icon_purple)}'
                        f'<span class="action-card-item-alert">{item_titulo}</span>'
                        f'<span class="action-card-item-normal">{contenido_html}</span>'
                        f'</div>'
                    )
        return (
            f'<div class="action-card {border_class}">'
            f'<div class="action-card-head"><span class="{icon_class}">{icon_svg}</span></div>'
            f"{pct_html}"
            f'<div class="action-card-name">{name}</div>'
            f'<span class="gauge-tag {tag_class}">{tag}</span>'
            f"{top_res_html}"
            f"{cuerpo_html}"
            f"</div>"
        )

    # Ícono morado fijo para Markdown/Ads (palancas comerciales activables),
    # gris fijo para OPS/Menú (señales operativas) -- así se ve en la
    # imagen de referencia de Sabas, independiente del tag ALERT/HEALTHY.
    #
    # Top Res YA NO va acá (vigésima tercera vuelta, pedido explícito de
    # Sabas: "eso vamos a transportarlo a una sola pill en la barra
    # horizontal de arriba") -- se movió a la barra de contexto (ver
    # top_res_pill, más arriba en este mismo tab), como una pill más
    # apilada en 2 líneas en la esquina derecha. _action_mini conserva el
    # parámetro top_res_html (default "") por si se reutiliza en el
    # futuro, pero ya no se le pasa nada desde acá.
    st.markdown(
        '<div class="action-grid">'
        + _action_mini(ICON_OPS, "OPS General", ops["pct"], ops["tag"], ops["title"], ops["detail"], items=ops.get("items"))
        + _action_mini(ICON_MENU, "Menú", menu["pct"], menu["tag"], menu["title"], menu["detail"], items=menu.get("items"))
        + _action_mini(ICON_MARKDOWN, "Markdown", None, md_c["tag"], md_c["title"], md_c["detail"], extra_items=md_c.get("items"))
        + _action_mini(ICON_ADS_LEVER, "Ads", None, ads_c["tag"], ads_c["title"], ads_c["detail"])
        + "</div>",
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
    # ── Funnel: escalones (rectángulos redondeados) centrados entre sí,
    # como un embudo -- rediseño septiembre 2026, novena vuelta, pedido
    # explícito de Sabas. Los COLORES semánticos por estado (morado fijo
    # la baldosa 1, rojo/verde según traffic_above_bench la 2, azul/gris
    # según cvr_above_bench la 3) se mantienen igual -- confirmado
    # explícitamente que NO pasan al degradado morado→naranja fijo de la
    # referencia visual.
    #
    # Alineación bullet-barra (misma vuelta, mismo pedido): la leyenda ya
    # NO es un bloque HTML aparte con su propio flujo de texto (que podía
    # desalinearse verticalmente del SVG por casualidad de alturas) --
    # ahora se posiciona con position:absolute + top calculado con las
    # MISMAS coordenadas Y que usa cada barra del SVG, así el bullet de
    # cada nivel queda garantizado a la altura exacta del centro de su
    # barra, sin depender de que ambos bloques midan igual por suerte.
    total_w = 280
    level_h = 28
    gap = 6
    funnel_svg_parts = ['<svg viewBox="0 0 320 130" width="100%" height="130" style="max-width:280px;display:block;">']
    funnel_legend_parts = []
    y = 4
    for label, val, color, width_pct, texto_interno in levels:
        w = total_w * (width_pct / 100)
        bar_x = 20 + (total_w - w) / 2
        funnel_svg_parts.append(
            f'<rect x="{bar_x:.0f}" y="{y}" width="{w:.0f}" height="{level_h}" rx="8" '
            f'fill="{color}" opacity="0.9"/>'
        )
        if texto_interno:
            cx = bar_x + w / 2
            cy = y + level_h / 2 + 4
            funnel_svg_parts.append(
                f'<text x="{cx:.0f}" y="{cy:.0f}" text-anchor="middle" '
                f'font-size="11" font-weight="700" fill="white">{texto_interno}</text>'
            )
        label_color = conv_label_color if label == "Conversión de la marca" else COLORS["muted"]
        val_color = conv_label_color if label == "Conversión de la marca" else COLORS["text"]
        top_pct = (y + level_h / 2) / 130 * 100
        funnel_legend_parts.append(
            f'<div style="position:absolute;top:{top_pct:.1f}%;left:0;transform:translateY(-50%);'
            f'display:flex;align-items:center;gap:6px;white-space:nowrap;">'
            f'<span style="width:9px;height:9px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0;"></span>'
            f'<span style="font-size:10.5px;color:{label_color};">'
            f'{label}: <b style="color:{val_color};">{val}</b></span>'
            f'</div>'
        )
        y += level_h + gap
    funnel_svg_parts.append("</svg>")
    funnel_svg = "".join(funnel_svg_parts)
    funnel_legend = (
        '<div style="position:relative;height:130px;min-width:180px;">'
        + "".join(funnel_legend_parts)
        + "</div>"
    )

    # ── Comparativo vs mes anterior (Tráfico arriba / Conversión abajo) ──
    # Nuevo (septiembre 2026, pedido explícito de Sabas): la otra mitad de
    # la super-card, junto al funnel. Usa cvr_delta/traffic_delta -- la
    # columna "vs LM (%)" que las hojas CVR%/TRAFFIC ya traían y portfolio_
    # for() ya cargaba en row.cvr_delta/row.traffic_delta, pero que hasta
    # ahora ningún lugar de la UI mostraba. "Mes anterior" es tal cual lo
    # que diga esa columna del Excel (LM = Last Month respecto al mes que
    # esa hoja tenga cargado) -- no se valida ni se muestra qué mes
    # calendario es, decision explicita de Sabas.
    def _mini_delta_bar(icon, label, valor_disp, delta_frac, tiene_dato, valor_anterior_disp="", incremental_texto=""):
        if not tiene_dato:
            return (
                f'<div class="mini-delta-row">'
                f'<div class="mini-delta-head"><span><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{icon}</span>{label}</span>'
                f'<span class="mini-delta-val">s/d</span></div>'
                f'<div class="mini-delta-sub">Sin dato para comparar.</div>'
                f"</div>"
            )
        color = COLORS["success"] if delta_frac >= 0 else COLORS["danger"]
        arrow = "▲" if delta_frac >= 0 else "▼"
        # Barra: 50% = sin cambio: crece a la derecha si sube, a la
        # izquierda si baja, con +-50% como magnitud maxima visual (un
        # cambio mayor solo satura la barra, no la desborda).
        pct_visual = max(-50, min(50, delta_frac * 100))
        bar_w = abs(pct_visual)
        bar_left = 50 if delta_frac >= 0 else 50 - bar_w
        # Subtitulo: agosto 2026 solo mostraba "245/sem actual · vs mes
        # anterior", sin decir cuanto fue el mes anterior -- pedido
        # explicito de Sabas (septiembre 2026): agregar el valor anterior
        # calculado (ver dl.incremental_vs_mes_anterior).
        sub = f"{valor_disp} actual"
        if valor_anterior_disp:
            sub += f" · {valor_anterior_disp} mes anterior"
        incremental_html = (
            f'<div class="mini-delta-incremental">{incremental_texto}</div>' if incremental_texto else ""
        )
        return (
            f'<div class="mini-delta-row">'
            f'<div class="mini-delta-head"><span><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{icon}</span>{label}</span>'
            f'<span class="mini-delta-val" style="color:{color};">{arrow} {abs(delta_frac) * 100:.0f}%</span></div>'
            f'<div class="mini-delta-track">'
            f'<div class="mini-delta-mid"></div>'
            f'<div class="mini-delta-fill" style="left:{bar_left:.1f}%;width:{bar_w:.1f}%;background:{color};"></div>'
            f"</div>"
            f'<div class="mini-delta-sub">{sub}</div>'
            f"{incremental_html}"
            f"</div>"
        )

    # Incremental vs mes anterior (septiembre 2026, pedido explicito de
    # Sabas): "cuanto hubieramos tenido en pedidos si no hubieramos
    # perdido ese trafico/esa conversion" -- espejo de los insights del
    # Funnel (_incremental_por_trafico/_incremental_por_cvr), pero contra
    # el mes anterior en vez del benchmark de categoria.
    inc = dl.incremental_vs_mes_anterior(row.traffic, row.traffic_delta, row.cvr, row.cvr_delta, row.aov, row.ordenes)

    traffic_anterior_disp = (
        f"{inc['traffic_anterior']:,.0f}".replace(",", ".") + "/sem" if inc["traffic_anterior"] > 0 else ""
    )
    cvr_anterior_disp = f"{inc['cvr_anterior'] * 100:.1f}%" if inc["cvr_anterior"] > 0 else ""

    traffic_incremental_txt = (
        f"Si no hubieras perdido tráfico, ~{round(inc['pedidos_trafico'])} pedidos más "
        f"({dl.fmt_money(round(inc['gmv_trafico']), CURRENCY)}) este mes."
        if inc["gmv_trafico"] > 0 else ""
    )
    cvr_incremental_txt = (
        f"Si no hubieras perdido conversión, ~{round(inc['pedidos_cvr'])} pedidos más "
        f"({dl.fmt_money(round(inc['gmv_cvr']), CURRENCY)}) este mes."
        if inc["gmv_cvr"] > 0 else ""
    )

    comparativo_html = (
        '<div class="comparativo-card">'
        f'<div class="funnel-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_TENDENCIA}</span>Tráfico &amp; Conversión vs mes anterior</div>'
        + _mini_delta_bar(ICON_TRAFICO, "Tráfico", diag["traffic_disp"] + "/sem", row.traffic_delta, row.traffic > 0,
                           valor_anterior_disp=traffic_anterior_disp, incremental_texto=traffic_incremental_txt)
        + _mini_delta_bar(ICON_CONVERSION, "Conversión", diag["cvr_disp"], row.cvr_delta, row.cvr > 0,
                           valor_anterior_disp=cvr_anterior_disp, incremental_texto=cvr_incremental_txt)
        + "</div>"
    )

    # ── Dato Ancla + Benchmark: se calculan por GMV, no por AOV (mismo criterio
    # que Growth OS: percentil = cuantas marcas de la cartera tienen menos GMV;
    # benchmark = la marca con mayor GMV de la categoria). ──
    def _pct_slider(pct_pos, fill_color, dot_color, callout_text, left_label, right_label, left_color=None, right_color=None):
        # Slider visual reusable -- rediseño septiembre 2026 (imagen de
        # referencia de Sabas): barra con relleno hasta pct_pos%, marcador
        # circular en esa posición y un callout flotando arriba con el
        # valor. pct_pos siempre 0-100 (ya clampeado por el caller).
        left_style = f'style="color:{left_color};"' if left_color else ""
        right_style = f'style="color:{right_color};"' if right_color else ""
        return (
            '<div class="pct-slider">'
            f'<div class="pct-slider-track">'
            f'<div class="pct-slider-fill" style="width:{pct_pos:.1f}%;background:{fill_color};"></div>'
            f'<div class="pct-slider-dot" style="left:{pct_pos:.1f}%;border-color:{dot_color};"></div>'
            f'<div class="pct-slider-callout" style="left:{pct_pos:.1f}%;">{callout_text}</div>'
            "</div>"
            f'<div class="pct-slider-caption"><span {left_style}>{left_label}</span><span {right_style}>{right_label}</span></div>'
            "</div>"
        )

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

            bench_pct_pos = max(0.0, min(100.0, (row.gmv / leader["gmv"]) * 100)) if leader["gmv"] > 0 else 0.0

            ancla_html = (
                '<div class="analytics-mini-grid">'
                + f'<div class="glass-card"><span class="ancla-badge">{ICON_MEDALLA}</span>'
                  f'<div class="card-label">DATO ANCLA</div>'
                  f'<div class="card-value" style="color:{ancla_color};">Percentil {percentil:.0f}%</div>'
                  f'<div class="card-copy">{ancla_texto}</div>'
                  + _pct_slider(percentil, COLORS["muted"], COLORS["muted"], f"{percentil:.0f}%", "0", "100%")
                  + '</div>'
                + f'<div class="glass-card"><span class="bench-badge">{ICON_CORONA}</span>'
                  f'<div class="card-label">BENCHMARK</div>'
                  f'<div class="card-value" style="color:{COLORS["brand_orange"]};">{dl.fmt_money(leader["gmv"], CURRENCY)}</div>'
                  f'<div class="card-copy">El líder de {row.categoria} es {leader["brand_name"]} con '
                  f'{dl.fmt_money(leader["gmv"], CURRENCY)}. Ese es el benchmark real.</div>'
                  + _pct_slider(
                        bench_pct_pos, COLORS["brand_orange"], COLORS["brand_orange"],
                        "", f'{dl.fmt_money(row.gmv, CURRENCY)} (Tu Marca)', f'{dl.fmt_money(leader["gmv"], CURRENCY)} (Líder)',
                        left_color=COLORS["brand_orange"], right_color=COLORS["muted"],
                    )
                  + '</div>'
                + "</div>"
            )
        else:
            ancla_html = '<div class="card-copy">No hay suficientes marcas de tu cartera en esta categoría para comparar.</div>'
    else:
        ancla_html = '<div class="card-copy">Sin GMV/categoría para calcular Dato Ancla y Benchmark.</div>'

    st.markdown(
        f'<div class="funnel-comparativo-grid">'
        f'<div class="funnel-card" style="margin-bottom:0;">'
        f'<div class="funnel-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_FUNNEL}</span>Funnel Tráfico &amp; Conversión vs Benchmark</div>'
        f'<div class="funnel-headline" style="color:{diag["color"]};">{diag["headline"]}</div>'
        f'<div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">'
        f'<div>{funnel_svg}</div><div>{funnel_legend}</div>'
        f"</div>"
        f'<div class="funnel-insight-pill"><span>💡</span><span>{diag["texto"]}</span></div>'
        f"</div>"
        f"{comparativo_html}"
        f"</div>"
        f"{ancla_html}",
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

    # Insight de comisión (Take Rate) -- pedido explícito de Sabas
    # (vigésima segunda vuelta): esquina superior derecha de AMBAS cards
    # (Ads Plan y Markdown Plan), chico y discreto -- solo dato
    # informativo para que el Farmer lo tenga a mano al negociar con el
    # aliado, SIN mezclarlo en ningún cálculo de rentabilidad (Sabas
    # decidió explícitamente no armar un P&L real, ver conversación: "no
    # divague, tocaría tener en cuenta todo lo que viene en una
    # facturación de Rappi"). Se muestra tal cual venga el dato, incluso
    # si es negativo o llamativo (pedido explícito, sin filtrar) -- "-"
    # solo cuando no hay dato en absoluto (None).
    take_rate = pitch_info["take_rate"]
    take_rate_html = (
        f'<div style="font-size:10px;color:#9CA3AF;text-align:right;line-height:1.3;">'
        f'Comisión<br><span style="color:{COLORS["muted"]};font-weight:700;">{take_rate * 100:.0f}%</span></div>'
        if take_rate is not None else ""
    )

    if row.gmv_last <= 0:
        ads_card_html = (
            '<div class="campaign-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_ADS_PLAN}</span>Ads Plan</div>'
            f'{take_rate_html}</div>'
            '<div class="campaign-sub" style="margin-top:8px;">Sin GMV del mes anterior para calcular el modelo.</div>'
            "</div>"
        )
    else:
        pct_label = f'{plan["pct"] * 100:.0f}%'
        gmv_actual = plan["gmv_semana"]
        incremental = plan["gmv_inc_1sem"]
        organico_proyectado = gmv_actual * 0.90
        total_proyectado = organico_proyectado + incremental
        roas = plan["roas_1sem"]

        # Escala compartida por las 3 barras -- el ancho relativo ES el
        # mensaje (una inversión chica al lado de un GMV grande se debe
        # VER chica, no ocupar el mismo ancho que las otras). Techo con
        # 5% de aire para que la barra más ancha no toque el borde.
        escala_max = max(plan["presupuesto_semana1"], gmv_actual, total_proyectado) * 1.05
        pct_ancho_inv = min(100, plan["presupuesto_semana1"] / escala_max * 100) if escala_max > 0 else 0
        pct_ancho_actual = min(100, gmv_actual / escala_max * 100) if escala_max > 0 else 0
        pct_ancho_proy = min(100, total_proyectado / escala_max * 100) if escala_max > 0 else 0

        # Inversión: siempre verde -- es un valor FIJO en el % recomendado
        # real de la marca (nunca puede quedar "por debajo" de sí mismo).
        # Proyectado: verde si el ROAS de la campaña supera 3.5x, rojo si no.
        color_proy = "green" if roas > 3.5 else "red"

        bars_html = (
            '<div style="margin-top:16px;">'
            '<div class="ads-bar-row">'
            f'<div class="ads-bar-label"><span>Inversión semanal recomendada</span>'
            f'<span class="val">{dl.fmt_money(plan["presupuesto_semana1"], CURRENCY)} ({pct_label})</span></div>'
            f'<div class="ads-bar-track"><div class="ads-bar-fill green" style="width:{pct_ancho_inv:.1f}%;"></div></div>'
            "</div>"
            '<div class="ads-bar-row">'
            f'<div class="ads-bar-label"><span>GMV actual (última semana)</span>'
            f'<span class="val">{dl.fmt_money(gmv_actual, CURRENCY)}</span></div>'
            f'<div class="ads-bar-track"><div class="ads-bar-fill purple" style="width:{pct_ancho_actual:.1f}%;"></div></div>'
            "</div>"
            '<div class="ads-bar-row">'
            f'<div class="ads-bar-label"><span>GMV proyectado (orgánico + campaña)</span>'
            f'<span class="val">{dl.fmt_money(total_proyectado, CURRENCY)} total</span></div>'
            f'<div class="ads-bar-track"><div class="ads-bar-fill {color_proy}" style="width:{pct_ancho_proy:.1f}%;">'
            f'<span class="txt">+{dl.fmt_money(incremental, CURRENCY)} incremental de Ads</span></div></div>'
            "</div>"
            '<div class="ads-roas-row"><span style="color:'
            f'{COLORS["muted"]};">ROAS de la campaña</span><span class="val">{roas:.2f}x</span></div>'
            "</div>"
        )
        ads_card_html = (
            '<div class="campaign-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_ADS_PLAN}</span>Ads Plan</div>'
            f'{take_rate_html}</div>'
            f'<div class="campaign-headline">{dl.fmt_money(plan["presupuesto_semana1"], CURRENCY)}<span style="font-size:14px;font-weight:600;"> /semana</span></div>'
            f'<div class="campaign-sub">Inversión recomendada: el {pct_label} del GMV de la última semana '
            f'({dl.fmt_money(plan["gmv_semana"], CURRENCY)})</div>'
            f"{bars_html}"
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
    if tops:
        # Top 3 como barras verticales con íconos de ojo/carrito -- pedido
        # explícito de Sabas (vigésima vuelta, aprobado como mockup): "VPD"
        # se relenguaja a ojos (visitas del producto), y el número de
        # carrito se CALCULA como ojos × CVR (pedidos reales estimados a
        # partir de esas visitas), redondeado a entero -- no es un campo
        # que venga así del Excel. Altura de cada barra proporcional al
        # máximo de ojos del trío (mínimo 34px para que el texto entre
        # incluso en el más chico).
        #
        # BUG REAL CORREGIDO (vigésima primera vuelta, pedido explícito de
        # Sabas -- vio "Combo 1" y "Promo 4" con el mismo número de
        # carritos pero quedando en el orden que traía tpmap en vez de por
        # su tasa real): el orden es por TASA de conversión (CVR real del
        # Excel, carritos ÷ ojos), no por la cantidad ABSOLUTA de carritos
        # -- "no importa que tenga más VPD, lo importante es la
        # conversión". Ordenar por el carrito ya redondeado a entero podía
        # empatar productos con distinto CVR real (ej. 1/4 y 1/9 redondean
        # ambos a "1 carrito" pero son 25% y 11% -- bien distintos), así
        # que se ordena por el cvr original del Excel, no por el carrito
        # entero derivado.
        prod_data = []
        for nombre, vpd, cvr in tops:
            ojos = round(vpd)
            carrito = round(vpd * cvr)
            prod_data.append((nombre, ojos, carrito, cvr))
        prod_data.sort(key=lambda p: p[3], reverse=True)

        max_ojos = max((p[1] for p in prod_data), default=1) or 1
        bars = []
        for i, (nombre, ojos, carrito, cvr) in enumerate(prod_data):
            altura = max(34, round(ojos / max_ojos * 100))
            # El chicharrón/último lugar del trío puede quedar con una barra
            # muy baja -- por debajo de cierta altura el fondo naranja pleno
            # se ve mejor en un tono pastel con texto oscuro (mismo criterio
            # de contraste ya usado en el resto de Wingman para barras
            # chicas), arriba de esa altura va naranja sólido con texto
            # blanco.
            es_chica = altura < 55
            bg = "rgba(247,77,4,0.3)" if es_chica else COLORS["brand_orange"]
            txt_color = COLORS["text"] if es_chica else COLORS["brand_white"]
            nombre_html = html_lib.escape(nombre)
            bars.append(
                f'<div class="md-prod-bar-wrap">'
                f'<div class="md-prod-bar" style="height:{altura}px;background:{bg};color:{txt_color};">'
                f'<span class="metric">{ICON_OJO} {ojos}</span>'
                f'<span class="metric">{ICON_CARRITO_MD} {carrito}</span>'
                "</div>"
                f'<div class="md-prod-name">{nombre_html}</div>'
                f'<div class="md-prod-rank">#{i + 1}{" — el que más convierte" if i == 0 else ""}</div>'
                "</div>"
            )
        chart_html = f'<div class="md-prod-chart">{"".join(bars)}</div>'

        # Insight: nombra a cada uno de los 3 con su propio dato real
        # (ojos → carritos), sin promediar ni proyectar nada -- pedido
        # explícito de Sabas tras descartar una proyección de CVR de marca
        # que los datos no sostenían (ver conversación).
        insight_parts = []
        for i, (nombre, ojos, carrito, cvr) in enumerate(prod_data):
            nombre_html = html_lib.escape(nombre)
            if i == 0:
                frase = f"<b>{nombre_html}:</b> {ojos} visitas → {carrito} pedidos, el que más convierte."
            elif cvr >= 0.5:
                frase = f"<b>{nombre_html}:</b> {ojos} visitas → {carrito} pedidos, buena conversión."
            else:
                frase = f"<b>{nombre_html}:</b> {ojos} visitas → solo {carrito} pedido{'s' if carrito != 1 else ''}, el que más se beneficiaría del descuento."
            insight_parts.append(frase)
        insight_html = f'<div class="md-prod-insight">{" ".join(insight_parts)}</div>'

        tops_html = f"{chart_html}{insight_html}"
    else:
        tops_html = '<div class="card-copy">Sin productos rankeados para esta marca.</div>'

    # Ícono del grupo de coinversión -- grupo_icon ahora es la CLAVE del
    # grupo (ver COINV_GROUPS en data_layer.py), no un emoji; se resuelve
    # acá al ícono SVG monocromático correspondiente (novena vuelta,
    # pedido explícito de Sabas).
    COINV_ICON_MAP = {
        "new hunters": ICON_COINV_NEW_HUNTERS,
        "new rest": ICON_COINV_NEW_REST,
        "churn": ICON_COINV_CHURN,
        "churn prevention": ICON_COINV_CHURN_PREVENTION,
        "prioritized": ICON_COINV_PRIORITIZED,
        "rest": ICON_COINV_REST,
    }

    if coinv_plan:
        # Con coinversión: la campaña principal es 30% + PRO, con el desglose
        # del ratio Aliado:Rappi sobre el descuento total combinado. La regla
        # por defecto (15/20/25 según CVR) queda como pill debajo, no como
        # recomendación principal -- pedido explicito de Sabas.
        coinv_icon_svg = COINV_ICON_MAP.get(coinv_plan["grupo_icon"], ICON_COINV_REST)
        coinv_html = (
            '<div class="coinv-block">'
            f'<span class="coinv-badge"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{coinv_icon_svg}</span>Coinversión activa · {coinv_plan["grupo_label"]} · ratio {coinv_plan["ratio"]}</span>'
            f'<div class="campaign-headline" style="font-size:26px;margin-top:8px;">'
            f'{coinv_plan["discount"]}% OFF <span style="font-size:15px;color:{COLORS["brand_purple"]};">+ {coinv_plan["pro_extra"]}% PRO</span></div>'
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
            '<div class="campaign-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_MD_PLAN}</span>Markdown Plan</div>'
            f'{take_rate_html}</div>'
            f'<div style="margin-top:10px;">{coinv_html}</div>'
            f"{default_pill_html}"
            '<div class="section-title" style="margin:14px 0 8px 0;">TOP 3 PRODUCTOS</div>'
            f"{tops_html}"
            "</div>"
        )
    else:
        md_card_html = (
            '<div class="campaign-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_MD_PLAN}</span>Markdown Plan</div>'
            f'{take_rate_html}</div>'
            f'<div class="campaign-headline" style="font-size:26px;">'
            f'{md["discount"]}% OFF <span style="font-size:15px;color:{COLORS["brand_purple"]};">+ {md["pro_extra"]}% PRO</span></div>'
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

    # Barra de contactos (teléfonos/correos adicionales) -- pedido
    # explícito de Sabas (vigésima segunda vuelta): mismo estilo visual
    # de la barra "COINVERSIÓN MD" de 360° Action (fondo gris, pills
    # blancas), pero acá siempre 2 filas fijas (Teléfonos / Correos),
    # SIEMPRE visible aunque no haya adicionales (se repite la pill del
    # dato que ya está en la cabecera, pedido explícito: "si el único
    # número que aparece es el que está en la cabecera, pues se coloca
    # la pill de ese mismo número"). Sin nombre de marca repetido en las
    # filas (ya está en la cabecera de toda la ficha).
    telefonos_pills = [row.telefono] if row.telefono else []
    telefonos_pills += pitch_info["telefonos_extra"]
    if not telefonos_pills:
        telefonos_pills = ["?"]

    correos_pills = [row.mail] if row.mail else []
    correos_pills += pitch_info["correos_extra"]
    if not correos_pills:
        correos_pills = ["?"]

    def _pill_row(label, valores):
        pills = "".join(
            f'<span style="background:#FFFFFF;border-radius:999px;padding:6px 14px;'
            f'font-size:12.5px;font-weight:600;color:{COLORS["text"]};">{html_lib.escape(str(v))}</span>'
            for v in valores
        )
        return (
            '<div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;margin-bottom:10px;">'
            f'<div style="min-width:90px;font-size:10px;font-weight:700;color:{COLORS["muted"]};'
            f'text-transform:uppercase;letter-spacing:0.4px;">{label}</div>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{pills}</div>'
            "</div>"
        )

    contactos_bar_html = (
        f'<div style="background:{COLORS["card2"]};border-radius:16px;padding:18px 24px;margin-bottom:20px;">'
        + _pill_row("TELÉFONOS", telefonos_pills)
        + _pill_row("CORREOS", correos_pills).replace('margin-bottom:10px;', 'margin-bottom:0;')
        + "</div>"
    )
    st.markdown(contactos_bar_html, unsafe_allow_html=True)

    oc1, oc2 = st.columns(2)
    with oc1:
        email_copy_label = f'<span class="lever-icon" style="margin:0 6px 0 0;">{ICON_CLIPBOARD}</span>Copiar'
        email_btn_id, email_copy_btn = _copy_button_html(email_body, label=email_copy_label, tamano="grande")
        st.markdown(
            f'<div class="glass-card"><div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_ENVELOPE}</span>EMAIL</div>{email_copy_btn}</div>'
            f'<div style="margin-top:10px;font-size:12.5px;white-space:pre-wrap;line-height:1.6;">{email_body}</div></div>',
            unsafe_allow_html=True,
        )
        _render_copy_script(email_body, email_btn_id, label_original=email_copy_label)
    with oc2:
        st.markdown(
            f'<div class="glass-card"><div class="card-label"><span class="lever-icon" style="margin-right:6px;vertical-align:-3px;">{ICON_CHAT}</span>WHATSAPP</div>'
            f'<div style="margin-top:10px;font-size:12.5px;white-space:pre-wrap;line-height:1.6;">{whatsapp_body}</div></div>',
            unsafe_allow_html=True,
        )

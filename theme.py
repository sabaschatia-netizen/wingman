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
    "brand_orange":     "#F74D04",   # naranja — acentos, hovers, botón Entrar (se mantiene)
    "brand_orange_soft": "rgba(247,77,4,0.14)",
    "brand_purple":     "#9A54F6",   # morado — hover, sombras
    "brand_purple_soft": "rgba(154,84,246,0.16)",
    "brand_white":      "#FCFAF8",   # texto sobre naranja
    # Color dominante nuevo -- décima vuelta, pedido explícito de Sabas:
    # reemplaza al naranja como color de fondo de sidebar/header/login
    # (logo recoloreado con este mismo azul de fondo). El naranja
    # (brand_orange) NO se toca -- sigue siendo el acento de hover y el
    # color del botón "Entrar" del login, confirmado explícitamente.
    "brand_blue":       "#123E4A",   # azul petróleo — sidebar, header, login (nuevo color dominante)

    # Superficies (light mode)
    "bg":              "#F7F6F2",   # fondo general, blanco marfil/hueso tibio
    "card":            "#FFFFFF",   # cards, mas claras que el fondo (contraste)
    "card2":           "#EFEEE9",   # segundo plano (stat boxes, inputs)
    "sidebar":         "#123E4A",   # sidebar — décima vuelta: azul petróleo, antes naranja

    # Texto
    "text":            "#23272E",   # texto principal, oscuro sobre fondo claro
    "muted":           "#6B7280",   # texto secundario
    "text_disabled":   "#9CA3AF",
    "sidebar_text":    "#FCFAF8",   # texto blanco sobre el sidebar (sigue igual, blanco sobre azul también contrasta bien)

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
# ICONOGRAFIA — rediseño septiembre 2026, pedido explícito de Sabas
# =========================
# Reemplazo de los emojis Unicode (⚙️ 🍔 🏷️ 🚀 etc.) por un set propio de
# íconos SVG monolineales (stroke, sin relleno). Usan `stroke="currentColor"`
# a propósito: el color real lo pone el CSS del contenedor que los envuelve
# (.action-card-icon, .lever-icon-active/.lever-icon-inactive, etc.), así
# un mismo ícono puede pintarse morado (activo) o gris (inactivo) sin
# duplicar el SVG. viewBox fijo 0 0 24 24 en los 4 para que se vean
# consistentes uno al lado del otro en el grid de 360 Action.

def _icon(paths, view_box="0 0 24 24"):
    return (
        f'<svg width="18" height="18" viewBox="{view_box}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="display:block;">{paths}</svg>'
    )


# OPS General — engranaje simplificado (6 dientes + centro hueco)
ICON_OPS = _icon(
    '<path d="M8.82,4.33 L9.71,1.75 L14.29,1.75 L15.18,4.33 L17.63,3.13 L20.87,6.37 '
    'L19.67,8.82 L22.25,9.71 L22.25,14.29 L19.67,15.18 L20.87,17.63 L17.63,20.87 '
    'L15.18,19.67 L14.29,22.25 L9.71,22.25 L8.82,19.67 L6.37,20.87 L3.13,17.63 '
    'L4.33,15.18 L1.75,14.29 L1.75,9.71 L4.33,8.82 L3.13,6.37 L6.37,3.13 Z" '
    'fill="currentColor" fill-rule="evenodd"/>'
    '<circle cx="12" cy="12" r="3.3" fill="{}"/>'.format(COLORS["card2"])
)

# Menú — 3 líneas horizontales tipo lista
ICON_MENU = _icon(
    '<path d="M12 5.5c-1.8-1.3-4-2-6.2-2-1 0-1.8.8-1.8 1.8v11.4c0 1 .8 1.8 1.8 1.8 '
    '2.2 0 4.4.7 6.2 2 1.8-1.3 4-2 6.2-2 1 0 1.8-.8 1.8-1.8V5.3c0-1-.8-1.8-1.8-1.8-'
    '2.2 0-4.4.7-6.2 2z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<path d="M12 5.5v14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'
)

# Markdown — símbolo de porcentaje en trazo
ICON_MARKDOWN = _icon(
    '<circle cx="7" cy="7" r="2.4" stroke="currentColor" stroke-width="1.8"/>'
    '<circle cx="17" cy="17" r="2.4" stroke="currentColor" stroke-width="1.8"/>'
    '<path d="M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'
)

# Ads — flecha ascendente dentro de triángulo/cohete simplificado
ICON_ADS = _icon(
    '<path d="M12 3l4 7h-3v8h-2v-8H8l4-7z" '
    'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
)

# Categoría (imagen 1 — ficha de marca) — bowl con palitos cruzados
ICON_CATEGORIA = _icon(
    '<path d="M3.5 12a8.5 7 0 0017 0H3.5z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
    '<path d="M9 12V4M9 4l2.5-2M15 12V5M15 5l2-2.5" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'
)

# Palanca ADS — megáfono sólido (forma clásica: cuerpo cónico ancho a la
# derecha + mango rectangular abajo-izquierda + 2 líneas de sonido rectas).
# Corrección (segunda vuelta, pedido explícito de Sabas): la versión
# anterior usaba curvas concéntricas tipo "ícono de audio/parlante" y no
# se leía como megáfono -- esta va con la silueta trapezoidal clásica del
# emoji de megáfono (cuerpo sólido, sin curvas de onda).
ICON_ADS_LEVER = _icon(
    '<path d="M2 9.5v5a1.2 1.2 0 001.2 1.2h1.3l1 3.3a1 1 0 00.96.7h1.1'
    'a1 1 0 00.94-1.34L7.7 15.7'
    'l8.8 3.4a1 1 0 001.36-.93V5.83a1 1 0 00-1.36-.93l-8.8 3.4H3.2A1.2 1.2 0 002 9.5z" '
    'fill="currentColor"/>'
    '<path d="M19.5 9v6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'
)

# Palanca Markdown / Markdown Pro — círculo relleno con símbolo de % en
# blanco adentro (mismo ícono para ambas palancas, difieren solo en
# color de fondo: morado activo / gris inactivo, ver icon-purple en CSS)
ICON_MARKDOWN_LEVER = _icon(
    '<circle cx="12" cy="12" r="10" fill="currentColor"/>'
    '<circle cx="9" cy="9" r="1.6" fill="white"/>'
    '<circle cx="15" cy="15" r="1.6" fill="white"/>'
    '<path d="M8 16L16 8" stroke="white" stroke-width="1.6" stroke-linecap="round"/>'
)

# GMV — círculo relleno con "S" (símbolo de venta/moneda) adentro,
# reemplaza el emoji 📈 (tercera vuelta, pedido explícito de Sabas:
# GMV/AOV/órdenes seguían con emoji Unicode de Apple sin tocar).
ICON_GMV = _icon(
    '<circle cx="12" cy="12" r="10" fill="currentColor"/>'
    '<text x="12" y="16.5" font-family="Arial, sans-serif" font-size="13" '
    'font-weight="700" fill="white" text-anchor="middle">S</text>'
)

# AOV — ticket/boleto de entrada lineal (rectángulo con muescas
# semicirculares a los lados + línea punteada vertical), reemplaza el
# carrito de compras que tenía antes (cuarta vuelta, pedido explícito
# de Sabas: AOV = ticket, el carrito pasa a ser el ícono de órdenes).
ICON_AOV = _icon(
    '<path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v2a1.5 1.5 0 000 3v2a1.5 1.5 0 000 3v2'
    'a2 2 0 01-2 2H5a2 2 0 01-2-2v-2a1.5 1.5 0 000-3V9a1.5 1.5 0 000-3V7z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<line x1="14.5" y1="5.5" x2="14.5" y2="18.5" stroke="currentColor" '
    'stroke-width="1.4" stroke-dasharray="1.8,1.8" stroke-linecap="round"/>'
)

# Órdenes (sub-línea de la card de GMV) — carrito de compras lineal,
# reemplaza el ícono de caja/paquete que tenía antes (cuarta vuelta,
# mismo pedido: el carrito pasa de AOV a órdenes).
ICON_ORDENES = _icon(
    '<circle cx="9" cy="20" r="1.3" fill="currentColor"/>'
    '<circle cx="17" cy="20" r="1.3" fill="currentColor"/>'
    '<path d="M2.5 3h2l2.2 11.6a2 2 0 002 1.6h7.7a2 2 0 002-1.6L18 7.5H6.2" '
    'stroke="currentColor" stroke-width="1.8" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
)

# Dato Ancla — estrella (imagen 2)
ICON_ESTRELLA = _icon(
    '<path d="M12 3l2.6 5.9 6.4.6-4.8 4.3 1.4 6.3L12 16.9 6.4 20.1l1.4-6.3-4.8-4.3 6.4-.6L12 3z" '
    'stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>'
)

# ── Bullets de estado de los items en 360° Action (OPS/Menú/Markdown/
# Ads) -- séptima vuelta, pedido explícito de Sabas: reemplaza el
# punto simple dentro del círculo gris por un ícono según el estado del
# item -- ALERT: triángulo de warning; WATCH: ojo; HEALTHY: chulito;
# sin dato (None, "no la está pidiendo"): se queda el punto simple de
# siempre (ICON_BULLET_DOT). Todos con stroke="currentColor" para
# heredar el mismo gris del círculo contenedor.
ICON_BULLET_DOT = (
    '<svg width="8" height="8" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg" '
    'style="display:block;"><circle cx="4" cy="4" r="4" fill="currentColor"/></svg>'
)
ICON_BULLET_WARNING = _icon(
    '<path d="M12 3.5 L21.5 20 L2.5 20 Z" stroke="currentColor" stroke-width="2" '
    'stroke-linejoin="round" fill="none"/>'
    '<line x1="12" y1="9.5" x2="12" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    '<circle cx="12" cy="16.8" r="1.1" fill="currentColor"/>'
)
ICON_BULLET_EYE = _icon(
    '<path d="M2 12c2.5-5 7-8 10-8s7.5 3 10 8c-2.5 5-7 8-10 8s-7.5-3-10-8z" '
    'stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>'
    '<circle cx="12" cy="12" r="3" fill="currentColor"/>'
)
ICON_BULLET_CHECK = _icon(
    '<path d="M4 12.5l5.5 5.5L20 6" stroke="currentColor" stroke-width="2.6" '
    'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
)


# ── Analytics (octava vuelta, pedido explícito de Sabas) ──
# Embudo lineal -- reemplaza la lupa 🔍 en el título "Funnel Tráfico &
# Conversión vs Benchmark".
ICON_FUNNEL = _icon(
    '<path d="M3 4h18l-6.5 8v6.5l-5 2V12L3 4z" '
    'stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" fill="none"/>'
)
# Ojo lineal -- reemplaza el semáforo 🚦 junto a "Tráfico" (gris, no el
# color naranja/rojo de la referencia -- decisión explícita de Sabas).
ICON_TRAFICO = _icon(
    '<path d="M2 12c2.5-5 7-8 10-8s7.5 3 10 8c-2.5 5-7 8-10 8s-7.5-3-10-8z" '
    'stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/>'
    '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.7" fill="none"/>'
)
# Diana lineal -- reemplaza el 🎯 junto a "Conversión" (gris, mismo
# criterio que arriba).
ICON_CONVERSION = _icon(
    '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<circle cx="12" cy="12" r="5.3" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<circle cx="12" cy="12" r="1.6" fill="currentColor"/>'
)
# Medalla (círculo + 2 cintas) -- reemplaza la ⭐ del badge de Dato
# Ancla.
ICON_MEDALLA = _icon(
    '<circle cx="12" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.7" fill="none"/>'
    '<path d="M8.7 13l-2.3 8 5.6-3 5.6 3-2.3-8" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)
# Corona -- reemplaza el badge de texto "LÍDER" en Benchmark.
ICON_CORONA = _icon(
    '<path d="M3 8l4 4 5-7 5 7 4-4-2 10H5L3 8z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)
# Tendencia ascendente -- título de la card "Tráfico & Conversión vs mes
# anterior" (antes 📊 genérico).
ICON_TENDENCIA = _icon(
    '<path d="M3 16l6-6 4 4 8-8" stroke="currentColor" stroke-width="1.8" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M15 6h6v6" stroke="currentColor" stroke-width="1.8" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
)

# ── Campaign Designer / Outreach (novena vuelta, pedido explícito de
# Sabas): reemplazan los emojis Unicode de Apple por el mismo sistema
# monocromático del resto del rediseño.
ICON_ADS_PLAN = ICON_ADS_LEVER  # megáfono, ya definido arriba -- "Ads Plan" reusa el mismo ícono de la palanca Ads
ICON_MD_PLAN = ICON_MARKDOWN_LEVER  # círculo con %, ya definido arriba -- "Markdown Plan" reusa el de la palanca Markdown

ICON_CLIPBOARD = _icon(
    '<rect x="6" y="4" width="12" height="17" rx="2" stroke="currentColor" stroke-width="1.7" fill="none"/>'
    '<path d="M9 4V3a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" stroke-width="1.7" fill="none"/>'
    '<path d="M9 11h6M9 15h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
)
ICON_ENVELOPE = _icon(
    '<rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.7" fill="none"/>'
    '<path d="M4 6.5l8 6 8-6" stroke="currentColor" stroke-width="1.7" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
)
ICON_CHAT = _icon(
    '<path d="M4 5h16a1 1 0 011 1v10a1 1 0 01-1 1H9l-4 4v-4H4a1 1 0 01-1-1V6a1 1 0 011-1z" '
    'stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/>'
)


def icon_medalla_numero(n):
    """
    Círculo relleno con el número (1/2/3) adentro -- reemplaza los
    emojis 🥇🥈🥉 del Top 3 productos en Campaign Designer. Un solo
    generador en vez de 3 constantes, mismo patrón que ICON_GMV (círculo
    con "S" adentro).
    """
    return _icon(
        f'<circle cx="12" cy="12" r="10" fill="currentColor"/>'
        f'<text x="12" y="16.5" font-family="Arial, sans-serif" font-size="12" '
        f'font-weight="700" fill="white" text-anchor="middle">{n}</text>'
    )


# ── Gestión General (décima vuelta, pedido explícito de Sabas) ──
# Gráfico de barras -- reemplaza 📊 en "Rendimiento País" / "Rendimiento
# Farmer".
ICON_RENDIMIENTO = _icon(
    '<rect x="4" y="14" width="4" height="6" rx="1" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<rect x="10" y="9" width="4" height="11" rx="1" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<rect x="16" y="4" width="4" height="16" rx="1" stroke="currentColor" stroke-width="1.6" fill="none"/>'
)
# Expandir/pantalla completa -- reemplaza ⛶ en el botón "Pantalla
# completa".
ICON_EXPANDIR = _icon(
    '<path d="M9 3H3v6M15 3h6v6M9 21H3v-6M15 21h6v-6" '
    'stroke="currentColor" stroke-width="1.8" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
)

# ── Gestión General, segunda vuelta (pedido explícito de Sabas): Brand
# Coverage, Contact Performance y las pills de Rendimiento País seguían
# con emojis Unicode a color (🎯📞💬🖥️👻⚡🏆🟥🔥⚠️) que se me habían
# escapado en la primera pasada -- estaban fuera del rango de líneas
# donde busqué. ──
ICON_TELEFONO = _icon(
    '<path d="M7.5 3.8L10 6.3a1.2 1.2 0 01-.1 1.7l-1.6 1.4a11 11 0 004.8 4.8l1.4-1.6a1.2 1.2 0 011.7-.1l2.5 2.5a1.2 1.2 0 01.1 1.7l-1.6 1.8c-.5.5-1.2.8-1.9.6a15 15 0 01-10-10c-.2-.7.1-1.4.6-1.9l1.8-1.6a1.2 1.2 0 011.8.2z" '
    'fill="currentColor"/>'
)
ICON_MONITOR = _icon(
    '<rect x="3" y="4" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.7" fill="none"/>'
    '<path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>'
)
ICON_FANTASMA = _icon(
    '<path d="M6 21V11a6 6 0 0112 0v10l-2-1.5L14 21l-2-1.5L10 21l-2-1.5L6 21z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<circle cx="9.5" cy="11" r="1" fill="currentColor"/>'
    '<circle cx="14.5" cy="11" r="1" fill="currentColor"/>'
)
# Los 5 estados de _RENDIMIENTO_EMOJI (pills de la tabla Rendimiento
# País): rayo (blue), trofeo (green), cuadrado relleno (red), fuego
# (purple), warning ya existe como ICON_BULLET_WARNING (yellow).
ICON_RAYO = _icon(
    '<path d="M13 3L5 14h5l-1 7 8-11h-5l1-7z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)
ICON_TROFEO = _icon(
    '<path d="M8 4h8v4a4 4 0 01-8 0V4z" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<path d="M8 5H5a2 2 0 002 4M16 5h3a2 2 0 01-2 4" stroke="currentColor" stroke-width="1.5" fill="none"/>'
    '<path d="M12 12v4M9 20h6M10 16h4v4h-4z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/>'
)
ICON_CUADRADO = _icon(
    # Reemplaza el cuadrado relleno (🟥) por una X -- pedido explícito de
    # Sabas (tercera vuelta, después de probarlo en la app real): el
    # cuadrado se veía "negro y feo" en pantalla. Mantiene el mismo
    # nombre de constante (ICON_CUADRADO) porque _RENDIMIENTO_ICON en
    # wingmanapp.py referencia este símbolo por su rol semántico ("red"
    # dentro del semáforo de rendimiento), no por su forma literal.
    '<path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>'
)
ICON_FUEGO = _icon(
    # Reemplaza la llama de fuego por un cohete -- pedido explícito de
    # Sabas (tercera vuelta): mismo criterio que arriba, mantiene el
    # nombre ICON_FUEGO porque _RENDIMIENTO_ICON lo referencia por su
    # rol ("purple", el nivel más alto del semáforo), no por la forma.
    '<path d="M12 2c3 2 4.5 5.5 4.5 9 0 2-.5 3.8-1.3 5.3L12 19l-3.2-2.7C8 14.8 7.5 13 7.5 11c0-3.5 1.5-7 4.5-9z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<circle cx="12" cy="9.5" r="1.6" stroke="currentColor" stroke-width="1.4" fill="none"/>'
    '<path d="M8.5 14.5L6 17l1-3.5M15.5 14.5L18 17l-1-3.5" '
    'stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M10.3 18.3c0 1 .7 2.2 1.7 2.7 1-.5 1.7-1.7 1.7-2.7" '
    'stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
)
ICON_BILLETE = _icon(
    '<rect x="2" y="6" width="20" height="12" rx="2" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6" fill="none"/>'
    '<circle cx="6" cy="12" r="0.8" fill="currentColor"/>'
    '<circle cx="18" cy="12" r="0.8" fill="currentColor"/>'
)
ICON_MAPA = _icon(
    '<path d="M9 3L3 5v16l6-2 6 2 6-2V3l-6 2-6-2z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<path d="M9 3v16M15 5v16" stroke="currentColor" stroke-width="1.5"/>'
)
ICON_PIN = _icon(
    '<path d="M12 21s7-6.5 7-11.5a7 7 0 10-14 0C5 14.5 12 21 12 21z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<circle cx="12" cy="9.5" r="2.3" stroke="currentColor" stroke-width="1.5" fill="none"/>'
)


# Íconos de los 6 grupos de coinversión (COINV_GROUPS en data_layer.py,
# antes 🎯🌱🚫🛡️⭐📦) -- diferenciados entre sí porque cada grupo es un
# concepto de negocio distinto, no variaciones de un mismo ícono.
ICON_COINV_NEW_HUNTERS = ICON_CONVERSION  # diana, ya definido arriba
ICON_COINV_NEW_REST = _icon(
    '<path d="M12 21V11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'
    '<path d="M12 11C12 11 7 11 7 6c5 0 5 5 5 5z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<path d="M12 14c0 0 5 0 5-5c-5 0-5 5-5 5z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)
ICON_COINV_CHURN = _icon(
    '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" fill="none"/>'
    '<line x1="5.7" y1="5.7" x2="18.3" y2="18.3" stroke="currentColor" stroke-width="1.8"/>'
)
ICON_COINV_CHURN_PREVENTION = _icon(
    '<path d="M12 3l7 3v6c0 5-3 8-7 9-4-1-7-4-7-9V6l7-3z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)
ICON_COINV_PRIORITIZED = ICON_ESTRELLA
ICON_COINV_REST = _icon(
    '<path d="M12 2.5l8.5 4.9v9.2L12 21.5l-8.5-4.9V7.4L12 2.5z" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
    '<path d="M3.5 7.4L12 12.2l8.5-4.8M12 12.2v9.3" '
    'stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>'
)


# =========================
# CSS
# =========================

def build_css(login=False):
    LOGIN_CSS = (
        f'.stApp, [data-testid="stAppViewContainer"] {{'
        f'  background: {COLORS["brand_blue"]} !important;'
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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {{ font-family: 'Plus Jakarta Sans', sans-serif; }}

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

/* ── HEADER (area principal, mismo color solido que el sidebar) ── */
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
.business-mini-card.lever-ads, .business-mini-card.lever-md, .business-mini-card.lever-pro {{
    /* Sin borde lateral de color -- pedido explícito de Sabas (décima
       tercera vuelta): las 3 cards de palanca del Home (Ads/Markdown/
       Markdown Pro) quedan completamente blancas, sin el acento de
       color a la izquierda que tenían antes (naranja/azul/morado). */
}}
.business-mini-card.lever-menu  {{ border-left: 3px solid #6B7280 !important; }}

/* Estado "apagado" de la tarjeta cuando la palanca está inactiva --
   pedido explícito de Sabas (septiembre 2026, segunda vuelta): la card
   entera debe verse gris/apagada (no blanca brillante como las activas),
   sin perder legibilidad del texto, y sin el borde lateral de color de
   marca (ese color solo tiene sentido si la palanca está viva). El
   corner-badge (ej. "Penetración X%") también se desatura a gris. */
.business-mini-card.is-inactive {{
    background: {COLORS["card2"]} !important;
    border-left: 3px solid {COLORS["border"]} !important;
    box-shadow: none;
}}
.business-mini-card.is-inactive:hover {{
    transform: none; box-shadow: 0 2px 10px rgba(154,84,246,0.06);
}}
.business-mini-card.is-inactive .corner-badge {{
    background: {COLORS["border"]} !important; color: {COLORS["muted"]} !important;
}}

.corner-badge {{
    position: absolute; top: 12px; right: 14px;
    font-size: 11px; font-weight: 800;
    padding: 2px 9px; border-radius: 999px;
}}

.card-label {{
    font-size: 10.5px; font-weight: 700; color: {COLORS["muted"]};
    letter-spacing: 0.7px; text-transform: uppercase; margin-bottom: 5px;
    display: flex; align-items: center; gap: 6px;
}}
.lever-icon {{
    display: inline-flex; align-items: center; justify-content: center;
    color: {COLORS["muted"]}; flex-shrink: 0;
}}
.lever-icon.icon-purple {{ color: {COLORS["brand_purple"]}; }}
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

/* Pill de "Estado de conexión" dentro de la fila de 5 datos de la ficha
   de marca -- más chica y totalmente redondeada (999px) que .ctx-pill,
   mismos colores por estado (ok/warn/alert/info) reusados vía la misma
   clase modificadora. */
.conn-status-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 13px; font-weight: 700; padding: 5px 14px;
    border-radius: 999px; margin-top: 4px;
    background: {COLORS["card2"]}; color: {COLORS["text"]};
}}
.conn-status-pill.warn  {{ background: {COLORS["warning_soft"]}; color: #A97A1E; }}
.conn-status-pill.alert {{ background: {COLORS["danger_soft"]};  color: #C4483F; }}
.conn-status-pill.ok    {{ background: {COLORS["success_soft"]}; color: #166534; }}
.conn-status-pill.info  {{ background: {COLORS["info_bg"]};      color: {COLORS["blue"]}; }}

/* ── BRAND HEADER (franja fija) ── */
/* Título + ID centrados, y los 5 datos (Teléfono/Correo/Categoría/Local/
   Estado de conexión) en una sola fila centrada debajo -- rediseño
   décima primera vuelta, pedido explícito de Sabas, aprobado primero
   como mockup visual antes de tocar código: el Estado de Churn deja de
   ser una pill aparte arriba y pasa a ser un dato más de la fila, con
   su label renombrado a "Estado de conexión". */
.brand-title {{
    font-size: 40px; font-weight: 800; color: {COLORS["text"]};
    letter-spacing: -0.8px; line-height: 1.1; margin-bottom: 6px;
    text-align: center;
}}
.brand-id {{
    font-size: 16px; font-weight: 700; color: {COLORS["text_disabled"]};
    letter-spacing: 0.5px; text-align: center;
}}
.brand-stats-row {{
    display: flex; justify-content: center; align-items: flex-start;
    gap: 48px; flex-wrap: wrap; margin-top: 36px; text-align: center;
}}
.brand-stats-row > div {{ min-width: 160px; }}
.brand-stats-row .stat-label {{ text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }}
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
    display: flex !important; align-items: flex-start !important;
}}
.login-box [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    display: flex !important; align-items: flex-start !important; align-self: flex-start !important;
}}
.login-box [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div {{
    width: 100%;
}}
.login-logo-col, .login-form-col {{ width: 100%; }}
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
/* Toggle Farmer/Supervisor: pedido explícito de Sabas -- BLANCO cuando
   está seleccionado (kind="primary"), MORADO cuando no (kind=
   "secondary") -- antes se veía al revés (morado sólido cuando activo).
   Apunta a las keys específicas del toggle (.st-key-login_toggle_*), NO
   a ".login-box .stButton button[kind=...]" en general -- el botón
   "Entrar" TAMBIÉN es kind="primary" y vive en la misma .login-box; una
   regla genérica lo hubiera pintado blanco también, sin que se pidiera.
   Con la key, el cambio queda aislado al toggle. */
.st-key-login_toggle_farmer .stButton button[kind="primary"],
.st-key-login_toggle_supervisor .stButton button[kind="primary"] {{
    background: {COLORS["brand_white"]} !important;
    color: {COLORS["brand_orange"]} !important;
    border: none !important; font-weight: 800 !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="primary"]:hover,
.st-key-login_toggle_supervisor .stButton button[kind="primary"]:hover {{
    background: {COLORS["card2"]} !important;
    color: {COLORS["brand_orange"]} !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="secondary"],
.st-key-login_toggle_supervisor .stButton button[kind="secondary"] {{
    background: {COLORS["brand_purple"]} !important;
    color: {COLORS["brand_white"]} !important;
    border: 1px solid {COLORS["brand_purple"]} !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="secondary"]:hover,
.st-key-login_toggle_supervisor .stButton button[kind="secondary"]:hover {{
    background: {COLORS["brand_purple_soft"]} !important;
    color: {COLORS["brand_white"]} !important;
}}

/* Botón de submit del login ("Entrar" / "Entrar como Supervisor") --
   pedido explícito de Sabas: blanco, no naranja (con el naranja
   genérico, quedaba casi invisible contra el fondo también naranja del
   login). Mismo criterio de key específica que el toggle, para no
   afectar el resto de los botones primary de la app (ej. el de
   Gestión General, que sigue naranja). */
.st-key-login_submit .stButton button[kind="primary"],
.st-key-login_submit_sup .stButton button[kind="primary"] {{
    background: {COLORS["brand_white"]} !important;
    color: {COLORS["brand_orange"]} !important;
    border: none !important; font-weight: 800 !important;
}}
.st-key-login_submit .stButton button[kind="primary"]:hover,
.st-key-login_submit_sup .stButton button[kind="primary"]:hover {{
    background: {COLORS["card2"]} !important;
    color: {COLORS["brand_orange"]} !important;
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
    border-radius: 18px; padding: 32px 24px; margin-bottom: 14px;
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
.md-ladder-pill.active {{ background: {COLORS["brand_orange"]}; color: {COLORS["brand_white"]}; }}
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
/* Ícono de ritmo dentro del donut, centrado y debajo del % (agosto
   2026, séptima vuelta -- pedido explícito de Sabas): solo aparece en
   las 3 métricas medidas en pace (Adquisición/Upselling Ads,
   Conversión MD), mismo criterio de color que ya usa la tabla
   Rendimiento País/Farmer por color de ritmo (ver _RENDIMIENTO_ICON en
   wingmanapp.py). display:flex + align-items:center en el padre
   (.donut-pct) es lo que centra el ícono simétrico respecto al número,
   sin necesidad de margin/padding manual por caso.

   Ícono SVG monocromático gris en vez de emoji Unicode a color
   (segunda vuelta, pedido explícito de Sabas) -- display:flex +
   justify-content:center acá porque, a diferencia de un carácter de
   texto (que se centraba solo por herencia), un <span><svg></span> no
   se centra horizontalmente sin flex propio. */
.donut-emoji {{ margin-top: 2px; line-height: 1; display: flex; justify-content: center; }}
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
/* Insight del funnel como píldora separada, con el 💡 al costado --
   octava vuelta, pedido explícito de Sabas: reemplaza el párrafo con
   borde superior por una caja blanca redondeada aparte, mismo lenguaje
   visual que la referencia (no tiene que ser una píldora perfecta, hay
   bastante texto). El bombillo es el ÚNICO emoji Unicode que queda en
   todo el rediseño -- confirmado explícitamente. */
.funnel-insight-pill {{
    display: flex; align-items: flex-start; gap: 10px;
    background: {COLORS["card"]}; border-radius: 999px;
    padding: 12px 18px; margin-top: 4px; font-size: 11.5px;
    color: {COLORS["muted"]}; line-height: 1.5;
}}
.funnel-insight-pill span:first-child {{ font-size: 14px; flex-shrink: 0; line-height: 1.4; }}
.funnel-pitch-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase;
    color: {COLORS["muted"]}; margin-bottom: 4px; }}
.funnel-pitch {{ font-size: 11.5px; color: {COLORS["muted"]}; line-height: 1.55; font-style: italic; }}

.analytics-mini-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.analytics-mini-grid .glass-card {{ position: relative; }}

/* Badge circular en la esquina de Dato Ancla (medalla) / Benchmark
   (corona) -- rediseño septiembre 2026, octava vuelta, pedido explícito
   de Sabas: la ⭐ pasa a medalla y el badge de texto "LÍDER" pasa a
   corona -- mismo tratamiento circular gris en ambas, ya no hay texto
   ni fondo pastel naranja en Benchmark. */
.ancla-badge, .bench-badge {{
    position: absolute; top: 18px; right: 18px;
    width: 34px; height: 34px; border-radius: 50%;
    background: {COLORS["card2"]}; color: {COLORS["muted"]};
    display: flex; align-items: center; justify-content: center;
}}

/* Barra tipo slider con marcador -- usada en Dato Ancla (percentil,
   marcador gris oscuro) y Benchmark (gmv vs líder, barra naranja). */
.pct-slider {{ margin-top: 16px; }}
.pct-slider-track {{
    position: relative; height: 6px; border-radius: 999px;
    background: {COLORS["card2"]};
}}
.pct-slider-fill {{
    position: absolute; left: 0; top: 0; height: 100%; border-radius: 999px;
}}
.pct-slider-dot {{
    position: absolute; top: 50%; width: 18px; height: 18px;
    border-radius: 50%; background: {COLORS["card"]}; border: 3px solid;
    transform: translate(-50%, -50%);
}}
.pct-slider-callout {{
    position: absolute; bottom: 16px; transform: translateX(-50%);
    background: {COLORS["card2"]}; color: {COLORS["text"]};
    font-size: 10.5px; font-weight: 700; padding: 2px 9px; border-radius: 999px;
    white-space: nowrap;
}}
.pct-slider-caption {{
    display: flex; justify-content: space-between; margin-top: 6px;
    font-size: 11.5px; font-weight: 600;
}}

/* ── ANALYTICS: grid funnel (izq) + comparativo vs mes anterior (der) ──
   Nuevo (septiembre 2026, pedido explícito de Sabas): la super-card ya
   no es solo el funnel apilado sobre Dato Ancla/Benchmark -- ahora tiene
   2 mitades lado a lado: funnel a la izquierda, comparativo de Tráfico/
   Conversión vs mes anterior a la derecha. En pantallas angostas colapsa
   a 1 columna (mobile / sidebar abierto), igual criterio que el resto de
   grids de la app. */
.funnel-comparativo-grid {{
    display: grid; grid-template-columns: 1.3fr 1fr; gap: 14px;
    align-items: stretch; margin-bottom: 14px;
}}
@media (max-width: 900px) {{
    .funnel-comparativo-grid {{ grid-template-columns: 1fr; }}
}}
.comparativo-card {{
    background: {COLORS["card2"]}; border-radius: 14px; padding: 18px 20px;
    display: flex; flex-direction: column; gap: 16px; justify-content: center;
}}
.mini-delta-row {{ display: flex; flex-direction: column; gap: 5px; }}
.mini-delta-head {{
    display: flex; justify-content: space-between; align-items: baseline;
    font-size: 12px; font-weight: 700; color: {COLORS["text"]};
}}
.mini-delta-val {{ font-size: 13px; font-weight: 800; }}
.mini-delta-track {{
    position: relative; height: 7px; border-radius: 999px;
    background: {COLORS["border"]}; overflow: hidden;
}}
.mini-delta-mid {{
    position: absolute; left: 50%; top: 0; bottom: 0; width: 1.5px;
    background: {COLORS["text_disabled"]}; z-index: 1;
}}
.mini-delta-fill {{ position: absolute; top: 0; bottom: 0; border-radius: 999px; }}
.mini-delta-sub {{ font-size: 10.5px; color: {COLORS["muted"]}; }}
.mini-delta-incremental {{
    font-size: 10.5px; color: {COLORS["brand_orange"]}; font-weight: 600;
    line-height: 1.4; margin-top: 2px;
}}

/* ── 360° ACTION: card de contexto + super-card de 4 palancas ──
   Rediseño septiembre 2026, sexta vuelta -- pedido explícito de Sabas:
   antes título y pills iban apilados (título arriba, pills en fila
   aparte debajo); ahora van en la MISMA fila (título a la izquierda,
   pills a la derecha, como en la referencia de Growth OS), y las pills
   pasan de cápsula celeste sólida a cápsula blanca con borde + número
   en morado (antes: fondo celeste, texto azul, separador " · "). */
.action-context-card {{
    background: {COLORS["card2"]};
    border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px 12px;
}}
.action-context-label-block {{ flex-shrink: 0; margin-right: 8px; }}
.action-context-pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.action-context-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
}}
.action-mini-label {{ font-size: 10.5px; font-weight: 700; color: {COLORS["muted"]}; text-transform: uppercase; letter-spacing: 0.4px; }}
.action-mini-value {{ font-size: 14px; font-weight: 700; color: {COLORS["text"]}; margin-top: 2px; }}
.action-lever-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600;
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    color: {COLORS["muted"]};
    border-radius: 999px; padding: 6px 12px;
}}
.action-lever-pill-value {{ color: {COLORS["brand_purple"]}; font-weight: 700; }}

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
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 14px; padding: 16px 16px 16px 16px; border-top: 3px solid transparent;
    position: relative; overflow: hidden;
}}
.action-card-icon {{
    display: flex; align-items: center; justify-content: center;
    width: 34px; height: 34px; border-radius: 50%;
    background: {COLORS["card2"]}; flex-shrink: 0; color: {COLORS["muted"]};
}}
.action-card-icon.icon-purple {{
    background: {COLORS["brand_purple_soft"]}; color: {COLORS["brand_purple"]};
}}
.action-card-head {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.action-card-pct {{ font-size: 24px; font-weight: 800; }}
.action-card-name {{ font-size: 12.5px; font-weight: 700; color: {COLORS["text"]}; margin-top: 2px; }}
.action-card-title {{ font-size: 12px; font-weight: 700; color: {COLORS["text"]}; margin-top: 10px; line-height: 1.4; }}
.action-card-detail {{ font-size: 11px; color: {COLORS["muted"]}; margin-top: 6px; line-height: 1.5; }}
.action-card-item {{ font-size: 11.5px; margin-top: 8px; line-height: 1.4; }}
.action-card-item-alert {{ font-weight: 700; color: {COLORS["text"]}; }}
.action-card-item-normal {{ font-weight: 400; color: {COLORS["muted"]}; }}
.action-card-healthy {{ border-top-color: {COLORS["success"]}; }}
.action-card-watch   {{ border-top-color: {COLORS["warning"]}; }}
.action-card-alert   {{ border-top-color: {COLORS["danger"]}; }}
.action-card-inactive {{ border-top-color: {COLORS["muted"]}; }}

/* Bullet circular (círculo claro + punto sólido) que reemplaza los
   emojis Unicode de colores (📶🛑⏱️⚠️ etc.) junto a cada item de
   OPS/Menú y junto al título de Markdown/Ads -- rediseño septiembre
   2026, sexta vuelta, pedido explícito de Sabas: mismo lenguaje visual
   monocromático que el resto del rediseño, gris para OPS/Menú
   (operativo), morado para Markdown/Ads (comercial). */
.action-bullet {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; border-radius: 50%; flex-shrink: 0;
    background: {COLORS["card2"]}; margin-right: 8px; vertical-align: -4px;
    color: {COLORS["muted"]};
}}
.action-bullet::after {{
    content: ""; display: block; width: 8px; height: 8px; border-radius: 50%;
    background: {COLORS["muted"]};
}}
.action-bullet.icon-purple {{ background: {COLORS["brand_purple_soft"]}; color: {COLORS["brand_purple"]}; }}
.action-bullet.icon-purple::after {{ background: {COLORS["brand_purple"]}; }}
/* Cuando el bullet lleva un ícono de estado (warning/eye/check, séptima
   vuelta) en vez del punto simple, el punto CSS (::after) se anula --
   el ícono ya viene como SVG hijo en el HTML. */
.action-bullet.has-icon::after {{ content: none; }}
.action-bullet.has-icon svg {{ width: 10px; height: 10px; }}

/* ── TABS (Home / 360 Action / Analytics / Campaign Designer / Outreach) ──
   Distribuidas a lo ancho de toda la barra -- pedido explícito de
   Sabas (décima cuarta vuelta): antes quedaban agrupadas a la
   izquierda con gap fijo; ahora cada tab ocupa espacio proporcional
   (flex:1) y el texto queda centrado dentro de su tramo, repartiendo
   las 5 a lo largo del ancho completo del contenedor. */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px; border-bottom: 1px solid {COLORS["border"]};
    width: 100% !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {COLORS["muted"]} !important;
    flex: 1 1 0 !important; min-width: 0 !important;
    display: flex !important; justify-content: center !important;
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

/* LOGIN_CSS va AL FINAL del documento a propósito: con el mismo
   !important en ambos lados, gana la regla que aparece ÚLTIMA en el
   CSS, no la más específica. Antes se inyectaba arriba de todo, así
   que la regla normal de fondo claro (.stApp / stAppViewContainer, un
   poco más abajo en el archivo) la pisaba 2 líneas después -- por eso
   el naranja nunca cubría toda la pantalla en el login. */
{LOGIN_CSS}
</style>
"""


# =========================
# ICONOGRAFIA DE CATEGORIAS DE MARCA (26 iconos, base64 PNG)
# =========================
# Reemplaza el bowl generico ICON_CATEGORIA por un icono especifico
# segun la categoria real de la marca (Americana, Asado, Sushi, etc.)
# -- pedido explicito de Sabas: iconografia disenada con ChatGPT,
# extraida (trazo aislado, fondo transparente, recoloreado a
# COLORS["muted"] #6B7280) para integrarse con el resto del sistema
# de iconos lineales de Wingman. 3 grupos de categorias COMPARTEN
# el mismo icono a proposito (ver CATEGORIA_ICON_MAP mas abajo):
# Argentina/Carnes: un unico dibujo de corte de carne con tenedor.
# Pasteleria y Postres / Pasteleria / Postres: unica porcion de torta.
# Pescados y Mariscos / Pescados / Mariscos: unico dibujo de pez.

ICON_CAT_AMERICANA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAAmbklEQVR42u19a3RdV3XuN+daa+9zjh6W5EcixwkOoYHIEC4EkvJM"
    "eFwK7aW3vXfIMG4ftDTIiY2SOE5SXunWSYACiXGIgcS6tAx6aW9rDR4d0AIDekmaEUooCaVg8SbOy0psR7J1Xvux1pr3x95HOpJl"
    "xw6xEyesMc6wdbS1zt5rrjXnN+f85jwKT+ERRRGvuugic0b5XP3zn3/HAcDmrZvLL1r3X//m/AteNfDvd91xT3Gdvv322z1OwkFP"
    "xUWfmppSg4ODUq1Wbfv9S7ZEz1eg85j4Od773w2C8JdJGv+j6sHnB4D65OQkTUxMuF8L4Fe7F+l8Y8uWLV01199b1jjFirsEXt7W"
    "3dNTajYbWL7iFOx9ZEqI4ud94qMf+uno6Gi4ffv2dPEcT/WhnyqLH0WRmppaTePjG7L2my2/7ELN9mKQPo9BAx4+bDTq8N7F1mYl"
    "AhrMXQ4n8XhST8Dw8E41NLRLVcfGMhAJAGwYjYZ0gFcqDtZ6cS8RL6+qVLpKSdyCiKDS1Q2lNZqNxnfSNPmU6u3/hwFMNycnJ+XX"
    "KuiYhhCQLzqiiDclYX8gvDqz8R+Lpz+udHetslmGLEtBRGBWyGw2bbQ5aIyhRqP2l7fcdP14YTeCarWanowngJ8swY+O3hy0f7i0"
    "Zk+TJImE/JeI+B0C3x+3msXiMyqVbnT39EJAn3POv05Arz1Yyibafz82Npb9WgUdPcrRbXQzsunqFy8bWPV7WZKenmbZ63t6e9fY"
    "LIX3Aq01sixFmmZfM4H5tg4CJPXknz++7X3fac81MrLDjI9vsCeb4X0yBUBRFBkAfrqFU8lz1LNs4OIkidFqNkEEiDgH4RkQ1QTu"
    "UfHqultuir7UIcAAACYnJ93JqPOfTAHQjh079MjIiN245X1rWMxnu3p6zms1m13eOzFBQMyMJG7dR4QbAf1PTmArVJreuvXqxhL3"
    "LHgajBMKQ3/4wx8yEcnlV7+vkllcoLUJnXNpT++yoFGfvQciXwTR/SWSr91447UPL971AGy1WvV4Go0TKoCBgQEBgNRJk0D3Zln6"
    "G8zM1toH4d2tH9923f9u24koioJJAEP5oqd4mo4nzREjBrq7e1Wz2fhlK7Z/Wuaeu9u/K4z000rVPNkCIABYt26dGxmJKuL8kCgf"
    "MhPES7zrnh9/5/bbPxNfffXVPbt3704mJnZmcz7C03ycED/gwgsvVABk/fr1zlQwRExvJaAvjmMQoXTeeWvPGB7eqSqVSjIxMfGM"
    "WfwTJoCLLrpo7nNI0auMCYYBXpalKUSEWj6xExPrHZ6B40R7wiQeq8qlSpdSzM47AcgrpQTP0HGiBSCAtKyzTkSEmQkg45yjXwvg"
    "xIQhWIgIgAJAIgIRL0p1/foEHOfhC3jpATChiG4myT4muquVcRMApqZWP+MEcSJgKFWr19koirhW06cl4tYAgNIacauxS0Pt7FX7"
    "ZwFgZqbfP91x/4k+AbRz504GBNPT6I7FrRf4852zyDURfqrJ375t27ZYRGhiYr3/tQp6gsfMzAwDQAvoFeB3TRA+xzlbfDjt++hH"
    "q/sByNjYmHqm7f4TIoA9e/YQABiVBAycGQRhSUTakMiKCD1JiOyZh4Jk0Q4nIiGiZywCmovRdMJEADw1NVW8f94idbKHMHToJEOH"
    "mXx6eprcwIBZCaT7a1grQl8pVypnpklMQVhC3Gq+f0WPXF9cHgA4bNRzsuNzpqamZHBw0D0dQtMLUFDxQE/0QyUAsPGqaBYOoML6"
    "FiPuCDWnj3MDyUmvgoaHh9XIjh3meH5Qj4pbROTb609EgHj7q8w5PBwZPAXZfce0g6Io4vZRHrniPYMK5gUEWclMxnkEihAAgIiQ"
    "EBGYFLxnBsMzGE4UMSmIGABeiIQBFiIiESmMrCfGgBd6W2CCPmszaG2QZek3vPj/xyDDRMaLHBKQExEBkROIU4RAhEQI97dmpv/p"
    "05/evq+tOk9WdUTDwztV/7Pv7u4z/Wuajfi3PeR1BDwbQEkgZQKX29cKRBFBA1AEAjHnnB2loJRGHloQcPG+iMB738b8SJO482ch"
    "ImKloLUBE0OW0CbtObx3MMYAImjF8f1G662pbX1hVY+eKtSnOxnVEQGgTVdc92fdvd3vi+NmT5ZlIUBlAJ4gJJjX2QQhLNDhNPfb"
    "fMHb/1+4gLlAGM7ZQkjwACwRFBGpznmWQE5oT8zMIGZkaWa7enoONmv1XZ7SP7zlox94cMeOHXrDhpOPoqIBiBe3pqdn2bOIAGtn"
    "YUyAIAyZQIfuSmn/I4vwpSy0ipL/QADSNEGWJRlAmoigtOJyqRKAAPGy5M5fuEvyiZIkRpamiYDQ1dW9vFGrnW8UlQDID3/4w5PS"
    "j9DFzjowO3swTZIWi8BmWWqzNHkURE4EBAjaeL3DcToMopX2ySCZl0o/s+rL1TnBO5c16rWHBZLHJI4ggXye4ggQ9TPzMu8la9br"
    "lgj3EasMmE/4n5QCEBZDBJMvnoeAvwX272H4vdaGmrnpmPOkCR0l5hDRhtlmQAke/vKwVLo8TdNix+N7pOwVLP5hzkKdcdMdLikz"
    "Pw8Ary8PSuXL0yQ2XjwAMs5mJzUK0rl1JUERnzdBqGyWmRXdfHe1er19Ij5k4+bol0ppaC1Ik/jnIPrSJ268/t+OdZ5NV0b3MzOY"
    "mdqH4mnhiImICHIEEwYhZak989Fa8pzR0Y/dWyrFwd69zay399iO+MDAtJmens4AwIksbxtRIfmFgL7/9qs/3NMVP5gmSaLCcN1h"
    "88Gl0oNBHK9J8/ucHmgjrVxzgU/2VBojt8JSIBPkO0s6MPX+Y550dnaaJmd73cDAgCRJpcTMvd57QATiodlDL8d+DAwMSFfXc49C"
    "sD8/LEB6WpwAIg6M0Ry30EaZyfKePbur1b9M2qGExzs2bYpWALQMAJRSIMj3AnR/9YYbotaxhDIAYOOWsUeJch/DOUsQqXsqQieT"
    "J3MsiHwzTdMUQOC9BwGlffU152+4PLo/DJzJ6tapytEzF4hKnGbWhYEzmaVXs8hZ3nuQUgCRa0prYOOW92rNYeB9chg7U2qjILY+"
    "Tr3TCl6eJd4DICRxywG41zpJAWCqf/VJjIIEP06arbud+JdmWaYFOAXe/K1itJxTnkraFA6s5LD0sQTgoRiptewIshzEy9Ikzr1m"
    "0MWA/X3xOrPeGiJtRAi5Sgfm5icHAuBFZhVMkxgrQFiZpkmBjvAgAd8ri2kBwE8G98jJqJbyE8D6R5nN7mRFzyeiHiIEXV09a7zk"
    "IQDOndVjcK8JzjuI9xARWJvBO5cKBGFYXq6NWe6cA1GulpYENEQgAFmawnuPUhgiyzI4m4GVAjHf78X954EZigFg1bp1J+sJENrf"
    "M/bIyoP6LpD7I2NMT5amab1REwKCnLsz59genQ8wd23uwbJSUFoHAOC9QxLPa530CPNKhxfcajYAkUxpbZRSyJx7kJyZXLvWpQBo"
    "aNeuxyOAYwVRT7iQdRSNmWq1ml5y+XU/UIJYKYUiAmG0MaTNExOlfrxU53Zow3uHNE40UR4EVF4eWt7nf1atVn1n2dPhHUOhsbEx"
    "mpxcRxgGhnbtWrD480mofAwODh5yq7cBWDU5KTt37vRPVCZP796dQ1FSSRMwvlDyWgeGszS7LbPZbcVCaFqYwz3yVum4QVr0N0v9"
    "bnGog4jEe89g9iSiAH42gPOY1fMUKQik1rHovESYXXW874loPlA38StuJiKMjOwwg4N7aGpqtczMfMM/3nIp3XawSHQIAnnvwczK"
    "mAAuSb/y8W3VjzwVdOXGK67978S8mpmfVzhhXiTPOix1aJY6EVEUBfV6t2H2fJCFXdpSpTShLAwpzFICuosr6zAmkHrxk0kS8R5e"
    "69DNDiD9TLUadxaUL3Fgj9EI56jCE8EXga+cNshingqLv3nz5nLKdL54OTPfIB5MtHjxaWRkRA8ODtLkunVuYv1CtvWlV15/+t6D"
    "9hzi1holrldnqGjQMgnCUAu0N0EASVQRfxIPWCPwAiEJSzF5aXjGgfIs33vxlvfe86mtH7h3oXC/qSdxG+8cG8uORT3NCcA5S8wm"
    "ZKXm4/9C5Y76rCMmzZ/oMT09Tc4NmJUrkR48iEF4vC4IgtOcs2ClcvXU3q/1uomiyFar1bldeekV176ZiF8IIsVMobN2BROtFrgB"
    "L1SCIARQBsSAmCHQed1Oe/uRJ0AIBIhkYEoANBmyPxB936bN0f2lSjdazVrDOf3FavU1PwMAqlYxHEXBRH4vctQCCIKSF2+b3to5"
    "ECMd9VlRFOEE12pRFEVSrVbTS694Fxil1SYITdxqtt31OQFs3bq1kZ+U95zGlf4gbcWDXrJrgrD0SqU0mBnOO8yFWqTIQbTzGI+1"
    "TFSgMQDEBCKGFNA4aTVA2vde/Z4PfyGuNfdu3159cOIY1omTpORzK2VbAH0viVuzzAqchyQ8jtLoHs9RhKr9AkiTH3OKokgDwBvf"
    "+MYwhr7Je/svTtz/AfGL80LvBNZmIABMDJVDYmhtoLWB0QGMCWCMgS5eZvFLB9DaQGkNJob3HpnNMFs7mENlwcWs9Re8wd9dfHG0"
    "ptiwenh4WD0W1NWDuQcJdK2sy+y+O72X5xqlXgiinEJS6LPVq588V98ZR5waK0WS32Z5DiCKIqpWq/Yd73zv63t6ut+c2uxNYVDq"
    "CoI8jOG9Q7PZgI3t3QT5sZDsI6GDQuREhNRjJpnmUI8ICQmoBx59BDmHmV9RrnTBewEgpypjoLU5Q/fTdRsuu/ZLwMqvT0xM1Of3"
    "y9J2QU9OTgoA7Jtc1Ro8Y/pOK/5lSqkXFoa50sbY/f39TxrrgDLlAIHWmrxI4rN0tyfcU61W/aYrP3g2s70qDMu/JSDUZg9kAMUC"
    "2U9E8IIHCDIhor4ZYuaX27Ztaz3e+xARuuTKD6w2Pnudh/dJkqzJbAYSWdFo1MthGOqgVPpT5+wL9tX3mdHR6Kvbt1dn169fzwCW"
    "hKl6YmLC7dy5U61fv96NjOz4z6B7z73M+TETklMeOeDOEpGfEpF7kugfpDMtVsEbE4KAWfHyj6f00Zc3btzYLZLtKJe7LqjXZxEE"
    "IYiV8d5+hYSuJ1aPemel7qen//bmm2v4FZ2nYhc/9Id/uOVzy5d3/6tznhS4z4u/kojWK20QtxpQ2pwrWXJdFkj5Xe/64Jd/ESa1"
    "PKw1n9pdYIS/kTOY3fj4hmzTlWONtrESj9UK6rmXXXbZbgDJ5Lp1J8Qe5D0jci0CQBxjFUBKKQUAs0LqXw/U8dKw74w/SuP4onJX"
    "N+qNOpqtxqdA9DOIu+eTN33guwsm3b69aIe2Wg0O7jnm55gEgKI/xWc/u7UBYK59wjuvuPZWkPpu3GqtI8I7li3rDmo199xA60tn"
    "Gs09Ex+6/usAsGHDuAGQHSKAmYLBHEUR750lJSJwzoGJ1oL8BTbtugNAsneR+368hve5zqxWq3bz5s3l2GOISMqZzQCRAJBzMi8X"
    "9pUq/807h/rswVkA3yfVfe0nb7zm4bYRBMC5p9rvh4Z2SbValcULcKx7Q0Ro/fr13N//ei4E6avV6p0A7rxkyw2rlG8+N45bLySi"
    "ZYEJLsiCdP3oNdGPtn+k+tBPfrJHFtuDQ7ihm7ZU4b2Hcw7amDNdlr5G6/AWADMXAXz7CeBjrl8/MaczY9+1FkpeBHBXs1GHEFYR"
    "6BoISmmaoqvSjdrsgX9QWq7b/pFrHu54lseqtqd2avMYnqcocYMDJvziuW/devXe0dHoD9I0eW+5q/uSNEkQBKW3Jq3W2VddFb3l"
    "xhurD4+NISg2gSwVQ8kpiAIP7xGEgRaiQQnsCfWIf9k/M3dfzOpFitUbmLiSJolnorBULq00YdgTx41H0iT++yRObt3+keqDADAy"
    "ElWGh3fOwb8oimipZ4yiqL0T5bHWfHh4WBWQcnFkVICcWxtFUSXXdNUH07T1+TRJvp2myUy5XOkW4OWNxJ5b8G/9ko4Y5qNazEyc"
    "k6ZyZiCdYE/g2YN76O65xaKzQhMOOeeQZZkFgKTVjLt7+yq12VTNNuo3jX/ig/dEUVSqjo0l48TNzjUt1M5SxlSOVutMTOCIgbaJ"
    "iQknIq1qdYxGRy8LAjPw/WZz9jOs+EPOWhAwrUzp9+lne/ZWb6z+R1toExMTjgGgf2F1ovdFTj6nkp94R6yz3oAZujC+KEwzeZAy"
    "xgAErSjbV4QuChalHFXsf3R0NBx99wdWXv32D/cssP6/EkIiDAwMyNatV+/Txv4rQB5MIKblumT+gJz8VnE6gaEhNXcCfjJ49txd"
    "i5eHsiS933s/yMyGSEQb/WR6w96LeAAMIsvMWhHrZqP5HXj8fbAsnC4MbjvWMOc8brwqOhUa3ftC3N8ZHrjkiui1nulPJU76Wn3p"
    "XwH4IgBc+Bd/oW+vVm3bUA4P71Rr1vzHqZmY5xJ5SXrX3DVe3dB8DDjuAYheveLe9KHG1laz+T+CMHxxudzVk7bi3nZLhvam13k6"
    "b9+8AMT/wDp7BxH9jjamD2DvReyTtfoiQlTYKgIcM5Mxgao3al+/9abrtwHAhRdeqG+//Xa7eKdrUj3i3fJ+YE9nIFGIhwB5C4gs"
    "RL7cfn/V5EKb2N8/w9aaZdDyG6LIl9H8HoDm5OTkYZN47ZLc6pYtreGd8qFV/xb1Bj3LXpymifPiK6OjUe/AAOrAiAM2MAPAzuHh"
    "OWnaUtePCXQHAQ2lNeSpREGT+fUlmV/QzmYgnc6WxPvuT8r4z0EgLsqvcrVGfA+EryVRF/vEfXVel8N2JofGx0csMPALA5owjj63"
    "Z/K0WqHz/ZFucvXq1QoAJtaTE1ANAjhrFYALncafTE+ju1olH0UR5+TcIrC1c+dOXr9+/cHLLqveY5XETAwQKZ+406NIHly3Ls/6"
    "SOErnYDtT7K5uuRuY2Y9HEXBEGAHBgZoqaDX9u3bk45kDLevSVTwg7Duf3TLLe+eWXhqxgSodkBXku3bsRQ36ojPXjC1KYoimq4z"
    "i3hYaxEE4TnWZv+zBfk8gNncxHXMtmvXrgK++UcA8TkHByUQv2h29qN96/Mkh4wtAe2Ok0ssgD+srp2oVtNqtepLpZLvgIWdL2oH"
    "2gqdLQDkr2/481qx+NSRxZKiT1EnQqIoivjCKNLDO3eqYq5OYdNhXrk4x8ZERFTREwNBGJYAPJthwxw4DJBe8gyVAcpyagkJyl74"
    "xQ3MfhvAdJGcZjzxxXxHir8sOdrYfM+ePWp4eNgDwxga2tXuziW7du2isbExRFE0H1KYXCdtrziKojxJf0iiOJ9nsrA9505PE+64"
    "A2O7dkl7rqmp1TIzuIcOUyFqoiiSsbExiCdetLpyRD8gV0nQDl5ZayEkFYi8XLN8HcB3AaA+tfp4ngBaty4n627cGHUTaJnP+aqQ"
    "DkjsAe5IhLtDF/Gxx1I+wuOZZ4kxZ5/euWVsOo/qE7z3AojlUtjOFSwtAJtZEdHknAUThVB0tog/bc5Rmpl3lJ7oMTw8zHlkdsT4"
    "AOeD/PPbpU2AKC9enLMg4OxLN1/7GhEmCBsTIM4y64kDJ0I+rxW0YGZxTgkzi7UZl5RX3jNBwzvPeT7Ap0opVswsUpxsclQH02ya"
    "WbfEBmWtglJmnRO4xLkcpitlc2ipwsC6JAUALzjDeycF2YEEgM/i2YmJCfe2t/220UeOO4kQMQVhieJmo3vOURo6fru/v//1DEy4"
    "MFzeZ4neIiK/6axtmyr2zmWp8yDgDSB1AUNISMg7eMUKApeX9BSISZwHwwMe0ExwIAJ5gidhuNxQUM7Oc9bPVe4LxIuDV4chwHvJ"
    "iFlABK+VW4QdUtJqTtX0pUmaeRHHSpUJ8I/MNFoAoFbtPZIAxHQUVZ8wKNoOFaccdCngN8uV7t5Ws2mZSZdKlcCYAF48tNKBCYL+"
    "dr3A4nh2m5nXfoI8FZwbw0U2BkQMYgIXzOvOOeZzx8UkRX64Hcgj5g74tbBMSyDI0gStVhNpkiCJY2Gtlz/v9GdV12y+7lOfuOHP"
    "f7CkAJzAEuHhNE0HAdIACMwnNBFTKsXI0nKvNsYXyQyJk3g6juNZArSQMAm8gBQBLCREQu26wnadoCeSYu2I8uugSHK4kzPA4CQ/"
    "NpYAC4iTvGKoLQNVeMYEmVv7du2bh4gnWhqQ5H8GBlCGoC/LUl0qlfrCSvmyer2WjFzxnm16Ebb1AJBKs1HiZf9ibTpgTHhWO0N2"
    "IkdmtVBBLS2WdR8DHwFnn3dZsIK1DFpRgRK7HKzKJAiFEJCDF/iUmDIRxCDEhdIIBegV4T7AawE8iIg9zwJ+ryPsDQN+BJ5n4zi1"
    "WlcIwiGppJdEQvISWFIleMkM53M6tk2fmQOpS2Kl9CFaQqsgSFKXGePXKpa3kqPfcc6f1mjUAPa/p0Wfs+AErCsYxhVrG97Iv4ng"
    "PKXUWXmBPDkc31wAdW4CLzTAAqe1hggOitCnjdefvXnb2CMA7n1bFJVcvawGsunujEygCBpijTC882SZtEPcqK9cFR68DbfxUPKy"
    "Ht+SZQQTCnKmBQHs4NMyY7boW3TYEUUR74YLwqnV7palWXFHGvduvCqaIUKPUuqtaZpYCJ0O0JkLBLArZxjTzTffnF5y+bU/0ko/"
    "oIjb5+6ENMaYnFxXJCpUV+7wKhAjgdBP67MHmu3rPlOtFjsbjSPN97YoKp07fa5s3/6hGQAzh7tuZGTE6N7B5WJR0QHS2TL2d3xG"
    "25GLj/V52oG7T95Y/Y+Nm6NJpRR58cbDstZa8eKMWBRFiohkeurcXwpoKieNCYipZ3R0NMwXadLhiW+SIQCo//V5MqZMmAYEaZoC"
    "gn7Avb3UVzr/WCb8s8vefUqp4d8kasXrL/1f7+rvWBS9+P61PuXF5Om9zPQ3PsMHK3W/7ol4qHbU9F2XvqufhM/w3sF770DESqkl"
    "/QDOA07r3cbNUZzjZA8RrHZu5XOGh3f+uOjtdlxOxGCRn3YOMSjn9gASEujlAF2zaXP0qrYjRkTZIuBMQkRcqDGBnA7Bc0CSVp41"
    "8Lubrox+IqQ/V61eex8AXLIlWsVCrwuMWeecP8d5d75Wao212TryHGzaUp1USpGzdlqIp8S7CgF9EHRT0cSkyFNKZ91s0aaEkDct"
    "EQBc93K6kHu590Cl0qVqtdlvp1n2tSPBUIJE1E7Qi/PPI4NXr1y56z4A9eHhYZ6YmDhuqihV1sGbohyVLAGBMaU3KK3f0IaPzKqN"
    "ZDracRVQBbnwvHN5hU25jFbc9CQuvOTq6z4fiAqty14GksvLle5zrM2QxDEAgTFhn9L6LVprEIBarTYL8b8gQi8JDepAV7QJFoJP"
    "og4gSu3Q/twO9d4jSxN478Q51yKRf/jER8duOqIjxnoMXvIEPRGGiHCRAF8AUC8cpuPVZpIWKSciJnLOzjX80NpAm3bfISzqVzHf"
    "/YCYwQCarQaYmb24y9n6P3HkiUgqIjg1iVsgZpggmI/MiSBLUzjngJy3fg4JsUCMcw7exwv8DqZ2HxNCOzPnnSt8lKLixQRI07SV"
    "xK0vEdQ3DxuKWJigF+/FcVguV5IkOQflPJL3eLg1Rw665X7ObUVGKWC9MhMo8TKXJyUGl0olaB2gVjv4SJbGdxBRTfKmLgaQsuTe"
    "UgaASXIVJfArRORsbfRZy/tOOcUEwSkEwDmHmen9iFvNHzLoRwLsFqYGcjXzbEDWKaXO6u7pYcWqJCLwRaI8J/nmpyzPV6cJgWqS"
    "p+QaEDFs9GlhqQxrM6Rp2lJalyRpTTfqyYf/+tYPf3/z5q3lIzdu9dBExBBAKS2QpIfp+DT6a3OBbi+4QJlgCIJScfoYIPJe6lma"
    "1l3mYoJ8DV4+w4Hfb21FPCUlEvSKwGtwS2tWkvpWAnhR/gwFvtA5+4rpR/cOzue7Qd7Lbmb6Blv+5s03R/+ex6Oi4NQ1wcs8Z2/w"
    "4l9dr9cGqQMqiwgDBBJyQj4jUB1CUyDsz6kMmAEodDZ7SdO6QQLKBPQppYjAUu6ulN5+9Yd7bKzTI5+Awo1sd545nuyITi5Qy/We"
    "pYjOA1DJbAoiUkppsll2l7N0iwK+nxEODPbx7OTkpBsaGqKpqdWUDO5RTcAPwVnAYeyGMSGQDEfRvSv2Jt/1pe5b4DNjtCXnNGmt"
    "SVmbJElcm5k5rz6fGaumIyM7voXuPbuUx1+JcUYSeGNCC8Rz4Q1ltWRKixd4Jy0b2i4L1HNWQ08vMNvo5rJj58NXMfwNzrkSMU4l"
    "Un9Xyhrvu/nma/7uEAEsYEEzHsyS5AHxciqzMiLijpcQCi6QAwDSss6Lf70iXbLWWa2UVkohy9JJ28i+8onxanOR8zbnQHfi74ui"
    "MRVhrq4hPZIfEEURb968tZz0zqpwdtZt27ahhbxPw/5f4bEeBYANl0dCCo9kWbpKKWP6+pev3btvz1oikkMEsGfPHplff5q0Lvs2"
    "hH5Lm7xcMsyzT0/46OQCkfAZWvMQEcNntklEOm9zQFPj42PNTuCzefPmchyuKjGEszShLpltbNu2rdXuAHn7YRa7Xq+XW61uWrkS"
    "zWq16ovrFzCnN0ZRtxzEqsAok4k7+Mkbqw8foxfGqFY9aTRJ0CwgvcStZsZCjTnMvwStIt9OLtlNJHcTock5N8fbuqXj4IQt4AIR"
    "pOD4Ewjwcx9Hki1OyibS/QZlk3dKkl6jha5O0PuazgT8UuOBZrOrhe7zJMDLazUMHPbCunsjEf7Gg75KHldGkRyb/SucMJMiFuFl"
    "xgRFpFDaRI9DUVA7SxRFEU9PT++n0sofOOfjfAcCCVwIQI5/wQZ5ACwAOWd9mgpD6M0brxzrKVpoWQICgC4QhzMAhMXJeMH+Or1q"
    "0+ax2TlaCxeRUMCLFxGHFQDWEpFJgN2bNo/tERJikPIQh5yF1E0e57NSryiXK2jUa8P7atf5jVuqdTiniJBK7qTwnDPm88odT54J"
    "YBJlCldygCCnZWmaMJEulcqmUav3Hg6GSp7znFLj4+PJps3XPQDK6Rog0lqr04aHh38+MjLiNmzYIMcvQNfebVIChDObwpjg1dqY"
    "VwOAYgVibrdBmDdbSp2plX4TtRMpc3mAnMsx183R5U0WWan5jo2CDnacwGYWWZag2WjABMHaIAj/HHnLNXjn8oJxVh0IpTP/IHDW"
    "od2HKYlbsDaTsFSiuNk8APEPH04FAQANDubIS3tXQ4GZASoL6ILTzz53NRH5dgrxuKflc6oqvHewWYb8Cz/zZh6qaHvZfuWV/rQg"
    "B+69h/O2HdYoWm1y3nOCaG7B5pM7+b5SWiEIQoSlEowOikW1cNbmrTSdg3N2ztsGZK7vhQiQ2TR35mwGEdiu7l5KkxStVutjyPDl"
    "x3TEOukXNssgIr0i/nfiJn8fwAN5enLoCbcHQnm3TGYGIPd5Z1MB/YaIkLMuY63QbDVvg5fbQWACNOXh8rwMReDB7VZsVPbwz2HQ"
    "KiEcIMJPRKQBkMq7cnoPkGKS5QIOxEuLGLEI4iLtpeYq/YVWCsmZIDqdgF5AagLsJ8GsgB4RYK8ixCKwAgwQyTu0Nsusdak2hrMs"
    "u816++V6rfH5z35q656jEYCklDCjRNZaEKFMrF4CJ2cD+OeCnnE8gKknImitkSSySwQ/J6IKiE9jxUEQBLBZ9o1P3lS94Wgmu2T0"
    "fS+CNs9mj4c/flN051LXXH551Jf1lUvlOtUWfXno3Bgd/cDKVKcvZcIL2GOFJzwK0H0kss+K/HzHx6q758Lb0Y6KqU2dz8wXKCVh"
    "EASoN2r/fOu267a2w+SfqVbjx/wKE6VUUVqbZ/WDsBQmreayxTncJ2z3i9CmK68TJi7axqopwN8lgmeRdxXWanmumHxwtHOeMqC+"
    "D/gfATgsx/VjH6seeKx5tm9/777R0dF/SSqVO0tpSTVM7LrSVemDD826iYlFtcFTyKiCL6Y26wlM8CLK03rtLsQIp6bc0ZyAtj7T"
    "7brcQtGZzgr6TuLTIQmWo1ykB5rNcGRkhxBRtmnzmOvQ4RkRP0oiD4lInYiWExE8GCJCV111YyU2WUlmkwQrOybcB2AlYAE/OTmZ"
    "TExMxBChkSlU9CC4/fv2tUoNZAMD07Ib4HAKrDV48XwrVyKtVqtLtnEbGRkxwKBBf9noUsvR/kdDD3nIp7bGYdH9C6qnTaecXLfO"
    "Y3ycjvZLfDLv/Twdj9D8FdvOH5HMBEi4QB9lvkEKD4HoAIGe1c7bj42Nqa1bq43Hyop12HMZB5rHAyqMj49nizxxu39WXqgDM1gA"
    "GCHAtmnywzvzOoHDIpj2V0pRqjMi3B+3Yk9F72Y5jj0jRi770BkAnZ53WQRASNk3d1ulvwWh+wA4Zy0YeMH+Br8UT9HRbDYNwL9d"
    "KpXXOmsFIhaQOU+7P69MFX14fk5etOF92ALSXV7s81nMgM1SBdCbNl451kUiOVTxvqB152ghbzFPQnkU2ReNYSE03wtIAJ+3ZCEF"
    "BU2gzFswKD5bgN+0NhOttSXv4yw7uK+sK81MYaZUKqtms2m99y9k8Lsv3TL2g4KqfsK7ucp8y4ROerwSwDa8LAfw/DTJGGDp6u41"
    "Sas1ZzvvL3pd68PnZy/yACgIwmZM9ptM+C9a6Vdam0Ep9dogCF8757XNtXaex8BtElROhzy0rXobNzMxWDG8Fwh5sNZF5shDKWUE"
    "0MXxPrDxyujHSdKqMVOP1mYtK16rtXkzPUlfpDHf0poWJrZzOIy41RTnMgRBiRr12h6BPNCu4Dnj+c/3RzTCRQFBUK1eGY9EY1/l"
    "Gl1YKpVf2Wx6ZFkqVPSSW/Dch/DopLOmYsHFbc8xPyZF6o4I7aQ1M6sgCAGQmc/RqX9KkmS10ma0q7sbtdmDeZvFdsvFEy6BJfJ3"
    "RfFEQSi2ff0rzIGZaau1erv2uGt4bMxMANl43mr/yChoampKAJLxKpqbroy+3oqbL3HenaeUpixLJWeiCR3+hgiHa3O5gMTX0Q6T"
    "ABuWSirLsnqjVvusEHbm1I4xWdE79pOH9icf16H7ERGGtTavyL/cwToA6oRLgeYcNOl8T0BWMWttQkri+OsQ938/9pHoa53Gt71a"
    "RxTAzMxMO9ygvHa/iJP4Wwx6QRiWenxqHQgL+1nS0qnGo3K158+TC4LQZGlyoDVbv+WWT75/V15ZSH5qakQ+NT7+UwA/vfTy6JSu"
    "7q7XZFkG710CIDjx3yZDSzx33uYn7/oWoF47+PVbP/b+Tw8P71T9Q7vC8fXrF6Cw/w+ATRKwfu512gAAAABJRU5ErkJggg=="
)
ICON_CAT_AMERICANA = f'<img src="data:image/png;base64,{ICON_CAT_AMERICANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ARGENTINA_CARNES_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGAAAABaCAYAAABHeVPzAAA01klEQVR42u29eZhdVZU2/q699xnuVFMGUgFCQByogBPajjSo0GrT"
    "jW1/3ur++UkHsb8KSShCJSAow7mHoYOGEEMx5bYiaW2HVGs7D58jTrTagG1bhQpIFEyFVKWGO51x7/X9ce+tFBlBoNv+Paw8eZ7U"
    "zbn3ntpr7zW8613rAM/JsyaDb3mLUyzukIe7hp5bpsOL552ufP/uFADWXOK/radn0YtnJicShvnsrTf5v159+cZuROHZixf3LpuY"
    "3B05hj8aCChi866M5S4M02SaiH5w643ePWuHrjwlV+j+C6Use2p2+ifZqvmpem6JDy9TUy+WwN2p53lismLe093V85cm1ajM7H0E"
    "wK91EL/IkuR1dS84sVarIE3Cr1Cqu3PZjs3ZbB7R3scBbW4H+N+YvNd3dHb/g5IKlZm9I1EGgXhuiQ8vUXSyAYCdO2EDHNRrNTSC"
    "GhiiDgASOAbMSWV2BkGjzsZQDDYWG0YYBjDMEYgKAwNlBSNqjVoVtVoFzCSNwDHPKeAIMj29iwBg+XKkgGikaZzoNEkATgCAhZFM"
    "FCRJlIC4GoShAQBjTGp0mhCjAUYKACQ5SZMkSZI4ISKtSNrPKeAIsmTJFAGA7/spMzMRWQBZzEYCABnEBAgiYQFkWUq1/CorABYA"
    "ASLd27uLmUmCyCKQZYxRTETPKeCIcuK+iIWI23GLEIKbr0kFxkHXkZvvkYaNOwYIYubm6wxIstikhecUcAR5cF88JAA0V71pYpqL"
    "abQNQDSXuy3N2IaZwWxsIspmd0KQaSsAgGHLgDLPKeAIUuiZYgAoFqFAUE9caDR3Mswh15FIKBCyWtckC+L20SCQEs8p4MjSBxgA"
    "WNrXlQWzheYmBlHzMAgmBxCiZV2eaIKYQUQCzK7dK4Qhah0BBgALZLLPKeDwQmgpoB7M5EFstRfaGNGyJMgSQc5XgNqnARARAKhc"
    "NqSmCeKmFyBIZjwXBR1JfP8aAwAitfMAWXOWR6WmGVpSrhXtHFSEECCGG4VH03zn3DwB4rkTcGRhMDNZhvPMsPedAMPMTGCTZ4Zq"
    "vk5PiIAYDCEEQHAlsWDRtkAMAmyCfi4KOvzaNxe7VCpJAmUI7YUGBAkulUoEQBExHV6FEHEUUjOMBQgEEJiZ+TkFPAkZG4OANBb2"
    "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"
    "SUVORK5CYII="
)
ICON_CAT_ARGENTINA_CARNES = f'<img src="data:image/png;base64,{ICON_CAT_ARGENTINA_CARNES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ASADO_B64 = (
    "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"
)
ICON_CAT_ASADO = f'<img src="data:image/png;base64,{ICON_CAT_ASADO_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ASIATICA_B64 = (
    "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"
)
ICON_CAT_ASIATICA = f'<img src="data:image/png;base64,{ICON_CAT_ASIATICA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_CAFE_B64 = (
    "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"
)
ICON_CAT_CAFE = f'<img src="data:image/png;base64,{ICON_CAT_CAFE_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_COMIDA_CASERA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFoAAABgCAYAAACdSWXJAAAdCklEQVR42u19e5hcVZXvb+29zzn17KYrCUnlC05AEO1kcHhcFHwQ"
    "FRkvcufOp1Z7Z8YPxlc3JEQguSg64qkDoqLykEBiekbn4uhcTXm94+cLB0fT+GBUclVMChVxADFNXp10vc85e+91/zhV3RUMkiAh"
    "IT3r+5J0+uxTdeq3116P31p7F+Eol1KpJCuVigGAVVf6o9mBwY0A0KxNj80fxD8EQWD7xxytIvCcFAZJkQqCwAJApVKxAOg/gX6G"
    "xALCWgutNayxrxy7yj+7h/ymTZsO8FmYfN8XzEz/CfShCEEwW+g4AsD/XYHGeiBu27ZNHuAGDoKAiY68sqsjbgSYaWSk7GSGIZYC"
    "Uc8cHFAriIiZYa1FNj+gWo3aC8rlMgHgqakCPamdOQrkiANNRAwgeqpxvu+L3fXZFUhEMRP0AfUeYN/31d69WNzS8elO2tu+4Sb/"
    "x73X+UOTeUybjresXZtdteqaeb7vqz6w9pMgCCxjP2AdBnkHiFIEAExNuUNW0NvTae9TZM07etcnJyflnLHR/c5p9XtvWJA36Q+y"
    "635vdwundbXOOeDDigRoZoZSCgTOPnHM8PCwLJU2SZuKTmDCpYX5C+cJopnX21ss0pwBemxsTAEg3/eVCeM3ZXODF2dz+ReywZ/5"
    "vu9Wq1XTW+bd0A2XXemfZGJ7GjOzVI5utVo/IEsbgiBgACgUpnpxtK1URkzMwhNSHC+EtJbI9CZ3aHKS5wzQXa3iIAg0gHPzA4OF"
    "ZrNZE4AFlope8lGtQnWdmSCiN0olX8vWUCqVVmG7dfcdtwaf7F6nJPoDyuWyefu73rtQxPo11tp2HIcCjEzXaaJYLM4ZoAnVZf1Z"
    "nLXWgmBdS+KBIHhr6Pu+CwCLFiWRRKlUIhAuTKXTL9DGwFoLEmLqCXZZ9JxrWriXSCnfDyCldQxiNj0HWD1CyvWsv6nv+7JSKdlV"
    "13xo3sqr/A+yta8I220IkikS0iSh2hQBQK02QN3Mz4DZyWTyZI2ph2Hn85LMd3uvWalUeHJycsb2WsKSgYEhj4io1WzEIOzsXRta"
    "vHhuaPTUVEECxIxwiIB3pDPZE9utZmwtP4o4tgCwfPlyC4A8LzKlUkletub6E0CkQWSJUAvD8B/Cxs6tpU2b5GzS2L9kuA1CDBDi"
    "KL6HGd/uXTt/aMjOCaBrtURbKYIAkXAcl2MdTzHsXcIkmrd9+3b2fZ/Gx8fiJUuWuIA5l8Hzma0AKFau2DY+Ph5ntm07YHTCRCyE"
    "cIgIQoov6+bk3b2QsVQq2blio/vCPLAUAsxch8AvtA6bAFBdtmxmeQ8MDBhJHBORBoOZwdrWNQAMTE3xkyRBBpRoORtE4+PjcS9D"
    "FELwnAKaAMGEjLWWlFJDxPRak/YW+r4vhrdtoyAI2Pd9VS6XY0D/BGyNtYaIUEg7C65fdaV/VhiGthcG7jeBlrNgCGaGcuSbL7ui"
    "/OZSKTEzb3rTF+ScAtoyNIGn2+22dV1vnpTqv0qS2SAI7NTUlOzyF5KI+PabbvgPYtrb6bQhhBzM5nKXQohXdjUV1WqVnkCitjvt"
    "jma2yOZyrxKCX1+pjBgAqNe/q+YE0J43aQBAE/Yx6P9qHU4q5UBrbRwycZJ8FBgAwjBlZ82MuK/dbu0SQiCKQoDZ64s6TH98LED3"
    "hZ3mTwAYIRUAmgkn8y8pHBHT8awvo/vuu483A+pPPXQaRv4axp6WSqVPCcNQG8Opc85dsSvt4bcTExN80nsuptLwME1MbMZLzv3O"
    "Y1bbrOt5ZxtttDGxPOvcFbX7/v2eXwDAqaf+tdyy5avW933VaTo7DYcNEvL1rpeiTrtdO/vcV08OX3DJ707BvnjFihU0MTHBx7RG"
    "ExGnp6ZkEAT6kx/7wC8FiZ0kBAHsSMf5Wwt6VT+7lpgF4ttvDn4BKX5EQsBao4jEq8EYgbUEAI8+urVLJk3Jdev+bpdyMvcyg3Uc"
    "CSL8GcDvyDYfPi4IArt48WI5J2x0vjCzfAlgxxgNIqJ0Oq0YmD+TXHzrW/3PR1IgB05CDxKCiYj8bmp9yinJoJ7ZMdB5AmCMAQkx"
    "COBkI5ECgK1bt4o5AfQMscMMJjzWajY6RAQiYYn4gEu65PuOtVaBCEIIWGsfJsb9PVKpF4H0skqHZMgAhFQA814GP9gx6PSPnTt8"
    "NBGzhUtCCACQQgpmuL3L/Q6uEgQRmPZKIaEcZcD4pjH8lR6pVCwWDQC84hWv0KOjfiaK26cAgFIOGLyVIP4eWewD88zYZ1OOSKjT"
    "zwkTuJjN5tx6bRpRHGoGNWftM8Tw8LAGgFWrrpkHohOZGa7rybDV+fn628pbu3H0zOuNjIyYy68MTodwRiyzFIIA0CN33OzfDQDn"
    "ASoIAjO3NBoAkYiEkGC2ttNp/RCCftC7tmRJTQZBYJmZ4LrvBvidURTGDMAwO/s7zNnPYgVf4KUzryOCMEZzPxdyfDKO5wTQw/0k"
    "kKBYCBkSoWXj+FPCcX6wqUsWaa37xgnteKklruc57WazQswTvYywUqlwtVqdrScynzJUmJ8DhGm32wyi5hOzxzkBdD+lCebBXH7A"
    "U8rNibR33x0fed+eyclJ1Y0g4kTrywSj/k8Ydv5Xo1n7eqMefXD9J4Kf9ieaw8PDCbfBTGDcU9s3VXVcR0VR+HMS+E7PaQ5v3nxE"
    "SKUjbqMBrkdhG1rHsSWb6kYODCQF2WRMwPMH/Z9Wq8vfAVTQq8D0wOv+rAFgbGxcFYsYnw7bv4kj/XkQfXrdRz/wxXkZS0EQcDAx"
    "YeaMRg/3VbMF4Wa2+nWAfb2rxYMAKCGS9if6giCwlcqIGViyZPCyaz481Pv9JZf4qVKpJGcjle0mCAL7k3u/9W0Q3mAp/89ESSPN"
    "DBVyZEi0o1WYfL9MDz3USA/Oz73IEl4olVrKRj/PMu0ZGjjud7v37nlg/Lbr/y3hmTfJHnHk+77qaTgAlDZtkpWRkSPaBHnEgS6V"
    "SnJo6HxRLG7nbtjFAKhU2iQqlRFz6RXvP1UJ9XFIcVHKS0EbDbaMwcEh7Nmz837hOeeHe+bv87yOWLfuinDW9DOVy2UJwB6Jhpmj"
    "wkb3S6VSscybbNIeF/Qq2jw8vI0BQEp5KoMuSLketDHwvDQAoNmqw3Hd0+Iw+r7K7XxbIa//fXR0ozM+PqYBcNI9xuZo6Ls73BpN"
    "pVJJDA8PEwDRS43/kITLl1tv61aR/NsR7O5+tWW5Rkl1vpdKmWa98WMQfw0ArDGvKcxfuMIajVpj33nrbwruGR31M1u2TMYXXVTk"
    "KiCSVP9M7C1uJwBYdIBneLxQYFSXmZ7Zea4ATb0s7ZlYrquu8tdn8gOXtRp1k07nqNWqf3j9LcH7AWDVmvL18xYset+eXY/HYPNX"
    "Qs//er/peLrPHgRl7sLyjDrNZzTqYGZUq8uoWl1GT7cn+eqrr87PfnShZJcG6bSbmojafTRJXseRAMiDkBeb1PRr3nb1jfnVvj9Q"
    "uumqdNcpCvDBKZPv+1StLiPfL9NRqdG+74upqYJTKBQ5CEb26wq9bO21Z5KVZ4H4vzhSHWestdwVEDExMyfdpL2ZkgRyiBBZwIJx"
    "huM6fxLHsWBrrSD6BUAPdkefphx1Yqw1iFFnwq/B2A7ipGuJoalnoLvv030/IiKy1kjX8UjrcAdr/tL6bvTSk9WrV3vAySgUpkyf"
    "k372ge6mtKI/jFq79vo/iRWdJSHR0a2FxPQSAp2pHHdZOp0FM0NKCSEEiARIEAgEEM08SDIHyf86nRbCsANBAkQE1/PguqnutTbC"
    "ThtCCAgp4boelHL6OBQC9zGuDEaPyzbGQMcxpFJo1KdhjPkKA1/MprPNTlhvtUTne5/+2Mfq/RHMyMiI+GP2yTwjy+Qta9dmh6JC"
    "xqp4jZdOXUNEiMIOiCSYbdIjwNxTLQNiA8ASkwV1NYXB3Kc0BIBBAtQzbwwwWZrVLAECMQBiMAiW97NXBMzOH7rzR2AIECQApzch"
    "RAnPlE5n0GzWdxjL78kI+lqjgdbevVVdqVSiPxajQw7vSqWSHB4elkEQRIlT8l9gLT7jDrjpdjsuaK0BBpRy4boeQARrDdgy2u2G"
    "BfBjMP0MzL9lwY8Ti2kQGsRoMVMUp7WlNoSSwmHLKUEyBY49yyoSQkaAsSQEs9UpAqfBbC2Laek4NWusYYcFh1aCyZGElCEoYeAK"
    "snkwCgwuMugcx3HP81JpWK3R2xcThh0AdDwBQSzVGiej98zPDn8RwHoA2FQqyW3DwxQEZQMQHzaN9n0/FQRBJwH42tcS1OnM9jQv"
    "nfmbdDqDTqcFgoBUCvXa9HYAXwd4BwkiZiZBtIcM/coSPczS7JLh1N5169aFeBakVCrJxYuH80bpIWvVixg4y1EqZYzJMnC2o5yX"
    "eqk0jNGJORISnXYTWuufea53Vxi2fsgD4u71QdDomc5DiazoECeFX/e61d4Lz1i4TIf2467jvApCQMcRtNYA0S5Bcp/jOgg7ra9Q"
    "FH3ojjs+sucPRCk0MlIRQ0PfEnuLRUri3JMB/BqFQoEnJxdzsbidNwNY8QTWr1gscrW6jHcOb6NTJxeT520VvXu7zB9PTk5yX5Xm"
    "STPES6/y/5qAd6W8VCEMOyDQIhKUF0LAcVy4Xgq16X3brKCPmNq+u4rF/L7NmzdjYmJCHyx48mAd3/HHHy+q1Sq/9qI/v9CV3pdI"
    "iFPDqAMhBEnlQJu4DYv1LO2lJPOfZskTOx+r7qtWq3yAeFUcf/zxogLQMLZRPp/HAoD37dsHY3axMYbz+Tzn84k/Wtq9MZ/Pz/wB"
    "gAULdtFSAPl8Hf33zt4/GylWq8uwbBlEqVSiiYmJ/R7ojNNWPKSALyMlPsU6+hogFgNYlspkwNag025DCLGArT5HOm4qBv3m8ZOX"
    "Tj8yMcEAExD88Ro9OjrqbNy4URMRr1pTviKdyb1FCDqr025DShFGUfQAW1O2JHY88P9w38REoPEcl7e//b0LvcHUcunInI3iEy34"
    "ikw6t5TZQhsz2Wm0/sf4+hvu6fleoqe210/pDIvFIhERl3zf5TouzmZzZ+zcsb0BkHScTJrBTYfFz7SA+6fnpFYsP/O6jCBmY20s"
    "JLS1lgUJhgGssAQoCGGJraDDS9NqkBAGDGusZSEECytYCMtxchksbE/RhGLhWCEIZEM2ZhdJ+0DtcTuVHsTJUolRZrZRFGvXc4qZ"
    "/EBp5f/0awB+drD2Wj0VVRkEFAPA4pY8UbPttFp1JhIpACJpzaLlWuLLAJ8g2A5ZAiwzAxRbAwuSbC0sERiQEmBhDUmApUgqp4eN"
    "L7OGNQERQWq2YMNsrCVDBMsCIEgJwBJgrYALZstMHSFVizVP5wr4lQWFzDzfshHWGhF2bDQwMHh5NN0+hYhe101uXADh0wa6VKqI"
    "SgXG9/3U7hovB5DT2hjqZhnGWE0EjxnDUkolQCApwBAEZpf7gthuFoH+OPdwE2tCsGJmNUNcPKFlhGj290TUdfcMa2EB0gQ+WQAx"
    "CMcZrQFYshYmlx9ArbZvSe91CoUCHZLp6HG4k5OLCdiC88+HBZLqhYD9nQGl0qmMCjsdDRh4Xlo5rqsAwFoLtjZ5SXqi8af9ihuz"
    "E3D4uUn6/YfpS4h6lwi9ZKmrQ4IIrpTSBQjNRh1xFBrX86SUTnrv3t2bQfyF3l6bWq1Go6MbZ9LSXxa380Swv686KGfYa49ddVX5"
    "H3P5gVKjUfdIQLKxNQbVqZs4zzz9USp00E/H4GS9WQITgxZKISCkUiTQbLfab9x42/V3H3JmeCDeYpZYKSzYOLpxx9j4WMzEn2q1"
    "6vOVUhd5qRQa9drt0uFPog0YV0op9VF9ZsZ+0gaQfpKfAYSQngcdGoUUCF/MDQyeVqvtm2aNrxsWDxxESKyq1WXc47mp32OuuuZD"
    "82wnfHs2lz+h1awzSAwQc5aJmrDcJOK8ZXu666WWp1Jp1Ou1letvLm/AMS4r15TvHRqa99K9U7vrDH6QSFQJqDGzgRCAtegyhVYp"
    "V3ai5r0bb73hcwBwnu+riSDQ5Pu+aDRy6YadPllBXQiivyvMm59tt1rJWkv29EGQALNFJ+yAwfDcFDqtpt8YwEcBwDRyUuYa5phB"
    "92GksBQd9Rgy3iC+ncsNvrjZqEeO67iO46LbLphwXV2HmmzlUKjXp7eC9bv3NVtbPrswt9vv2mhauSZ4NTOXCThXKSmM0QYgeeC0"
    "GVoqqTwvhXaz+b47bil/GDg6Ks3PpFxyiZ+6886gMzrqZ1QW38sPHHd6vT4dEuA9hX2PHcdTcdwxlukG06zfPj5+057uFmB+eS6b"
    "e5nWMWkdw3Fc6Xqp2dAsyX9gEoZLYU4KgwChlIM4ji2B2wBcgI2QKuWl0xAkEEWhw5aRSmWV43pjTaIHAfqcuvzK4N0MvhAAhWEY"
    "MXPM1t4fR/EvE1fNEsymG2kuYeAFSsoTiAj8JL3Mx5wQ9U6xMdrEjwvib8HyI5bIESSMtiavW81BYSGYcAosXhTrKJ1KZxZZwjtX"
    "rS0rpTznxljHaLdbTAQXoAmQ/MgdN1/77d8rll7hr2BBa4noBEEC/IQdq8eiZLMDHKJuk+IANDNvlRq33nbbdfcf2HH6LwfRewTJ"
    "i2rT+yyBznMc9zzBzACzcdykH5yJ/n5eTt9zwMWjYAnW9vK7gyFTjgmFZiZmm4TDTAtjhdyTjd3122X3MuGzjuPAcV1hLVtmhtJa"
    "R4njZMnWTjPEr4Mg0GvXfiy7LXpUL6wVqLU00VzRgLI8u5Xs2NfnJ1ppEAAXFrnR0VGnWCzS1NQUhWFo9xaLNDQJNT4+0hq7wv9h"
    "HIf/JpVztlLSjaIQCmCHAOgoAoMfAxsvSWAa4V3BOlMqlUQlSIqSK6+4tgmS7Weu2vicAbhXfrRM3JTKtjeMj8dPpEl939e+74vd"
    "oVfnOP5iFIanplLpJUZrI7qVYrJJ8bQJMuGTUX6slCXJPJdAPkAaL6w9MOtYrVYpCAJr4lBay0MgKGab3ARQDCBWSoFZLJEkB0dH"
    "R539msV7lsJaoqTRe66Bi261ncAs5YGBpuHhnTQ6Ouo40jmJiN/sOu6QMToGyIpUKuUC5EipQITFYSusj4+Px9lsViU3D8/A6iaz"
    "KeawOjMRNPMBvRPVamc44+PjcafeMI5yXuw4rmeMFVIpR3TCdghwC0QgIqQyuUWjo6POwC0DIQDbv6FdEwSOlvbMZ9NG9+LohEvt"
    "GGHNAdyUHbhlIBwdHXW8TO54YzRbZhCJ2OjYKCJcSZb/kiBexcxuNpe+LY4WbggQfBxgGjrpxpzvD7cnJxcz0U5FiCXImaO5YRLs"
    "IU5IztHxcXVbpyNWrrzdWbBgVysIAjvmXbsmk81e1mxMk9EmAvPDDPqFchcP3Bk9Vn/J4OBxbrvdjACclMlmLlu5NugsyJXXB0Ew"
    "PcNNr/l41SXzMHW1n+ZKZjirvQagBhyV7CoYG+ttAQkBYOVV/uUpL30ZgU9iRjQ4VHD37Hr8N8LSx9Uta9d2Vq4t398OW9td113c"
    "qNXbuXzupCiO1u2axuNXX33dz2phBA1TU6ZeZCnySZIzx8xzUuoyIOyRUJNBcK2+7LJrhuBmFjmup3XcGSbiddJRaNRrLdd1MzqO"
    "tlvgrg23+t9Xo6OjyrP5TzZr9YeFFF/KZDPpVqvZAXMKgjbGQlqp1B5p5Q+I6PkMPs0YA2MM+CjYMfDsxtLJIQEedNP3fbG7hisY"
    "5mIine8lya1Wo51OZzLaaDRqzctbef7Gpk0lqYrFIgfB2vaZZ5751XNeedElAL9TSvVyL5UCERWssTDWzjcwBWbMk0KK5I0ZxMe+"
    "Y2w2a6RyJKy1YMCFpZeFhDs6NY5B9BIl1YleKoV0NgurDYw16TiOf2Li6Nbb7/nqV7FlS+yNbnRUEAT6Et9P3RkEnS1btnxmbPX7"
    "W1KqHTqOjgOJUwFe4nkppLz0gk6nBWNNW0qZnltekKlrLqXjOM9zHPd5UklYa2G0RqM+bYnEQ8z8MEDaWL1p4yc++BkAuMT/x9R4"
    "8NaOAIA7u42LANOigvyX9beW3xQPTP4FW/s5wD4eR6FpNhvaWmvB7M7lOFrrGO12E/VazbaadaPj2BDRg4C9Y8EALlp/S/nCqe2/"
    "/KekVQy4M3hrB9i/U4h8v0y9Au14MN7SiD9hFb2RCedJ4vMA/q7nebLX4G3nGKtEXV7puMJ8ANhO4L8REOcJR/5Vh+v/1GtlrlQq"
    "prtFY8a09jszDoKAS6WSXLRokQrD5Xb81rFJAJO9AZevDW6MooiUcl4phASIzNxAmHi2M8XuCNvte0H419tvvu4L/cNKvu8umirQ"
    "/cl2jP06Cn4vauhuHzBAshsV2CYxDNSnpuj2m/xvrFwbnCKlfKUQAmKuEP9c61ZYyAL8q+bUlL9hw4fv931fFQoFuW3bNrt3715b"
    "6Wr0geQP8haVyogZHoauBEF817p10eiVNxeh+YRusWAuBdFMQoDBGkR72HEtAATBdXpqaioeHx/XT7W/5WAJIgbACo0CCxw38wue"
    "e7wHWbIEm06Oyf+AKJfLjINI3w4p4bBOpIVRGnNVmInBnjCie8j4we+lPCTKU8Suoifp95gbUQclHUlPg1N7SqD7aVJBUGyheK4R"
    "HTP2kwEghnPoQcChabSBIoG5q9FE1gKh1sYcVqC700pzFOQkR2O0XJGOZ43JYQCaVbI7dc6BnGwhh2W2BKobJ4r6ZuCZAbq/Zhhy"
    "pBlW0xxU6oSOJiPINhDr+LCaDmldTSTmaHhHIIIFqG0arA8r0EK2DIHNXIM4Oeqie1iK5VhK5/A6Q825JoGaScU88Q19X9FxTKrx"
    "tNKKmKnbcU5MRK7r0GEFeuqxeJrBM4e0CiFsr/l8eNu2Y8pJtlo1AsCf+ui7G/0sJdHTK989JdB9B/NRpRI0LNtGsh2PYS0WrV79"
    "Ca877qj/3tdDkUxmgAFg1apylpllUpwlDeI9NBgf8okMB73pvncu/tkvXfF85aiLrGURR6FDMm684mVnPHTBBRcYAPKRRx55rlOn"
    "xMz0059uFsvP+fPjYPWFTPT6dDoz2Gm1tmvGhh1nLPuPBTt3HtJnPdSEhawgL5XKONYY8rz0cgP932666aZmEAT2+c8/O32kT7X9"
    "Y2V0dKNas+bmVBAEUWt656Bw1LsE0SKAJIMXSolHKyMjZunSpYdkQg7V3rAUYk+r1dyhtZ6XTmcysY5Ov/yq6148b8BsC4KgPhML"
    "zexLPdpNd/8zEo+Pj8UA4tWrb1igsnQRSLzUGo1Ws9EA6Od5mWoDwMAZZzDuvPOZBbq/jZdb9u44Z97D1n4o1nFRSnkyE317d8O8"
    "EcBmAPC/8x05+b/HqFj0eXJy7Ki22/3PWCz61Kv7WaUDx81d3Go14TiOicL2N5Xg8o03XlMDgMe/9z19qNN50FIq+W6lEkRvW3X1"
    "4pSb+Wk+P7ig0ay1U6lMWmv9/TgO7zGMf9l4S/Cj56LZWO37A6Yu3wCYlyuh3iCVGorCqDN/4cLUrh3bx9ffct1YgkNJHuqJYYcE"
    "9OrVq71CoWAaDzW89oLcDSkvNQKiYhh2kM3lUa9PWyJ8lg19WUjRJIJ4khbXoyi11oJZJYd8Ey+Hxd9mstnlWkcwxsB1UhBC/KjZ"
    "qm/QjcnPjY+P602bNomRQ9xTecjLuv/I4FVX+R9IpdMf6HRC6hYRZbeI+VzNAZO/E96sk0pn3U6r0bQGL99wW3D/6tWrvad72NYh"
    "B9/lctkEQXKGkBH4JCB/TKC/YPCl8xcsQqfThjUGxj7HMvXkS3TguSlAEPZN7ZmK4/jTlvCNDbcF9wOzR+E/XZf79OxZ3+yuvMo/"
    "WQhxoet4z+uEnecT4QwAi5IzA4/yAi4xE4gECRhrH5aC7rOgRxm2OvW7qX/9/Odv2wEAoxs3OuOzbbrPHtCJU0j6PiqV2X6G1Vde"
    "9yYj7HsE4azuET/iKFdkKwQJpRS0jr5pYf31N13/w8RMsgDKqlwux3/snsr/DwgWTCfgYfCxAAAAAElFTkSuQmCC"
)
ICON_CAT_COMIDA_CASERA = f'<img src="data:image/png;base64,{ICON_CAT_COMIDA_CASERA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_DESAYUNOS_B64 = (
    "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"
    "AElFTkSuQmCC"
)
ICON_CAT_DESAYUNOS = f'<img src="data:image/png;base64,{ICON_CAT_DESAYUNOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_EMPANADAS_B64 = (
    "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"
)
ICON_CAT_EMPANADAS = f'<img src="data:image/png;base64,{ICON_CAT_EMPANADAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HAMBURGUESAS_B64 = (
    "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"
    "W2+5cq4g3MbCryuK4tH+/sFAnOvYwiIIwmcB7p39yr3xyivj5bOzs7rH2b8wR5977rnmvPPO4yRJ+K3v2PDMFScuT8Tai4hU7ti5"
    "SqUaCcs3ms35T9z5sfdPAsCGDTdWa7Vmdryj/UvB1yK0Zs2kyYZ36q1JkgLAxVfE49Va3zu11i9pt5opIKK0jkjwjWa9edXH7/rQ"
    "P42Pj3vDw8NyrHelYzydto2NqbGpKfeuDfFKX3uXhGHluiztOOts7nt+JJCdabt52V23ffCvx8e3eMPDOylJFi2rf4tt3bqNQZaF"
    "PDm5phi//JrRWnXgYxC3Ks/zVGvtGePrPM83IqMPbNp0zZ6e6oejyOujWoYXTUwEY1NTKQBooTuisPLv2u0G2HLat2xZtVGv1w15"
    "F+6QxndLUbGmeLJdr09F27TpsrxniQZc/7zLqg9Zyb/Y17+svzE/27bORn3VgXc23PwwgP8EABcB/lYgfUyE7jpiCADWxXG/229e"
    "wGJfpbXuZ5a82tdfLYri284Vd9yxMf4GAKxff3N0660bOk+BTvyUyO2D3ukb77r82vWFzddElb6XpGmrcGxrSus3rr0i/qDW+JSp"
    "9z8ACJXex0PXJDqKQQIAcsXV8bOLQn2QgPOJ0A9ABWFlV2P//LVbbr/hz+M4Njt2wGzdmqT4FWwXXfRfw9NO22GTJLHjl71vfKCv"
    "/0Npli6zrmiGQdQPAtJ26013brzhc4BQHC/q6cfk6ImJidK3SASXmTO0kQtJaU8E7Ip8Psuy6x6kFZ9GaY5aAIxf0dZu/12RJKXe"
    "r5X6P+1O+3QB1hhjqj3/N2ks6/FtkoC7DHwAVx9i3Yxu26ZX7NmDMz/9Y/Oyc895g2V7qecHZzpbuL7+AW2tjdrN1nVTd1yzc3w8"
    "rtx33732V0NcHL5NT08LAFq/fn206xUvnDU/e8gGQTReq/WrTruVioiElb7hF77ot2unnbLi29PT0zw+Pm7uu+8+PqoeXdm+3UuS"
    "hCcn1xQi9O/DKLogz3ILkM2yfKe1xReCSmV+fMsWb25u2uJp0vr7+93U2BgHUfgjZ/Mv2CJ/VCnFzE7Xav0vB/jCqampHIBUq2ea"
    "YxssO5Z8qbDS9wMQwYRRxc/S9t/Z1swfbL75fQ/N7dxJvRs/DegsSZLkcRzrO25Mdi7ft2Os025/0Q/CiEiptNMCQAtO99nZuhyN"
    "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"
    "F0o0AAAAAElFTkSuQmCC"
)
ICON_CAT_HAMBURGUESAS = f'<img src="data:image/png;base64,{ICON_CAT_HAMBURGUESAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HELADOS_B64 = (
    "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"
)
ICON_CAT_HELADOS = f'<img src="data:image/png;base64,{ICON_CAT_HELADOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HOT_DOGS_B64 = (
    "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"
    "SUVORK5CYII="
)
ICON_CAT_HOT_DOGS = f'<img src="data:image/png;base64,{ICON_CAT_HOT_DOGS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_INTERNACIONAL_B64 = (
    "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"
    "AAAAAElFTkSuQmCC"
)
ICON_CAT_INTERNACIONAL = f'<img src="data:image/png;base64,{ICON_CAT_INTERNACIONAL_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ITALIANA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFsAAABgCAYAAAByiw73AAAy9klEQVR42u19eZidRZX+e6rqW+7WW9YOBIICDh3ABdBRRDZF3HHG"
    "G1xwIqgdktAJScDI+vUNIAiEkHQW0gqKIjrdMi6DiD9xaccZF8QFSRgVnAAhnfV2992+rarO74/bHQIGAQXHEet57vP0c+/t+uo7"
    "db5T73nPW3WBv7c/2np6eryJvxec3/vB+edfNrZgae/jCy/85AwA1N29Mfts+6K/m3P/jZmJiLhp0CDj+PZ4FnSO6/n/lKTxGFv7"
    "4amt4pulUkk/5ftP2+Tfzfq0TQwNDYGZ8Y1vff94ckSvVPJtjutIozWRFJPCROw58fVv2fFf/3VPCoCGhobwd2M/x1YsFuW6det4"
    "8+zZ4ge3DB4OiXOUlGdIKUUSx4kQwhMkDrHWTk/Z7nrraW94uFQqmSAI1NDQkH26ftXfTfuHzTvoIJ+I6gDM/MWXfjBfaHt3HIdS"
    "a2OZLRFJktJxtDavYNjZw8A9QRCIRqPhdXdvjPr756VBEIgtgDur2aUulUr67zH7KWtYsVgUg4OD5sQTT1SzX3XSG5WSazPZ/Etr"
    "ldHEMhSRgBBEAMFac7cl3HTTDaWvP6u49Hf7PtGCIKDft79RAMCRx570eiL6uuP6L63VKjFIuEQCRCBmhmXze6HEZ6YVcOff0cif"
    "APH6+voSALxgSe9HCy0tH9VaH6fTFGkaayKhrDXV1rZJhUa9Cm3MWeRGd3PFizmD09JYv81znWnE/NCkMj4+3KIOyObU9YXWNpR3"
    "bh+c3IIv/d2zmx4ttm/frpkZC88PjmXiHtf1jovCRpQmsQZIAmRzuULBaL3dGL1xSoEH111zzZ5KXJkOw93TpnWe43n+25jJqU4q"
    "5ImSt+QLrWfkc4UzAJy+q4KX/H2BBGh4eFgODg6mC5f2HkrEnySWs/fs3slE5JMQzExGCKGIpG7Uxz67btWKiyYmqVx3ZlujX+e6"
    "rh0dafxb2nrAhbay+zXKke8ZGylbncZNh7aY8aL27GKxOA59j8GSJVcewMb+ExO91vVcAUADgDU2yuVzSioJa3VPauINE/+/vazf"
    "ly8UrpLSyY2NjtxPcL7ciW0JkP6L6/nHMpskk8kBTFXO+L9+UXt2V1cXMTOIKJ13/iUnZTK5D2id+NYYDRABgOt5nrF2TxzHd2/e"
    "uvm2ocHBGgCct7RUVI4613Hd2a7vorxn58bGSPx9O6P9SiXEab6XyQkiNGq1u5j43zdcc9HIi3aBDIJAlEolCwDzLrz0MJedaz0/"
    "e0YchWyNsQwiIgg/k+VGo/51x7jz2tuTXeVy2VHZKf8Qp/zdtrb2jtGR3SmAB+Go9ztEk8BiyHEcGGN0HMfb4jg69eb11zw0d+5c"
    "/0UcRma5AFAEpDRivZ/JnxaFobXWEoNJCAKD4ziOHgTzd9asuWRHqVSyCVrfJaX3JTC3Z7JZABjWVDsVsX5DNtvSb61BNl9AkiY/"
    "loLfcvP6ax4CgFmzZiXyxejRQ0NDPHXqB/jkt3W9ctJJb11MJD8ohHDiJEqISDFzlMnmXN/PqjCq3yak+7l7f/S9sYUXrHi/63rn"
    "5nL5Y7P5AtWr1a8kjfA6Sf4hjuctbmlrPypNE+g0/WoYh2s3rFrxn8xM5XKHd+21H9cvRs8WADA4OMdYbd/pZbIfY8u2Ua9EgoQH"
    "AEoply3bWrXyqJRqcP3Kyx6Zv/jSI6w2n8gXWk4cGSnbOAp/NzJS3jipbcYm5TiDmWzuVXt2bo+jqDFcHRvr7b/xin9/e3eQnTNn"
    "UPT1LY5fdNxIEARi8+bNHASBOxJlpqdRbVYaxyBiAQjJzEwEmy+0ympl9BcQ6bvXXX/VI+ctCV7N4Css28mO64LBtUzee4Mo8xuN"
    "k65HzAAY2ujfg9S5G9eW7geAOzf2htiHdn1ReXa5XHYGBwdNqVRKdBx25/Itx4dho2GMTUBkpVQgISmN4+8bnV65fuVVjyxZsuKo"
    "OI7OJqHeOL1zZq5WGbsrTRrvHd76+CktbR3zHMd9iRASYSP8b4BvWb/ysh8A4J6eHg9P4bdfLJ5NALjS0UE9QdBiR+1sEuJs5bgz"
    "bKOeKuU4bKyVUsKypVq9ctdNq6/8NwCIbPrP+UJbkcEiSfV95dHdt0w94KDf1fbs2eRnsu6uncNaKqdhdPplm9VfLBYHZFfXJgaQ"
    "vigp1gkmbxag91Tl6RD0KemoybXqWEoEATAAbvJLDEgSLRNzxEIeNXla56Rtj21JQm6825XOy02Y/EgI4VbHRiGEiCybAYL60sZP"
    "rHgcePqqDb2YPBsAuhddcnZ7W8ctYRhCKQVrLdIk/QLDvHxa54FHpkmKcnnHT43R90jpHpTPtZzmuOpXI3t236pN2tLWPqmolHty"
    "rVaBSXWDgf9ntV5xyglH379p0xwulZozt79BqL99rx6Qg4NzTBAEYmcdR7rCfXUUNWIplQfGriSNv0/s3ADwifVa5V2NeiNkSwd4"
    "buZCP5N1hBDYuXO4rFy/ooRc73vZll27tqdCSAIwxGw+fVPflb+4qQ9ULBYdYDB50fLZ2ewmBwB6e3tZWP6k53kf1dp4UikkSXTH"
    "lALev+7GS38ROfVPjx5QeNOOR3/9dhL0q0w27zTqNVQro5HreO8SzF8Gc35kZA+ISBDbe8lS3/pVK+7aJ1Qlz4g5/6bzxFnjcYSI"
    "mZHL5PISzGmSxI/oVN87Xh3nW667rto/b146dWbX28D26DSJwWwNs5VEwnc931VKCoBBRPcRo9cR+e83+2Xq6uriZxqL+puO08xA"
    "b69dtOiiaVq4JwgiPw7DFCCTRtHXyMv8bO7cwG/Mgm0HFEbsa5npaqVUVxyHBiDZXNQY1hgYYxvM/GMBvrXvxtL/A4C5cwOfiKKn"
    "i9MvigUyCAKxefZsGpwzx5y3LDjFWv6W63qKhEQSRTUBenvfqmBoYvFctCw40lixgGE/4rqek6ZJCsABw0pHCZ2mMQh3aYMb+1eX"
    "fgCAisUBMTg4xzzbMf1f8mwqFgdEe/uI6OzcNuEkFoCdYO/2bb29vZiz9AYXQBglaaOQKygigjYaDBtBeLvGJ0WWSiUdx+kbWlrb"
    "z4yTyNFaW2YLkIhbWtu8arWylQSuMkJ+r7NgHh6/BI/jafxNGDsIAjGxrpRKvWZwkAwAs5/vqc2bZ/Pg4BwLgIMgUESkAYQLlpVe"
    "k/Vzc8JGLclks66O0mEmcbPmRrXZb0kvOD94j5fJvo8EdVjLVusk8fyMr5SDJI1/ZKz5UtiCz95aujwCgI0bNzrz5s3T+5vkv5kw"
    "UiwOyAMPfMwdU9sVAOSiKOnr64ufek89PT1uX19f0t0dZFSOvtjW3v7OsdER+JkswjAcrO+x/3LrraWou7vbybR0zjaWvptraWuv"
    "jJZDIUSGCKnrZVQchrUU6Zz+VVfdPVHVGRzsYuC5Gfmv1rPH0105PDyD+/vnpU9474lqZ+PBExLDp2RN7iXWWhiR+eEFC4KvXL++"
    "tH3Cw4eHh93tHR36w4sumuoIsYyJ3xBH0QQ3XSa2D9x6aykCAGSmnOH4uSuFse1howYALoA0my04YVj/HyJc9Gha+V7TyIPmz3VO"
    "9dcUMoaHh2V//5x0IlTMX3TZcUrJY0nIwq6q7hCw/8CgowF0ggAQDo99eeSyi6/bWq9Xflkqlb6J8drh/KXBSwF+P0AtaZrafL7V"
    "q1ZHv6E0fbnZ96VnZQst8x3HOzyJKyZNkkQqxyeC1Gk6nKZ68KbVK/4VAHp6Vnt9feX0T/Xov6owsi+X0N29vNVp9XMyxmQj8TGA"
    "zszm8orBMMaArYXl5j0LIijlwvVcjI2O/piBSykOfymz2Q62OMewXeJ5vsfWcpIkjzmC5rTl7b17Iv8oTuNvtrR2dI6O7K4TiQxA"
    "Vimp2Bo2Wt9Cwlk9ucVsAoDNm2fTc0Edf9VJzdKlN/gTf0vfPROWBq0j7gTRO5mtiKIQRmtIIaAcB67jwXVcKOXAWINqtQIpxSsJ"
    "vMF6mau1tutI0AIwu9lsFlqnDxjLJ65eGfykXBNvU7B3uq7XWa2M2aahAUGAMdpYyw8K4I7JLWbTxAL4fBj6f92zu7u7Hc/zRF9f"
    "X/z+cxYcPG3qgYvZ2lNTnR6dzRXQ5JcJcRQhDhsPgujbDN5BTMzEJJjaLfHxSjqvbWlpQyOsIQqjChFy2Vxeho2G9Tzvx2GjsXr9"
    "jaWBRReuOCyJ0yvaJ006M2w0EMdRSM3qTJQvFLK1SrVMlnsU4a7Vq3vHmk9dM/t8Pu73LxWzifnJ450zZ47o7+9Pm/H1kpm+k/+w"
    "n8ksSZMUxjKHjRpZi/92XKeRpuluYrp93areW5/a8bnLSm8xWi+r1SqHpnE8WUjRYq2N0yRlpaSqVeqf27h2xUBPz2pPm5GzlOMc"
    "XxkbiwC4QghPSilIiGyaJLsE0ZfWrum9HQDmBrP8W0tnR/Q8uuNfwthULBZFb2/vk4btea/2gME6AJBVKz3ff3u1MgZm6JbWdlUZ"
    "3VNniAU+5M/37Czr225bWd9f5zetDL65fPk1/9XQ4ZsAfMxaHDOOKgggkCN3A0Dqlg8TTKf7mcwBYaNum3PPLISElBJJFK72RPXG"
    "cVJJ3lo6O34heN4XJlUG1PRyB/X1LU6ejjeYtyR4tSLRLZV8v+9lMtXqWMLAjly2cGcSNgb7VgXfe//8+e2t3rSziDBLSJG1xioi"
    "uADHmXyLrFfHdm4Yl4MtXFp6M8PemvFzU5Mk0gAca+33mPlRgKYT4QTHcbNJmnCT4OZIkPylIP5qFCd39Pdd9fB4nZLGod7z2tQL"
    "YejxhWUv3bhg2SUHC3IPdByl4jgxzVkWGYb9QC6XnxsnEVcro3UhVYYEi2p19MGMUL9YsDR4vSAxF8BH2tonQY6T/WAgTWP4mSxM"
    "muK8C1eUGeY7RtsxQZQKqdhorRmQmUz2ZKUcaKMRRyHHcZgKqRQBBEZkrB1au6r32nFcREAvBgcH7QvyiL8QMK63t5cmVvL5i1cc"
    "IaQ9D+APKMfJpolOQZBg0AR6azoZW5AgKRW0STaB+VEQjneUV0jTVEgpiIj2Fl2Yx19EECS0NenvmHmYiF4jlZPVqTbj/Yt9xsYA"
    "rBAkACLLXCaI2zgyl6xfX6oViwNyYKBom9cB/1UaOwgCUS53OB0d5bRUKtn3dS+d3JZtWSwFjmBQO7M53HHcA13Ph1IKruuDiKB1"
    "iiSJQSBQU8wPISTiOEIU1lkqh5RyEEVRhRnfEMAdTHpUgDqswWkQOJmEPCSbzYmwUQcz1wBkPD8jHcedMPC43cavwQytU0RRaJht"
    "DZDDIPs7Aqwx/K2bVq/YMB633a6uLqC5RcP+VRh7X83ceOb2Oj+TPS1uhAvz+cJk5ShoY6CTFHHUSBn0OyJ+GEwxAMV7Qxk3LQFY"
    "gA4golc4jitJCCRRVLWgO0F2YMMNpa8CwHlLLy8yxCcAHAIgFkJkfT+DKAphrPk1Ab8ffwoE0OyaQUzEkplmOo46OpPNNQOaEDBa"
    "o1qv/JogPgGbbNq59Te/mai8FItF+XzE8OfNszdv3kxTDzyqCzCfybe0HlOrVi2zJYBSIZrbI6yxDzD4FsfittWrS6NP19955192"
    "PCAvZoGThBCeZZaCCMYaQ4QrRVK+2rody5npIiLyqYmHLcOmxNhMJK5ee0Mw+HRj3VmzbxMsVvqZ7KwwbGhickBg5TgOGNBp/GXN"
    "8sbprfYnpVJJP9Wh/tT2J2v9isUBuXnzIAPAUce+cVY2P+lcCFwshDxKCik9zydmJmv1zULSx6zFvxKbO1NB319/Y6n8x/r+6Y9/"
    "8NirX3fiz8niLsuIpVTHtHVMgpJKRGF0BGTu7dby8QTqyGSyor1tEhqN2t0wmAcWX+PE3n/vvUO1/fU9NDTEh5x28pZsip+7yh1I"
    "TPwVAlkGdRUKrUprDa3TGULghEaMl73uzWf86JOli8K5c+f6Z5xxhh0aGuK/tGdTd/dG1dm5zWyvpJ0Ou+eQoA+7mczBruthdGTP"
    "HiJ5DxHvIOYvrF1V+umTEpGlK14prT5aKCertWapyDCL8VXJjMLITetvvHwTACxeHLQlQryfmKeRoHf6mcwrpJRwHBcj5d0shPxx"
    "Llt4qF6t/OvaG4Nv7HudRcuDg0xkD2AhWomgiNAQwM72PH5bKpX2oqV5F1x2vLTibULII6WU73BdD0ZrRHEYAlgDJT+//trmeP6c"
    "kEJ/mlc3L9jdvbzVzfvzmGmh43kH6TSB72drUVj9ekOG595y3XVVADimu9t5nTepzemYxGGtfgixnU9MZ2ay2ay1FswMISXYWsRx"
    "tIst3wnCl11OfxH7NprqeXUAdleVPpPPt3ygXquQcpxqmqb3QfAn119fuhsABgYG5NDPH2qb7Hm8sx4dSJyeKgxezcAsEHwGdhHZ"
    "ByHoJ8zqP6UrGrZStWvXXVMmgM9bdskhDOe7mUyuM6zXGQRPKYe0Tja6XFmyatWqqBgEzuA+E/UXwNldEoCx0j2UQfOlkjOllFAq"
    "izhNLhYOfe2WT15fnfj2K722aVa6n5UsJpNlS6CZJChrrIWSCiQEBBG4ibamxFH0HoY9PiE3ETHSXQkiAixbO8NaC8/PIE30JWD+"
    "ppbRronr3HPPPcIpzLgtcrPTyaYawFQmLgDkjXNNLwXE0Wz4bUSmqqxUiev86sPnXDgft1xXXbvyqv85d1nwjiSKL5VKnWm0Tojg"
    "wuLtWrQ/tmjRRZ+OhofLAwMDcs6c505OPSdjn3hioIaGSnpwsJScd37peDfrn6fTdFYTBTS2W60Hy1F82+0brhkBgIXLVxyFxB4r"
    "BL2GhDw1l8vB9zwYY5CmCeq1apwS/ZrBuxiICKQYmKaUevXkqdMLUViHMQZEAswMqSRq1ao2afLFyu749s9//po9ANCzfMUrdWJf"
    "pYR4CRNOz+Xz8DMerLUwxsBaM0Eo+VLKgpRyWhxHYGakJj0sP6W1Mv/8y77pz2y7Z9WyZQ98dP4laxzf8fKFwhlxHIGE7LRsP+hl"
    "C4P9a67e0dnZqV4Iz6Z9shVMndMrxld0d0+FP+Rnsu8di8rGWsta63vXryotGv/c31nVUyg172Pmj3p+YXKqE+zYvrVCkBWAUyI0"
    "BOFnRHwnrPyd65m6SR0/5eRQo/U7du/a/jpr7UxmFmxZEpHKZrMVrZPvWIELPv/5a/b09PR4MXVMs7F5HxG6s/l8axRFGN726CiR"
    "GHkCX4PAPJ40wjbf5E5AOEopz3O9+VbblyfDNXXOhZ+851PXLf+vhecHV9Sq1Vc5rjPD9TwVxuGsKElO7ekJtgOo7UNR2z/X2FQs"
    "FkV7+xv3VrK39H5WtEzv4CDYmN1V2XYSwEekzYSEorjxGwK+O/HPeyo4mqAuZeANTKJgjIbvZ5HG8U9ImJVpah+Co8Y6CxidOEJi"
    "H5TzYFfXprtGR+0hrOy3PdefkaYpeRlfpGF8Q6yT/pvXXL2zSS51HOZYvowZbxJCtTIzstk80ji5WwnnKm2TSMqUjVHj8g/hgUxM"
    "kBli/blcS/4VjUYDYaMO1/OPi8LwImVr24MguBfA/SMRn2BMOpDN5l8TRQ3XsrkcQgHgm4MgsOVyWXZ0dKTPFhbSUxc+dHXJrqY8"
    "QO+fg97oOPnhLynHfQMz2pQk1WjUVrmut0Hq3FaixuQwjT4sHPcyKZsKImvsTkc5n451/M31N5R+CAALl6w4ioQ9nS0UBDnczL9H"
    "wOIxwHpSin/Q1i5oa22fVqtVjBDy5uru8iduuWXlIxM0gKX0bEeoxflCi1utjI4Iqb7lOO6vQxN/ZcO1lz/4x278vKXBGY7rvTZO"
    "kmMJOCVfaEGjXocQdJdO0mDdjaWfNccZXO752Q+laXxQrtAiKyPl3vU3rig9Bbu75XKZOjo6JmDhfrNOesrfezHkORd+suAm1Rlu"
    "NuOZyDDYONZCQ4mXEezN2UyuEMcxhKBIp+asdauCOwBg4bLeswWJBQCOVY6LJArHGPjs+lWl8wFg/vxLZsqsOoyZelta20+QUoKI"
    "kCQJatURDRYPMPPB7R2T2uuNOoSgOI6iIV1X52zceOnjxYEBOeM/NxUSYKl05IfAfKBy3JE0Tr4Ftjesu7H0s7lzAz/bamfDUQJW"
    "5RU0SFAFAIwxLAx29vWVtjZJsmAOmAIl5EEkZNbzPVGtjn3cuPFNXmNGZGX5KMP2XN/3P+xlcrpWGbmVrVylEZXD1CbRzleN7q+S"
    "M17qexLHIiY+OPHEE/cmOHPnBn4mjc+UUg0IxvcZ9nsQdI+Q9H1iezNA+SRJYY2JdKq/A4ltT1wF7/Yz2VcyM3zfB8B3ZET+kuaN"
    "lV5DngisxYCU6jXVyhgajToa9RqSJIKQjgL45SC01Os1SCERRdF3ydKV5fLhuwCg/cc/btfEc4XAe13Xm8nMNo3jB4jwlcmt+CUA"
    "5CfjX0jSVyXwLaL0ywb2XzXbb1ribzJhwCrqWRCszQOAVplvAfYTxtj7hRQURxEAvFWmmdP7+hYnOx/f/AuQ+DEAJFGoiOQHCPZb"
    "SqhLCxn/PVMPfvDV+3tyent7ZRAET4octG8qumjZimOsse9UnndYmsRHkKBXZLI5GN2MKDQOz+IoSn0/o8JGYwtZMQ8m/Dm7XjsI"
    "7wHzspaW9snVyljDy2Y/raP6p9asLD0AAAvOv/Qyz88tFUK0eb6PsfLIQ0y4noCEYbuYcQYRHep5GU7TuE5C3hHH9c9vXP2J7xIR"
    "H3fqqZNeffQJ3QB6Pd9z01Q3LFvput72Rr1+/cY1V6xdtuxzuYh/f1O+0HIWGHBcF47jgqhJRDXqNVQqo8NGmx9JJT6z7obSnd3L"
    "l7c62t/Y2jrpzNGREet5biNOwq9vKtDcoVJJ9ywL5hDJ20DCISIo5SCM6sMADROwE6BHGMyu53lpHFd1Pbl248ZPPP4HC+TmzbPp"
    "w0uCDlfblxvmD4AwN5vLq9RRSNMUcRRh/HEAs4XRxgIwynUlhY2y4LYf9K0L4p4LgmOMwceFkK1pklgAqJSrn/v0hiseOGvZslzB"
    "ZE+SjnOacpy2KGwgTZPfksBt627o3dgsJKx4uaP4dDBFRORZa3dorTf2r7n6R53truhZGry2tWPK8SN7dp/EhPu11i8RUnQoknBd"
    "9+A0Tc489/xLNifJtt+ypBQWSRjVbbUy9iAJ2tPcnEQM4GDHcV5WKLT+U7U6ti0IgrtLpdLYgmWX3xfH0UkAT8lkc/kkiTqHJtYt"
    "QkVb8zNBfCw3WUObyeQ6lXI6pWxWeuI4hpQSYEAIUfnoosu+7rjisfXX9e4AUTNxGxycY3yIE4UjNgD8ISGFGhvd02TPjAazhbUT"
    "WJUBgmACsWUCsRQdNjOx0hNRq1IOGCwYbHJZpQCgnfzpQsg1nusfH4UNWGuMYV1Katuu2RvPyP6DFGq263l+FIW7APoOyGwBgF2j"
    "ONoyf8XzM1eDaMeUAh9vUvMlx3HGY31Fe55/vCC5KqWwDYIfc33PlUr5kLRqcoHftmsr3p7WOt9OhE9hnM4loKNScaYBgEntV6Ow"
    "fjsRIiEEAGG6u69pBQCR4r8B3GmtHXUc1wGzSuIIjUYN1eoYRkfLaNSrGBstc5rEEEJc5CjxRVjxoYUXXd0BgHt7e6UY5yNeUmhp"
    "e5njulIICWa71Vi73mr7Ibb2vUabM63h92hrljPzfUoqr6W1jcCiLayOKgCkDSwDMZGI4iSJQfwIybQGAHFsDmPY6ZlsnoyxW9ny"
    "FeuuL90+UfBdsDR4PYGLQghSyoFl8z02vC5H4ei8ZcFJhni54/lT0zSRljgtlUqJNvE6m5rzGfg3tmY0lysQAVM98muCMEpCgEgA"
    "mh8plUrJ4GAp6e+fl4L54fE6gjHGzowoPa57+fLWjWuu/J21+m4wmzSNmdnOVrnwqnmLg1lhOONxCNoD0Ei+0BIx84i15qPW6HdZ"
    "o99lrTmHmbdMmjSVlHJARDKXK7yUwB+yafoSAJg9ezars3sumgKIGSCyaZJYP5OV2qSPGnDpphtLO58EDZcsyUwWLaNa62KjVpsE"
    "4FdeAc0ao0A2k8l6+UIrdm7fVoegb6dCb1904YrDpJD/khpdjaI6EZG1IFqwtPd9xJSAbMqgM4lxotapdT1fCCF/s/7G3vsBYMEF"
    "vSco13l3kiRxec8uIm7GtI19V28GsHnBxy69h7S6XUrZDojdzLYFjDZjNKwxAPGp8xdfuktZ+XgcQ4NpGlvmOIrJ9f1ZaZK8JZck"
    "3+ru3uhINXwIGyAMI85kc506TRbCpAPr++dtWbCs9yVEmOU4rgshfrt2Jd9C9AS8O2/Z5W1JEp2apulRDNMipJMnopcR490LLgge"
    "KxaLO5Sr3EOIMNmkWgAQQgjAQrsmoZ6eHs+YDkfrGTFwH/pXrQqLxeLNU6ce9aPyyI4p5HrDO2Gi8bU2jcJ66nkepKB7Ic1X1l5z"
    "zZ7zlvX+i+dl38cg1Ot1LYgOUkIFRBOYSICbZJQGIIzRIPAhF1101ZR6XWa0DY9yPNcz2kAphSROpixadNU0KZO0pQW1nXG8DSxj"
    "a41k4naj0ncw21fEUQRjNIjEmQDyWorvOhlbZ+Afma0wRiOXL8xMk+S0OJatXn5HJ1s+G0R5ozUppVjr1AohzHhtwzBzZfvw1hYQ"
    "/cfSpWgDUA6CwB3H1avmL15xtxB8HUicotNEWcsW4DlkxH1EdIfSxn1EiLhCRIaIZBSFBoSjjPIGQR6IoR0xvIl059cA3NOkFwd/"
    "vRcmBoE/Nwh8WxH3SjZvZRYkSJTbs7wJAIzlPXEcljPZXIfn+QoApFJNZMMW1lrEUYQkjqS1No6jkME4aSxKB0imAsBhaRLHYGad"
    "agB4lZbplwyBd1cpFfAtgIPHRkcigArMfDZB5KIwjJgtmPggQMwR4FOY2IIwk0hAORKZTBZR2JiViuwHjNF5SHFEPlegNE2QJMmD"
    "zHS3TOxjQRCock3dpm3yXWMS4Treo/XajAnJcdJMbAbc3WMPnMKgY6VQvtZp8zwpoM2yze1NahYsvvyTk6ZM+9joWBk6TVPHdZ1M"
    "JgtCUzweNmpjYPoOMf9EOHKUITTBbkcs71uz5pIdT6942ujY/LZDpDZvEUIc7TieMEYbBmfAyIKQBdBG4JlCyE7Xa9YmXdeD5/lg"
    "AHEUIk1ikGhuV1SOA9/PAONQjgDU6zWkaQIlFZTjwFoDnaZ7v6OUglIOmBnVyhiSJHqUSDzsON72REc72eJn46v0EWT5ABCFrM0v"
    "XHKG2trMw/vNpoNALKjakzOZ3EFRFIGBLli803Xdw40xDAKs0QmD7mAdf3LDmqvvbxr7/ODilra2FfVaVRpjNRFLgCwzCyIiISSE"
    "aJbypJQgCIRRbQtYrLeCbyXHTxVZFVuZeDMyUd/ixX9U4NLTE7SkQnYKSVNA5hBh+TgLHAuigwnIcDPCTGRlcoJBQjP07PPZONHU"
    "rDgRmMEEi73l4wkKDUwMBiEixkMM/h6x+F7SsPf195caz6Ls546OIsuceMx5m3a4RLXGcYL50lyh5R91msDoJmIzxjBAcTaX88NG"
    "PSQj3r929eVfLRaLUgEAS/Grer3+c2vsMVIKaYyBVFIyM6SU8NwMGAzdPN5h/K7FgQT0CBbvlTqRxljtkPgZPxZ+GcA9f2zwfX2l"
    "ShAE0cO1/NbWaM+D1s/9AIbzLFKfjCCWlhU71gjDe/PdFBBCMo2n3Hs7cxnCSLLS7M3WpBVkrSErJQljnlCQMSxJRCww6tns2Nr+"
    "C5/R0D09q1t2VkaKIPseIb0DGQnLamqYkWXYA5MoQrNy5EBrgrWW2DJLKQGwMsyPA8D06dOVaiaG9j4d6+8KKY9SyvGNManVepsl"
    "3G2t3aFTnbGMAwX45FyhMN0ywwMpz/NmEomZOk0QxRHiODqEmDoXLO09QRBGm0+m4xkTMyB/y7C/Xr+q9NA+sS4BUAew539V4Hn+"
    "xZ1COkcIS4cBPEWQJGabgNgYHukUwPEk5Wv8TBZCNA1LJGDZoFapIEnih0G0i9lOEyQOkUo5cRzVmelXJO0IM9Oc3l6miRLXecuC"
    "f7KWPpfJZnNRFMaw9n6Qd9a6Gy7+LQAsWBIcKoDzpeu+wxgLa3QKIgnmHEDtSklFJKCUgmzmMrDWQgiJJI6QpMlPBXCnkfRDcsXv"
    "EQFstJRSszGKlFJkjCbHhRaJkxpT18awTvNtWlVD43kVo/UsCzyE7ds7uL19Bnd2bqNyuYOU2iKEEGJETBUmaci8jqXxPSkjKK3g"
    "SvEElSylYq01p1pzNqdMqu00QeJ4NnQaCK/1Pb9NSAVmCylk84nWGkanYOaJMFEFMOp6LidJsoeBuwDOSSHfwNYe4/sZhGH9fgat"
    "VBpf7esrVQNmUl1dzRIXGzwKYs2WrZLKTTk9UirbMTHIKS34faWCyw3ktWArtYGRJHJC2DNAvDiXK0xLdbqXSGTbFK+nSQxjDAAc"
    "ZYFDhOYPw5gUAEiQsFaRIMBaKwXAOqXtROmjVniPkaJhJ452sYddVrTt0VQOLXfoKQcikXIn794NaWTZTdGSF0LkHB21uEA7+X67"
    "Ip4EV8yQsIeToGngpsGNMRCCrOso1glZIimZOUOEHDOySRJDiBRCSJBqioYmUnICod6oRrD2Tmno805OPmwsh7buhXCT630/Mzts"
    "1CGlNCDxgM+FwRv6lkZHbpyh5hGlagsgwEy09LIUkALEAgQoqTJREh4zd3Hw32hDVCqVIgDl8dc+4sgrK5L01jiOOuM4tExkyMIF"
    "+GAAr2Lg2EKhVUqlMlLKjFIOhBCwzLBGQxsDk6awtkkLxEl8sDVmNoFHmDEGgSoYNcNcE5JSATJMbKy1DFcIAasA8mCsJ4l8Fsha"
    "5iws8kTcKoXscD0PNL7GChKQ40+fkrIZDqyFTpNmGc0axFGIJE0ejpP4p0R4gICIhFACAoJpxFj7y76+Fffua4eFS3rhep4/XoiQ"
    "VK+5q1YtC1dhGVZHqwUAqAeGhw2IGMuuqBCn34ij8C1SOS1aa/Zc/zTS9rcbS8G3gyAQlUrFaz7Kzba9o8wbS5c+DuDzf7ib4JKZ"
    "KdSbDNPjjXrtUAasZaubYm0wE7vEyAJUAFAAISelbBrDlXkhZF4QzSQSIDEuHWsijyez8AzwuPYP/IQG0HJTPmiNRZokeyl7Yw1g"
    "uQagBkKVgQYAg2aNUo3rCHeA6D8h7J3rV15x39OJfRqNRq5ez7JS6NCwbUmcWAAUNmp7wPj9xCEFvu9bAFD39ffrYrEoJ+X1I9tT"
    "fYEMnZzjuG81Wkvfy7zF6PquIAi+UyqVuKenx06cd/RM7YYbrnosCILbGo3MYE1aBQB+HFEUxcwAZMabRowjreBXA/Q6gF4upMoL"
    "IjTlDRaGCQT7BAik/akv+A8kkLzP+0KIcQ1nE7bqUEfEfC8T3ycgf6ok3V/TZpcbxRz7HrlezIbZ5pKpSUuh8rT3unnzZurq6qrX"
    "jDrAwCwnpn+0RhMzOAqjW1jI9RNFhW3btpmJGiR3dXXJcXTw+IIlvZQvtMgobLDjOA7YTCqVVlgA2Kfs86QZnihCDA8PEwCMvPGN"
    "dnDOHLMP4thfGwnmBlvKU9QvQPYbsDQtjuOCIsGaNQsIWNi9WyyetNXC/KGmi5mfTNTz+LEt4+8zMzVRBNdZYKsUzrAy2W2rrlsW"
    "PpNGpr29XXR2djIAfB/A1M2b+fWvf71avHhxvPDCwMDQ2x3Hmd4U+XvUiOr3blzZ+0ixWJQDAwOWiOzegu/w8DADTN3d8xQIP63X"
    "qocDODxqhFopNWXhBaV3i3j3XaVSKX6qImi88PDkelt//95JKJfLstLR0TTEFgCzxnceDA+bUn8pAvDw+Ot/bV9PHHfKiXEBQEu5"
    "g+PYtyMj99jxezVPLXd1dXXxwoUfn5Qm+gRHOlOFVNboNE213uWSv5WZ6aTeXhrfccF7jd3f36+Bfu7sDMzmzV2fmHrA5kch8Blj"
    "tZLSeZ1O4iMS1XoKgF+Noxf7TPrlfSZB46+4jdO86bP9fm9vrwSge3t70/OW9r7JAS0H2CECaaMfB2OtTcXviIiDILClUomfKmVg"
    "ZqY5cwZpcHCOmbfwkkf8XIaaFQaQUqrDhslxy5dfs6VScRIAafMI0z9bME4TdbrNm2cTin8B6w4CExv8xw3xnO6hXC7LgYEBJiIz"
    "b/ElXdlM/uVxHFk/m6UwbMRW4gvTWuOR00/v8UqlUrzf6vrEjoEtW+C2Tsah2vJiIdRZfibjh41qzXEyP0yq0dXr15d+MEEy7bvd"
    "+cXQisXAHRxssnznLrvsLb7KXCikPDlNE7ie/3CjXrt9w6rS5eNpvvdUMLF3CwQR8UThd83K0gPrV634qLXme0TCAiLveu7pwqd3"
    "B0Hw4j5zm5l6LrjipYLFzcp1T06TGESEsFa91Ufl6gkHXrNmUfKMiqhZs56IsUKJq+MkjpVyz9BpCi+T/cCuamM6g99P/ZQuW3Zd"
    "buXKC+t/6/YdLxCgVColH14Un+62TrrCGtMZNepgtinY7jQ2uW/VmlUhwBQEvWICgTyjZLhYLMrp06ervr6++CPnXfyhjOffqE2a"
    "y7e0qTgKYdN0cUK4vf+G0u4gCNTm2bN5cM4c87do6H3DwbxFl741ly8s9vzMadWx0YbredkoDC1be3FWOV/andc7bi2Voqc712+/"
    "IaGrq4tLpVIcBIHYXTH3WaO/JoR8TxQ2lDXaAPiEAJuenp5Pl0qluClafLKi6m+l3d9RNkEQiF01NZPYrnFd76VjI+UGCfIcx43j"
    "KPwvHR5ww8r+eencIPD/ICfYX8zeD2wDAJXWd/43UroKwCOe54Mtp0LKnIRYmoq2+eMBn5ctuy6LpyQW/7c9usfr6VntDZVKevue"
    "5LWuknd5nv/SWqUSKalUa1uHDKPws9byR/r756XMTLOePoF75p0H+yKOBef3ftDxnEWZbO7YerWa6jSRjus9JIX8/M6tO27+whdu"
    "HAZAPT2r3e3bf6hfiB2yf4HVj7q7+9VvfrONh4aapbD551/2jkKhrVtI8fZ6rdYQQvpSSSGIPr2zvLPvcxuuv3/8QBp6OjHqs97m"
    "0d290ZnIpOadf/kH8rnCtdboGWmahq7rZhzXQRw2lptQfKav75Jd++n7/0po2RsGi8XAnTEDWfbRYlL699a2jqNHR8oNIvJzuUJS"
    "rVV+tnvrptMGBwfDBQuC/Pr1pdqzucAznjfS3z9vr5dGI3SHiZM5cRqH+UJrJkmSRqNeg/IyH7dOun7hxz8+aZ/H0O3u3qjG0/a/"
    "cvxclHPnBt4Ej1I4SHdqRct1Qv8hpXPk2NhILIRQbW0dIgobdxhO5gwODoZAIKZMQeO5zOazanODwL+1yWnj3KXBR3KZ3FlapycK"
    "Inh+BpXRkToEfdlznB2pTr+1dmXpu/vGPwDYvn37X014KQ4MyK5Nm+Tw8DBPKLNQLMr5B3ZdVsi3HF6rVv4xm8sdkiQJmlV/gBk3"
    "je7Z/elPb7jmvubeT6iJJOd5NXZTSjzXnzVrli6VSrq7Z/k7lJO5WIA6LZsZjus7SkooR6Feq36drbgUZOLJBWwvlUqVfTPVfRKp"
    "v2CYmWD//vC6iy66ahpp06bZHONI7wvZXB6V0REIKaBTXc21tIzWq2OPjdS3v+uL/f27FwRBfn2p1MBz2OLxnI29b1wLgkCVy0k7"
    "O+7xzHRFrlA4sl6rgpmNIGEYXGfgfwTxVWtXlv5tnwRhX7hpn6994c807mKxKLq6umiCJp1QqBaLRTl1xuyPQeIsIpoJogJbkyrl"
    "OiQIaZL8gKRaK5P026tXl0bBTPgTneRPgWrU3b1RTaCUuUHgt9TVG4SS73SVu1A5DuKoAYAQxxEI+JGUarNmA2v05zesumLoqRAL"
    "OBTAQwAORUdH2fT29po/9aigYrEou7q6ZLmjg/BQ8739FTzOXXLZPwshTiaLNgIdx4TDPT8DMCOXL6Bc3r3LWnMRlHxo95bHfzk4"
    "2D824SzPhDqeT2PvG/OcEpCgVLLnnLPsYL+tcEvGz7phWD/Adb1DJnTdnu/DWotapfol4dB6ay0JIdiYZMuGG6567OnKTs91TL29"
    "vfx0k7RwaXC4YHuAEK7RbD2GudhzMycpxwWzgbWMKAwtAQ+0traPjYzt+Y8Nq1ZcMoHIPC8SE6dO/Dlw53kk4jc6qjP1uLLrY77n"
    "XQYSSOMoZcAZj5daENnm5lKbAPSpdTesWNosYTHt+4MMEyzkszVyb5Oo36+xz//Yitmp1ivA9CYhhW8tMzPUPmeRcC5foHq18ohl"
    "fOQVR8wYuv32J7D284kt/+w+BgYGxL47XucvvWKm79CxzOLIJI3Oam2bdLhlC7YMIQS0TscFleEOBn4ogJSU9I1OKwK4M6nRN56N"
    "LGy/Hrzk0qOI5PuU4x2hdcKWWQvQFAt+TcbPZiaEacyEXDaHsbEy0lhfn2vL/2e9Wq9uKtihvfF8YEBicBDPF4J63jw7CAKxZQvc"
    "jo4KrVq1KgSAuYuDtpyis13lvsGwgdGmhYCXMDANgHAdxyu0tO1NfWr1CpIo/IGFuEuAHiKyhoUgsvaPxm9DEJJhWSDLhk8miPe2"
    "dUzKM09MrkatWoFlE0qhyDSFLL/K5XK76rVamWNcuWFD6fcT/S1ZsiSztaXF/Kl71P8iYeSpFZhmfHuCn5p/QfBGYflCQJwqpZLG"
    "pOmTEywS1Gx/Bt08IWeAJWJuCkSbYlYG4kwm64WNep1IvnfdDZffue/COl6cfcGg6AtTCGieyP4H2TpbK61FmxDEjuvChPoRsjwI"
    "iYZlPlkKecoEIgAAy/ycr2ts84nXSaqZsQngHwrGdCZ6D4Gc8YnUIcW/firTuc8awf93jE3EpeY51nuFPdtP6NTix5te6bjOS7XW"
    "xNYygxIm+wgb3iqkUNZaGYaNNjKcY0IbE3JNUMvP7iFlBoNTIRUDbEAQBLiWoaiZy1DzUDQol+lN5y274jse/J2PPvrTqNTba/EC"
    "ejXwAv/I/dDQEN785jeba6/9uDnxpa9qlcacnclkX2OMFtZaAltFRDmCnAqwZMYeAaoyQYG4FUytQpAzPk5n3Dn2+xr/tTsJIGFw"
    "fVxzMAPgIwFxKBFcMPO4Ds0lppmW7O/WrLzk/s2bN3Nx9my5eXDwBTX2C1pPLBYHRKk0x/T09Hg2jE6whKOEkM3z+YyBEKLdWnsK"
    "w8YAEgIZyyyJ4AHIPAHNnl0YH/9WlhkeNX8b3Rn/+e6J2ECCBJSrEEXR4cQ8bW8Y2bTpBefiX1Bjj0sGqKOjw4yMYEsq+Bu1ei1h"
    "a/JNb23KjQVRKwkBEgIEwFoePyyRdTNuMzVD+L6PuQVATGgegkuAYCYpBCSRkPue/QeGZUCDEBmjY53aLRL4MrP94T47nF9w2uCF"
    "DiNcLBbl+vXrzU9+MrTjuNedFMLadhA1CFwFcQyQJbYhM0JjtWFmtpaZCAYETYRx+RYZIquJ2BCxIYYWQMrEmgALEgCswP4OPyBY"
    "Io4AqoC5zLBD/u7CNav7L9t60kknyaGhoT/roK1n2/4/vdUvSkIEMBUAAAAASUVORK5CYII="
)
ICON_CAT_ITALIANA = f'<img src="data:image/png;base64,{ICON_CAT_ITALIANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_JUGOS_B64 = (
    "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"
)
ICON_CAT_JUGOS = f'<img src="data:image/png;base64,{ICON_CAT_JUGOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_MEXICANA_B64 = (
    "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"
    "K4VzDJgErwAAAABJRU5ErkJggg=="
)
ICON_CAT_MEXICANA = f'<img src="data:image/png;base64,{ICON_CAT_MEXICANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_MILANESAS_B64 = (
    "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"
)
ICON_CAT_MILANESAS = f'<img src="data:image/png;base64,{ICON_CAT_MILANESAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PASTELERIA_POSTRES_B64 = (
    "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"
)
ICON_CAT_PASTELERIA_POSTRES = f'<img src="data:image/png;base64,{ICON_CAT_PASTELERIA_POSTRES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PESCADOS_MARISCOS_B64 = (
    "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"
    "YII="
)
ICON_CAT_PESCADOS_MARISCOS = f'<img src="data:image/png;base64,{ICON_CAT_PESCADOS_MARISCOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PERUANA_B64 = (
    "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"
)
ICON_CAT_PERUANA = f'<img src="data:image/png;base64,{ICON_CAT_PERUANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PIZZA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAF4AAABgCAYAAACUosWzAAA4WUlEQVR42u19e3wdVbX/d+09r/PIyaNN2kBLaxEqKe9WQARaRMG3"
    "yL2nvu0Vf6a0JW3TFkEE5gxQ5GFbStqU5urVqnglUa96fYCiEkWBSn1BoyBqUWj6TJqT85qZvff6/XFy2oDFqwiC9zqfD39wOpnZ"
    "s2bNd6/1Xd+1N+ElesydO9fq7+9XAJDN9sq+vvl6/L/7vu8MDTVRGHqmtXWnDoLA4B/ooJfagHzfFzUjdqy67mhpiywZkY6iKAI4"
    "NIJHY637P3Hr9dvH/117+2Yb2IbW1tZ/iJdgvdQGdC8gAJj3rlyZUnE8v76h5QaAIMpF2JaNUrkAGOpZvOr6TZ5NlXJYKm7t37ur"
    "p2dhfBiH4n8a/i84ent75fz583U2m5X1Jnk+E84vjObBBKgoRCQkjDEgmPkC/BatQYKt/tPObL5t2zb8+JD3t1utra0MwLxUvf8l"
    "ZfhvbN9uMzjMteV4T57e6nnuqVEYRrbrOq7rwRgDL5GEJa0GEDVoraDi+HzpOHVLVlz7OLP5g47FPZs3XPOL2jU7OjrcpqYmHQSB"
    "+qfhn+XYPTTEBOLXD613jraGj00k05koCqMoDHcS4SmGKUZRVCeEyBhjJgsh62zXbbRt540EQrEwOmLb/LLll/mfjhQOFIcO7Ovq"
    "Wn+gBj++79NL5QsQL6VJ/q6urggApvHoSUxwiAgMVCDwcWHxRbamt7PrvY7ZrGDwA4IIlrRQqZRQKhUAQhISFytN3yaiT3gN9W8Y"
    "5/kOAAFmesk88EskkmHf9+XegpgtgGsZOKU+09BcLBYQxeo1m9b53z94fjbr7D7yFadbJI8V0jpKqei1iWTqTNtxEUchQIRyqRja"
    "tvNLreOfaU1f23Sr/43a3y9Y4HvTpyN6Mb3/JWH4bDYr+/r6DABetMK/MJ1K/xczEEXRAaOiX5FQ7wvze//guq2JpqYjFLCzUjPa"
    "grkLvLrZ099pmBZ4rttcicIWS8pmEMFzEwABxfzoN72EtyWslHc8/NN7f1rLD3zfF0EuxyDi/5NQ09bWdvDByRgOwxC27UCp+Fca"
    "vD6fsp7q6elRTU2oDMxqDIMgOHj+lv4tUVQYvCMhUm9WkboEMN9hZtiWjUJxlIuFUYBwDgnxKUP0nZknnXXGOKcTfi5H/yc93vd9"
    "C4AZAKyWPL2HgPdDiLMsy4ZhvUep+EEmfK4lja+Nj0w6O9ckwjAv9zYj6guCCAB8QOxd5p/IAsfbln2GUtHbUunMFGMMwAwGYLTp"
    "V3Hcr5Tuu/224JHqtToTP81k4v6/Y+Tzohu+s7MzsW7dujIALOnMfSnT0HjRyIFhw2ziRCLpAkAYht8j5i+QRY8pBcS2+e0nbg6e"
    "HBe322httVsBFYy9hIVLrzrGkvb7GPpsy7JnGWOaiQRS6TqMjAwVBIlPJ+sa7i7u3ftwd/fqJ2qQ19bWxn8P7H/RoWZoKMPj3MBm"
    "rv4vEVlhWOEwrDDAcw2hyxj6Nsjc7Sj6kO/zwbG3trbqVqASBMHB7HVyo3xiYsZc25yhC7TWd1YvyyiMjoAAhwiLiPWX4VqXjYM8"
    "O5fL8f9qj+exsG7hwh4rmdw5NRT8LjK0yHbsFqWU9hJJz7IsMDOM1tBGHxxuFFZ+J6T9C8sWOi5XvrphXfC5Q9C1ObkDO82WIKjU"
    "flu49KpjbMs+GYyTNOvlDY0TUoXRPBzHgTZ6TxzGd7Mjerpvuvq+GvwNAKIGYf+rDO/7vhgYGKC+vj69ZLk/h4m/YdlOCxiwbBth"
    "pfxzAIPMbAGYQUQzbNshYwxAQDKRgrQsDA/t/5HnJjaR4KHKyIGtGzfeuL/GaGLK/U4yk+HaS7jkEr+FErgilUq9Loqi441WSCRS"
    "0NqgEpa/wFJ+xRj18OY1wUDtBbxQGe9LIqoxQBMgJgohIKVEpVxUxsSXb1ybe1N+b+HtAG9i5seUUmA20Erp0dERHBjeDxDmGOjP"
    "MuMbcL13HoKN7dS3bl25ZvRsNitvvz3Ys2ldsLJcHL1GqahkWTZKxWIUhmUQ8E4yeovFFKxadfNkABgcPOIFc0z54iVMOc5mt4u2"
    "k86ZzTDvllK+MpFM6TAK7zcsOvdl6DsD/f36l7+8Pz7ljNftEMLcJwR9zTB+A2B6pr6xQUgJrbQlpSQhJQGYOeeMuafNedW58uM3"
    "5rZXM9b17qtffZwjpeRt27YZAJg08RV/aGque5BJDBjWrZm6hkkgglGxJaQ13fKcM46fdcq+ns1X/Nr3fWv69HnOL37R/7x6/ovF"
    "1VgARUEAtaQz9xrLtt8Ux7GxbUeq6MCuTeuv/QoALFjmN0xvQCkIrhoEMAgA7cuv3GoLN18uFl+toZsNmxOIKFMuFTmZTB8NoqPj"
    "KDryI7m1k0eGh7d2rV/24NikQu2YbQPb7J6enhK+jruyH+zcOrEhM1IqFd7ITG+wbYeV1gnXdc9NNTRElyz3y0EQfA+AymZ9p6/v"
    "+cP8FwVqhoaaap8wsaBTXM+bSgQRRRWWUgAY41MOoDIWHhLAxMzUWm/v3rjW//itN1/5dqWjTjDuNYaVFALlUlHFUWQIOAcQt5GQ"
    "H+/sXJPwfV8syOXcnp6FcU9PT6n2IpIqU9q0JuguwHmX1upnjpsko7U6cGB/2XG8C6SgTy693D8KALX9g0MNMTM9+OC3TMu8efa5"
    "p8w7BeD5rpc4KopCaKMf18Z89U3n3/tAf38/X3jhPNHf368BUHv7EdbXt/23Wwdg7De86fxz94Qxfi6F1a+1qiOBmclUmpSKSWsN"
    "kDhCU+WsYpkaKyOFx3750P1FAMh2rklk779br19fDT9/9uN7otPOmPuQAFwvkZhttLZVrJRl201SOmccf9KcJ9Z+evVvfN93Tjzx"
    "RGvr1q36H83wYtasWeLSSy/lubNfewTYfFja9ilgTmutoVW4xQjRu+ZjwV4ANG/ePO7v72cA2Lbt62Zbf39cM3o2m5V79+7Fpz7R"
    "veeBH333V7NPP3tECNqrtS44tjsDAASR8JLJl4VROKUxXd9w8mlnTiiNtDze/9/rwpkzZ1pvfvObceJFFzknH/V2cfvGVU+dMOvU"
    "PzKhmYSYGMdRUgghksm6qVLIxhNPfdW+NTdf+5utW7fqjo4O9281Pv29J1UAIggCtXD51a+2hPi+6yVtozW0VtBav6l7XfDNsfMw"
    "PoPM9vbKxnu2u62tAAAVBLkYIPZ9X8yaNYu2b5/PQQCzePm1s0jo7yZTdQ2lQkGDkGSGSiZTVrlciCXkRZXCk3f39PTEzEw0RpB1"
    "dKx3u7qWhQt830uO8k0Eeg+BJjBznMk02vn8yGM6IV8z2Y4HBwZg/a14/3fF+CAIeGBgoJoZGt0CEjYzg4ggpASR0QBQyx6z2ezB"
    "L3LS1u3nyiR/q6DS3959gFcv/vB1bb7vO4ODR8i+vj4EAQwAdN96zXZivDXm+HKG+VUymYbrula5XIRlOXaiLrVWeJNW1txu8WI/"
    "zcy0a1erAoAtQVCJY7oFwFrDZicIdqVSguM4xyaN/MpTu6NX9/UFUUdHh+v7vvOShxrf963+/n4eGBjA4hVXvyaRqHu/itXLLSER"
    "62jQaPWfkui7J53w7uFt20YJ2CFd92j7xBOn0+zZsyVZde9sPWLqB2zHPiqOKjOhjEjeiLvXblulzzrrLGvGjMvpldk29xf9/Wrr"
    "A/1PZY6Z/pumRGYoVvFeYszwvEQiikL2EqkJAKbPPuPs/JumdD/8ky3dYRAEmDUL4rzzznNOPvlk8e+b1h449YxX/84iSxPoOKXi"
    "NAlhUum6Iy3HaTh59mnDG2/7+GP9/f3PGXb+buHk0NCQBKCqIQu933MT74jCChzXRVSoPO5wvnPd2nVl3/++FQTn/knMvKjzmqeG"
    "hvePqDhKe643oaKLCw6ssL/dXvB/2NqKqKdnvgagUS3xyR07UOpeE3wWwGcXL/ftRDqdRRmJA8P7w7q6+pcrHX360qOO3xO1t/W3"
    "tiIay1A1AOro6HC71t3wVEeHv54tMYFIvkdrPfHA8FBU39Dw9rBiv3z58usvqK+Pdw8eMWhe0lCz6+yzDxqTDRI8prxwPA8AJdat"
    "W1f2fV/swL2HdYZ9IfUpE99sjFEkBEjICeTIz1gpXJzL5fQ4ipkBmC1bDnE1HCpfq3ghGL+0LDupVAwhJBzHvc1KiRuHKzhiHNNp"
    "7dq1SwFMXV1B3mJ5ExF/rnpZwuhoHrbjnWBsfGt/HnN6FvbE2WxWZrO98qU2uVI2mxVtbb08PHxls5b2xdJ25wuiWXEck5dI/DAs"
    "Fb+8YV2wAQDeevHFdVPrp76FhJgIwBhjQEQEALFREy3IWZZlnU5CTCFBj+qKuqrr1mu+CABz537f6u8/+LWQ7/v2jh0QtZdw6Yrc"
    "uxh4I7M5x/OSR3mJJEZGhocYuENodeeEevGTGq08vjy4pPPaE0DcYdv2h7RWDCKVTmfskeGhPgjc1r02uG984PDSMbzv231BEC1a"
    "+pETheU8lEzW2WEYQkpCpRwu2LQ++Ew2m5WZKW31Ccs+z6hoYyKZajbaQAiBGlUcVsp/hKA7WGMeCUwlo9+14dbrfjj25VbZs8No"
    "mLK+77RVuXrT8WF/CjQtAWgRE9VZliWUUmCtvmwgN+jiU/f19PTEvg8RBD4WLJjubNnygcqiRR+dKj35ZcdLnRxFZcmM2LJsJ46j"
    "O5vfOu+9wbnnqo6ODrerqyt8qUANNw4OMgCQSGgGDLOBkAKO40IIKABoPuIVcxzwfzi2s1YI0RyFIYwxYGYorRBGIYjEJAHxfoCb"
    "Gabv4Z/94P4xeBj7zA9PpffmcnEtNO26OXgSjr2WiS8zxuQ9Lwk2BsKyX08wK+30pNdks70yl2P2/Xli+vQdke9DbNq0+o+k9DuV"
    "Cr9X3ziBQGAhBUBo2//NH7yq3d+cbGpq4jFnphc1qslms3JgYIBnz54tXz33zWcS0YcYOE4IKbVS+2IV/5eB2HLkpClWXdOEGxNe"
    "4u2WbWWUUnC9BKKworWK/yiEaEgl0xBSSiFEnTbaAVN+YssU68zTX1eSMsxv3bpV+74vagnXM8JYwPdF+8yZ1rZt23jrfd8rzjl5"
    "7mNk0RCACYlEcgqIbKXVkWBM9BI7H3/zG8/bee6507m//1yeN8937733Xv3GN543dPKcM3ZbtuvZtnMiQGCtLTZ81OjQk9/pWnvT"
    "SEdHhztt2rRDYfOLYfijzjvPeXzrVr1t2zYz58xzFyWSqeU6Vm4imRSVcvlxxeHFpo72T6hvzkopLxdCmlJptAAGUTULfYAJ9zKz"
    "Q4CuhOVIaZ10HMcVQhwrQKcA5pddt938MADMrBrWHBZS+/uxbds2k81mRTabtT/+8aD8k/vv/clJc84sE3C60irjOK6jVXy0ZVn8"
    "tbu/+8dtD5y3CwDmzZtnurv3igsuOMPbsP7qR499xUk/B5sLhJBp27briMTMpOc9eurZ5/9+49obClWjMwHBiwM1xzwNcEhKaQEE"
    "2I4DEAqTM/agzNOyZLLuY8yMKKowQGCY+xT0+0jyB+od92Nac1ZrcR5APggV23FhjIbjedMgqPXQTWYfttLV3t5u+b5v+75vT548"
    "2aoNCACSNPplSPlWo82uhJcEACkd+z3C0IeWLPGPaG/fbA8MDFBb23Zeu3ZFBSB8evMtvxGxfn0cR/22XRtLYjVF4TW1+y5YkHNf"
    "lDh+LJVXYVNT0ipgjja6Tak4JiJRKRV/ZQifrkYM/gnJZKo5P3JA1Tc0WPmRA8PG4KYNN159z7jL7QeAK6742L58XJFhpZL1Eslz"
    "jGFERr1hYedVv3XUyHebmtrjbPYe2dfXVwsvBREZAPFh8mi8d+UtqXVrLisC+OmiztyVlUp5YV1dw+naqDpK4G1hGI72bFz4EQBo"
    "9/0kEZXa2/1kT09Q2rBh9e8vWX7198OwfLxWut6SdjMB71my0v+Vh/RXosgZ8X1f5HI5psPodl4www8ODsogCOIPdKxOSSe6xBLy"
    "TK21bTsuiqOj99x+2/WfvPiym+pIl6lYyMdEsLVWu8D8pU23Bt/OZntlXd3vk1OnlsoDgDiqkLZvvPGyYQAbFi29pmzb9qlRGCYc"
    "y3mt1lqpVOr+IKDh13d0uLVEqDahti+/srWpfkIqn8/DdV2EcTFG2drfveaywlzft2YOHkGb1i381CUdH1XJVN1RURxOTtVlpkRR"
    "fMnKj37sO6N7f/9ATxCUqoV1RL7vi6GhIVs54geVcul4x/PeM5rPGyFEs9FqdYkKj2zqCn48d+5cK5fLmcPN+i8U1JDrugIAMsko"
    "JQyd6bhuozHV8FAIbAfArir+KzOOB5FNRCiVyjnL4FoA6O3NmqlTS8UgCFRfEEQPPVQIDwE2PRqFlX5jdLku02AD9DKOXRsAJjU1"
    "US13AIDFK6+bZgl7faz09wH6tjb8PRj78+zSOzrXrEn0B4Fqbd2pAWD/rtIXtY472ZgDxhhIIRsM039Kr+WiWoI2NDQkc7kc79q1"
    "S7UksBWgr0oh4Ti2qGo9RRNpfSwz08yZMymXyzEfRq/5Qk2u9IY3vAHz5s3DcD46WUrrfZ6XTISVSpHBP3eYbzvpzHlCgD4ihDhZ"
    "SstRKkYlLN+8qev6xzZv3mzfdNPv0N196cGJ8t/+bR7mzZtHJ554kQNZboxUNJOIjkul65xyubSHCZ956P7+4snz/s26cN7Jpru7"
    "23R0fPRoSHGdJeXb6+ubmhqbJjRKKeuViqcabaaofDh66hmv3lPnyeK8efPs7u4bw6OOPO6JVH2yxWieSKBUIpHMWJY17cTZr7LX"
    "3HTtg1u3btU7dsA75phmHQSBnnPWvH061rsBHOslEg1RFHEymW7+2je+O3L7xjWPBEEAAE6Nzn7BDJ/N9sqBgT7T399vjpszb5Zr"
    "2+8H40TH9bwwKu3RytzatS64e8455x0rNJYKKVsIgDEalmN/bdqR5/zO80Z1c/NePD00zMktWz5gtm69S805Y94Jju28jYGjXDfh"
    "VMrlYSZ8+qH7+4vHtpwsmpthTjzx/Ilamg+5rtfhuq41PLT/t4X8yCPlUoEcx0uxMUcawxkB+fjHbwoe7+/v19ms77S1vSkO4yee"
    "UFrP8hKJWYXiaJhIJqeqOD59zqvO+/Erzz9n6Dc/R7RlS6Df+95bUv+x+aMHfvLAvfefetpZJzu2c1wcxzJVVzctDEvNp5/52h8c"
    "d/45FTPUhK1b7zIvMNRsl7UXIA29xba9ixloMMYwQMOmbH8DAEwl9hgccZUSqMYZGgYYOCzT19KyV9TgQwgcbzvumUSUUCoGEcs4"
    "jggA+vqCOAgCw1b8fiLRrlQEx/UgiH5YyPAFDPmjZColjdExARkpqLF2j8ZGWEFwrlr/8dx2A94OQZBC2vn8SGjZ9gQi81UU8Pr+"
    "/iotEIY7zaGgzXynVC4+RESmWBgFIM5m1rdnCpix6+xW5fu+PFjSfCEMv2fPvaZqgPmajWpwvURCCEHMRhAjSqfdAwAgWRQBPMbG"
    "jAhZneMF6z19fX06n8+4+XzGzfq+09Gx3u3sXJNoa9uu+vr69NKlqycBok1aliOEUGGpuJ/Z/HRior5Gio1J0XhWIpWabAyXSqWi"
    "ZsIx6RF+B4xqFkKSl0zaAL5CQj6UzWZlFYePiAEQEbGEfWdUqawWgoTruK5WCul0pknHZt6iFddN7ehY7wIZ7fu+lc36jmHzfaXi"
    "e1LptMUMuJ5ngc1Z5ZFyvm/+fD0wMCCYXyCuxvdZBAGx7/v27jxOdaTVKaV1kdJaaB3tIBaft5jXNDQg/+Rw1OyJxNsgzKJUOnNS"
    "qThK2pglwnXv3HjjlfsPd/2Fyz423ZLRvzL4HZZln+p5niiMjPyQiW9pqRd3Y4yPAUBLVlz7QcCssh1npjEMFYexENK2bBtSWpVK"
    "qfAQC/u93WuufqImnK39bWdnp7du3bry61/f4c44bsJdqWTq1FK5lASRlkIMxHHYs+nW624fm3C9IAhCALxkVfAqAfo0kZhiWbYT"
    "huWK7TiLo1j/YO8ffjnY29sbEwAQ8fPq8UNDt9nMjHzebpZEt9uud6HSsbRti8H0yYn1vHr9+mAEmO58Yv0Ne0xo94HxOyKYaiUK"
    "V3IYXXy4ay+97NpjLAovYzZXEOikKkQJkKB7W+rFt4IgiAbGwmPf90nEez+rwTdrpWHbNsBUAYBkKo2wUr6nbKXe2L3m6j+0t2+2"
    "gyBQ48qM/OSTT0YAcNddXSEZurJULt1nOw6Bjet6iZOIZLY2rnw+f5CZ2/PEI1uNkZdqrR6vlnwpbVvOJmLTsaetzRARsrmc/bzH"
    "8fmmISIifu/KWw5kTDzFcRwnjipIputkFFXCIMhVAKBU2mMTUQXA8OJOP5FIpmRhNK/BOALgDyzuzL2ciIkAiyEUM7NWpoXJzAFR"
    "U2PTRBrNDyOO4o+A8OWDVOxAdX4Y08+HixZd8V8mQak4jq+a0DypZf++3SNxFG+IlPrv/1h/+eizPUdfX5+uMo23RRvX0/2XLLt6"
    "eGLDJLl/726Ooop2HOe0pauu/4xivTGTNr+oEnXVxCqbzfY3TxlwUum0CPeXkUylUoXRfF1/cK16IWhhAsDtmzfb9OsnWqSVmEda"
    "X++5iSlhFCrbsX8bhuWPqcKRvT09C+POzjWJTCYfDsyaRc0PPHJlMpF+RxSFs6RlwbJsOGOUQPUrEAep4TiKUKmUkEik/lgYHflR"
    "963Xvmv8Q48f0ALf92ryvYXLrlndUF9/Tr6Qf/AXj/8s+PHXvjY6Nob42fhz3/edgYEB3dbWxvsL4hLPS14SReEJWqui5yVSrpvA"
    "/qE9H9i8/vpPA1W9fiaTD4F5Yt9o/5pkKv2WUrE4zfPcOAzjbyqjbhYhHmluRgWAeV6gpr293QKAnvZ2ZQv3bRbhk0LQNBBLNnpv"
    "WFGrttfRnbVEZd26lRUAaNu+nVVh141ReXSZ1vopAqFSLmE0fwCF0TwKhVEURkcwmh9GoZBHFEcwWqNUzHdLPfxv1eKHbz3T6LWi"
    "9cGIo7wr51HT63ThiI/8+GtfGx0bQ/nPFS1yuVzc1tbGg4ODckLa9JRU5VKlVd71EimlYhSLeUhhTaidv27dynL1aztX7anjy0qF"
    "wmYpJaI4dh3XeasA9xkrmh4EgR4aarKfF6gZHh6ufjlEzJ2+k6pvdIujI7AdD5VyOa24/Iv+4AY1r1qVjwBwEARgMAgUA3P7L135"
    "mg8preuN0g1M4gwQzyQgaYB9gs3jCrTdFnIXkeDh/L777/hEV1jV3gD9/X9KjBFVpR9j0BMDPfF4urrG5xyOym5rayMiUgC4vd33"
    "giAovXvRoocbvZZ+FcdzjdEJMCOZTi1YsirnTUzxx4JcjvMr1roAyn1BEC289Jqh+saMKBYLsG1bVko4wgH2AuCmpgw9H4anPXv2"
    "GN/3xchIPCk0PCksl0Jm2GFU2cegH7uJlDpMTZIJhPb2zXZPzyXxhjX93zoYvVx6/U+lY9ogTAqK94KsR29fd6hp+JAOZmkUBKRq"
    "km+g2k81RoxVYX/WLFrg+15TPkOZTF7ncrmYiPSfw3cAWLjwyiNl0k50rwseB4BJXgvFBv+h4nBaMp05sVQscDKROqFUKKggCFYj"
    "CIDONWNj63CNLf9QKI48AI02FccJEA1FJN+0sPPKu4HUXnoeYMaulsp8b98oFoNxsWU7s6RloVwp90Lw6k235B7GmAf+xW0uzMTV"
    "oPrZS0vPXsbkP/Pbs9zukLipfYU/0WaxFIwjYmGu6Fkb7Ktdb8kK/99TqcwHi8VReIkkKqXiTwjyQxvWXfOLcV+aFQSBvmSlP0sy"
    "3ZFMpU8sFUaZQbEQWLxhTe6TfzPGh2GrZGbai2aLQW9yPO9YYww8zwOM2bnp48EvQcSzZ7fbf8bolM1mZba3Vx40FlGNTuXxarJx"
    "55Dv+04NTsbOY4xPD8f9VvPEceeP3ebpvte+5PITpOH1lmN9UEi6KO0l71i03D+/dj0h8MU4jv8bQCWKQm3Z9suZzMZlK4PTFy7s"
    "sZiZBgEHAO9P4zEGT0im0gARNTQ2OczVTPlvhppSCYaIePFiPw0XR7pewo7C4bhSLj8lSTxSe74ZM1pp27Znd7i+vj6Nvr6xl9Ar"
    "GxvvEcBstLbu5IGBAe7r6zV98+kgzx4EgakpAjpWXXe0UtEr3GRSxOWSRUCrIbsiLeSN0hEDQyFjoGtdMDT+7wHgzjvvlPPnz9dE"
    "xMs+fNVxQOJSIcS7hbRgKEYqlT6/Uio9texy/7EDHnYBTT+uDO87ynadtwgpIaXV6Lreq0cOjEzu6VkYt7buFNV7fMobrOx2gfJn"
    "CqP58yzLeiUzx2BuXrjMn/43GJ4JIO7rC6L29vakdHCOBiwCAYxCWCl/ioWqFTO4rQ1/qbCfxxYF0s+GJDU8931f7B5GmzH6Q0LI"
    "dmJ4DMkkiIgNiK1q77DhXyaADb7vfzIIAjM4OCirqgTgnnvuEbV7aW290fXsdq1irpRLZSEoeWB4H5Ogs4zCO2Sp2N11S5BfvNL/"
    "tVJxybPspIojhFqzZdvNtQ51ACXf/77Vc9MHKgCuXNTpL04mkqdprRxDOMOSoOfMTvb2zpJ9fX2c9X0njbrXW7Z9LYGmCmlZURQW"
    "FMe5SRn70ZaWFntgYMAcrgj9HCtbTnd3t+rt7ZUDv917ayKZvEQpdbplW02JZAqpVJpcLwHbcSGkABjQWjdLIWYVKmg7/cy5j+/b"
    "XXcgm53HLS1LxIwZZdPf38/t7e02Oal/cV3vjKgS7jVGj4C5ThsTEqGJSeyFVN/a9qMfha989bwQQMxMkwnUoLWmZDJ1TH40nnzG"
    "K0/40datW3V//xYDAItWXj0bBu8lErOMVjDG1AF07HP2+O3bt1fZwCCIFi67ZlKyvq6tUi5W1xIADdu2vTMIAl65cqXd3t7OY+vH"
    "jD/+urVkmAlEPDQ0RB0dq5u/d//D5xCL/5dMpRIgBhtGfnj4t0R4hKsONQFsjnG9xEQhhXBc72hVKs7QsfpSX9/qX/u+L9rashwE"
    "8w0AiLrWRtZIhJVKmZkNiLUQUqSS6UShkP8ZEd8Tel44JpTdL9N7PqF0/LqGhqaZ+ZFhpDOZtnKp8Nuurq5w6crglQ0TJs4Y3rfX"
    "MszvgBDnxnGsAAPXSzZ5ntf0XA1PtU/V931nf54y5VLJkCARhZVBQHxHG1YAOJ1eU16zBn9zw262r0/0AbqrqytctPzq0yTJD4Ng"
    "DQ/tN4LIGNaxIHxBk7WZWLkEcQIJ8a9RGF4IQkIpRQCxbTsnt7ff+GAQXDEyXgXgWAlPmYqU0koIKRJRFIaWbVOsVETEn9y4JtgC"
    "VNXFPT0LCwD+uHhF7jdaxXMA2JVyiRlmd4fvZ3SeA2a8AYJATOMmcQthpaLCsBw/p6gm6/t2bRD7R2m9l0xdolQMS1ohGHdJKdaJ"
    "NErV5OXZjd7R0eFmnx6ZPOvReM/wwXMkWdNc15stLctmow8YY74iDC60ON64ae3Vf+xeFzxuGfN9w+wz8QUE/CKVToMIwkkmFtvp"
    "yqpD4bBflRZE9l4Q76+rr0cymcaEiZPcOFYMqMUIoy+Mn2g61q93qzS2WFsOw08CzHEUgYhep0fxTQDnlEpFCCFhWTZc10O6rh71"
    "DY0A8xYA5z8nj28ErLGIorC4M/eaZCo9o1IpwXETbrFcHO76+NW/BYBFS6+enazLnKhUyHGoNISQgAYRkwH/smvNddvGqxLGJiY+"
    "3EQ+PNxnGEydyz86WQHH2rYtQcQqVvcpwxs3rw/urcn1enO5mAgjAB0A8PiSZf5nw7DiADguna6fVi6V5hys9lvVmsS6dSvLly73"
    "v10YzbdEYYUTyaRQWg/e/+2vfmbbtm3x4sV+urs7KHR3B4VDo+IWSdRgAERRpInEtGQyPS2OQxitIaSFKKrsixS2RVG8U9oSBNy+"
    "cW3w0HMyfAgY3/fFgQPIROC9lXL55WwM5UeGS0QYymZ9p256yRXGWmpZ8v1gB8ZiSGmBWQLEULH6YkfH6sWWta8wltaXn72c2Cf6"
    "+ubr+VnfmSSssxh8QhzHLC2bmLh/8/rg3mw2KydPPsvqCpaFFARjQlmfAYiR2P7PQqFQb0l5TayUIdDgwa9HNh2kEjbcGnwPwPcO"
    "N4Yxg1N7u59wW5ssjI4crVkHnue9qhBHMEZJIQRKxVEwo2TbtolVHBHj64p5Y/etVz1U+2h837f+KqipVctLA7Pi/QU1TQleRMRH"
    "SimYifax5ks08783Topfl1CpLzqu95ZKuVytp9o2hCAwGFppSCFex7a6K0TmY5GVmTXO8//EGaoxPdDYBotJzAAwmZkJDAhRg7Ls"
    "04ba29trBgZmUT6fsY+b1rzPKLW/WjYkZZgPhqpNTa1/cbR18WV+q1WHG2wVfteAP0MkTigVCwCjIqWkTEMjEokkCPwlIyjLJM6X"
    "DvuP1uPnz0igzV/l8fPn9wkAuq9vvl620p+qhbgYzJOFZUkA6Q3rrvlce3t7Mtn0sg4CzndsBxWtEcUh2PB+gGzP8zJkO5BC1IPo"
    "1FKx8DKjtLuk86rQQePjs2ZN/ZPeolpE5DY1aT06spvYHABBA0ay4rpaqXHBAt+uRh2D/L73rXL6+tYUAZSXLL367XWZzBsqlQpL"
    "IR0BtNSuvWPHdlHLitu2b7cHAVHT0ADAwk7/NEvQLIKVYq2OAfBOz0u0WNKCUhFs2wEze8XC6A9LpeIvo1KJwfLzXTdeef8zuSUA"
    "2LXrPhUEgX7OUU2seZrt2C8nIpRLhRAwu5ctC16lCWe7rntBFIYYHTlQJKJRJvMkgR4FkIgqlTOEbTmVOLYZyDiu1xhF4buZhGA7"
    "f9P8+fN/h2pbJsYpsAwA3LZ0abR4+XUPgnCeZVlnsjEgIY9dutQ/8bbbgofHNyMArIA1aF/hTwTTEsdLnFephMgfGC4Qiz/Uzspk"
    "mhgA+uYfSto6OvyMMaFtLKuFiJex4fluwraYJeIoxsjw/mppnmk/ASIMQxiItetuuOIrtevOnetbM2cO0vDwa01fX9Z0dVH4nAoh"
    "PiACgAHGohVXTWFNS10vucrzErpYHLmHjfkhkTjXktaJ0rKbk8k67N+36zOAdbO2oygRS20MlJa6Ho4Djs1FtmXlbNuF0jHiOM4L"
    "gwu71vnfP1zXX61Fp719s20ld16XaWy8vFQoKCFEPo7DX1haL1q//vpHn+Zlqz56tNFWn+26rxBCJCrlMktLfgQVfUdTE3YODg7K"
    "VGqmVSym1fgFQxd1XnM5kXgbmBoFcasB11uWDUtaEMICiFEqFXZLyKucusQDcaEAG+nfr6nKAZ9JvB2WoPuLPX7A9y3O5WIA6Fhp"
    "vctKuOfHUWxkqk4azYaIdjPj1EzjhMZ9e3fvB8SXbSk/uX7NNdsPd71ll39sNI7LxxrDZ7meOxVAJo7DYxb4/v25XC4cM/yfdBr0"
    "9CyMO1b591bKpblCiDOSqXTTgeHKORGJK5as8LcbCAEYCEApg1ekkqlTmAHDBiCqaB3+qLtr9ZO+7zs9PT1RTVd56YrcO5J1mamF"
    "wogHQ+9xHPcVtmWDwRAkEEYVhGHlV2B6kMH7WOD3iHTvmuCy/NPh5HHs2nW26uur8j9/s2g1WS3eMgAs6cy9KZWqO3GostcURkdK"
    "gsQkBi4AeMQYkyFGaWjwDx/91Ke69l522WV1O3bsCJHN6rbt22lgYJZoa9uOIPjIjo6Oj16jJG6rszNTK+WyZtDMTFEeSUS/fUaI"
    "iVxung6CqhetWrXqh+WKXgeyriNRfJmQlu04zr8RqNo9QlRNWBiohBWwMZqBAzC42zLu7rGXGi1ffn0rJRNChfl6AwS2Zc90LBfG"
    "GGilxrJwDNu2E8ZRPMQCn9Mw/16jiX3fF77vOwMAqh0ny8bgpOt/tOdfbPjSrFkxACxZcsMERkhCSJAQoTHmcwBnpLTerLRyVRRL"
    "BnsynXABQCml+vr6FKqr7BHAuqNj0AGArq7Vv13U6Q+TEMSAJKajGGoagN+O0/2Yscxv7AXkaM2aNUXf97++b5RLcRxfVVfXcHoc"
    "hwgrFXDVsyGFhJdIQkqJQjH/uCDaLIz9+dtu++ju2jPFiK92Wb7WMAHgGaP5ETBX1QvpugxG8wdgDH2KCV9k5t2OwtD69cGBcQ0P"
    "BuAxiPrrVvL7SwxPY/VR6ljptxmOl1pCTonjKCaQhtZ3GuJjPMd9J2mBUqlQAfBYktIJ3/etwcEjVM14Vdgg5PM+jUURtG+UmA8q"
    "fTgBiD+rK8/lchwEAYIgKPm+f9eukViWK6VXqyg6zRh9Rn19o2vYYDQ/stew/gEb/jlL8cMNt/j9AHBpp//+RDo9vVgseMy4yHbc"
    "SSQktFKwHRdKRahUKg9WwvJWY/iPbOjr62+88lfjEz0A1uDgEbx5c7ui57h04v9oeN/3aeztqkXLr35ZMplcyADiOATDKNilX0On"
    "CQQIEohMpADeC8h8EFyjstnDdz+PRRFY0nmNEkKAAGbg92zRk+PMbJ7ZVVF70Gw2K++9F+jvv+6rAL566YogS0zFMKy8Io7jWID/"
    "2+jSv29ce+NjF192U92HP3zjcSUdnsvMvuN4LVppxHGMUrEIZgM22EdClsKwMkyEnl/99N477rrrrrDGR40j9vRY3Rg9PQufM/f0"
    "V4WTQjpFpRSkZUOpCAB2QcrQhCYhSCA2MRzbS4Zh5YSQokQ22yuPOupB2/d9FQSBYWaaP79PTJz4xEE62jAgpDRgKIK8b7enHmVm"
    "yuVyFARk/qfaaO2I6sw33CHcT0LaTkoW1wRX762qu65+FavyFcpLnGwUpwlcnx8ZBjNDCIFUOoNSYRSxUZ9hiu/QbO/mYjxcM3pt"
    "PsCztRS+EIbv7c3K7dvBg4NHyEUr/QuJzDuU0rHtOCiXo4eFpDWx65ZFRYxUwvIPjVLHu+lMfRhVJgjHTOvrm78DQLFGiBFROBYr"
    "Fxf4vpcaxTVSWqfGYSjSmXpnNJ8v9wVBlPsLNZ2+74t8Pu8CU7AuWFkCqsTckhX+sYtXXPMvlnRmKK3mENE827FhqkslIJFIIopD"
    "VMqlr0ZxdL/SOmajvnXrDblfHXr2XnnPPcNiePgeM/aSn9fV+f5sHL9gge/VkpIlnbk705nM/MJoHg0NTRge3n9n97rgnQCweJU/"
    "WSs+zxK0pqGxedLw8L4hEH/WCPMlJ/Qeq01o2WxWHnnkMS3G9tJRrM70XO/TyVQao/kRw0Y/qpmW7HvVcT9o276dnxnH/+m4+WkT"
    "2gc71zQlKN9ipJwBo5da0rrAS6QQhSFUHEMIAVTpiicSyWSxXC5FhmnF+DWL29s32677iNh19tmqb/58gxdw4X/rz9dT83QIWyEP"
    "FoYJgKCDk+DGW3K7/9+VN9wjK3EJMAAbj1h8ULK4UFnxN5as8NdvXBs8NrH15bNCyPcLbV4vhJgcRSGn6zKkjf4pBL+lJcVDpe3b"
    "7SAYn4H+aUHEz+Xk4OBCGh7uNbW9Qxwx+nbD9EELdKyGSCuluVQYpdp4U+k0KuUyYqNuZou+KF2b4v1PDD0zR6hGg114oY/DejxV"
    "VaS0sH2z5U7Y16DL5XNB4vJ0OnNCsTgKx/G+GleiT0+oN3cHQaBq1aFLV+TeYTteezKVfo2KQ5TLZWitnmLm+0A0yMZMJcJs10tM"
    "b2hoQqlUgorjO8vl4qe71wV31UiyZyq8stmsRFubnDw0ROM7pxctuqIRnneR57mnxVE0h9mckkimSSsFIoLtuCiXi1BafSLhph6u"
    "VIqsie+8fU2w59C1faexcZD/3nuLHNbjjTE0f/580dezML50hT+BhFhBJF9hjLGFsFAqFu/c3HX9N2r6+mwuZ/cyx0R058KOKytC"
    "iGalo+la6zrPSxzpuN47hBAwxiCOIpRKhZH8geHdsVLFYr609pObb9ja0bHeDUPPBMHB1J1836exrrmDPIrv+9auA5iSdO2WONan"
    "GZhLvURyphACcRwhrJRhtKmA+AlldDFW0R6LaN2aGy4bGK+rzAw18a5d96nnc4G3v9nwuVyOkM0CfX0gC01G0cmObbu6JiQVNDrm"
    "idTW1iaCIIgpCBi+LyYD3xgJ9cNxpNYIQRcaYxCFFWijYVvOWGaJXyqluqSKvztlsn2g+nUvCw8Txop5uRyAQwqFwQNmti3lCg06"
    "n4SQMGyPjhwAEcGyHSgdAYQHAbOaKtFPLENm165ZxWfTVb5YBx0uUghyOZ6by8lZeUxXWr/Pse1rXDeBMKrsZa1/TIQrJtThsWpf"
    "VQDf9zE0NGQXPc/5j1tuGa3RqZLQxsxSSksbNtqS0mImMib+3R6Tf7BvbDHn9s2b7Z6FC+NaMQN4HOMhZcnyK09lab9RCjmdDU/V"
    "Rs9OpzMTpLQghES5VEBYKW+FsO4S0L/XLH5/7pPH3Td/3N5Rte2KNm/e/JyTnhfa4y0QRf2AauvMzfUc7+1KKyWkkMaYPxrGbQlk"
    "ngDyAHLs+wf7ScOx/6q6xnXLtgLY+j9FTTumQ7Xu3KnHeBkNjGkXO6880mK7VZBIMfS72fC7Eul0HVVpCJRLRbAxv7Udd7+KomEC"
    "fXEPD99Re5ktvi9qkNLUNBTXIKynpwcvheNPDD9uTUgIYc50Pe94XSpUdYWMwUn1uDcIVpoFC3wPoArg/8lX09Q0FP8lN9+yJaiM"
    "F5yOV/GSsD8Apv9nwM1EwoZhURwdra4rnErDMJcEeHNoFb/gRU37MvX5eGOwTj+dR0EFL9HDemZRedeuPpXNZmXzlFNexqY8XQhB"
    "AFDthueh2sw/cWJajvHN5oOLr3i557mL2Zh9iJw7guDqJ2pJU1NT09MyzMHBIygMd8qmpgwptcOM9Q9Vo5QV/oWXrgjeqtl4AuJ0"
    "EjTNsR2QEPC8BMrlIsJK5atxHH2XmHZa7Px4w+qrBsdDp+/7VlXy1/eCxuHPK8bX9upYvGrVJNLpZSQoa1n29CiKiI35kbTpEw//"
    "BJ+fN69qwJ6ehXHHimtPsT3nPVEYrjRs9nNsulnwHZMa5O9nzZql51cTEfi+T7XVs59WrFjptyW99ORipQBj8OFEMnmBFBaUimGY"
    "YYyGiqMdCS+1sxKW97Pk27tvCb75zJJaU9OQHuNRXrLGfhr9Mr5a0tjYKACAVGoKwIscx53BzFIIIrLotgkpfK6/P9CFQsHt6VkY"
    "d3Ssdw2bWy3L6TRGGwI1CZs6pZAf3VtE0/z58/VYtwgHQY57e3vNwbh8LDTUmj8SG3O3MXQ3QOdVymUUi6MIw7IWQkCrWBPE53W5"
    "9L6JdXzRxptz3xrfot7VtSzs6loWjsX+/xBGf5rhiagms+NKGEUA1RERSctCXV09gUxtlSNOp9Nhe7ufZGffa0B8tJBCEAnDDJ2u"
    "a0wz6Gwdw+voWO+6bmuixlcTEWd7e2XzlFkrVl51y5f3F8SXQPQGIchyXdeybctK12WQTKXBhPvY6E425l9YyJ5bbw1+FwSBIiLO"
    "5XKUzfZKfons6fScoaYmW54717dOmoNXCNt9exRGl7mum9RaHWBjfqaMur4lI+6vSaMXL/bTlMCbYXCjl0wdVS4XI2aK6+rqvcLo"
    "yH4p7Nd0rfnoQO1c2GZWIpWaWIniGTB6eeOE5hlRWEGlXKq1TSKOoj22bf9eRfFuQ/jC9m3f7zu4tajvO8kdENOnQ73Uto97zpPr"
    "WH9o1N8fqONn5xa6tnNpHEWwLBthFP6anAnv3HRjx/4aLz2W1hcWd/oPgWi/lHIamCQRoFVkEcFWJn5VNpt9FJjisI3ziehyrc1p"
    "VN2dRg/v33uwEGRZwoqjCAS6WzFv2LAut7UKSb0SqDY4vZDbRrxohh9tahpHhpF0PQ+lYgFeIolisVC38caO/QCQz+efJutuzuAP"
    "+/L82bBSmdA4YeK0cqlohWFFA6gjYFXL1Fn/OgZnR4LxChI0xhKSTCRSICLkR0Z+xqw/z8yPEvGODb9/5DeHOPes+XvuVPN3hRpm"
    "0LycL08capJK7J0BEtckU3UXVcoly/MSv6qUSv/lUN0NmUw+HACsviCI4PvCR7VBoHlK28uUNq91XftUNjRPm3iGICldz4VtOTBs"
    "EI+1SVqWDRKEcqn8pG3bj2ijCqz01wvDT9y5ZcuWSg32duyAMwYp+h9pwvyrDF9rHlu6dPUkJeMciN/muYlWYwziSuWKjeuvvfng"
    "w4+xkM+gGKwgCNR7OvxMvU2bwHgnwCQEgQ0YBAEiMJvQlg6NSfg2cmhu7u4Odo2rY+LF2v7tRYlqwrBVVrPUKAXwBY7tTDbGwHYc"
    "GMa+mtHn+r7l53Jyge97C3zfG5chquXL/TktKfdzjuOcBaAMcMiMUFpSZOobUd/QCEF0tyS8mQRfUA6j9TWjjy94vFjbv71IHr/Z"
    "bm3dqQeHormW7X4lnarLlErFEgl6QiteVczo700H1L0Axm/JtmjFdVMdwecKx0NULr2tceLEi8JyGWEUwnMT0FqhXCn/1LGcRyCB"
    "SIV3jk98fP/71o4d91quO6h7ejarv1Ye8Q9veAC4dOV1L2MyS9jwh+rq6jOF0eE/wIibY5G+s2ftqn3jiwbNzXDQDPAoFifcxE3S"
    "tlAqFHGoq5EiIhExmwIMrth4a25L7V7ZbK8AgLa27f/rJsu/Oqppb2+3GeaCpJd6f6lUSFXLeyKqEN/9yXFGb29vt60ULSDwB52K"
    "Z0Iut2ijQYqQTKWqpcLCqGZCN4O/QIa1Q/jdeCKorW2slprLMYLg/7Ldxzx+xbVXT2xpuXZo/15IS46EUXRn95rcwpUrV6Ziypyv"
    "NLdYtjVZx/EbUunM6Y7rQqkYURiiXC6PCkEPAfwYGdptIHq7bz2klzwkT25VfeP48f/rh7Vy5XXTysZMKJVKBkQiqoR5JvpDR8fq"
    "5jLH55Mxget6R9PY0iWlUgGFwkhFSis22oRE4gEyYv2GW6sLdDIzNddX5d+5XE6PSTr+eTwzqqnouBdk/rVSLpLRGgy0CKDdWPE9"
    "xLyaQdPGNk5BIplCIpECiH4DLa4xks8TQiyNSurH4zkfAGbM6PxPEz8L1Fza6Y9RTRSjqrS1bcepdToARIAxKBULe6TjbGWtHjPA"
    "z02R77799kPV+jHunXFoXbB/Hn8OaphoAzPOTCSTp2oVQykNrRRUrMDGlKQlwzFIuSuK402b1wVbgarKzJjNdmvrTv4npDwHj1+6"
    "dPUkRfGqCZMmrVJxhDAsw3E8EAEHDhz4uZTolkLcR5E48NRT8f6nySGqmSz+t6b1L3hUs7DDb0skE29VWrms4jrh2ALa7NVG/wLh"
    "3h90d3cf7O0c2/bBBEFO/19Lep5Xw2ezWaevr++gFy/svP5IKWPd/fFDPMrQ0JAdhseb1tad+p/4/fwc/x+UzDCpTpkC8gAAAABJ"
    "RU5ErkJggg=="
)
ICON_CAT_PIZZA = f'<img src="data:image/png;base64,{ICON_CAT_PIZZA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_POKES_B64 = (
    "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"
)
ICON_CAT_POKES = f'<img src="data:image/png;base64,{ICON_CAT_POKES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_POLLO_B64 = (
    "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"
    "6/8BNmLhj3mYyJgAAAAASUVORK5CYII="
)
ICON_CAT_POLLO = f'<img src="data:image/png;base64,{ICON_CAT_POLLO_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_SALUDABLE_B64 = (
    "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"
)
ICON_CAT_SALUDABLE = f'<img src="data:image/png;base64,{ICON_CAT_SALUDABLE_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_SANDWICHES_B64 = (
    "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"
)
ICON_CAT_SANDWICHES = f'<img src="data:image/png;base64,{ICON_CAT_SANDWICHES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_SUSHI_B64 = (
    "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"
)
ICON_CAT_SUSHI = f'<img src="data:image/png;base64,{ICON_CAT_SUSHI_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_VEGETARIANA_B64 = (
    "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"
)
ICON_CAT_VEGETARIANA = f'<img src="data:image/png;base64,{ICON_CAT_VEGETARIANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

# Mapeo categoria de marca (texto tal como viene del Excel de Rappi) -> icono.
# Las claves van SIN tildes -- icon_categoria_for() normaliza el texto de
# entrada (quita tildes + minusculas) antes de buscar acá, así "Pastelería",
# "pasteleria" y "PASTELERÍA" resuelven igual sin duplicar cada clave con y
# sin tilde a mano (bug real detectado y corregido en pruebas: "Pastelería"
# con tilde no encontraba la clave "pasteleria" sin tilde).
CATEGORIA_ICON_MAP = {
    "americana": ICON_CAT_AMERICANA,
    "argentina": ICON_CAT_ARGENTINA_CARNES,
    "carnes": ICON_CAT_ARGENTINA_CARNES,
    "asado": ICON_CAT_ASADO,
    "asiatica": ICON_CAT_ASIATICA,
    "cafe": ICON_CAT_CAFE,
    "comida casera": ICON_CAT_COMIDA_CASERA,
    "desayunos": ICON_CAT_DESAYUNOS,
    "empanadas": ICON_CAT_EMPANADAS,
    "hamburguesas": ICON_CAT_HAMBURGUESAS,
    "hamburguesa": ICON_CAT_HAMBURGUESAS,
    "helados": ICON_CAT_HELADOS,
    "hot dogs": ICON_CAT_HOT_DOGS,
    "hot dog": ICON_CAT_HOT_DOGS,
    "internacional": ICON_CAT_INTERNACIONAL,
    "italiana": ICON_CAT_ITALIANA,
    "jugos": ICON_CAT_JUGOS,
    "mexicana": ICON_CAT_MEXICANA,
    "milanesas": ICON_CAT_MILANESAS,
    "pasteleria y postres": ICON_CAT_PASTELERIA_POSTRES,
    "pasteleria": ICON_CAT_PASTELERIA_POSTRES,
    "postres": ICON_CAT_PASTELERIA_POSTRES,
    "pescados y mariscos": ICON_CAT_PESCADOS_MARISCOS,
    "pescados": ICON_CAT_PESCADOS_MARISCOS,
    "mariscos": ICON_CAT_PESCADOS_MARISCOS,
    "peruana": ICON_CAT_PERUANA,
    "pizza": ICON_CAT_PIZZA,
    "pizzas": ICON_CAT_PIZZA,
    "pizza / pizzas": ICON_CAT_PIZZA,
    "pokes": ICON_CAT_POKES,
    "poke": ICON_CAT_POKES,
    "pollo": ICON_CAT_POLLO,
    "saludable": ICON_CAT_SALUDABLE,
    "sandwiches": ICON_CAT_SANDWICHES,
    "sandwich": ICON_CAT_SANDWICHES,
    "sushi": ICON_CAT_SUSHI,
    "vegetariana": ICON_CAT_VEGETARIANA,
}


def _normalizar_categoria(texto):
    """Minusculas + sin tildes, para que la búsqueda en CATEGORIA_ICON_MAP
    no dependa de si el dato del Excel trae o no trae tildes."""
    import unicodedata
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def icon_categoria_for(categoria_texto):
    """
    Devuelve el HTML <img> del icono especifico para una categoria de
    marca (ej. "Peruana", "Pizza / Pizzas"), o ICON_CATEGORIA (el bowl
    generico) si la categoria no esta en el mapeo -- nunca revienta con
    KeyError, cualquier texto de categoria que no reconozca cae al
    generico.
    """
    if not categoria_texto:
        return ICON_CATEGORIA
    key = _normalizar_categoria(categoria_texto)
    return CATEGORIA_ICON_MAP.get(key, ICON_CATEGORIA)
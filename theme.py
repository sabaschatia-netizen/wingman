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

from logo_asset import WINGMAN_ICON_AZUL_B64, WINGMAN_ICON_B64, WINGMAN_LOGO_AZUL_B64, WINGMAN_LOGO_FULL_B64

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

    # Pasteles de Contact Performance (barra apilada + leyenda) -- pedido
    # explícito de Sabas, mockup aprobado: Amazon Connect/WhatsApp/Meet/
    # No Contactado dejan de usar los colores eléctricos genéricos
    # (brand_purple/success/blue/danger, reusados en media app) y pasan a
    # su propio set de 4 pasteles dedicado, para no arrastrar cambios a
    # otras cards que sí siguen usando esos 4 colores base.
    "cp_calls":        "#A78BFA",   # lavanda -- Amazon Connect
    "cp_chats":        "#4ADE80",   # verde menta -- WhatsApp
    "cp_meets":        "#7DA6D9",   # azul claro -- Meet
    "cp_ghost":        "#6C9BD1",   # azul acero -- No Contactado
    # Rojo coral pastel -- compartido por las pills de Rendimiento
    # Farmer/País (fondo, reemplaza el rojo eléctrico "danger") y por el
    # segmento "Rechazado" del funnel de Rendimiento Comercial (pedido
    # explícito de Sabas: "ese mismo rojo coraloso pastel que usaremos
    # en las pills").
    "coral_soft":      "rgba(239,68,68,0.16)",
    "coral_text":      "#C4483F",
    # Versión SÓLIDA del mismo coral -- para los usos de "Rechazado" que
    # van como fondo sólido con texto blanco encima (barra del funnel,
    # pill de estado en la tabla), donde el pastel translúcido no daría
    # contraste suficiente. Mismo matiz que coral_text, más intenso.
    "coral_solid":     "#D9483F",
}

LOGO_FULL_URI = "data:image/png;base64," + WINGMAN_LOGO_FULL_B64
LOGO_ICON_URI = "data:image/png;base64," + WINGMAN_ICON_B64
# Logo completo con letras en azul petróleo -- pedido explícito de Sabas
# (décima novena vuelta): usado en el loader nuevo, que va sobre fondo
# claro (COLORS["bg"]), donde el logo blanco original sería invisible.
LOGO_AZUL_URI = "data:image/png;base64," + WINGMAN_LOGO_AZUL_B64


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

        # Pedido explícito de Sabas (vigésima tercera vuelta): el
        # favicon del navegador pasa del ícono blanco/naranja original
        # al ícono azul petróleo/naranja (mismo criterio que el logo
        # LOGO_AZUL_URI usado en el loader, ver theme.py más abajo).
        return Image.open(io.BytesIO(base64.b64decode(WINGMAN_ICON_AZUL_B64)))
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
# Lupa -- pedido explícito de Sabas (décima octava vuelta): reemplaza la
# lupa 🔍 a color del botón de navegación del sidebar, renombrado de
# "Buscador de Marcas" a "Ficha de Marca".
ICON_FICHA_MARCA = _icon(
    '<circle cx="10.5" cy="10.5" r="7" stroke="currentColor" stroke-width="1.8" fill="none"/>'
    '<line x1="15.5" y1="15.5" x2="21" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
)
# Ojo/carrito -- pedido explícito de Sabas (vigésima vuelta): íconos de
# las barras del Top 3 de Markdown Plan (ojos = visitas del producto,
# carrito = pedidos reales), en vez del texto "VPD"/"CVR" crudo.
ICON_OJO = _icon(
    '<path d="M2 12c2.5-4.5 6-7 10-7s7.5 2.5 10 7c-2.5 4.5-6 7-10 7s-7.5-2.5-10-7z" '
    'stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/>'
    '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6" fill="none"/>'
)
ICON_CARRITO_MD = _icon(
    '<path d="M3 4h2.2l1 3M6.2 7l2 9.5h9.8l2-7H6.2" stroke="currentColor" stroke-width="1.7" '
    'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    '<circle cx="9.5" cy="20" r="1.3" fill="currentColor"/>'
    '<circle cx="16" cy="20" r="1.3" fill="currentColor"/>'
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

# Google -- círculo con "G" en trazo, reemplaza la lupa 🔎 en el dato
# "GOOGLE / RAPPI" de la cabecera de Ficha de Marca (pedido explícito de
# Sabas, mockup aprobado): emoji monolineal propio en vez del emoji
# nativo del sistema (se ve distinto por dispositivo y no se puede
# recolorear). Mismo lenguaje visual que el resto de íconos -- círculo
# de trazo + glifo interno, ambos en currentColor.
ICON_GOOGLE = _icon(
    '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/>'
    '<path d="M15.8 12.15c0-.42-.04-.83-.11-1.22H12v2.31h2.13a1.82 1.82 0 01-.79 1.2v1h1.28a3.86 '
    '3.86 0 001.18-2.9z" fill="currentColor" stroke="none"/>'
    '<path d="M12 16.2c1.07 0 1.96-.35 2.62-.96l-1.28-1a2.4 2.4 0 01-1.34.38 2.42 2.42 0 01-2.27-1.68'
    'H9.4v1.04A4.2 4.2 0 0012 16.2z" fill="currentColor" stroke="none"/>'
    '<path d="M9.73 12.94a2.53 2.53 0 010-1.62v-1.04H8.4a4.2 4.2 0 000 3.7l1.33-1.04z" '
    'fill="currentColor" stroke="none"/>'
    '<path d="M12 9.44c.58 0 1.11.2 1.52.6l1.13-1.13A4.16 4.16 0 0012 7.8 4.2 4.2 0 008.4 10.28l1.33 '
    '1.04A2.43 2.43 0 0112 9.44z" fill="currentColor" stroke="none"/>'
)

# Rappi -- círculo con "R" en trazo, reemplaza el eslabón 🔗 en el mismo
# dato de cabecera (mismo pedido/mockup que ICON_GOOGLE).
ICON_RAPPI = _icon(
    '<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/>'
    '<path d="M10 8.6v6.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
    '<path d="M10 8.6h1.9c1.05 0 1.8.7 1.8 1.65s-.75 1.65-1.8 1.65H10" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    '<path d="M11.6 11.9l2.1 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
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
    # Fondo de pantalla completa del login (rediseño septiembre 2026, pedido
    # explícito de Sabas a partir de una referencia visual): diagonal grande
    # de dos tonos -- brand_blue arriba/izquierda, card2 (gris claro) abajo/
    # derecha -- con textura de puntos en ambas esquinas opuestas. El corte
    # diagonal se logra con un conic-gradient de 2 colores rotado 135deg
    # (mismo truco que un clip-path pero sin recortar contenido real detrás).
    # La textura de puntos usa 2 radial-gradient en mosaico (uno claro sobre
    # el lado oscuro, uno oscuro sobre el lado claro) limitados a las
    # esquinas via mask, para no ensuciar el centro donde vive la tarjeta.
    # Rediseño septiembre 2026 (segunda vuelta, pedido explícito de Sabas):
    # se invierten los colores del fondo -- antes era azul petróleo con
    # puntos claros y una diagonal partiendo hacia gris; ahora es BLANCO
    # liso (sin diagonal, parejo en toda la pantalla) con puntos de color,
    # mezclados entre azul petróleo y naranja (no todos del mismo color).
    # La "mezcla aleatoria" se logra con un mosaico de 4 puntos por tile
    # (3 teal + 1 naranja, en posiciones asimétricas dentro del tile) que
    # se repite -- csss puro (background-image con varios radial-gradient),
    # sin depender de que el navegador soporte nada más allá de lo básico.
    # No es aleatorio de verdad (un patrón CSS no puede serlo) pero al no
    # ser una grilla 1-color-por-punto ajedrezada, no se ve mecánico a
    # simple vista -- mismo criterio que aprobó Sabas en el mockup.
    LOGIN_CSS = (
        f'.stApp, [data-testid="stAppViewContainer"] {{'
        f'  background:'
        f'    radial-gradient(circle, rgba(18,62,74,0.16) 2.6px, transparent 2.6px) 0 0/68px 68px,'
        f'    radial-gradient(circle, rgba(18,62,74,0.16) 2.6px, transparent 2.6px) 34px 34px/68px 68px,'
        f'    radial-gradient(circle, rgba(232,102,60,0.20) 2.6px, transparent 2.6px) 34px 0/68px 68px,'
        f'    radial-gradient(circle, rgba(18,62,74,0.16) 2.6px, transparent 2.6px) 0 34px/68px 68px,'
        f'    {COLORS["brand_white"]}'
        f'    !important;'
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
   clase modificadora.

   Fondos más saturados + texto claro (corregido tras el rediseño de la
   franja a azul petróleo, pedido explícito de Sabas: "el botón de
   disponible se ve opaco") -- los pasteles tenues originales
   (success_soft/warning_soft/etc., con texto oscuro) estaban pensados
   para fondo blanco/card y casi no se distinguían sobre el nuevo fondo
   azul petróleo de .brand-sticky. */
.conn-status-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 13px; font-weight: 700; padding: 5px 14px;
    border-radius: 999px; margin-top: 4px;
    background: rgba(255,255,255,0.14); color: {COLORS["sidebar_text"]};
}}
.conn-status-pill.warn  {{ background: rgba(251,191,36,0.28); color: #FDE68A; }}
.conn-status-pill.alert {{ background: rgba(239,68,68,0.30);  color: #FCA5A5; }}
.conn-status-pill.ok    {{ background: rgba(34,197,94,0.30);  color: #86EFAC; }}
.conn-status-pill.info  {{ background: rgba(108,155,209,0.30); color: #BFDBFE; }}

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
    gap: 28px; flex-wrap: nowrap; margin-top: 36px; text-align: center;
}}
.brand-stats-row > div {{ min-width: 0; flex: 1 1 auto; }}
.brand-stats-row .stat-label {{ text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }}
.brand-stats-row .stat-value {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
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
/* Rediseño septiembre 2026 (pedido explícito de Sabas, a partir de una
   imagen de referencia): dos tarjetas independientes -- oscura (logo) +
   clara (formulario) -- superpuestas con esquinas redondeadas simples.
   Se activa solo con build_css(login=True) -- el resto de la app sigue
   con su fondo claro normal sin que este bloque se filtre ahí.
   LAS DOS TARJETAS: cada mitad es un <div> normal (mismo layout de
   st.columns de siempre) con esquinas redondeadas simples (border-
   radius) y un leve solape entre ambas usando % (no px) para que la
   superposición escale con cualquier ancho real de pantalla.

   NOTA (revertido tras probarlo en pantalla real): el primer intento
   usaba clip-path: path(...) con coordenadas en px fijos para lograr
   una curva en S entre ambas mitades (una "cintura" cóncava/convexa en
   el borde de unión). Se sacó por dos motivos, confirmados en captura
   real de Sabas: (1) las coordenadas estaban calculadas contra un
   ancho de referencia (991px) que no coincidía con el ancho real de
   pantalla del usuario, y clip-path: path() usa unidades absolutas, no
   porcentaje del box -- en una pantalla más ancha el recorte quedaba
   ridículamente chico en una esquina, con forma de gota/mancha en vez
   de cubrir el panel completo; y (2) el renderer disponible en este
   entorno para probar el CSS antes de entregarlo (WebKit viejo vía
   wkhtmltoimage) tampoco soporta clip-path: path() de forma confiable,
   así que no hubo forma de validar la curva a ciegas antes de que
   Sabas la viera fallar en su propia pantalla. Si en el futuro se
   quiere retomar la curva en S, hay que probarla directo en un
   navegador moderno real (Chrome/Safari/Firefox actuales), no acá. */
.login-box {{ width: 100%; max-width: 960px; margin: 0 auto; }}
.login-box [data-testid="stHorizontalBlock"] {{
    display: flex !important; align-items: stretch !important;
    filter: drop-shadow(0 22px 34px rgba(0,0,0,0.30));
}}
.login-box [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    display: flex !important; align-items: stretch !important; align-self: stretch !important;
}}
.login-box [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div {{
    width: 100%;
}}
/* .login-logo-col sigue siendo un <div class="..."> normal (ver
   wingmanapp.py, col_logo) -- ese caso SÍ cierra su propio </div> dentro
   del mismo st.markdown, sin elementos nativos de Streamlit sueltos
   después, así que el hack funciona ahí sin problema.

   .login-form-col en cambio YA NO es una clase de <div> -- pasó a ser
   un st.container(key="login_form_col") real (ver wingmanapp.py).

   BUG REAL #1 (corregido, visto en pantalla por Sabas, primeras dos
   capturas): el <div class="login-form-col"> original se abría con
   st.markdown() y NUNCA se cerraba en el HTML -- el resto del
   formulario se renderizaba como HERMANO de ese div, no como hijo.

   BUG REAL #2 (corregido, visto en pantalla por Sabas, capturas
   siguientes): al pasar a st.container(key=...), el primer intento
   apuntaba el fondo/padding a ".st-key-login_form_col > div" (un nivel
   por debajo de donde Streamlit pone la clase st-key-*). Eso terminó
   pintando una tarjeta clara SEPARADA por cada elemento del formulario
   (una para el toggle, una para Correo, una para Contraseña, una para
   el botón) en vez de una sola tarjeta para todo -- el combinador
   "> div" resultó demasiado permisivo, calzando con más de un div hijo
   directo del wrapper real (además del contenido esperado). Se
   resuelve aplicando el fondo/padding/radius directo sobre
   .st-key-login_form_col (sin bajar de nivel con "> div"), que es
   donde Streamlit realmente pone la clase -- confirmado leyendo el
   código fuente de streamlit/elements/layouts.py (block_proto.id se
   asigna a UN SOLO bloque contenedor, no a cada hijo) en vez de
   asumirlo por CSS a ciegas. */
.login-logo-col {{ width: 100%; min-height: 560px; padding: 48px 44px; box-sizing: border-box; }}
.st-key-login_form_col {{
    width: 100%; min-height: 560px; padding: 48px 44px; box-sizing: border-box;
    background: {COLORS["brand_orange"]};
    border-radius: 26px;
    box-shadow: -10px 0 24px rgba(0,0,0,0.10);
    display: flex !important; flex-direction: column !important; justify-content: center !important;
    margin-left: -3%;
    position: relative; z-index: 2;
}}
/* Neutralizar cualquier fondo/gap/padding propio que Streamlit le ponga
   por defecto al stVerticalBlock interno -- ahora que el estilo visual
   vive en el wrapper (.st-key-login_form_col) de arriba, el bloque
   interno debe ser 100% transparente e invisible como capa, para que no
   se dupliquen bordes ni se generen tarjetas anidadas. */
.st-key-login_form_col [data-testid="stVerticalBlock"] {{
    background: transparent !important; box-shadow: none !important;
    border: none !important; border-radius: 0 !important; padding: 0 !important;
    gap: 14px !important;
}}
.st-key-login_form_col [data-testid="stElementContainer"] {{
    background: transparent !important; box-shadow: none !important;
    border: none !important; border-radius: 0 !important;
}}

/* Mitad oscura -- esquinas redondeadas normales */
.login-logo-col {{
    background: {COLORS["brand_blue"]};
    border-radius: 26px;
    display: flex; flex-direction: column; justify-content: center;
    margin-right: -3%;
    position: relative; z-index: 1;
}}
.login-logo {{ display: flex; justify-content: flex-start; margin-bottom: 22px; max-width: 100%; }}
.login-logo img {{ max-width: 100%; height: auto; }}
.login-title {{
    font-size: 26px; font-weight: 800; color: {COLORS["brand_white"]};
    letter-spacing: -0.6px; margin-bottom: 6px; text-align: left;
}}
.login-sub {{ font-size: 15px; color: rgba(255,255,255,0.78); line-height: 1.6;
    margin-bottom: 4px; text-align: left; max-width: 380px; }}
/* Pie de página ("25 Farmers...") -- blanco translúcido (antes gris
   .muted, ilegible sobre el fondo naranja nuevo de .st-key-login_form_col). */
.login-foot {{ font-size: 11.5px; color: rgba(255,255,255,0.85); margin-top: 18px; line-height: 1.5; }}
/* Inputs y botón del formulario -- ahora viven sobre el panel NARANJA
   (.st-key-login_form_col, fondo brand_orange, rediseño segunda vuelta).
   Los inputs se mantienen blanco sólido (buen contraste sobre naranja);
   el label pasa a blanco (antes texto oscuro, ilegible sobre naranja); el
   botón "Entrar" pasa de naranja a azul petróleo oscuro -- un botón
   naranja sobre una tarjeta ya naranja se pierde por completo, necesita
   un color de contraste, no el mismo tono del fondo. */
.login-box .stTextInput input {{
    background: {COLORS["card"]} !important; color: {COLORS["text"]} !important;
    border: 1px solid {COLORS["border"]} !important; border-radius: 10px !important;
    padding: 14px 16px !important; font-size: 16px !important;
}}
.login-box .stTextInput label {{ color: {COLORS["brand_white"]} !important; font-size: 14px !important; }}
.login-box .stButton button {{
    background: {COLORS["brand_blue"]} !important; color: {COLORS["brand_white"]} !important;
    border: none !important; font-weight: 700 !important;
    padding: 12px 0 !important; font-size: 16px !important;
}}
.login-box .stButton button:hover {{ background: #0A2E38 !important; }}
/* Los botones secundarios (type="secondary", el toggle Farmer/
   Supervisor cuando no está activo) necesitan su propio contraste --
   blanco translúcido, no blanco sólido, para distinguirse del botón
   primario "Entrar". */
.st-key-login_role_toggle {{
    background: rgba(255,255,255,0.22); border-radius: 16px; padding: 5px;
    margin-bottom: 22px;
}}
.st-key-login_role_toggle [data-testid="stHorizontalBlock"] {{
    gap: 4px !important;
}}
/* Toggle Farmer/Supervisor -- rediseño septiembre 2026 (segunda vuelta):
   vive dentro de la píldora contenedora blanca translúcida de arriba
   (.st-key-login_role_toggle) sobre el panel NARANJA. BLANCO sólido +
   texto azul petróleo cuando está seleccionado (kind="primary"),
   transparente + texto blanco translúcido cuando no (kind="secondary").
   Apunta a las keys específicas del toggle (.st-key-login_toggle_*), NO
   a ".login-box .stButton button[kind=...]" en general -- el botón
   "Entrar" TAMBIÉN es kind="primary" y vive en la misma .login-box; una
   regla genérica lo hubiera pintado igual, sin que se pidiera. Con la
   key, el cambio queda aislado al toggle. */
.st-key-login_toggle_farmer .stButton button[kind="primary"],
.st-key-login_toggle_supervisor .stButton button[kind="primary"] {{
    background: {COLORS["card"]} !important;
    color: {COLORS["brand_blue"]} !important;
    border: none !important; font-weight: 800 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.10) !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="primary"]:hover,
.st-key-login_toggle_supervisor .stButton button[kind="primary"]:hover {{
    background: {COLORS["card"]} !important;
    color: {COLORS["brand_blue"]} !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="secondary"],
.st-key-login_toggle_supervisor .stButton button[kind="secondary"] {{
    background: transparent !important;
    color: rgba(255,255,255,0.75) !important;
    border: none !important;
}}
.st-key-login_toggle_farmer .stButton button[kind="secondary"]:hover,
.st-key-login_toggle_supervisor .stButton button[kind="secondary"]:hover {{
    background: rgba(255,255,255,0.12) !important;
    color: {COLORS["brand_white"]} !important;
}}


/* Tabs de Rendimiento Comercial (Ads/Markdown/Churn) -- pedido explícito
   de Sabas: "ya no quiero [el botón sólido naranja tipo hover]... quiero
   que ahora la forma de esas tabs sea así" (refiriéndose al look de las
   tabs reales de Ficha de Marca, .stTabs arriba). Siguen siendo
   st.button() reales (kind="primary"/"secondary"), NO st.tabs() nativo
   -- necesitan persistir cuál está activo entre reruns para el botón
   Volver de la Ficha de Marca, algo que st.tabs() no permite. Este CSS
   solo cambia cómo SE VEN, reproduciendo el mismo lenguaje visual de
   .stTabs (fondo translúcido claro en reposo, texto gris; blanco sólido
   + texto morado + más peso cuando está activa) en vez del botón sólido
   naranja/gris por defecto de kind="primary"/"secondary". La línea
   inferior naranja se simula con border-bottom (acá no existe el
   highlight nativo de Streamlit, que solo vive dentro de un st.tabs()
   real). */
.st-key-comercial_tabs_anchor .stButton button {{
    background: rgba(255,255,255,0.4) !important;
    color: {COLORS["muted"]} !important;
    border: none !important; border-bottom: 2px solid {COLORS["border"]} !important;
    border-radius: 10px 10px 0 0 !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: background .15s, box-shadow .15s, padding .15s;
}}
.st-key-comercial_tabs_anchor .stButton button:hover {{
    color: {COLORS["brand_purple"]} !important;
    border-color: {COLORS["border"]} !important;
}}
.st-key-comercial_tabs_anchor .stButton button[kind="primary"] {{
    background: {COLORS["card"]} !important;
    color: {COLORS["brand_purple"]} !important;
    border-bottom: 2px solid {COLORS["brand_orange"]} !important;
    font-weight: 800 !important;
    font-size: 1.05em !important;
    box-shadow: 0 -4px 14px rgba(0,0,0,0.08) !important;
}}
.st-key-comercial_tabs_anchor .stButton button[kind="primary"]:hover {{
    background: {COLORS["card"]} !important;
    color: {COLORS["brand_purple"]} !important;
}}

/* Botón de submit del login ("Entrar" / "Entrar como Supervisor") --
   rediseño septiembre 2026 (segunda vuelta): el formulario ahora vive
   sobre panel NARANJA, así que el botón pasa a azul petróleo sólido con
   texto blanco -- un botón naranja se perdería contra la tarjeta, ya
   naranja. Mismo criterio de key específica que el toggle, para no
   afectar otros botones primary de la app. */
.st-key-login_submit .stButton button[kind="primary"],
.st-key-login_submit_sup .stButton button[kind="primary"] {{
    background: {COLORS["brand_blue"]} !important;
    color: {COLORS["brand_white"]} !important;
    border: none !important; font-weight: 800 !important;
}}
.st-key-login_submit .stButton button[kind="primary"]:hover,
.st-key-login_submit_sup .stButton button[kind="primary"]:hover {{
    background: #0A2E38 !important;
    color: {COLORS["brand_white"]} !important;
}}
.login-box [data-testid="stAlert"] {{
    background: {COLORS["card"]} !important; color: {COLORS["text"]} !important;
    border: 1px solid {COLORS["border"]} !important;
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
    background: {COLORS["brand_orange"]} !important;   /* naranja fijo para todos los Farmers -- pedido explícito de Sabas (décima octava vuelta), antes morado */
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
/* Rediseño de la cabecera de Ficha de Marca (pedido explícito de Sabas,
   mockup aprobado): fondo azul petróleo (brand_blue, mismo tono del
   sidebar/header/Rendimiento General), texto blanco. Antes fondo
   blanco/card con texto oscuro -- .brand-title/.brand-id y los 6 stats
   (Estado de conexión/Teléfono/Encargado/Categoría/Conexión-Órdenes/
   Google-Rappi) se sobreescriben puntualmente abajo, en vez de tocar
   .stat-label/.stat-value globales (esas clases genéricas se comparten
   con .stat-box en otras pantallas que siguen en fondo claro). */
.brand-sticky {{
    background: {COLORS["brand_blue"]}; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px; padding: 32px 24px; margin-bottom: 14px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.18);
    transition: border-color .18s, box-shadow .18s;
}}
.brand-sticky:hover {{
    border-color: rgba(255,255,255,0.18);
    box-shadow: 0 8px 26px rgba(0,0,0,0.28);
}}
.brand-sticky .brand-title {{ color: {COLORS["sidebar_text"]}; }}
.brand-sticky .brand-id {{ color: rgba(252,250,248,0.65); }}
.brand-sticky .stat-label {{ color: rgba(252,250,248,0.65); }}
.brand-sticky .stat-value {{ color: {COLORS["sidebar_text"]}; }}
.brand-sticky .lever-icon {{ color: rgba(252,250,248,0.75); }}
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
/* Markdown Plan -- Top 3 productos como barras verticales con íconos de
   ojo (visitas) y carrito (pedidos) -- pedido explícito de Sabas
   (vigésima vuelta, aprobado primero como mockup): reemplaza las filas
   horizontales de VPD/CVR en texto. "VPD" se relenguaja a "ojos"
   (vistas del producto) y el número de "carrito" se calcula como
   ojos × CVR, redondeado a entero (pedidos reales estimados) --
   ordenados por carrito descendente ("el que más se mueve"), no por
   VPD/ranking crudo como antes. La altura de cada barra es
   proporcional al máximo de ojos del trío, así el más visto se ve
   más alto de un vistazo. */
.md-prod-chart {{ display: flex; align-items: flex-end; gap: 14px; margin: 14px 0 4px; justify-content: center; }}
.md-prod-bar-wrap {{ display: flex; flex-direction: column; align-items: center; width: 110px; }}
.md-prod-bar {{
    width: 72px; border-radius: 8px; background: {COLORS["brand_orange"]};
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    color: {COLORS["brand_white"]}; gap: 4px; box-sizing: border-box; padding: 6px 0;
}}
.md-prod-bar .metric {{ display: flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 800; }}
.md-prod-bar .metric svg {{ width: 13px; height: 13px; flex-shrink: 0; }}
.md-prod-name {{ font-size: 10.5px; font-weight: 700; color: {COLORS["text"]}; text-align: center; margin-top: 8px; line-height: 1.3; }}
.md-prod-rank {{ font-size: 9px; color: {COLORS["muted"]}; margin-top: 2px; }}
.md-prod-insight {{
    font-size: 11px; color: {COLORS["muted"]}; margin-top: 12px; line-height: 1.5;
    background: {COLORS["card2"]}; border-radius: 12px; padding: 10px 12px;
}}
.md-prod-insight b {{ color: {COLORS["text"]}; }}

/* Cards internas de Ads Plan (ROAS 1/4 semanas, Venta incremental
   1/4 sem) -- pedido explícito de Sabas (décima quinta vuelta): antes
   usaban .glass-card (fondo blanco), que se perdía contra el fondo
   igual de blanco de la card contenedora "Ads Plan" ("blanco sobre
   blanco"). Mismo gris card2 que usa .top3-row en Markdown Plan, para
   que ambas mitades de Campaign Designer (Ads Plan / Markdown Plan)
   tengan el mismo tratamiento de "card externa blanca + internas
   grises". */
.campaign-inner-card {{
    background: {COLORS["card2"]}; border-radius: 18px; padding: 20px 22px;
}}

/* Ads Plan -- 3 barras (Inversión / GMV actual / GMV proyectado) en la
   MISMA escala real -- pedido explícito de Sabas (vigésima vuelta,
   aprobado primero como mockup): reemplaza las 4 cards de ROAS/Venta
   incremental. Inversión fija en el % recomendado real de la marca
   (ver ADS_PRESSURE_TIERS en data_layer.py) -- ya no hay slider ni
   rango movible, es un solo valor fijo, coloreado verde (el recomendado
   siempre se cumple porque es fijo, nunca queda por debajo). GMV actual
   siempre morado, sin semáforo -- es la referencia fija. GMV proyectado
   verde si el ROAS de la campaña supera 3.5x, rojo si no -- el ancho de
   la barra representa el TOTAL proyectado (90% del GMV actual como
   orgánico, margen de conservadurismo, + el incremental de la
   campaña), pero el texto adentro de la barra muestra SOLO el
   incremental de Ads (lo que le interesa destacar al Farmer), no el
   total. */
.ads-bar-row {{ margin-bottom: 18px; }}
.ads-bar-row:last-child {{ margin-bottom: 0; }}
.ads-bar-label {{
    font-size: 12px; font-weight: 700; color: {COLORS["text"]};
    margin-bottom: 6px; display: flex; justify-content: space-between;
}}
.ads-bar-label .val {{ color: {COLORS["muted"]}; font-weight: 600; }}
.ads-bar-track {{
    height: 34px; background: {COLORS["card2"]}; border-radius: 10px;
    overflow: hidden; position: relative;
}}
.ads-bar-fill {{
    height: 100%; border-radius: 10px; display: flex; align-items: center;
    padding-left: 12px; box-sizing: border-box;
}}
.ads-bar-fill .txt {{ font-size: 11px; font-weight: 800; color: {COLORS["brand_white"]}; }}
.ads-bar-fill.green {{ background: {COLORS["success"]}; }}
.ads-bar-fill.red {{ background: {COLORS["danger"]}; }}
.ads-bar-fill.purple {{ background: {COLORS["brand_purple"]}; }}
.ads-roas-row {{
    margin-top: 18px; padding-top: 14px; border-top: 0.5px solid {COLORS["border"]};
    display: flex; justify-content: space-between; font-size: 13px;
}}
.ads-roas-row .val {{ font-weight: 800; color: {COLORS["text"]}; }}

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
/* Variante azul petróleo -- SOLO Brand Coverage y Contact Performance en
   Rendimiento General (pedido explícito de Sabas, mockup aprobado): el
   resto de usos de .mgmt-card (selector de país, tabla de login
   tracker, Rendimiento Farmer, Comisión Ads Proyectada) se quedan en
   fondo claro de siempre -- por eso esto es una clase EXTRA que se
   agrega junto a .mgmt-card en el HTML, no un cambio a .mgmt-card
   directamente. */
.mgmt-card-dark {{
    background: {COLORS["brand_blue"]}; border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 4px 18px rgba(0,0,0,0.18); color: {COLORS["sidebar_text"]};
}}
.mgmt-card-dark .mgmt-card-title {{ color: rgba(252,250,248,0.65); }}
/* Los íconos SVG usan stroke="currentColor" -- heredan del "color" del
   .lever-icon padre, no de una regla CSS sobre el <svg>. */
.mgmt-card-dark .mgmt-card-title .lever-icon {{ color: rgba(252,250,248,0.65); }}
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
.donut-label {{ font-size: 11px; font-weight: 700; color: {COLORS["sidebar_text"]}; text-align: center; }}
.donut-count {{ font-size: 10px; font-weight: 500; color: rgba(252,250,248,0.60); text-align: center; margin-top: 1px; }}
.donut-sub {{ font-size: 9.5px; color: rgba(252,250,248,0.60); }}

.cp-total {{ font-size: 30px; font-weight: 900; color: {COLORS["brand_orange"]}; }}
.cp-total-label {{ font-size: 13px; font-weight: 700; color: rgba(252,250,248,0.75); }}
.cp-target-row {{ margin: 6px 0 4px; }}
.cp-target-label {{ font-size: 12.5px; font-weight: 600; color: rgba(252,250,248,0.75); margin-bottom: 4px; }}
.cp-target-label .lever-icon {{ color: rgba(252,250,248,0.75); }}
.cp-target-bar-track {{ height: 8px; border-radius: 999px; background: rgba(255,255,255,0.14); overflow: hidden; width: 100%; }}
.cp-target-bar-fill {{ height: 100%; border-radius: 999px; transition: width .2s ease; }}
.cp-bar {{ display: flex; height: 26px; border-radius: 999px; overflow: hidden; width: 100%; margin: 14px 0; }}
.cp-bar-seg {{ display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 800; color: #fff; white-space: nowrap; overflow: hidden; }}
.cp-legend {{ display: flex; gap: 18px; flex-wrap: wrap; }}
.cp-legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; }}
.cp-legend-dot {{ width: 11px; height: 11px; border-radius: 3px; flex-shrink: 0; }}

/* Bloques clickeables del funnel de Rendimiento Comercial -- técnica
   real tomada de Eagle (mismo problema, ya resuelto ahí con Playwright
   y varias vueltas de prueba real, ver eagleapp.py/theme.py de Eagle):
   CSS Grid, no position:absolute. Un `height:100%` sobre un elemento
   position:absolute solo se resuelve contra un ancestro con altura
   EXPLÍCITA -- nuestro contenedor (.st-key-comercial_blk_*) mide su
   propio contenido (height:auto), así que ese enfoque nunca cubre la
   card completa. La celda de un CSS Grid sí hace `stretch` por defecto
   incluso con alto automático -- por eso la card y el botón comparten
   la MISMA celda (grid-column:1; grid-row:1) en vez de superponerse
   con absolute/inset. Selector `[class*="st-key-comercial_blk_"]`
   (contiene, no clase exacta) porque Streamlit agrega esa clase junto
   a otras propias, no sola. */
div[class*="st-key-comercial_blk_"] {{
    display: grid !important;
    grid-template-columns: 1fr !important;
    padding: 0 !important;
    margin: 0 auto !important;
}}
div[class*="st-key-comercial_blk_"] [data-testid="stElementContainer"] {{
    grid-column: 1 !important;
    grid-row: 1 !important;
    margin: 0 !important; padding: 0 !important; min-width: 0 !important;
    height: 100% !important;
}}
div[class*="st-key-comercial_blk_"] .stMarkdown div:has(> .comercial-blk-visual) {{
    margin-bottom: 0 !important;
}}
div[class*="st-key-comercial_blk_"] .stButton {{
    z-index: 5 !important;
    height: 100% !important;
}}
div[class*="st-key-comercial_blk_"] .stButton button {{
    width: 100% !important; height: 100% !important;
    background: transparent !important; border: none !important;
    color: transparent !important; box-shadow: none !important;
    border-radius: 14px !important; padding: 0 !important; margin: 0 !important;
}}
div[class*="st-key-comercial_blk_"] .stButton button p {{ color: transparent !important; }}
div[class*="st-key-comercial_blk_"]:has(.stButton button:hover) .comercial-blk-visual {{
    box-shadow: 0 4px 14px rgba(154,84,246,0.18);
}}
div[class*="st-key-comercial_blk_base"] {{ width: 440px !important; }}
div[class*="st-key-comercial_blk_contactado"] {{ width: 400px !important; }}
div[class*="st-key-comercial_blk_cierre"] {{ width: 320px !important; }}

/* .analytics-supercard eliminada -- pedido explícito de Sabas (décima
   quinta vuelta, mismo criterio que .action-supercard en 360° Action):
   la card contenedora gigante se quita, las cards internas (Funnel,
   Comparativo, Dato Ancla, Benchmark) flotan directo sobre el fondo.
   Los colores de Funnel/Comparativo (antes gris card2) y del insight
   del funnel (antes blanco card) se INVIERTEN a la vez -- pedido
   explícito: ahora las cards son blancas con su propio borde/sombra
   (mismo tratamiento que .glass-card) y el insight queda en gris
   card2, para que la pill se distinga del fondo blanco de su card. */
.funnel-card {{
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 14px; padding: 18px 20px;
    margin-bottom: 14px; box-shadow: 0 4px 18px rgba(154,84,246,0.08);
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
    background: {COLORS["card2"]}; border-radius: 999px;
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
    background: {COLORS["card"]}; border: 1px solid {COLORS["border"]};
    border-radius: 14px; padding: 18px 20px;
    display: flex; flex-direction: column; gap: 16px; justify-content: center;
    box-shadow: 0 4px 18px rgba(154,84,246,0.08);
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
    text-transform: uppercase; letter-spacing: 0.4px; text-align: center;
    vertical-align: middle; padding: 0 8px 6px 8px; overflow: hidden;
    word-break: keep-all; overflow-wrap: normal; line-height: 1.35;
}}
.sup-table th:first-child {{ text-align: left; }}
/* Anchos por columna (9 columnas fijas de Rendimiento País) -- pedido
   explícito de Sabas (décima séptima vuelta, corregido en la misma
   vuelta): NO significa que las 9 columnas midan lo mismo -- significa
   que cada una tiene la proporción que su propio contenido necesita
   (una celda que no necesita tanto "aire" queda más chica, una que sí
   lo necesita queda más grande), calibrado contra el contenido real:
   Farmer lleva el nombre de usuario más largo del equipo
   (luisfernando.hernandez); Objetivo Ads Bookings es solo un
   porcentaje corto ("75%"); Objetivo MD Full/PRO llevan la pill más
   larga de toda la tabla ("11.54% / 10.41% - 111%" + ícono). Antes
   Bookings/Revenue (8%) y MD Full/PRO (17%) tenían más del doble de
   diferencia sin que el contenido lo justificara tanto -- ahora la
   proporción seescala con el ancho real de cada pill. */
.sup-table th:nth-child(1), .sup-table td:nth-child(1) {{ width: 15%; }}
.sup-table th:nth-child(2), .sup-table td:nth-child(2) {{ width: 11%; }}
.sup-table th:nth-child(3), .sup-table td:nth-child(3) {{ width: 9%; }}
.sup-table th:nth-child(4), .sup-table td:nth-child(4) {{ width: 9%; }}
.sup-table th:nth-child(5), .sup-table td:nth-child(5) {{ width: 10%; }}
.sup-table th:nth-child(6), .sup-table td:nth-child(6) {{ width: 7%; }}
.sup-table th:nth-child(7), .sup-table td:nth-child(7) {{ width: 12%; }}
.sup-table th:nth-child(8), .sup-table td:nth-child(8) {{ width: 13.5%; }}
.sup-table th:nth-child(9), .sup-table td:nth-child(9) {{ width: 13.5%; }}

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
.sup-table-fullscreen th {{ padding: 0 20px 10px 20px; text-align: center; vertical-align: middle; }}
.sup-table-fullscreen th:first-child {{ text-align: left; }}
.sup-table-fullscreen td {{ padding: 6px 20px; text-align: center; vertical-align: middle; }}
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
.sup-table-single {{ table-layout: auto; margin: 0 auto; }}
.sup-table-single th {{
    width: auto; white-space: normal; text-align: center; vertical-align: middle;
    line-height: 1.35; word-break: keep-all; overflow-wrap: normal; hyphens: none;
    max-width: 130px;
}}
.sup-table-single th:first-child {{ text-align: left; max-width: none; }}
.sup-table-single td {{ width: 1%; white-space: nowrap; text-align: center; vertical-align: middle; padding: 4px 10px; }}
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

/* .action-supercard eliminada -- pedido explícito de Sabas (décima
   quinta vuelta): la card contenedora gigante que envolvía las 4 cards
   de OPS/Menú/Markdown/Ads se quita por completo, dejándolas "flotar"
   directo sobre el fondo de la página, igual que en Home. El grid ya
   no hereda padding del contenedor eliminado, así que se le da margen
   superior propio para separarlo de la card de Coinversión MD de
   arriba. */
.action-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
    margin-top: 16px;
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
   Distribuidas a lo ancho + estilo "folder" -- pedido explícito de
   Sabas, aprobado como mockup visual antes de escribir el código.
   Cada tab tiene esquinas superiores redondeadas (pestaña de carpeta);
   la tab ACTIVA se ve más grande/elevada (fondo blanco, sombra hacia
   arriba, texto morado, línea naranja debajo); las inactivas quedan
   más chatas, sin fondo sólido, texto gris -- como pestañas "detrás"
   de la activa.

   CORRECTIVO IMPORTANTE (misma vuelta -- confirmado inspeccionando el
   DOM real con un navegador headless): esta versión de Streamlit YA NO
   usa data-baseweb="tab-list"/"tab" -- esos selectores nunca tuvieron
   efecto, es la razón real por la que el intento anterior de
   distribuir las tabs a lo ancho no se vió reflejado en la app. La
   estructura real es role="tablist" (contenedor) y role="tab"
   (data-testid="stTab", cada pestaña individual) -- confirmado
   navegando la app real con Playwright, no asumido. */
.stTabs [role="tablist"] {{
    gap: 4px !important; border-bottom: 2px solid {COLORS["border"]} !important;
    width: 100% !important; align-items: flex-end !important;
}}
.stTabs [role="tab"] {{
    color: {COLORS["muted"]} !important;
    flex: 1 1 0 !important; min-width: 0 !important;
    display: flex !important; justify-content: center !important;
    background: rgba(255,255,255,0.4) !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 11px 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: background .15s, box-shadow .15s, padding .15s;
}}
.stTabs [role="tab"][aria-selected="true"] {{
    color: {COLORS["brand_purple"]} !important;
    background: {COLORS["card"]} !important;
    border-radius: 14px 14px 0 0 !important;
    padding: 14px 16px 16px !important;
    font-weight: 800 !important;
    font-size: 1.05em !important;
    box-shadow: 0 -4px 14px rgba(0,0,0,0.08) !important;
    position: relative !important;
    z-index: 1;
}}
/* Línea naranja bajo la tab activa: se deja el highlight NATIVO de
   Streamlit hacer el trabajo (ya la pinta él solo) -- pedido explícito
   de Sabas, tras ver en la app real que mi ::after manual se sumaba al
   highlight nativo y quedaban dos líneas superpuestas/duplicadas. Antes
   yo ocultaba el nativo (display:none) y dibujaba mi propia línea con
   ::after; ahora se quita esa duplicación por completo -- solo se le
   da el color de marca al highlight nativo. */
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {COLORS["brand_orange"]} !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

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
    "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"
)
ICON_CAT_AMERICANA = f'<img src="data:image/png;base64,{ICON_CAT_AMERICANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ARGENTINA_CARNES_B64 = (
    "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"
    "TkSuQmCC"
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
    "SUVORK5CYII="
)
ICON_CAT_CAFE = f'<img src="data:image/png;base64,{ICON_CAT_CAFE_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_COMIDA_CASERA_B64 = (
    "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"
    "X4n9HGJyAAAAAElFTkSuQmCC"
)
ICON_CAT_COMIDA_CASERA = f'<img src="data:image/png;base64,{ICON_CAT_COMIDA_CASERA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_DESAYUNOS_B64 = (
    "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"
    "AAAASUVORK5CYII="
)
ICON_CAT_DESAYUNOS = f'<img src="data:image/png;base64,{ICON_CAT_DESAYUNOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_EMPANADAS_B64 = (
    "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"
)
ICON_CAT_EMPANADAS = f'<img src="data:image/png;base64,{ICON_CAT_EMPANADAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HAMBURGUESAS_B64 = (
    "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"
    "1SCKuDH7AAAAAElFTkSuQmCC"
)
ICON_CAT_HAMBURGUESAS = f'<img src="data:image/png;base64,{ICON_CAT_HAMBURGUESAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HELADOS_B64 = (
    "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"
)
ICON_CAT_HELADOS = f'<img src="data:image/png;base64,{ICON_CAT_HELADOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_HOT_DOGS_B64 = (
    "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"
)
ICON_CAT_HOT_DOGS = f'<img src="data:image/png;base64,{ICON_CAT_HOT_DOGS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_INTERNACIONAL_B64 = (
    "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"
)
ICON_CAT_INTERNACIONAL = f'<img src="data:image/png;base64,{ICON_CAT_INTERNACIONAL_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_ITALIANA_B64 = (
    "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"
    "xv5/HaQdz3O5wAEAAAAASUVORK5CYII="
)
ICON_CAT_ITALIANA = f'<img src="data:image/png;base64,{ICON_CAT_ITALIANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_JUGOS_B64 = (
    "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"
)
ICON_CAT_JUGOS = f'<img src="data:image/png;base64,{ICON_CAT_JUGOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_MEXICANA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGAAAABNCAYAAABZqmHQAAASqElEQVR42uVd+5MUVxX+erpnZt/s8lhYAhuWQCDmiQQhxEdM"
    "jDFWfJaWpaWWpf5H/qBV/qAVo2WVZanRRMsoaIwkQhQwEIILhCUBsgvhsa/Zmenp9of+TvqbS8+ysMsyA101tctsP26fx3fO"
    "+e65Fy+OY7TAkQOgA40z/u4BqDW43su4xufPSP7my/1j5xpffo8y7nddh9eECvBEqI1eNifnQQQfALgfwBL+HvOnD6As5/0X"
    "wAVHuK7yAgAdfFaJ17tjiOb7skETCj92hAoAeY41AlDJePEOAD0A1gH4NM8piAI9CrkEoBtAF4ADPG9MntVPwbYBWAmgj/8e"
    "B/Aur88BeE/uG99KHuBlQMwSCraXAjgD4LRzzhMAdlARBblPJIKyj1n0FIAqgB8BmKTwvwmgkwr3HS+r8JMD8CyAU+I5162I"
    "ZlFAzsHcDQC2UECdAJYBKAIIKaxxnmsC2khhtFPgIYV4EcB5KmU5lTnN54W895tUSA+ATbx/xGdrzDHFtgE4BuAggNdFsVEr"
    "KUAtXbG0F8BaAA8DWE9hFHiOKanGjy8Q2snvIl5zgZh9jHDRBmCAny5RRkjhK9QVef0FgSaPcNTH70oALgF4CcARiSOuEuJm"
    "9wCDhBoF8yQtvz3DK7KuNUWGEqx/D+BfTsZiMSCmkJ8AsI2Kg2PB4wBe46ckgXwHgEfojQZjMwB+wGuyAvlVoWkxFOBJ1hI3"
    "yGoKALYygHbwxWoA3gBwXDIiTREfArCZwp+i9/wKwDCAiTmMazM9bRPhJgTwZwBnCVtu1tMHYCmA1RxnmQH9KICX6W1Zhy8p"
    "cryYWZDCjGsZRXl2GzH8YeLwDK8ZBvBihiDsGKXgijznCID/NMj0eqjYLiq7RC8zz6jwXmcIPd08f1JiwUV+TnK8a/j9AICP"
    "SozICUSO0DsaesRieoBZ+gp+ihzkUgAfogXnaM2jAH7Iv+dpne4RZWCu1gcWMFcDGKKgVgqExAJjIZU4TIH7jB1vcyxl8V6P"
    "ScJjAO6S+BSKwkv8+RKAV/i32mJBkC+DBa3p0wBW8W8+he/J7x1iaW8Tdi4AuIc4rRWqWdEJALsc5QwSq/vkmnbevyhWqnGh"
    "JuMNxULLzJgqPPckgH8Toiz1fVwMZEKMLOD3lwlnPoBfMnAHCkfBDbB00/QdtLg1xPdQLNdyZxuoXV8Wa3uG3087wjclrqVy"
    "z/F+eT7rAQoj5jPNI6p8tsYjDfKxk/XkeH9LQftpDCd5n9WC7WcJXx49bJDndPC6IoCdjGnvaCW9UB6g2JYnxHwSwIOC05pt"
    "VCS7UIuoAtjHn49T+LHD81iqmJPUM5b7W3paked4MkZvlveInXeye+XEcMx7rC6pMni/zOuGADzK4O5xvFZNj9ATqjb+hVJA"
    "XiDkUwDuJeQUxfKqPG+MQg553gZafRXAPwDsFwWOAfgfg6Hh6r0APkGrLIpgqiIgy072AHh/jsJ3FdAtBWE7752TuGS4HwL4"
    "g6S+FvQLtPqtYmTgeX8jPOWCBbB8TwLXTqaH7RJQOyiMUULDMN1wiJlPTAW000Un+FIv8xrLInookH4RZI3XttG6RgTq3uaz"
    "rvcYZRw6z2fW+BwL6CUK2ScB2MNx7ROi7zUaySbKAYTIV01+wQLBT8DK9fOEDUszL5Ez2cXAakFxKQeyXKzmFK/1mYoO84WX"
    "87vPMFuqCmFW4ucUgL2kB2ZjTa/liKUiVk/fyoKsTUjC9Yw/ecLeflr4GQp7nZCJRY1784EgpY03EhY2yN9KAH7NAmWGljkI"
    "4EuSlRQp9AMAdtNjCpL7P8msBkK0VcTj9hJmSgJjjcZ5PQpoBLftDLY7AHyY72DU9TkK/lkxrm4A32Ad0gXg5wDeAuDPxwN8"
    "yW/7aQEWbNoAPM+HzPD8nQDupvuO8/t2WsgbxHlL/1bw/E2Cv+Ydp3nfy7T8c47FuwKM52lgrgKr/IzTGEZYDzzAdyrSEL/A"
    "GuB9FnBVGWM/s6nyfBQQUSArpCqMiOGHiIVW9a5iUK3RIjwKfATAXyVABizItpOrqUnWM850bz/zcWTMYkVYuCNukBkpMXia"
    "n7P8biXhdUY8Yx/f1ZMgvoxeMRPMw/prZBS/LSV+yMCz1ymOvuNUn3soxJLzcpsJZQP0olgmQX5Hq3EturaI5GHcQNEnqYgV"
    "tPyVrBm206D+lFHNL0ghlqfGTUhVSc0A4OOsZiNacJVYPyyQA97jYaaYgzx3khnIQbrwsJPve1dhSxebza1QCS8yWdjJ972f"
    "1j4gwXfcCsxgng+dYqZj+bhRtFbEbKFndHBwBwkh9uyQ8LSVAa3AgRUIT6/TU7TIC5tA8HCqZ4Wlk8yc1grnNUQZlCmnUZsY"
    "CubhhpDJkgoH8rLk3hskBkSsFk+IckJC1+eZRXlSDZ8H8GOJM6EEwGY8lBj0aOE/ITzn+Z6GDjl6NK5VAb4DM10MlG3U7IxM"
    "790B4GniYI7V7DknexoE8BRzaKOEp5kR7RVsr81hcqaZDoWk4wy4BSEpY+G35gRBWnVaNbiOAtwiwTcmJHkMzisJTzMA/inE"
    "WCgc+joRfszqdR/hypfntkTzkniDQdJRCcg5pJ0aaymrKJgj5ECo43sBfI7CdDmSgAKvymDO0TMg1zxJoi6WTOeSEFX5Joab"
    "ucqrxoLsAN81kiC81ViCqynAKk8Qq5czsHQinYetOTf3nOJFM5c+ckUbhC6eRDqtV70JqeWNPo6zKv4skaGDVPZqAKdyV7m4"
    "Qot9lHDTT9KpLESY0bOnMtJETyYoYkLONt7TeP+jZAhHxZOiFhe6ebZ58hGk89xWcN4NYHNwFe4kYIn9NIWTd2DGAuoJUgpT"
    "TsCOKOiQmt9EL7DZp8tIuhhmWhx2ZosHlra/w+TEeK0hAMuDBlHcLtzBYsqXdNNH0n1wRoJ4hcKEPMCN+E/xoTnSFScA/FG4"
    "orBFhayMq9vxYRYfkRGe5nwJmEX2BFdxoUFmPQEvnuKNDja4bhtL70Fe3w3gTlLJD4iQhwk7F5y6oFWtfC6QNMmEJBSojYNZ"
    "cv5u4n0k5NlBUgmGY1VCSsDg/IykqqaANqTzolVC0h7GjLxDXbTKoTNsRVpzyAIsmkWmbZKiAhkTMuYuJsxByXJ2I2nrhgjf"
    "B/AxAPch7W6InAzJR31zlvbKRC0MOzUmGI+S9zkP4KdMqbVLznPS7YrUBWikgE4yk5EURO/xYhP+Wuaz9zC9Gkc6SX2QPx8i"
    "0WazYyVC2BTq50lb9eihnC5JRe8mMrp4pIL6ZoKGlbDnRHEgnecNCSk7yOG0yTWXABxm5Ztn0O3m71Mk1k6IF8UtKngbt8W7"
    "URKHVfm75yQXyxkP8/L+s07I5DI0GVHgXyf2G/aVafW7mNV0EJb6hD/fg3SSplWzHpcCt7aaKZKNFQdaA1HKl4SSNlnOOiUZ"
    "OQ8u8+JHCD+jFPRfmZKekzogz9iwRGDpgsSEWotbvv08zSp3nAynL3yXsbcbiBbr5bsZJLNorwdzeGCOwp+gy32ENwhYZr+C"
    "dGarQKE/QBbQeoLGeP2tUOXqMS4puXYF5ih4n6n5evm+SnntA7B/rgoo8cIBYnqNFv13cTsryB5C0jdpC+PGWLidzwhQt9Kh"
    "i002APg+5ZGXhMPmuN9iNpgZhH0nmtcYgAsCHzMU6DGkvS5GKfcKXNlU5Xm5961AtGkur13RX6Gcljq09AwRoAzgBcL1BJwJ"
    "GU+ynEmJA7b2aifSDmObtQql5I55XlFK8kkSUd4tYv26dNagdCNj4XIknRCXkXbBWRZ5lmn8KSSTUx8E9MBxISuTux23AoOq"
    "LX4bRdoNbNcVmPksF1f8L2OE3avVrT+SWBezDniG72wNyH1ShIZIJpleQDJXbEr8IJMKxH20k+E+nuCjfuLZeuWPor7NOqbb"
    "PcZBWRveRSGk5r2m9ialnX6G8XwcycRUgLRX1bq+rUvuBVp8FfXNY3VTqwHqV3dspxt1on6hgifwkmOG08MAq5PpK4ltBcLP"
    "dIvCjkKNyWY1kga0TmY2XSL0kPI4QqMrOYUZUD/FClcBOVatX6Xg2iVn1dzXutoepPDHJE50I+3nn0KyXusC6le1tEqhpVBj"
    "WcwjzOeNA7NCdZwCP4+keWyygSIz4deg4l5iWSRwdEiEmAfwNVq+MXpL5D53I5lkt0ULlqJOO/DWzIL3HDQAkgmkHcT4DrHi"
    "kLRLL4BfIOn/9B3hu1QOZlPACqTrp2w91CuC8yC09FDIk6KAHDmOIYkpsQwm18SCdzsvTBYb+a5D/H0Kabt6Jw1zjN8dy8gk"
    "1YviqynAJgdsE4x3kUyWvMO/tVPT3VIXWHeXabkgmVABaRNurYlhRvG4gHSPiK3M+Iw2Cen1lwk3E0hWP15yOLN4NqiZTQED"
    "tGZ72AEymibcQcJPm1R2v7NKTl7EcuMSGc+sPXeaCWp0+nAIyZq0VZRJUf42yXffg6RhLBbOC/OlVgIkTbGrKFiPuK07gAQC"
    "Ke+TUh4WF15NtzXvOIKk/zNaiAEuoOBzTgHVQdqkH+laYpvzLiFdk3CI0HO4QYCdl5FZ10MgGU67CN8yJOvPP0Mr0JaTbUhm"
    "+/O8ZkTy3pud/WSt1l8i+P4xyfggMpgm1BwmaTYhLG+E7EXi162AXqRTiK5GbY2W7Z+Td84pIpkRaxfM95sIblwjWEahb+G7"
    "5DPg6CKSCaXXMvB8wdtmAlzZ/KpBxYRec6zIPCNAOgFvlERwky3f5eRjGtFOKmCtjNliVpGZ3z4G1zGH5b1hzcEBK90c6pec"
    "xqLxkmi+my58GelypGl6gFXD0zdB+FlQ4zGB6JA6ZVzGatz8aX7/JurbbYKFhptGCniLFEKvpKV2GO3cxkHcwYrwVQ66S17E"
    "YwA+e5O4eJdKWIekn3WZsJO9UplXifG/RbqLlucQkzf8CJA0xW7nIG2/heNIO92Os9p7grnyVqkK+6mECj3pMBW2GMuHsjj5"
    "AtPJAbKSK5Guoq/QkE4ypZwQD3ar1kWD0IAF14PCcawjDu6Sl9N9HXp4fifSLcVCvuAZ3Ph535xTEBpR1s/PdimeNL6NMJ08"
    "4UBN1v6hi3YYdTAtTGcvs4T9/H4TXblTqNkOCsG6Imy6rYwr29NvFCdv+4EGtPq7KPSCnFsRTv43SFe9Z+05elMOU8Bhuqyt"
    "Sl8B4HscnO3JaSvUzVIKUrzNhsduFXqtC6g9hwSz435mNgHSZUAe0lX5BSSd1yP87oIzxqagyS1lHGXFdw8zHaOXLUuaZn58"
    "SmqGOxkvfMxtyvFaY0IWJ7+UYwRhcKl4ggn9JJLpvwlW7eUMoqxpKBLdC+e8MJ622ZClYGUkW8n8RyDgo8KdeHOw6oLUHdVZ"
    "UjuXk/eR7m64hc81+IOkvyVSJS+hfvpPF8c1HTmo9HFOmEwLdBPMhp7DlTsRzmUnEu0ivosec5GQV8KV+y/7Gda5BslGF7aJ"
    "a5d4hnE2B2kgkTPOaI7GcdMhyF6+QwRnm9gdQrqutShwkL/GPP2y8Cxhg6ymJs95nEJfg3Q61HY8rDADO8Dzj+DKzbiV52/a"
    "I3AGXRDhlMmHjAgJpbv/zXVhgh1n+MEsVO4q3n89ocb2A7VJ7yoVWSYc7mmQTrZM94V2KNvvFVrZa8Jqhk5gXCh6WAW1AsB3"
    "KUCz+KJ44xSSyaJfNcDzlmx5CZwXiEXQNckwojlSAN5VUknlmmrMtB5DutugrcAsMHW0OeW/SCo5nREzWrbfVGNAKIVNgGTH"
    "j2PkfLwGBVEuQyFeA5JMW/gG+LeNSHpsLgqvZPtPjLEiP+tATSAG0/JtjoETDCNRwHri7+kG3I4F07xjgXGDTMiOuwF80YGY"
    "ZfL3Ei39ZxK49QhxCx0aA2wKrk+sawBJL6PxRLrTrG0TPyAKsIZcH/XbyhjUdCP9nykqAknj/O555vJlJ6tZkOm/ZlWAroJ8"
    "FcmOVWBKupHfH+JPdfnTzERs3Ws7rVurzzv5/RBSPr4L9Vu72OKOt5D2kSrbeUP5+GbxAJ9Zxm7Cwf1I+33sf6/4N9JWQx/p"
    "4gRbyN2FZK7gIsmvtQC+TMvuFCoBSDdZLSPZYep4RhC/pQX/AT5z20rF6aVI5k0fRrom7DI/tmfnSVp/wNTRtnIE0qVKtnN5"
    "VSgI84DdhDbbYyLKiEW3xRE42UuO2LuXELSZVm/7QduuKP1Ie4k6UN9v04u0iasqvM+7zGh81hgTGZ5Yu52Erx7gKsUyjW+R"
    "CuhBOgkfo/5/J/KRPWlttIPl9c8hXZwAqS9i3MZHlgIUjvqI/+sYnPU/y8kJP5MTltNmx5Yg2dT6KO95zkkhvdtd+I0UoGmf"
    "zj5tJlej1MEQ0vVQNWZG7zBjKuPKvUGV7bzthT+bAuZS6t+F5H/GuBPpPgh7kUzyTzucj4fW2/ttUY7/A1Ehf3a8Kus5AAAA"
    "AElFTkSuQmCC"
)
ICON_CAT_MEXICANA = f'<img src="data:image/png;base64,{ICON_CAT_MEXICANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_MILANESAS_B64 = (
    "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"
    "QP/Q/Yc4vwfAy/FsZToWgwAAAABJRU5ErkJggg=="
)
ICON_CAT_MILANESAS = f'<img src="data:image/png;base64,{ICON_CAT_MILANESAS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PASTELERIA_POSTRES_B64 = (
    "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"
    "YII="
)
ICON_CAT_PASTELERIA_POSTRES = f'<img src="data:image/png;base64,{ICON_CAT_PASTELERIA_POSTRES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PESCADOS_MARISCOS_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGAAAAAtCAYAAABRXm6KAAAMmUlEQVR42u2c229cVxXGvzNzxvbYcWI7jnNpGicY2iRtIW2g"
    "jdoCaYBAU4F4KFRIFAQSICFU/gN45BXBQ4UQEgKpiGsboVJa2hBK27QlJSS9x2nStE2IU8fxLfbczjk8zG8zKzvH47EzNk7F"
    "kUYzmTmXvdfl+7619naCJEm0RI+MpFjSJyTtlNQuKZEU8B5z3kFJ+yWdTblenLtkJxkuwTEFxmi3SfqQpJz5LZKUNca9RlKv"
    "pAJOKUv6De92ntFSdESopXskktZLWiaphX9Hkt6VtAKDhxi9Q1I3DlrG9ROSTkk6JKnCd9mUjLBZ9X8HeBDyLAbNkwVTkp7m"
    "81rOSTDsVZJWSiriuKykD+KYs5LelnTey7I0yPKDQAvpnHCJRr57PylpUNJGjJ5I+rekEynX3SzpI2RLJGk1nz8qqU3SPyQ9"
    "I2mE7PGfmcwRIpuDt0uUhN0kt0vaTWSL6N4r6XkiPJrh+jZJ90nqxAkOesqSnoO4W3jOBV4FQ+zzdc57BoISov5W8D7G+G+Q"
    "FUoxfguE/H5JW7gua4yXYb63AE2BuTbynC+eeQpnH005J2POS95LDnCTuwOcLxOhv5A0hCGulXQT3ODIOS+pC8xPjFKKIGFn"
    "pJIxZmBeWewRmCC4ASg7b+5xTNIBzyGhcUZ8JTvAqZpI0hqMnyO610kaAFYGINoiBi1iuBCidteclzQGvJR5Fbgm4fwWIKuH"
    "V54xOEcsN87J8txe7hsAaRfMHLJenbLkHeAiMDZycaOJ4hCj7zF1gNP1rRh1wuh+F81nJZ2WNIyBihi/4EFGC0prvaQ+MmgH"
    "55TIxkmMnpc0TfZVcFw7QqFEhk7NhawXmoSDOionTXbmINxvMbnQRJPD3GmM6e7/NOqmMMfxBB7Bun93SPo+Bp6W9KqkJw13"
    "CKM7Eq/g/KykJ+CMaRNMdR2xkA4IGpCadnC9KJ7riezE3KPC55Kkh1ExicH4Zk0iK+lGSV8kqx5DvgYmIxNJd0naRmb64yzj"
    "iKf4d6YeHDkHBF7vJL5Mw2fqSETf8AOSdoG13UY2liSNE+0PEVUxuF6aRxAks0BxRdImSfeQhSclPYgS8qO4E9hKUGo3M74O"
    "zi1IOiPpLyiowDgiaSQD5s3q5vgMMJLl4RkMdxB83ops7APzJz0Mf1zSKJF4rE7V2oxqNQO+7wTf2yX9VtLLBFJknBmY4Oom"
    "W9sIpJ2Mox0uGJb0mqR/8tny3UWGbkXadUh6C6/7k40bSN+ICL6FqB7j+iKDCiWtwgHXMvAE44eQ2QRk9pR3b5nBx02ESheZ"
    "m82YCoylaHgoMc9fRwANSHqHc09w/kbu1cpcN6CujsMPiS0ine7dJumzfHlK0p9JyTEjsYIGSDQiNXfzuZ3ULDCIDIXSBu7T"
    "RmRM4vh95nkZ0+uJtfDNsnWIgBjnR360GmdtxwErJfVj8FckPUL/6tvMbRXnX0dNMQkk/ZcbnA7eDnnkTTU5xc32MZBigz2c"
    "mIlkuOdxSf+S9DV+y/J7kWf8gQhyEwyaAH/z4S2nWi5Aokppd8Smbujkuhz8VTRc8SOyYw/1TCvX3wOfHZ6pT54xA+qAYLaR"
    "Cfebc9L6I7GJkNNERh5Vs9mk3hgQ9BBwM+3dY7GPGPLdYBp59eCqiDgoYHwnGLKeTU5K+ik1xcewZwdOWQnHZUJT2JQ4wZbr"
    "Ocr7HtJqGBl4weBybOCiTJqt5HMG75cwtMPBd7mXZnHqYjT8hJHWm0yfqdHnMvhZguduVNkjcEBgqugKrwNk+p1Acruk27HB"
    "i45gnmcQ7TzgJbhgB07Ig5GbuPkxFjpio8Uj4GsrPFBUbYVqRNIRSa/TTlYTZW8zjj7GkCdDZ1JWLkjGaEFEBNzLKU51aq6I"
    "fZdJ+rRqq3vXSzocmn7G+zipg5s+iZc3USRtJJKvQS0sw4uvSLqaxtkOMqbEaxJHviTpxfn0ShbpKBqtXmgAspzgeC6FoK2z"
    "Kgbm9wHF67FNl6Su0HhtFLjIISMPE+WHIJzvcF4PD7gDZ/1S0ifJHte4Gud+j6KDLd9ES7ADmzHw0TJLFW+5KtuAYIiMhD1r"
    "oK5VUp9txp0gutfy4wozuAlJP8Br95KyHfz2Va/tW5D0ADBl11srWrqHVV5tHozUO6IG7+2Ks63G2eOSjmZMSh2jqeU06h6a"
    "T4nB61FJP5f0AjjojOo6kicl/RBZueDrqU1WQoGZa9Akp7Zy705J3+XdtVP220rYsfYQxmwjFTeA8YlRKhNcPKHqtpGIc47i"
    "oJEZMHGhjmxKz2euhVubUYMymRvM0/BORRVV3Syw2yjMLB3WNyQFoSevzkv6G9Gfh4Cvgw/cYHIY+u8MXEitEQ/rF4tko1lw"
    "PfGq+LRxvQ28Vky9Up7jHAIPbtsRKzeC+67DewAESawD3CAnKMNvgwPc4sRxfgsYmG0N+56vLBJmu6xcpdpeILc8edYr8Oq1"
    "yZ0K7DHtiK1Iy0qDY5FXxwwQvDux13JqgSN0SF0dFYVe6jrcetP05dvx4KszpLVry04vItFmTKF4L9EbGtm3H+1dMHDg2sRR"
    "igHfRi6vJvB2w2ej5r6ztWBCXislfYNrcgYxDtDiuKQZ50dVDr3q0vC06WnLUzZZKuQOWguHFrmyzTJht13RzWcX0Rd7fZ7H"
    "ERrllLZ21sBIHxxYTwkFXod2o+n9hKamGJH0e+yY+LBp1wNyDHS5pO+ZKm9Q0q+M0VuAn26ibx2/jQFTR+ARv5WcNNEpFoJu"
    "ZeJTBELOQKRtIbs+zgjvQwSNm3sHTcldZP5btBgGmbO/xOj4oV/VDcS9vJxjz8Odjh+TtI5ymFIwdJiCqUgquirRNZ76aTD1"
    "mmtzMP5yIqgIbA160JGZg4ZupPP6LPCX4bkfJ3A6PRJ2Buzhu6u5/k+8jwK9TkT0Ytg2U8XbY6uq+4/WEv2OtCsE4jM4YNxb"
    "EUtd+XI/uihw0fI6bYSMccomjN9vuoeDpgrO0/suMclu7j3MBOutbM0nOyqoChfJBXhrO8bLGHIeBuPbOf92WgRuQWhM1TXg"
    "GzhnDU4QQqQL0l/BytkKTzFNY7NjBo5z/F536dFh31pu7JbdhvCgMHaPpM9DvJ18f0bVTVObgIIVvNo4r89I3AeBirKkcw3I"
    "vEa2dgQmwioQXUh0urWHiHk8oOqC+geYT+xh/7Ck32HkVQRTL1D7V+B2Mw5rNQs455jTIVdgmeAq1xu8r4JaDflkjYE6JX2Y"
    "lqptRp1inSAmQn6MevqyKWycRMxD2FM49o+6eOkzqgM1s8GRfXVJ+joGdK31cUk/I8Jt0E2ptk/I/t3B/ZK+SYOylXN3mes6"
    "DSIMQrKjM3BE/eiBhJ0s2iLpS6TfcQZ9laQvACU50+d/kmibToEVV3J/jv5SXrVF+QAnT5nC5wUibKqO7JwtkEoooruJ8MQs"
    "/jxA1N5nHDMk6ScmQttU3d1wk+kKh57SiZjvBbjjFM8tzDFrL8mAGNjYrNoi9BD96wF+C4mkYVU3Qw0ymMAr3WMmLgxq99O8"
    "BC+sUG3ZMqPqtvJ+sxgSAFlvgqcjs8yjhIa/E4cnGOV5HFtGm69WbZt7l6RPASsWYrtU22jlmoshY3iCOU172Wt5dE48ZtvR"
    "jtXdd/26eH/mNKx+hOzw+z1JSjOr1Yvec3BChQm2YPTIEJpzzDXwymbV9gIFKRHmxrCe8bui6zUidQdzWedF9HJgpWA6uW67"
    "uttJfYwiraLq7oejKXVIcjnrG9YBa3Tx9o815hy3nLjXi+iZ9tPHHrY7g29WbXeEO++kavssV5L+JaNm+mkKBp6M9Xki5z13"
    "Ekjp4D7OqGXTvw+Mchshu0umd38QkeEXa7Hhjcs6/DogSNHZF4j6vV6nrxH14gbqyvnVRiqW0Ne/NkS/TdU/yus2kZU1JX3O"
    "q8ZtKznw+GKHF2CxuWfJK6zeQcEc1KW77mxTr+mLSb4D7F8jllXd0fWoant1Gh2Ec+C4katZ0/B7mAnbMn+CDutT5vsQGbiB"
    "TOiHRP12SNrRkrKMeAIeGlR1OTVqoAZZ0K5ukCSJS+02eOAuVRfOH9PF263n0y7Ig82rwP9RHDumBncPG0c4iZwzlW2fpK8Y"
    "B9vsdEReRCa6DWIFzb7Hac5q5nIcYIksi/ad1KW7F+J5OCDxqsE0aRmnNLcaicBW5PEWr1Uyzuc3iPbRlApcKQsu/5MVvNBL"
    "0UgX71K7nBS0q2hlwx+J0hex6xnAbhhzzuxH7xfN2EN4JaAJdqZOQ3BJ/AW9vzs68FrJzepcqonRlTF1y+04wlWlr9AE82Xi"
    "UtoCU9cBV8ph4a3Vw/Qr4v+IcMd/AIerWZtKKslQAAAAAElFTkSuQmCC"
)
ICON_CAT_PESCADOS_MARISCOS = f'<img src="data:image/png;base64,{ICON_CAT_PESCADOS_MARISCOS_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PERUANA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFgAAABgCAYAAACZvLX0AAAUzElEQVR42u1da3Nb13VdF7gEwDclUQ+KsSRKtmRJjh3Zli27"
    "dpq2mcRxm8m008enpu10pr+mPyHTb22nHzrpNJnUdePGlRtLoezIsmlFtvUypdrWk+ITIHCB2w937dzF43NBiAQoyMM7gyEJ"
    "XJ57zj57r732PvscBHEco0uvAEAOQF3e2wLgCICvASgCqAL4PwBnAFTkvrzzfw/sCh+A0OxqNrMmoDqA3QD2sq9DAEYBDAPo"
    "4ed9FPYi7zFhhwAafH3lBRw0EWog79vvdWrvCIDfAXAcwDw/7+FPu3crgH0U8CCFe55/+9pHi5PcnoFvEETkOLiGM6g8f9r7"
    "dl8dwDiAv+I9IxRYQ4RrgotF8HkAtwFcAPDvbLsIYFna1qvRaSFvhAa7eNhHYSw47xeIqSDOfp33zvL9DwHccfDZBDQM4DEA"
    "/RzTkwCWALwlwm00mXzIZD10Aq4D6OVrC4Cd1Kq7AG4CKFMYJtytAH6feFuk4C8AeIPa6bsGCSHPUdgVAH/AZ5zn34bVpsU1"
    "Prf+sEKEau73ADwOYEC0L6JQKwAmAZwGsA3A31FgNd73GoD3KcBmGF8EsAPAn1OT+6jx73FyXqWWl6ip0wDe5eSpNrdVk9eq"
    "wYqDrtOw9yMO5kUAR6nBRRFsg5OwG8AJCnWU91Wp2e8BOEc4MRiJBT/1qlBoFwgvvbz/Wf7+pOMkD/P9CcLQRVqUKUfgPKPR"
    "SQ1ulV65/3MQwN9SWAVOaJkvUNNK1NaIg89RoNcB/IM4qqrn2YE4R/t7D4BvEsfBNssUWuhMUJVWFtKCzhCG6mtgQ2vWYFdb"
    "W/W8Y6I1fez0EoBTAH7Fe74D4Bm218OXOjHVnsB5rjqnhgQl0wA+IiQ1HAdaFyuzcfTyf08Qot4CcLkFh9hYr4CVWjUcbB0j"
    "jRp2NKkK4B4992EAh0RTAOBtAO8AmOHfv6Qj2kd8LFNb8xTKdn5e4/07KYRbfFl/Go5TvQbgc/ZzjhM8RUwO+D81jv8l9ref"
    "fe4B8KiMaxbADU5c3RNpxs1wO2xC/LXTvTTlkJ0+TA0pONpVIo4t0eEU2YkKQ9r/ZHsGC9f5Osj/H5MIbYjCvMs2+skS9lLD"
    "pmjOS475BpzkUwCeZ59rAP4rg4Xs4nNtsh7jhNvfEYBP6Aum+X6VvLyeETB5MVihQGGghyzgMDsbiMOCx2wtxFXNep8DviL3"
    "6QT2sM1DAP6Ek9QL4N8A/IbCfpFw0k+BzQC4CuDH0kbNaXOc/ZsTq3Gv3YwWj7FfeY/QzOnW+YyLAF53Jjfng47QoScNmbmX"
    "hcQ/RTOr0pzKfFDewyLqfOAA712m5lx1cDUvE1rja4paW+azbsjnnxEnZ2gBA3Rks4SdBbZvk1cD8KkoQE7yE7Eow2dsc1H6"
    "XXPwvyb/00eWkuP/fUbMrzuQFauATbADnPm9AP6QDQyKIAZkFhsemhbIYAx3IwBfyHOyoqqAgn3Neb+HmnKOpruPAi7x/W+y"
    "n2c9dCp2BFX1hMoBFSASBhM7bcQUXJ9QzacohztUojly9ZoLEaE0/n1iay+FaQ7OGEAfgH+lqefEIyv/zVMLT/B/XyeORtJx"
    "lwbZxJU9Qs9LP/qJ+/sAvMKBDVC4J6nNrVLIvAODA+ThNYETDcd3cUxHqO1F6ds8+/86gF9L+5Fh8CMMBp6jZtQFQuZJ+Jco"
    "pNP8udq1lT/vej7bDuAbHEyv0LhlwbxZRlrwYGwPMbPA9+b5KhJTC8KClJYt06lezbCi3Cr0az+te5C/76awDbun6TPesvZC"
    "CvEoB9wn3HCW5jIF4GeeMBgeGtcn2rjMz0cpMBNmD53Vy2y/z+GnATtdJYbWxMkoxZoUJZigg9xLDZsX+NMUaD+AD9jHz6Xv"
    "kWTr1D+4UHGZryLHcIJjGmb7uwAcIC5fNw0+wnDyADswRy3+EU0lapIHyDm49wKA35NOm7ZdJlU7LKbeLyFzQ/A5FPNdIN+d"
    "FIw1ilcnFP2ANKvIZxXE0frywcvsS1Uc3SXSuDmZNJ10X/RWoHIcBfBtarXB6W0A/wtgMqQmjUijn9M0LztsIxamoVy5n5g4"
    "JvF9RTpWAvAEhWIrDxXB4ivkrRVqwgQDigXef5Bt7WCgYpN9jJ89LtCyJEkiX1htji6S0LnA/gV0WMYKbNyRJ/gyLlylhecY"
    "sGwTtjFqDewX4dYJDVec/GzkIfPW0AFO0m5JTVrS3DQq4jPsOYsUyoekWGauQ7Smr1PYRpnGuA5XIacOmI4sSChumtksGxbI"
    "akmBk9/D/j3J/79BHj7jjDv2RG0W6Z2iJo+w7QGOdSSI4/jvHUewwMZPkhrp7OWcrNk4zWM/NcLyrr9mJy0EXpYJmWLbNd5f"
    "EYgJZOAHGXTUJKipivZvEWYSsK+vCU5nJWxiCuAAqdZuWcMrcPzzAP6Rwu5xLNfHgsYA/DXbLcqy1WRIhrCb6p1ng7uo8qY1"
    "1xm9RE74bPeY6VyiY7rCjk5LeGkY+xt2PCvvYcHJB9TiI8yQmfOxfO4if59iex81idbca4aad5twVKAMjnISt5Ffv5uR+Bkh"
    "KbBlql3sq8LoPIB7ITNbzxKkC5L130vcK1FwBQraaNROmrJ53wvkgTecgVxskkiKPdieE2v4OdlDPwdt6cwetn2FzulGE++f"
    "lW6d4+RM8e+DHPso2zlEa5yhFZXE0o4xgb/IezVKrAt1vB1yhvbwAQWJWhqSypugGdSomZcd+jPjDBQtmGns8c6+zNQZatur"
    "nFTz/u8zG3dnlaR47PiOIIPzXgHwL7TKFyjQw9TOaxT2drHeWH5mPtOcTkV4Y146UBPMC6k5I3RGkSR+ctTmEjsar7LWpZw3"
    "l/F5nq9lmn9JcrY3+d4d0R5kPFNzLM3y2DWyGY30LIv3BJ9RkT4v83kFwWlrf57wE1h27C7f3O50zPDQYn91EoEwg5Cz/giA"
    "/3FWf90VhKo4p2YDVi5dI9tYpDV9Kpk5X44ha40wlMS+q8khBfmoQ8dKMo5ekcGiOG+d4IAObhpAbKFyD2nK9yXGrgH4bzKC"
    "JxlAQDAyL7ijK7Vu/YLRvEic4OechBo25tpC5RmnEoyJEBWfi+K41F9EMuF1SUpdZc75W/y/Cu/5EceYC0WY0xSYZfchKbmz"
    "/OdBgQULLpZoJpC0Xl4cUiCm1E9vfU8CjobHEQUeODGzrLLt0EMbfTAQst+DhLetMum+59TEIqw06xrlY7Bwl07dICQQGlsl"
    "GsQGERrlzNL8zVNbXP8rWUezTh9jErzk5IZD4bJuSVQftWjMEUTgEWwz5xi0eK+7mJCTV8GzWFCjEGsSKt9h2PuB4xRDAN+l"
    "77FVmIg09LeVRxoCmyCfkeWhEWbYzjmpxIj8+RMnbdlL4T1KThl4tCv2DDrIMNm1XrGHAsYSrfpC6F5q6TlSy5qUHyx5GIpF"
    "sQUpGzhHarlk7SqG1njDBFnCoGTDRhmj52Vm1evqdYte/lO2EXtMschnDEiRiOV6l7G+isi8LG2VCUWWDF8SM3eTQBHXDS9m"
    "pGPz4tj7yZNHBaYsBbCo63mhs5Y2S8HsEa9ZEai456xB+QpPqk4El3XtoOPZQksZYTQ06FmKakVj3ZKoMvtrJVq3nRXqZivt"
    "RUfIsVhARCV8UXIhgdCznNLU0INX56lZzxNbivz9nuBwkLFkdD8lRzeJb6HDTHLrhAkfJEQtLhIMUbkiMoTljOhzG51lILnu"
    "f6YzXBFJhs7aVI4m/jGpx4I4vX0E8MVVBOqLmrKEUMfGVqLr6q/lnCNa09O0piEKdp6Q4Vbav0B40LC8TMuvukobNtGuaT7Q"
    "oGI7c6+TzeoAMkJg30ADz3peO6844++6E8wMMKt2ghZbJUyd9mDwNpYwVCVACaiQfcKXv7QiASfhMgvgnxgYVCWBfFwEkV/n"
    "4NWUY2dlox0vt11lMHnJ7v2RLP0U5P6Kx2e8LAvCoDVPMck1B091Zi7DWcRSy2BJ7AJTk68wWIha5K5roVXtfGXBV4l08nHh"
    "scY6fkaoDCVQ2sXkT13eu8Zk1GJWviOXkQOwWb7GzFlOIrPjDJ3zbRTwRmKw8fitSEurShzPAgOKNyk0s4Bh+qA+weOIaYSr"
    "gsdR1qJl1nWdyyGx5D5LzBXvx8pqyIfh0lWZMTqrkDAYUHPfchY+AeDPSFUL0s4snWC0Gudr5qQa9I4/YQbfQsxR/v2JrLBW"
    "u1y4WlfxDB2b1X1Ytu48x2zj2c7FiMdEa5dkMeAeVhaw4H40uCHYdJIJ7mVJ5BxkXiHscuFqABIyaf9d+hGrvHyPmcMG0mLv"
    "IuHwuBP5lWnVZyWczqyZXg0iVP3PEtBN8MMA/pI5Bw1RuxkWDgD4G/bd8jD/QQWCZBYDrmw8S9y19wtItodNZsjovgUcS5Q1"
    "i2SZ/brMms3yc2JCPV0GC3X29ZjQMYOFNxg8VbCyYOUgIXCI7VjY/ROupCy3qky5Fu5RfnyLWGU5CUs/vuKYXDfBQp4c9hX2"
    "tZ+CnGLSvO44un2M1raLk6vQgt9EupEmaqeAIcnkd5hxMjpnG1l+SJ7YDXChrGYvkpqFYaRFMD9Hskj726wXf9/DJM4hUZYe"
    "4vMpkUfL4X2rQlDSXiMWhw4fNrgo8XPXc28k5lrAdAxpIbltRThJ7S0LW7DyqaeI0znS0hpD5ilqsY2n0W4BawASMgCZockN"
    "EqtyjPTGidM3RbgBNmDjtQjY6p0nmD+wZZyPqY1KLQcZ0X2bUNKQLNmHSPaV1KTd+zOlNe70NIGNIFko3UeoMLyeA/BTdjCQ"
    "mY83CB7sOTsZ4uaRLELOkseqZf2Q9+1AupJeIruYRLoJcm2dWaOAtahkP03rGTHPiNm4KaF2ivkbfYZD0cntGt4eBfC7/Mx2"
    "mC5LuHwP69xeu1ZHVBczu8zE+X5qsW3iHucgyhR22Rlkp2FDd0wti08YpIa+xERPLFm0JcKI7SDKtZB67YgG+4S0hXCxFys3"
    "fS9QE95BsjoL4Zxxh7Q5a0vaQQB/jLR4xurNLIj4MSPWpXYpwXqplFW1RHR6vyRXPkJebHj3NaF0U0ySwJNXXs8BGbrU5G5J"
    "sxqzCaSbI23rgtVnvCvCbVvyql3HGQTCJ3Mk6k8zJWi7lawq5n1mrGrwbHtax+DcgZSIq+NIzp8YR7rD33C1QsUwtgAJIuJu"
    "ErDPqZToRH5A/LUiwTLSTYO27QkZGo0mGBhk+AXwWc8z3B2gX9C1NSviO8VEzwzSuo+2+oZ2C9j1uH3U5gmk+8uUT95ibG9h"
    "+EU0P3ij2bULSZVNnVHb4xRsA2n1UYUCP02YuoSVZ0S0/QyfdoezWvQXEs/eQFpetBVpoYlVAu3g7/P08B9KksldYwscTdf1"
    "wef4qvIZOazcO12hll5Huoam1LEjq9udPFJGTc0gI08vPsa/i1i5smxn92jNhUFKTd4LJeVozq1P4EX3VcxS4D9l5iwS4Xac"
    "Mnb6WC/f6X2HyDCK1DhLe+axcqW5IcIqYGUVph2RUBOL6aXwChRqAUkN8VV+fhorazo6Agmdhgifc6o7vPQjpPvQisRnI/sD"
    "WLk6GzhwoRNn+0n03jzS+rCIbOUTZ7y6/7rzcfsGnl3pq98dFNr0LB2iVaCHItxIojHbMhA6mT7j3CeRlHjlGODUV+nDV0bA"
    "bkDgRnGjTBUOM804RJy2jeFn+T9D1Pod0l6ZjOA6ad8dD+1rbKRgNwoimqU91YPbPhE78mUb0uT9MqmUBQJjWFl8FxBn3xbo"
    "sVB8w6CgmwTso3WuZs1j5f5opWcjTI/qPrsz1GC7ahsNBd0qYBWCFoPXHaHqWTp9Hqc3i3SDt7fC5kFdOXTPFTsmHXnYiO2i"
    "DJ0J0A3ojS4aU1cJOCuv4OYdggyo6cqjvLtVwN3ar6+UgPOrZNM2BdymwGRTgzvk8OJNAXc+2tsUcIcgwUpksw6C3hTwOgIO"
    "YOVBysGmBrf/arl6cVPAa4OIAvxpxk0Bt7Ffja+CBndbyf9aDuNHNzvCsMuEm2sBEuIMjde64E0Be7iuZsKqyP4OCz2zwoQ9"
    "62C2tv1AE0EP6uvOfEV/BXn1C1Wz837sijw4PYb0SNwKsk/Y3vC8RviANNYnYPtGmANI8rv6nXKa+FlAskQ0Lv1/le9fRFI0"
    "/UXGs+M1YnxXCljPJfMJdCeSHZRWEzHGv5WmlZGs070rbd0E8AsAf0GtHWEbdizNANK1PTt+8banbxtSF7GRq8pW/BxTEE8j"
    "KdCzQyxs+d5+LvCz10TAWln/p0gKvHdg5X44q/fNI90VZYc6NZBubtkYTOyQgH1l999AsoXVzhXuw8rjxW0jY44QMYlku9Vc"
    "hkDsDLZvIakWss3qeWEVWo5l5bJnkO6CQqc1OewALCgc7KXZ2znrQ0jPybSDRm197QKSjSp2AtYlpPUNqrl6zrtV7VziPYPU"
    "6keQflecHVfQg2RzoX2Fzy0ktWoLnv53rQbrOZB7kNSePUWh9op2VZGeRdZAUjDyJpLtYXC0K2ubgW9DTS+h5wnwiG9aiR1C"
    "Z3VyJvxfIKnmtK9p6FoBB45VHEKyyWQc6d5lO8+mgKQ2920K1r5fbtEjyGYDzvrMqjbtW2xfIjOJkB7wZCzCjjmfJDOJ2y3k"
    "sM3QENNMTxAeTGuW6M0/5qBuebQ1cPhuq7io9M/qgO28nTuEgAl+to+OtS5M4hD7o9+zVO82AevMDyIpe7IjwG3vxg0k5fqK"
    "i7anzhzdWs6dqGcI3ZjJApK6NhPoCZlAc4rjSL/0pKsr3DWIMOEF9PgnkOxtrjG0nUZyXOMX8H9bzHquAaS7PMf4u22KcXfL"
    "59m/cXz5O+O6DiJA87xKCmUnmYYyENvTvJMmfI9ORr9RILjPCVVaaF8gMsQgxL7bwvbCNYSaLUu0aF8Sle9WiLBrnuT+OOHC"
    "yvx1u0DEz/op7NWOug1ayKq5p7q6R9rqmWhWc2yO9yLSb1hsq1V3ItAwZ2XbtkboxY8h/eKRHsFdeIQRoPUjGmPn99jzmbVj"
    "X5hSRrLr9DzS/XJLD3OoPERNHc0wb8shDNC8LTDQavfAgaK6OMia0D3b0L1Isy87k2ns4jK+/PVqD4WAAycQaGU/8hAd0k5G"
    "WcMSSvcKG9FI0bYV2PasCoU6zyTPbTrQuSbP7Xj1+/8D8dyBJ9vht7QAAAAASUVORK5CYII="
)
ICON_CAT_PERUANA = f'<img src="data:image/png;base64,{ICON_CAT_PERUANA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_PIZZA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAF4AAABgCAYAAACUosWzAAAX40lEQVR42u1daZMV53V+uu8yyx2GYQYGGAHDLgSDBAK0IdmW"
    "cGxSsR3ZseOkUqlUNlfyLX8mH1xJnKoklQ+pbC5HtiPZBCQkJMwgQGLfh2XYZmD2mbt050M/p/q5L31nYbbL0lW35s5duvs9"
    "7znPOec5532vF4YhqvRIASjxuQcgTHgffD1MeL+qD68KBa9CbgHQAaCG/xcBjAK4BOCW8z2f3w0eh0lIV6MyUHBZANsBvMrX"
    "6yj4OgBHAHwMoMDHgFiHnQPVPAHVpvGe/N0C4CsAVvK1DLXZp9aPUrBXARwEcNmBoaqGoGrT+BS1GhT8Ygq6BGCMz0f4v8f7"
    "f57W0QPgAYBzAG46Ywz4eCb4SUzAEhHWKIA+AHnifQ2AhbSCAoB2PlIAmgEc5neGOFFVBz/pKoKYUHC6TeCiCOD/AByn1nsA"
    "1hCG1vE7tbSGAMBO+oZuAJ8COCqTGTwTfLLwPWL6NwEsolBThI4++exZavQSav4mAEtpEVmeZzUnYy2AU3zouEvzOQnVpvEB"
    "gEYK36DhOoD7nAATWIkh5SXCzX0Auyj0ZlpACKCVk7OI3+8DcEP8iDdfwq8WwbuDryE+PwDwEQUWUGCukywRTo4BWAHgDQDb"
    "iP05fmYt4asGwN9zwrz5xP1qCCd9DtwHsIMYvZpCHqKGdgI46Qg9LRGPZrhtAJbRal6Uz5mQr/JxXJKwDM8RPE0an6J2lgBs"
    "ZgiZoqByADYSOnIA7vD1ew7mp8S53uCji35gLeFmASd4OV+r52TeJVSpEoRPg8anBXP/jJra6Aw+FG30APwawP8mJF4KGxYV"
    "eQC+A+BNnsMT4Q4B+ALAfybcy1MBNU0AXgawmzhsVlCkoEyj7Rik0y0wYepMsGIV4BJCUBuAr1HgCxgFjRDzPwFwxeF9Sk8i"
    "1HhCauUYl9fwtQKAXgD9FHoLo5UihbKQEUyR0FQCMMzJGJbzp6nZd/m4yO+t4jVreP0OOe8tALdlAoInTeNV8M8D+BE10Jzd"
    "31GbM4xUXqOQQxEKJNIJAPyc5FmS0HyBmg4AfySvp+RcJwk9g0+i4D2JZFaQgXyVLONdAB8COC2m3kitr+fnd1JYGbKV5pz7"
    "qfUnAZzgNdTx2vmyzH7bGEk18LUaOuSLAD7jeXw+ik8C1PgSvq3nw+PgRgB8yc/V0Qr6+QCAa6QOVhKnV8hnwRCyiUK8zdCx"
    "JNdN85xnOUljtLgX+DzLCXmFnzvP+0zNJOb7VZCxtjFcNE1U0y4IE2nHAID9AP4ZwM8AXODrAYWdYbj42wC+TUF7wlLm5Vxj"
    "dKr/Sm7H3suRdPt9TqI3G5o314KGaNAKpvOGd0PU0KSM0qdQ9Z5vAHiPgjvL7w3xvXpaxV/QcdfJ9zJiYTYB/0ZLG+G91RKC"
    "fshcoiS0xWMHNao5Cxg+LpDo4wyxHeJ4IXF3kKA0t/kI6B9aid/2/nL6CIOek7QkYystabpBXM8xc27kxLQSdoycm5F4f66d"
    "q0YyawD8tQghBeAnFHySxnuiKIFDE2jytAzAX/F5HbU7pNPMAvhHRkulhAy6xGt8i063ntcaolX8LaHOny7ez2ccv0ASldDh"
    "Sizj1HBuPeniMWruZ6QOQpkMMA7/CWHsNUJZGnHN9rcAPAfgV+JX8vL9In3IAIC3eJ+1fPwxgF8y6kmjvIZQtYL3RUgbyMsY"
    "Jz5CTe9zSDNlEFdTeDkKDnSuoXA7VjrsQlQKHKNlbUVcMGlCVCh5QFYzL5ZjNMMDRAV1nzlEEz/XzLA3PV3YmWvBFzmwnXRY"
    "aUJAD4CfEna8CprUR9PPUQg76RMuywQWZbLGSCV08jpriPM5/v9DJkkXxdoCgbQ+5hM50hk54v56+o2b/H7wqMKYq0MFmZXn"
    "o4hrp55kke5xnIIwJ1sH4AfUwCCBXVQt/CWjn26J5QMAv0M8b0zIcC3a+bVwQSGhpwXAnzNqChzauWo0Xh1qAwXVJDH7bTo7"
    "G1iaSVC9YL0dtYSk5yTL7E+4pvoIj9DxgJP6AqJabR2vsZ2fP06IKolsSsT6w7zfHZLJNgJ4m8pwOcEnVQXUeJL6m4PMUCu/"
    "APAb3nQtTfld4VAC+f4osXch3/svMos+Hm7hULiy83zOz+8G8Dq1t8T/mxD355ScCegG8AEddovE+Jt53ivia6pG8BoSKqde"
    "IlbbAFcC2EMirF4gJZRwM0WtC6ihVxNCyolgrg/AAfqVbxPiGunw07zGObGakljNPwH4LqLCeiPfW0rHf91RknA+MV7Pv4aa"
    "ZQ5wlLBxmdrzNrU9J3G3T5rXMtKCRDaLOQmLUd6BNp7VpeRcnwP4BaKq1iA/s473uMpJ3Mzv9CCqAZ+n1Qa0mrepLCW5BqpB"
    "8CVi6zZic4GD/wUH/QIf1jNpgj9PlvEmJyAQzn4jY/I2caT+JKgKm4A8KeTD4uBDwsdOnlctxpMwcj9DYPNJG0m01SG5ID/v"
    "4aSFfXlqTD+AdxiueYiLzpeJqXdEyz0O7jv8fj0fjRVgrZKCuS0dJ4jhP6LAauncwXsYlHPbBN8B8GMA3+cEZaj1yxkWTxjf"
    "z6bgDR8zxO/l8ppFClZ8NuH0c/D7hHUE4ja8ozzHVg7YR9Rj2UPrKDqRhTdBdmlZ600WUXYIf7+BlvCeEGsF+dvLHKAFcVvh"
    "y4zSvuB3K/btpOdAw2uY/a0SLbhOwdcIl+5RwOeEacxKfG9dwh/zvK3E+jU85xVH8DroRsRtHqHwL3mxBlOEryMuM75OP3Rd"
    "MtySwNUFKk4HsR7MDW7xfiq2DaZnUds90ZTVKK/kdPNmXuKNm0A+QtSYBIGkMAFGblMY6zlZzU7i5YngFzF6WSY4bhbXKc4e"
    "vHaeiZlPxfgDAO8LheALjl8jlWxhZZrw14q4cB7OtXM1rVvMARQlYbrISMaqRSa0uxLNuGYaOo5xWHA3rHD9FhZENkmEBCZg"
    "u+nsGyXWL5CG6ORni5ysXYjbQ4pCkAXU+vc5mQaJL3FsmkfMuuC1D3IpMRhChnVSwI2ihWnJTFMVBOmJqTfIhKUdyw2lirSL"
    "/qAoE2YCbuP7y8UP2GcO0YGWRIO/QVjLCnxk6Xz3U8PNtyzjxDbLvXmzLXhfLrSFWmUYPoy4azfLgfkJmj0RfC2j4EzonhMy"
    "GhH3Gt8fo5X9mBGThYK1TmXK7sVaPMzK6qkgf0rrCRLu9SydvFEjaxn1tDiJ1axDTShJRSjO1sw9T80fE5M0ti/lPHRVRwMt"
    "SWHmhji/UCbHaOI6Qt52OsGA1/2COO07jhNMsA6K9do9bBRrC4TauMCHJXx5Cn9Mxj+rgjfBtZNTqZWE6IxkdgN0TD2iQSs4"
    "WUU+jDMxATdLclPDQfUkOEmPpj8oDr6dVPAq3tMtfq9HvhPI57vJTF5FXMetpX/YLPdmUVQ/I6AhCQqs0rZotjHe8DlHM9vA"
    "QeRZMfoA8VqmAfItvWKKexCv8nOPxUxS9kgMHzJ+Py1CsKMT0UqSNOJ2QFAwXYgaph6I4MIEcq3IOP6WxPDNdJ5JCdk1AP+N"
    "qAnWwuFvobxvMzUb4aSyiE28WdD8dPBW3xzhYEYIIQsRFZYXJ3DjDUzE6jlZjRTsqQqYa8xnlhNmTvkQIWFsHH4nkJzjKuI1"
    "WIt5v8sYZn6CeKGbJVYX+XyIFmKZdzAbcbxGMguJbaO8sOH6gEPf2oCv8MZCCiNHasB3zmuUQsBzd5Fl1EEHDq8/QpxeSL9w"
    "j8IawcSrAUOxqktUpBbhbDby9S4n3A0IqWsQF9zrCHXdBokz1WWgXVZv0LwyFGQeUc/KOWH7PAfu1gL4Q05UJuEzumY1C+B/"
    "WIAoTrL4oMvvgykqlAm/HcBfyqSCJN/+BAVMAfgqaw/maPOEt1sA/PQMQwxE0wxbszRHbYMLHR7lEifHaqLtiFqrM7SWe7xh"
    "qzZ1Oc50ovsqJfi2YIJwOBCtL0ji1y4h7BaOaZ8I3IKCUTr3HF9rotWHMwU1ngiygdib4XsFKad5FeJ1CzPPyHvXCQ0m+Dso"
    "XzSMhEn0HOtIglS3jaRSVAbE62jvyXc/o3P1hBndxujHvV4PfVFWgoktHOfATEQ1vmR9LzPUMs79OqJC8xAqL3FJEkIXy4Gf"
    "MPK5OUFVaaLl8yXRxMkcORJkexAvYBtB1IV21cmOS8LdF2VM5wD8ByMnCw6+T/8V+DMIMz6F3ihMYj8dCsahAhRLvQT4CBOy"
    "V8+pKFUSvvtaehLw1Mby3svU0B9QWHa+44yKjMdpAvA95ge+M9a7nBzLA/ppKTMCNTYoW+Zui3xHRejeJM4ROsJ1qYTA+YzG"
    "2y2EpoDCaKTFjfC1YWL0cELsrc9bSTNsEStuY8Z7h3BxhXDTgbjlr5Vj75KxWv/+EU7KIsm8m2dC8CUKeq3MeJ6ace4Roomw"
    "gkOs5FeWUlivC/+vhWqfjvkgMVrpCzjPX6CmQ6iKRaS1txH6xoTHCRF3MNeL0K2GMMoCy27mIFk652lpvIZOG4mHDUL/nia+"
    "zfTy9ZQ463cp+FZJ3IYEhlIc7HJEi85WIu4w8BwfkyJs6ELmRv5tZtLkCX29j9SvMZCv8vkHDlW9gnUD62BYNl2NV3NvpNAt"
    "Te5DvA610trRR11Pautf11HL+xAvIisR3uwzS8TaGmgZJxCvl9Xr1/HeU3KuULLW80IvD9F6niecZZmDWOF9Ja9XR0tZL7lE"
    "AMBLT1Popik1TvZ5VjC5MEPa7gkjuZE0ABBvNhGyJnuI2rWcGrkV5S3ebUIDuCGgJ5WneskVPiVWa532ATV/kUzcAL+7F/Ee"
    "Cq5/y04ngbIEJMuymiUVgxT6gQSaNunQSk44hcluEm0eoy/5lGHngFDM3cTl71KQi4jhNQxzlW4YpCb3Ie5ya2ZIeMoJEgzu"
    "DnAC3+R3NiLqVmiTfMFQwZq3zgM4PB3B28k2yk0ZL9Mj+NbqhIB2dDPOd8PScAKnu4DnNJy/iKgAfsERim2fdY+WYGXGNOLt"
    "tvS6RSpNjWTdedZhi6LpuoaqAfH6rQyfZ537sHymj/8fBnDtUQVvUUMNNcW6ueqoNRYRvMmKTUYqTqa5p6hNeYkEJuPI19JB"
    "mdO+SKHramzPiXw6KZRVPEd/hUTsAsrbSvTIC2T5HPNeWoVLiRfk86epGNdUcR9V8CWa7XbGr7bTxk+pNZso9FahRAtOmLaB"
    "ZnmZ+Hl9HB7Fl9CwWZK0AA+vIoFDxvko3yKrOMlSY9Jh7XptFHCzwJJHra6jUh2h9Q/i4Y7mMP2IDi6kwHfxZvqp0Z38+wpj"
    "3zGJdUcc8wtp+js4ER/TWZXGgZmAAxnh9SE1U+1CsAnOUyhbeT8QTsn1V5oJq/WtYsiapV/ZLkWRUMLXO0ygMpTD1fEY0ulE"
    "NS2Il0oa5LQTCtqlVGbh2B0pwdl3aikcS1r2kViqRKiVOLiNFIKZ/HImScUECMkxgVkicHg/4dzaomcbWSxAtA5qO+L90LLC"
    "uw8LA3sA8cJo4OENSEuPWghRx7iQ5mYtGzcJGXsJLxlOxGUKU/cbsLDzRSZdlppvpyPrTYhilEa+y4ksMlJZz/v5d76nRwuA"
    "P6GCWFa9H1EhW/khF952kxKoo/A98SmjEon9nGP0JaBwyT+vUjg31UgGFNIaqeKAYdxKCjxLJu8oHt6K1ti6MWphOweYpvZe"
    "wfh7hgUMyVaK9axD1HrX7WSkrULjGoRc5cS5S+S3IW6E3Sm+y+Aky3vv4v89VJQxB048J1Ofdu+kztxmxMsla4iZlsVZxeVX"
    "nIQaxBV5DSnvM5b+HqOUGiGbesbBeVDLDtFHWD99Bx+e41yzQieckji/JNpcx2pRhmPx5bsjUtToZL4wJDLRjHTSSy+nIng7"
    "ab1gl8W5tRR8LW/KR/li4MBxkNroPyzEVRNhoWccjbeJPcm/e/gdi6O1TjsiucUntMBBOdc3aDVZwpJC2gCjp8Mc4xAfo44y"
    "zNo6V+1VaUW86NY4jWOEjE3CVHajfLM2twvAS4i1LQmZ6J5CifvP8BorGbWsoWANty/yXmyrRBBGGqhAL0oN1RLCtJT5hmgl"
    "tyvUYR95L5upaLw1gW4XAfgO4RRIuj7qaHclDl4told8ACYYmDnLL/l4iZi8kO+dJizcJYwtYe7wTU5avZQoPYm5S4Sxz53c"
    "Q+952tunTDWcHEPcb5KmOVo6HUp0sFzCrlRCEcNzNMiinssSmUy0Gac7KafomH2UdxO3I17UtkBSfE/yggYmPEeo5cNOLF/C"
    "DG8Omp4CzHRQq0xQPYgaigoSUj6HuMO2iRqcl2sVhbFME2OXURg22BImv1hX9x0rCBW9hPe6iIJfRyWxpT7WSKV0w5kESPES"
    "ql9zIviUCGs7kyN77S7N0QoDv6EQjbPeKnH3IOIeGNuEzTZmHuJr9yRJmUoGXRCn38Dw8S3EixasIlUvdc9+jv0jh5vxnbB5"
    "1jYAnazGJyU0it0D5Gj2Shj2GoV/igO8y4nZyQjI2kACWss/UOtTmHhTBk167J46eE3bWzgt1EDIya9jQncc8dIfF77mZLfV"
    "iQRfojZuoGO11y5R233Hob5HwVqE0kiB5KhlixB3BD/guS5QEAOO00RC+q3+wHiaF+lTVjO6GRaePo/4py2uc1JPSBwOJw6f"
    "s8170pModuQQtaMtFjLpFKMG3+Gej/Hv1xBvVWuwYr3kWWEJ7zPyuCq0apDAz7s7MzVx8lZLEcKW+9Ty872S/Hzo4Hd6JiOU"
    "mRS8wkqdOE3TvFHnsyqsk4gWCvwuojYJy259oU9vIF4hPZrAi7sOTgW/kr7B6pgZmTTb7ekqM+cuxIvY9Chino/0OEL3CS+b"
    "EfcPFggNvU7yY0lIiibei6it7UuULyw2QfZSKAXHulxI0Ur9Jsls24XjH6P236YV9vJxCQ9vJufNl4ZPRvCaba5D1GtiGtlH"
    "Te2tQKlq/3sX4hbm8a4foLzFWRlQc8A7SB0rIWV98n0U+nFSAoWEUPOx+3GWdsT7Lhp/cUE0vDjJ5KbSUXTiZRX+K4h6VXKI"
    "1xllhS0sMsM8yv+DBA6/iCo90hWEZiW2FhmMrXIIE5zfEkQ9LsNk8O47Gl0p3XdLcR30CxlWfhai/Ee26jjxZ3gvlyUa0jBT"
    "0/vHQvBG/uQQ76RkfEY3ojYK33GGzzGk+wri5p4jzGxLCf7DNfulotW29F6XwqQ4oXc5AYdQ3tKdSuB+qv5IV3CsTRQChGs5"
    "gGhNkWm/LdZ9F+Vltbf4/Z9RG7XgECY406/Tj9Q6lhQIW3iUYecDJP9GyGN3pMdhDG05YxFxM04o8JCh821B+bqmMVILFual"
    "8fDv8H2VSU8NP2s0r/2ymTWaHkf8Szb3EzLqEI/pkU6I25cxpS+IQLoZb6ck4klLslKL8gW/GSGkjKNfzs8tpj8A4u1GbLJH"
    "CSkjzIxPoHw/AK8aI5TpCF5DyNdJiGURrz/6F+FRINTrdTq5jPgHW+u/mkJMMQZ/B3EjUuj4CpusE4jaqa8lcEUlPEFHpQRq"
    "lA5vRChb4OE9de8zinkD8a5J5ozfptP1EC93zDvcju5qeo9x+T0H+ubsl2rmQ/DGNi4W2tYYvfOC027XlrXilajN6xH3qi9A"
    "vHlERr6bF2ux8t2xhMQneJyilKkeXhiGhtsNpHW3CLfyPqJiRzgJMq0WwO8hbk5yl7oEKG973icx+GPvLB9F423QWWKxVeq1"
    "fKZJj+8QTQG5lHfoQAsCDx7iHTmMGAsILwMOpHiYx9/emw/BWxhoP35iZbl+hnKafWpE0cRwMkBUZmsTaLEI6B4FHjIHuOD4"
    "kpRQs0+NtqvgmxEvKbR+lEOIV1BrlmiRzXZE+z4WEa8FtejDdkE6iKgkCDxc5K5qLmUuBJ+i0DsQ7z9gTfpupWYXqQTbS93I"
    "K/1djo8Zg4cJEcpTh+XjCd4cqy7GPU+hZRF15i6gVm8hJI2JtaQYoVhR+xjK+yXnpbT2OAi+iUKtE8E8QLx9yV7E20lZomTt"
    "1bafy4ecLJd9nFI/4dN0eGEY/g2igkNOCLF+xPvNNIlTNafZh2i5oW24M4DyBiDvmXZPrPErndQ9xUmwTrBhidWvIKJ7b9IH"
    "DDrnCp9ByuQFfxBRF0Azyn8lzNb2jFGbzyLquO0SrVZIKT4T59SgpoHJj1V+ahDvIjeE+FcERqj9ScWNZxr+CIIHeRZbFmmr"
    "9IYRtzi7qx6eWA5lLgXvFq0XUqgDToYZ4AlkCefr+H9F0mjZiI5L4gAAAABJRU5ErkJggg=="
)
ICON_CAT_PIZZA = f'<img src="data:image/png;base64,{ICON_CAT_PIZZA_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_POKES_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFQAAABgCAYAAACDgFV6AAAV7klEQVR42u1d+28c13k9Mzu7y12SoviQKFEv62GJDmnLj1iu"
    "Y/kVx67jOE7jokWDIEARtEWBIug/0x9aFG3QpGiKFHnUcB9OGsdRZceVLMWSZVuy3pRJSbYkUiRFch+z0x/mfJrDq9nlUiKV"
    "iPQCC5K7M3fmnvs9z/fdoRdFEZbxy+O7FcAjAJ4DMALgRwA+BhAB8AHUmh3Q/wxM1PjzHn7eDmAXgLwch88AbX7+PQB2AlhD"
    "iQworS03g1GwjIGsAQgBPEFAWwBUKJGTBBfy8zMJnUPdITZyWj4vU+39OVTep0AGimOwTMGMAGQBbAXQBaDI76qUzvcAzPDY"
    "sIGE19xxlyOgGQJXAPASgA6CCwAlAOcA/LscG6YsRo3CmOVnJTsuWMbqHlIyKwTOgA7m8DkV/v4w360A/hPAoeUGqEpXJ4BB"
    "kTBT7REAH9RRaQMzD2A3gM8BWMmFeJTfn1yOEhoC6AXwOMHxaC99AEdoPyFOyxP7mgfwAIDnaWvbCXovgGcA9CzXsGklVTUk"
    "IObtx8R21hxAI4ZXL/C7dn6W4e8rADy9HAHtArBJvHUJwFUAbwIYFtNgQX6Vx34JwAC/nwBwAcBlqn9EczCxXAD1JUC/H8B6"
    "ADl+PkWQ3nY8uydO6nMErszoYBjAzznGbgDjHOficgnsPQF0AEAbf68RlKvinOx4nz+3APgmM6k2HvsKgLMA1vH4Gdrff14u"
    "EloT6csIaNOUzINiLyP5fgsl0M4vMzwaYcj0oDiraLmETaaFnfTsBUpblYBeBXApJcWsArgLwEb+fZU282ckTx4lkJYMnASQ"
    "DZaBqvsEpwMxLRc6IVRZ7KZynz10Xp5I8xF686/TZrYAuAbgvwB8AiCzHCQ0EvByBNeA/CdKJ5xwKQfgTwlewDF+SsD/SgiR"
    "ywB+QDABIPKXgap7AB4C8EWR2GnGjpcJsC+gbwLwDQCreFxZnNAGHlPlWOdoT68vhr/E1T3i5LciJpA9xovmXIoSUpm6byao"
    "Zhr2A/g1gG0A7qP0zlAq3+N5101FsAxU3cocRZHCswB+6LBPZjdXidc+A+B1AvYcv28hoAcAfOjGucESl84WqvvdSEoa15x5"
    "55AQzE8yVMrwOONFv0MJn+a4/0qv7i7ekmXsM5IOPkQP71M6h8goZXncNH/fTZU29T/M878EoJvAlgH8D729nXdbAfWc982e"
    "N9/zDdRVVNOQ4EQA9gJ4V+i5PLOnL1NyWwCcRkwy95NdKvLc9wG8xntRbnQWx7fYMaBLhdXmeZ6b8URNqHoIoA9xAa4FCatu"
    "IZGO9TRBC0jJHWNcuZOAFnj+R8yobC6p81gMQH0JpsMG4UzN+UyZ9HAOyYMwQlEdh7QSwHaOXWam8w6AURljFe2rmYNrBG2C"
    "mVCRx16mVI841N6iAqqMeI32pZsSYiXbMd40HBVWcNt5XprHvkwpSruujtfK0Mds3BTV85fOIu4i4WEqfQDARaaW62knA5qJ"
    "IdGwulqykIC65MIOAE8xH65w1fcB2CPpXjVlnMd5ngbbBvobdAr1JN9otweQ1NqNBK44C9BDKq9FbOIRMkgv0LZmABwnoC4/"
    "itul8oMAPk8idy294xSS/qG7GFTvl3P6+R04oYrYPLOpOY7bR8k7SImK5JiQf2+l1Fmd/Qivl+XYWwA8S224SBy+Sy+/g2ON"
    "MjT6lQjJnD1OwQKpujVcbScwfXIDWd5chddbTSksivo/SHtW4mRamGNP8+8VHN/jcW08ppVjH6bktNJc9AnAMwCuUGVBm/kI"
    "JXQcMfN+jOB+gccXGFrt5fcZ3Fi0WxRAMyIVA/Sq3WLPKpz4L+gkniUYXQQ2krgvS7NQZo78vwQiQ3u2m2OazdvIMQ38EQL6"
    "PJJae8jzy3KNrxGwFbTJ+wjsdzh+C4DzAH7MBc7x/KZezQLqS3qlRSttBBjkKme4yjlZ0WkAJ+hpv0mgW4WYGCXI3+Mx9pnZ"
    "xI8pMSHV9Wu8fhs/+xZV9hpz7irfZQBv0UP38Lx1AD7lPXyfxz9HsMcJ5k8IJtJizYUAtJ64h7yRF8jElAnkXkrRIM97mDd4"
    "jJ6+g8cG/PsoVetUHWc3w7cRvSs4pjmUIu9hQkzQFI87SqDv5nuCwB2jibpfpPk8neYVzG53XDBAPQlDVjje3BN25vMSogwD"
    "+G+qVSviAtdGpnBv8rwsr11i9rGXamvxaJhiWjz+LNGE+IwV23it7TJ5u7ejvJ8OSqLFxxNki15iGFbkZ2/TqwdISsxYCEA1"
    "/OkE8BjfZSFcS5xgi4Qlo1zhgGq+n1LaRXLhXjHwJQbae3ie1yADiSSWNarsdd7Ps1ygvBx/jdL+bwTwaSQNtdaCs1PGGwPw"
    "KqUW4hdumoStJ5kRb2SAgFk8OUPpywrnOM7V/lDs60nSZFd5bijSfUzA1Kynj+r8EK/bLsG0Ah5Smk7zs4p8N0FtKLNcMcC5"
    "VriIw1zgkPe8jza+iqS8fFM8R9AATJ+e+D4Cl+ONjlL92xzVuMTwpSS0WJmx4heQdLxFBHo/bRWokuso7YOivlcJ2pCQEVP0"
    "6BWq7VuMbT2R/ixteh+vPcnPrvJ6BZHMfYwotLKZJnRRM1IbNMg4CiwbbJBM4iA95l10Aq0ija/JxEORRiBpGDC7eYj2ze7h"
    "fl7LTIjFrGsQ9w3VhKMMGdJ8xN+n+DMQgegG8KL8bcW0s5R+i1j2ccEzPF/td9iIBGkGUJu8OZcivWJNPhuiJE4w9PgWpet7"
    "jB3TTIZHKVvBcWpOKPIHDIWylJjjdDoetUODbXOQnRzjbtJuOadeBEdiM9SoHTx/XKKOTUx182IuLpKt/8BJNefcERKkADAj"
    "RMQ7YsdM5YwKO0upbMXsjrVqikOxAN/aqO/leTnayssE9ANqgRW+xji5bTQDRQI+TEe3C0llssQxjnDctZRUIzjMcXlcnJpk"
    "dX1ip3uplev5npBQsORglQqoevQcV9LU/hAvkJOaTCQLsd+pqfjiqCKxR30EMMNjBih9U5Knn0HcuGqkb8jJvEOPPUmb/jYd"
    "0ZME2szOFCXuFX42SNO0igCaH4ikZvSQhHEeZreL93FRpjn3cZqpybnYJh3kAaZ4Vog6JpLlqnPoBP6WZ++glJ5ioGyh17QQ"
    "FsZH5nmdkwxbaqIB+rpCbcgTOFBiA8nE/o9SVObfb7Ja6VEjnqBwQBbfsjkrC+ec+fg0aRmmtNsA/IeAGqUBGtH47yLr080J"
    "WZ4ciA3toSSFDrtu6tJNo5+TNE5z/powQGqTjCfNCCOkjVsVebfT4WziYmRJ6R2WcSPHWx/iPb3I73K8n2GGeaMiJFpuaac2"
    "9fKzfh7zQ8GvmgboZgJqfxeQdFrk5QL3CK0VidH3aG+2c0XdwNia/C3PH6MUGSu1ke+hBmy9ObSt1AJzbocpmUZslJ3Qz5fI"
    "YiPvMRSg98wRDo0C+D3eq0ecLP6dcBMhU+UuTjQQaapSRQNRrS0McSKnulgD8BWuoEfb+mkDIvpVAP/CBctykl+h/XZtmi8k"
    "xUqC0k7gjnEcTxarJmFbRTK6CR47zN8rdHhpVKQK3CEAf4+k3QYA/pApdehWHwKJwUzNfs4bNcl7hhKcR/reHH1Nc7z3Mbtn"
    "qIJk38/rtK9lAH9HNeykA/m2hFQmWRfEwz5KFQzpeCbqMF/NVBYylLph2kS/QVmmJuptJitbzymtkcwBDJjPyDG/4k/LRlby"
    "Ri7x5joYD7aJkxuVyQViB21jgKnlCbGNRXFeFnFYG02BxwzIxN/jwhhTZJN8xAnKT9HEKPPvI+mNb5HkoF4F1lLlAdHa6XqA"
    "FpwAP5J4EbSXkwD+kgOvY7D9CifRB+CPJaefcUKQorBFEE2IJDyzUKtFJlYUDbpfQrKKLPSwjN1Ck/Nl4Q1WIN6q/a5UYbU5"
    "LONwDK1yn9ecgtx+jtfpVF9vAPQMJaxXJlxz6KuLAP4WwMuUxG3OgJ5MdEiaCjxJCvwUJqtG424liyuI2wYnSPcZZ9Dp3PNZ"
    "8eLGGH0RSTNXXrjRwAn7Jij1GdrjVkrwZjJXJsE/cOxm6BT6cmnmweyC2p9dzHEvyokl/m07zzqZMlp45VMyR1mZLIm6FERt"
    "NAa1ax7kpB7g92O0m7+U8m4HJS+kqr1GrbH7r9GxliUOPc8FOumEUOOSjvYSxCs0fVvpTLtp4saQ7LSrOKyXUonXhcTs27gg"
    "fh9XZtgx+B6leTP/7ncAqjF1POtIYuBIs++QMJ9Sqvup0rsYygzJOR0sU0wSrOOOU93En3ku6hFyC586UmY1+kkKRcD5rJUg"
    "v5vfV6UeVWUk0iXl77JDaEcahw7xBGN2Vjmibif+hPbzeSTdbAb6KSFoVRVKjsEPUrxoXtLDQdqvX/C7XsaBLTKe8gYdAP5E"
    "uM0fUTq1fKGkxhTHMJPU5qTVZQrGUcfxPCnAW9DvZorXdyOvo+ra5O7hjb4l0mAXPE3g7iEApmYn6PnNhummgLLUfwoOueBx"
    "Ah6SLuMtlNIKiYpBIUsOOiAZz3qZQI2kjK/hUA6zH0Cwn/NRp3leUtwifccGGcsIngJj6usaZ4CulgHz0nxgJPMMzcI5moLj"
    "lGjz7CNUs1JKuHFNQqAix/tYvH1GausvUU3XENy9Tr5+ntdRqtFat7OOnQ4cJ+KLg7VCYZUx80eOZrWxTlbjvQzKGJHgNFgP"
    "0DJmP2PDmPV+8YhXmDOf580YLVdlPlwQgEtiV2zr31pOcgvt7EgKDfYJPXuOdaBp3pctyBAXSLuSt8q1tQ28Xl1oWhosfEYY"
    "5+XYDsayj9GEFBwgIaz/RUd7b4g/bTWr0gpjF+5hVmNbnFvkvKe4opdoEk5Roi2TOUAWq50AvC+A1sT7/gOvsZme/ylxir8W"
    "86N0Y8GJe9GIr2TXykYJp55mBhaJ9y9KXKz1qqzYUGW+UgE1NbJ07z0e1En1Nqot46iQ2cUC1WMN49ppJLsoOjiO5ek7JRSr"
    "iM0dpTlYL4G2edxDBH2l2NO1lPhAHNsmAtIr1KOyXf0OSdziMFrWvhNJ88OHvI9tXGxP7j8VUDXcZSTN+mZPRpmtlB3mW2k4"
    "TxZghVPYyogzCOjQ2inNJbHbJQlNLDwxMngDQ5p1YgsHaEMzwsI/yetvlNBG2xBzEld60igxI+FQicJQpc3ew98jLrZPX3K6"
    "HqCRI6mBU+PeQ8I24s3uZCC+VkKiSM4NnEVyu5eznPCGlPYebaLwZfFels/g1I00K7tXFrHgTDhKia3NcR2jVg4h6UH1RN27"
    "+LZ7u+DEypEbE/opoGoNPJRa0z6uTpuAUZAmsC5KUyAxX1obT5hS0/JT0sWa2PSMwwBlHaBCAdqTrCxH5zMiDJOSKFc4t3q9"
    "TE/Q/melqWM6LbA39ak6OWtVbkYL/zXezGTKRc12dfNtrH+UAlzkfO6L5ASOpOqmgzQ2CCl5teeUsScI5seUrnovXYhAzNpm"
    "JDtHyk7KeQOgJwD8hrFfKBJSa9As5gbMVig77diW+b4yYuesTl5qkuu8ma4Zt/M6TGkBAm1sZ4qJumHQDD3ZSVGjjbSR2RRz"
    "AKcPKWq2q6LJlxEgk5SqqUUAEw41F83RkpQmVDNpIVrghEsWKnRL7WRcakdpMZ6rzl4DKa7HoKdNql7qmLZJAfO4RtSgtcZP"
    "caIBY/CCLPbbzBo9d5xA/vAdu9E7T8m4qYfvNSEZ826HuUWp1Xuwp9885mSHe5n93VB20ZTKAtiKOKWoTu1osV/RIpiSRq88"
    "pTDjaIVPbX2EDjfrLLCXZkPNRo4hfvzDJ0Q9T9Z87W2a1O1+aYTQA+Cr5FxXOTYzlJ85hwCq6+msd3JYDiwyx+2REMpbYqDq"
    "80j6mGWtEc1YzXTTOgpHSfeV6pmiIGXVypLu1ZgZeUtUSiPhQDsZo5YdUnlQ5n8cyW48vxGgmj7+FMmTBwN6+wqJ3XAJgRvJ"
    "vM8C+BuCOYbZe6/smEmnMOc1E9yC6dllxn8Bvf12cVKZJSipMySERjjvSEgW6wQcYlkkgwa7Q4KU+M4XsTcT0MWwYdyt8i0x"
    "B2VV1FWIq6GhkC97aRKCRuGhnxKD+eQev89Mxaeh/mskjan+EnNQ5i8MzN0MkQryeW4+Xi7NMY0gKaUaKbCThIe3xLy+kT8h"
    "59ePpJt7GvEDCUYxeytm04CaBBYQF84iIYH7kWz9i5YIoMpo9XJ+VkcqkePYi6SHNJqvhIZCLL9KFsp2cVg5RA3znQ6qOtmX"
    "kWx5rCGuwB6ok5o2Daibl7+O5KEBHknWb2B2ocy7Q9XcqqntAP4CcQXBOv3GSICcwuwSz00DagW1y5RS26lhRf7H6flLd6D6"
    "G4dh3YO7kXRTW4feacTV2QrmfnjMnIAaqNZgOsk8fxRJlfAZxLso8gvIMt1u8qUFcRn5YSRtlyVK548Zm2ZvJpdtdGHL8z/k"
    "27KlAuKeoz/C7J72zO+4tOZlXt+mE2oTvzEE4B+FBKkuJKAqeVXEW1f2IdmVbO0oX6dtrYlT+10C1hfnUyLp8SLV3B7OOsMU"
    "9A0k++Uz89W8Zh5AUJPc9gLijaZZxG2P7bzBB5lNFSR1Tato/jbDIghV9whjan3G1CTi5jhrM6/33KnGF5vnf/wyhqWImCu1"
    "rTh2A1V6xu8i2X1xO4niNDAV0F7E7es9nEMNSf3KHs4a3UpqfbOAGod4Fw36OoJqjPZRxB1t7yIpN6sJCBdJat0GYLvXTZTK"
    "Vbxn3Vd/HEmfAW6Vp5jvU3G0AjrK9wwldbskABsoDUWaiQu4sZPYZbswD5DTUt9IIhN72QbanXzbw1jzJHrOIC64nUX9x3Ms"
    "qoSmMTR2A39OEFeIlNhmsoO0vZdEchaj8KbOp48h0SCBtI2zthnsAHN0d48BfpuAqkR1I+6ueArJRgbdnHqVP8cQlxEON5EK"
    "1rtuPYJigLbdYsyVvIcKTU8e8QNmTtN2ji2Emt+KyqeFU2Yb7UF/VdJ99u9x7Dr2jKXVnOx6JP1KM4jrWcNNSortfF4v7FeW"
    "MWUPkidCzPAaV2jXs4i3i5fl3he0TO0t4P/1dB9j+ShTOg9JC0tG1Ksikykgbhv8gKBW5yAz1tDR3IukWUP/P5ztrLMFfgNJ"
    "b74tcIhFiDy8RfxHqfZ0wxqAP0PyIADtNlbnYmFXM9JiDWxZ3PgcUgveh0nsnEPS+7nor4V+OqMCZKmbPYfOHMYUwbb/FAOR"
    "qlCOa9RvZAW2GmY/TUK3HHbwbU/yzopURncKoO6N9iB+ek6XOKgx5svW7mNNtbaJy93KWM9uX+MYBtIox7GNaV2IW2iuMiwq"
    "3Q7+drEfu76BKaqxVhXaykNUQ3uMpUnTCjqWlUj6rrw6sfAY41vbI3+OZmUzkpbMPgC/j5goP3EnqrxKUj/ZqFDUMYu4V9+I"
    "lIw4k6xEA5mUwB0OwD2UZosKtiLZmZIRomY1Q7oTd6oN1Z3GIWa3QnqUxCJm99P7kqlkkL4vyAU4h9kPuC44C6HNwrftHyAs"
    "5oUuIK5j78DsfxCVTbmuAthskJ1xFiuH9JbxeT+y8lZe/w/G+lhqBBNgRwAAAABJRU5ErkJggg=="
)
ICON_CAT_POKES = f'<img src="data:image/png;base64,{ICON_CAT_POKES_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_POLLO_B64 = (
    "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"
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
    "fMSqbwAAAABJRU5ErkJggg=="
)
ICON_CAT_SUSHI = f'<img src="data:image/png;base64,{ICON_CAT_SUSHI_B64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>'

ICON_CAT_VEGETARIANA_B64 = (
    "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"
    "bf83V3ufjAAAAABJRU5ErkJggg=="
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
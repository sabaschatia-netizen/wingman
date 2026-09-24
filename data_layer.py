"""
Capa de datos de Growth Wingman.

Lee un unico workbook (GROWTH_WINGMAN-ARG.xlsx) con todas las hojas. Sabas sube el
archivo actualizado a Streamlit Cloud, igual que en Growth OS.

Reglas que no se rompen:
  1. Toda columna se busca POR NOMBRE, nunca por posicion. Rappi cambia el layout
     de sus exports sin avisar.
  2. La clave de marca es PAIS + NUMERO (ej "AR16516"). Si se colapsa el pais, una
     marca de Uruguay con el mismo numero que una argentina cruza data equivocada.
  3. CVR% y TRAFFIC no traen ID: cruzan por nombre normalizado. Es lo unico que hay.
  4. Si un loader falla, registra el problema y devuelve vacio. Un cero silencioso
     es peor que un error visible.
"""

import os
import re
import unicodedata
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
WORKBOOK = os.path.join(DATA_DIR, "GROWTH_WINGMAN-ARG.xlsx")

# Cambiar esta constante habilita el resto de paises (UY ya viene en los exports).
PAIS = "AR"
PORTFOLIO_COUNTRY = "Argentina"  # se usa en el query de busqueda de Google, no en el filtro de datos
ARS_PER_USD = 1400  # misma referencia que Growth OS -- EXPORT ADS viene en USD

# Los 6 grupos de coinversion de Growth OS (COINV_GROUPS), con su ratio
# real Aliado:Rappi. Churn es el UNICO grupo sin coinversion habilitada.
# ratio_aliado / ratio_rappi son las partes del ratio ya separadas para
# calcular el % que pone cada uno sobre un descuento total.
#
# "icon" (novena vuelta, pedido explícito de Sabas): ya NO es un emoji
# Unicode -- ahora es la CLAVE del propio grupo (idéntica a la key del
# diccionario), que wingmanapp.py usa para elegir el ícono SVG
# monocromático correspondiente (ICON_COINV_* en theme.py). data_layer.py
# no importa theme.py a propósito (capa de datos, no de presentación),
# así que el emoji no puede vivir acá -- el mapeo real ocurre en el
# render.
COINV_GROUPS = {
    "new hunters":      {"ratio": "4:1", "ratio_aliado": 4, "ratio_rappi": 1, "label": "New Hunters", "icon": "new hunters", "has_coinv": True},
    "new rest":         {"ratio": "2:1", "ratio_aliado": 2, "ratio_rappi": 1, "label": "New Rest", "icon": "new rest", "has_coinv": True},
    "churn":            {"ratio": None, "ratio_aliado": None, "ratio_rappi": None, "label": "Churn (Sin Coinv.)", "icon": "churn", "has_coinv": False},
    "churn prevention": {"ratio": "2:3", "ratio_aliado": 2, "ratio_rappi": 3, "label": "Churn Prevention", "icon": "churn prevention", "has_coinv": True},
    "prioritized":      {"ratio": "2:1", "ratio_aliado": 2, "ratio_rappi": 1, "label": "Prioritized", "icon": "prioritized", "has_coinv": True},
    "rest":             {"ratio": "3:1", "ratio_aliado": 3, "ratio_rappi": 1, "label": "Rest", "icon": "rest", "has_coinv": True},
}


def _parse_status_grupo(raw):
    """
    "5. Prioritized" / "6. Rest" -> "prioritized" / "rest" (clave de
    COINV_GROUPS). Se usa tanto para la columna de coinversion de
    ASIGNACION como para STATUS Brand de PRIORITY DATA -- mismo
    vocabulario de grupos en ambas fuentes, solo cambia de donde sale.
    """
    s = str(raw).strip()
    if not s or s.lower() in ("nan", "none", "-", ""):
        return None
    body = re.sub(r"^\s*\d+\s*[\.\-–]\s*", "", s).strip()
    gkey = normalize(body)
    if gkey in COINV_GROUPS:
        return gkey
    for k in COINV_GROUPS:
        if k in gkey or gkey in k:
            return k
    return None

# =========================
# ACCESO AL EQUIPO -- independiente de quien tenga fila en ASIGNACION
# =========================
# ASIGNACION sigue siendo la fuente de la CARTERA de marcas (que no se toca
# aca). Esto solo controla quien puede loguearse a Wingman, porque el
# equipo real y las filas de ASIGNACION quedaron desincronizados: Arnold y
# Claudia salieron del equipo pero siguen en ASIGNACION (sus marcas quedan
# sin dueño operativo por ahora, sin reasignar); los 6 de Fabian entraron
# al equipo pero aun no tienen fila en ASIGNACION (su cartera se arma desde
# DETALLE via load_detalle_portfolio, ver mas abajo). Los 10 de Chile (CL)
# son el mismo caso que los 6 de Fabian, pero de otro pais: tampoco tienen
# fila en ASIGNACION (a diferencia de Maria/UY, que si tenia 180 filas ahi),
# asi que tambien usan load_detalle_portfolio.
#
# Todos, los que ya estaban bajo Oscar, los 6 nuevos de Fabian y los 10 de
# Chile, se tratan como UN solo equipo -- no hay vista separada por lider
# ni por pais por ahora (aparte de la moneda de cada card, ver mas abajo).
EQUIPO_BAJA = {
    "arnold.camino@rappi.com",
    "claudia.pineda@rappi.com",
}

# IMPORTANTE (bug real corregido, agosto 2026): esta lista se armo en dos
# oleadas (los 6 de Fabian, despues los 10 de Chile) cuando NINGUNO de los
# 16 tenia fila propia en ASIGNACION todavia. Con el tiempo, Rappi fue
# actualizando ASIGNACION y 5 de los 16 (andrea.bolivar, daniel.caballero,
# johana.salamanca, juan.bello, natalia.arias) YA tienen fila real ahi
# -- pero como la lista es una constante hardcodeada, portfolio_for()
# seguia mandandolos por el atajo de load_detalle_portfolio (que da
# telefono/mail SIEMPRE vacios, ver esa funcion) en vez de la rama normal
# de ASIGNACION que ya tiene el dato completo. Sintoma real reportado:
# marcas de natalia.arias mostrando "?" en telefono/correo en la ficha,
# aunque ASIGNACION ya trajera el dato.
#
# Se sacaron esos 5 de la lista. Los que quedan (11) siguen sin fila
# propia en ASIGNACION a la fecha de este Excel -- confirmado contando
# filas de ASIGNACION por farmer antes de sacar cada uno. Si Rappi sigue
# migrando al resto, hay que volver a correr ese chequeo y sacarlos de
# aca a medida que aparezcan.
EQUIPO_ALTA_SIN_ASIGNACION = {
    "lizet.torres@rappi.com",
    # Los de Chile que a la fecha de este Excel siguen sin fila en
    # ASIGNACION (0 marcas confirmado). A diferencia de Maria/UY (que si
    # tenia ASIGNACION desde el principio), estos usan load_detalle_portfolio.
    "geraldine.carrera@rappi.com",
    "laura.guevara@rappi.com",
    "vanessa.ramirez@rappi.com",
    "steven.quiroga@rappi.com",
    "juliette.rojas@rappi.com",
    "david.posada@rappi.com",
    "alejandro.guerrero@rappi.com",
    "alejandra.pacheco@rappi.com",
    "shirley.rodriguez@rappi.com",
    "jeimmy.viviescas@rappi.com",
}

# Maria Pedraza es UY, no AR -- su cartera SI esta en ASIGNACION (180
# marcas con COUNTRY_BRAND_ID "UY..."), pero load_asignacion() filtra por
# PAIS="AR" para el resto del equipo, asi que necesita su propio filtro de
# pais (ver farmer_pais/portfolio_for). Los 10 de Chile, en cambio, usan
# load_detalle_portfolio (arriba, EQUIPO_ALTA_SIN_ASIGNACION) porque CL
# tiene CERO filas en ASIGNACION hoy -- pero SI necesitan figurar aca para
# que sus cards usen moneda CLP en vez de ARS.
#
# Sin tasa de conversion: por pedido explicito de Sabas (agosto 2026) cada
# farmer ve su GMV en moneda NATIVA, sin intentar convertir a ARS ni a USD.
FARMER_PAIS_OVERRIDE = {
    "maria.pedraza@rappi.com": {"pais": "UY", "moneda": "UYU"},
    "geraldine.carrera@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "laura.guevara@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "vanessa.ramirez@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "steven.quiroga@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "juliette.rojas@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "david.posada@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "alejandro.guerrero@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "alejandra.pacheco@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "shirley.rodriguez@rappi.com": {"pais": "CL", "moneda": "CLP"},
    "jeimmy.viviescas@rappi.com": {"pais": "CL", "moneda": "CLP"},
}


def farmer_pais(farmer_email):
    """PAIS a usar para filtrar la cartera de este farmer (default: PAIS global)."""
    email = str(farmer_email).strip().lower()
    return FARMER_PAIS_OVERRIDE.get(email, {}).get("pais", PAIS)


def farmer_moneda(farmer_email):
    """Prefijo de moneda a usar en fmt_money para este farmer (default: ARS)."""
    email = str(farmer_email).strip().lower()
    return FARMER_PAIS_OVERRIDE.get(email, {}).get("moneda", "ARS")

SHEETS = {
    "asignacion": "ASIGNACION",
    "ads":        "ADS",
    "ava":        "AVA",
    "md":         "MD",
    "md_pro":     "MD PRO",
    "priority":   "PRIORITY DATA",
    "cvr":        "CVR%",
    "traffic":    "TRAFFIC",
    "top_prod":   "TOP PRODUCTS",
    "md_names":   "MD NAMES",
    "seasonal":   "SEASONAL EVENTS",
    "churn":      "CHURN",
    "last_gmv":   "LAST GMV",
    "previous_gmv": "PREVIOUS GMV",
    "export_ads": "EXPORT ADS",
    "productivity": "PRODUCTIVITY",
    "detalle":    "DETALLE",
    "perfect_store": "PERFECT STORE",
    "prod_target": "PROD TARGET",
    "export_ads_kam": "EXPORT ADS KAM",
    "export_md_kam": "EXPORT MD KAM",
    "export_ads_relation": "EXPORT ADS RELATION",
    "checkout": "CHECKOUT",
    "pitchdata": "PITCHDATA",
    "toprest": "TOPREST",
    "opp_start": "OPP START",
    # "ADS COMERCIAL" fue renombrada a "ADS nominal ACQ" en el workbook
    # (confirmado por Sabas) -- se mantiene la clave interna
    # "ads_comercial" (usada en varios lugares del código) para no tener
    # que renombrar cada referencia, solo el nombre de hoja real cambia.
    "ads_comercial": "ADS nominal ACQ",
    "md_start": "MD START",
    # Hojas nuevas del workbook (confirmado por Sabas): equivalentes
    # monetario/nominal de ADS y nominal de MD, mismo formato de 4 filas
    # de header apiladas (ESTRATEGIA_ADS|MD / MONTH / WEEK / columna
    # real) que ya usa ads_comercial -- ver rendimiento_comercial_ads_for
    # y rendimiento_comercial_md_for.
    "ads_monetario_acq": "ADS monetario ACQ",
    "md_nominal_acq": "MD nominal ACQ",
}

_JUNK = ("total", "nan", "none", "filtros aplicados", "metrica", "metrica")


# =========================
# HELPERS
# =========================

def _issue(context, detail):
    st.session_state.setdefault("data_issues", {})
    st.session_state["data_issues"][context] = str(detail)[:220]


def normalize(text):
    s = str(text).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def name_key(value):
    """Nombre de marca -> clave comparable. Sin acentos, espacios ni simbolos."""
    return re.sub(r"[^a-z0-9]", "", normalize(value))


# Prefijos de ciudad/región conocidos que aparecen pegados al nombre real
# de la microzona en PITCHDATA (ej. "Bs As CABA (Palermo)" -> "Palermo",
# "Cordoba Centro" -> "Centro") -- pedido explícito de Sabas (vigésima
# segunda vuelta), lista construida a partir de los prefijos que
# realmente se repiten en el archivo real (no una lista inventada).
# Orden de más largo a más corto para que "Bs As CABA" se pruebe antes
# que "Bs As" (si no, "Bs As" comería parte del nombre real de zonas que
# sí empiezan con "Bs As CABA"/"Bs As Norte"/etc.).
_MICROZONA_PREFIJOS = sorted([
    "Bs As CABA", "Bs As Norte", "Bs As Oeste", "Bs As Sur",
    "Cordoba", "Córdoba", "Neuquen", "Neuquén", "Rosario", "Corrientes",
    "Tucuman", "Tucumán", "MDQ", "Mendoza", "Salta", "San Luis", "San Rafael",
], key=len, reverse=True)


def _corregir_encoding_microzona(texto):
    """
    Corrige acentos rotos por un problema de doble-codificación UTF-8 en
    PITCHDATA (ej. "Alta CÃ³rdoba" -> "Alta Córdoba", "Roque Saenz
    PeÃÂ±a" -> "Roque Saenz Peña") -- pedido explícito de Sabas: se
    reinterpreta el texto como si hubiera sido decodificado con Latin-1
    cuando en realidad era UTF-8, revirtiendo el error. Si el texto no
    tiene el patrón roto (Ã seguido de otro caracter), se devuelve tal
    cual -- nunca rompe un texto que ya estaba bien.
    """
    if not texto or "Ã" not in texto:
        return texto
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def limpiar_microzona(texto):
    """
    Quita el prefijo de ciudad conocido (si lo tiene) y corrige el
    encoding -- pedido explícito de Sabas (vigésima segunda vuelta):
      - "Bs As CABA (Palermo)" -> "Palermo"
      - "Cordoba Centro" -> "Centro"
      - "Bs As Norte Acassuso" -> "Acassuso"
      - "Belgrano" -> "Belgrano" (sin prefijo reconocible, se deja tal cual)
      - "ALVARADO_PULLAY" -> "ALVARADO_PULLAY" (idem, guiones/guiones bajos
        se dejan tal cual si no hay prefijo de ciudad que quitar)
    """
    if not texto:
        return ""
    t = _corregir_encoding_microzona(str(texto).strip())
    for prefijo in _MICROZONA_PREFIJOS:
        if t.startswith(prefijo):
            resto = t[len(prefijo):].strip()
            resto = resto.strip("()").strip()
            if resto:
                return resto
    return t


def brand_key(value, default_country=PAIS):
    """
    Cualquier forma de ID -> clave canonica PAIS+NUMERO.
      'AR16516' / 'AR-16516' / 16516 / 16516.0 -> 'AR16516'
      'UY13823' -> 'UY13823'
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    if text in ("", "NAN", "NONE", "NAT"):
        return ""

    m = re.search(r"\b([A-Z]{2})\s*-?\s*(\d+)\b", text)
    if m:
        return f"{m.group(1)}{int(m.group(2))}"

    m = re.search(r"(\d+)", text.replace(".0", ""))
    if m:
        return f"{default_country}{int(m.group(1))}"
    return ""


def pick_col(df, *candidates):
    norm_map = {normalize(c): c for c in df.columns}
    for cand in candidates:
        if normalize(cand) in norm_map:
            return norm_map[normalize(cand)]
    for cand in candidates:
        c = normalize(cand)
        for nk, real in norm_map.items():
            if c in nk:
                return real
    return None


def to_num(value, default=0.0):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s in ("", "-", "?", "N/D", "nan"):
        return default
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^\d,.\-]", "", s)
    if s.count(",") and s.count("."):
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif s.count(","):
        s = s.replace(",", ".") if len(s.split(",")[-1]) <= 2 else s.replace(",", "")
    try:
        n = float(s)
        return -n if neg else n
    except Exception:
        return default


def _drop_junk(df, col):
    """Saca filas 'Total' / 'Filtros aplicados' que los exports dejan al final."""
    if col is None or col not in df.columns:
        return df

    def _is_junk(v):
        s = str(v).strip().lower()
        return s in ("", "nan") or any(s.startswith(j) for j in _JUNK)

    return df[~df[col].map(_is_junk).astype(bool)].copy()


PARQUET_DIR = os.path.join(DATA_DIR, "_parquet_cache")


def _parquet_path(kind, **kwargs):
    """
    Un archivo .parquet por hoja. Si la hoja se lee con kwargs distintos
    (ej. PROD TARGET usa skiprows=1), se agregan al nombre para no mezclar
    dos lecturas distintas de la misma hoja en el mismo archivo.
    """
    nombre = SHEETS[kind].replace(" ", "_").replace("%", "pct")
    if kwargs:
        extra = "_".join(f"{k}{v}" for k, v in sorted(kwargs.items()))
        nombre = f"{nombre}__{extra}"
    return os.path.join(PARQUET_DIR, f"{nombre}.parquet")


def _read(kind, **kwargs):
    """
    Lectura de hojas con cache en Parquet (auditoria de rendimiento,
    agosto 2026). pd.read_excel era el 95% del tiempo de arranque de la
    app: la hoja AVA sola tardaba 11.4s de los 11.6s totales de
    load_availability -- el procesamiento (apply/groupby) es apenas 0.2s.
    Medido: AVA en XLSX 11.42s vs Parquet 0.22s = 52x mas rapido. Con
    todas las hojas, el arranque en frio baja de ~60s a ~2s.

    Como funciona: la primera lectura de cada hoja la saca del XLSX y deja
    un .parquet en data/_parquet_cache/. Las siguientes leen ese archivo.
    El cache se invalida SOLO comparando el mtime del XLSX contra el del
    parquet -- al subir un Excel nuevo, los parquet viejos quedan
    desactualizados y se regeneran solos, sin que haya que borrarlos a
    mano ni acordarse de correr ningun script.

    Si pyarrow no esta instalado o falla la escritura, cae al XLSX de
    siempre sin romper nada (el cache es una optimizacion, no un
    requisito). Agregar `pyarrow>=14` a requirements.txt para activarlo.
    """
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame()

    pq_path = _parquet_path(kind, **kwargs)
    try:
        if os.path.exists(pq_path) and os.path.getmtime(pq_path) >= os.path.getmtime(WORKBOOK):
            return pd.read_parquet(pq_path)
    except Exception:
        pass  # parquet corrupto o pyarrow ausente -> se relee del XLSX

    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS[kind], **kwargs)
    except Exception as e:
        _issue(SHEETS[kind], e)
        return pd.DataFrame()

    try:
        os.makedirs(PARQUET_DIR, exist_ok=True)
        df_pq = df.copy()
        # 1) Los nombres de columna deben ser str: algunas hojas traen
        #    columnas sin nombre (NaN) o numericas.
        df_pq.columns = [str(c) for c in df_pq.columns]
        # 2) Las columnas "object" con tipos MEZCLADOS rompen parquet, que
        #    es estrictamente tipado (bug real: ASIGNACION.TELEFONO tiene
        #    numeros y strings tipo "1151637677/49527206" en la misma
        #    columna -> "Could not convert with type str: tried to convert
        #    to int64"). Se fuerzan a str: igual todo el codigo que las
        #    consume pasa por to_num()/brand_key()/astype(str), asi que no
        #    cambia el resultado de ninguna funcion.
        for col in df_pq.columns:
            if df_pq[col].dtype == "object":
                df_pq[col] = df_pq[col].astype(str)
        df_pq.to_parquet(pq_path, index=False)
    except Exception:
        pass  # sin pyarrow o sin permisos de escritura -> sigue sin cache

    return df


def fmt_money(v, currency="ARS"):
    """
    Formatea un monto con el prefijo de moneda que corresponda. currency
    es literal ("ARS", "UYU", etc.), no convierte nada -- cada farmer ve
    su GMV en la moneda nativa de su pais, sin conversion cruzada.
    """
    return f"{currency} $ {to_num(v):,.0f}".replace(",", ".")


def fmt_money_compact(v, currency="ARS"):
    """
    Version abreviada de fmt_money para espacios chicos (los 3 puntos de
    mes del sparkline en metric_trend_card) -- "ARS $ 10.644.881" (16+
    caracteres, se corta con "..." en 1/3 de card) pasa a "$10,6M" (6
    caracteres). Pedido explícito de Sabas (septiembre 2026, quinta
    vuelta): con 3 cards por fila (Órdenes/AOV/GMV) el monto completo ya
    no entra legible en el pie del sparkline.

    Umbrales: >=1.000.000 -> "X,XM"; >=1.000 -> "X,XK"; si no, el numero
    entero tal cual (sin prefijo de moneda -- el simbolo "$" solo alcanza
    para identificarlo como monto, la moneda especifica ya se ve en el
    valor grande de la card).
    """
    n = to_num(v)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        texto = f"{n / 1_000_000:.1f}M".replace(".", ",")
    elif n >= 1_000:
        texto = f"{n / 1_000:.1f}K".replace(".", ",")
    else:
        texto = f"{n:,.0f}".replace(",", ".")
    return f"{sign}${texto}"


def fmt_ars(v):
    """Wrapper de compatibilidad: todo el codigo viejo que ya llama fmt_ars
    (16+ lugares en wingmanapp.py, mas usos internos aca) sigue funcionando
    igual para el equipo AR. Para farmers en otra moneda (ver
    FARMER_CURRENCY) usar fmt_money(v, currency) directamente."""
    return fmt_money(v, "ARS")


# El "USD $ X" de referencia chiquito bajo el GMV se elimino (pedido
# explicito de Sabas, agosto 2026): dependia de ARS_PER_USD, una tasa fija
# que solo tenia sentido para ARS y no escalaba a otras monedas (UYU, CLP)
# a medida que el equipo crece a Cono Sur. Ver metric_trend_card en
# wingmanapp.py -- ya no llama a esta conversion.


def fmt_pct(v, decimals=1):
    return f"{to_num(v):.{decimals}f}%"


def fmt_roi(v):
    n = to_num(v)
    return f"{n:.1f}x" if n > 0 else "-"


def fmt_delta(v):
    """v viene como fraccion (0.24 -> +24%)."""
    return f"{to_num(v) * 100:+.0f}%"


def google_search_url(brand_name, category="", city=""):
    """
    Arma una URL de busqueda de Google con nombre + categoria + ciudad + pais,
    para encontrar el local: nombre, direccion y mapa.

    El telefono se saca a proposito: Growth OS lo incluia en el query y eso es
    un bug conocido ahi -- buscar por telefono tapa los resultados reales del
    restaurante con paginas de validacion de numero. Wingman no lo repite.
    """
    parts = [str(brand_name).strip()]
    if category and str(category).strip() not in ("", "-"):
        parts.append(str(category).strip())
    if city and str(city).strip() not in ("", "-"):
        parts.append(str(city).strip())
    if PORTFOLIO_COUNTRY:
        parts.append(PORTFOLIO_COUNTRY)
    query = " ".join(p for p in parts if p)
    return "https://www.google.com/search?q=" + quote_plus(query)


# =========================
# ASIGNACION
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_asignacion(pais=None):
    """
    pais=None usa el PAIS global (comportamiento de siempre, AR). Se
    parametrizo para poder pedir "UY" (Maria Pedraza) sin duplicar toda
    la funcion -- ver FARMER_PAIS_OVERRIDE / farmer_pais().
    """
    filtro_pais = pais or PAIS
    df = _read("asignacion")
    if df.empty:
        return df

    c_id    = pick_col(df, "COUNTRY_BRAND_ID", "brand id", "bid")
    c_name  = pick_col(df, "BRAND_NAME", "brand name")
    c_tel   = pick_col(df, "TELEFONO", "phone")
    c_mail  = pick_col(df, "MAIL", "email", "correo")
    c_owner = pick_col(df, "BRAND_OWNER_EMAIL_NUEVO", "brand owner email", "farmer")

    if not c_id or not c_owner:
        _issue("ASIGNACION", "Falta COUNTRY_BRAND_ID o BRAND_OWNER_EMAIL_NUEVO")
        return pd.DataFrame()

    c_coinv = pick_col(df, "coinversion", "tipo coinversion")
    if not c_coinv:
        unnamed = [c for c in df.columns if normalize(c).startswith("unnamed")]
        c_coinv = unnamed[-1] if unnamed else None

    out = pd.DataFrame()
    out["key"]         = df[c_id].apply(brand_key)
    out["brand_id"]    = df[c_id].astype(str).str.strip()
    out["brand_name"]  = df[c_name].astype(str).str.strip() if c_name else "-"
    out["telefono"]    = df[c_tel].astype(str).str.strip() if c_tel else ""
    out["mail"]        = df[c_mail].astype(str).str.strip() if c_mail else ""
    out["farmer"]      = df[c_owner].astype(str).str.strip().str.lower()
    out["coinversion"] = df[c_coinv].astype(str).str.strip() if c_coinv else ""

    out = out[out["key"] != ""]
    out = out[out["key"].str.startswith(filtro_pais)].copy()
    out["nkey"] = out["brand_name"].apply(name_key)
    # fillna antes de astype: en pandas 3 un NaN sobrevive al astype(str) y despues
    # rompe cualquier sorted() que mezcle float con str.
    for c in ("telefono", "mail", "coinversion"):
        out[c] = out[c].fillna("").astype(str).str.strip()
        out[c] = out[c].replace({"nan": "", "NaN": "", "0": "", "None": ""})

    # Parseo del grupo de coinversion: nuestro export trae solo "5. Prioritized"
    # o "6. Rest" (sin el prefijo SI/NO de habilitacion que tiene Growth OS).
    # Se quita el numero inicial y se cruza contra COINV_GROUPS. Sabas confirmo
    # asumir que TODA marca con grupo asignado (menos Churn) tiene coinversion
    # potencialmente disponible, ya que no tenemos el flag real de habilitacion.
    out["coinv_group_key"] = out["coinversion"].apply(_parse_status_grupo)
    out["coinv_has"] = out["coinv_group_key"].apply(
        lambda k: bool(k) and isinstance(k, str) and k in COINV_GROUPS and COINV_GROUPS[k]["has_coinv"]
    )
    return out.drop_duplicates(subset=["key"]).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def list_farmers():
    df = load_asignacion()
    if df.empty:
        return []
    return sorted(df.groupby("farmer").size().to_dict().items(), key=lambda kv: kv[0])


def list_farmers_activos():
    """
    Lista de correos habilitados para LOGIN en Wingman -- distinta de
    list_farmers(), que sigue reflejando la cartera cruda de ASIGNACION
    filtrada solo a AR.

    Equipo real = (farmers AR de ASIGNACION - EQUIPO_BAJA)
                  + EQUIPO_ALTA_SIN_ASIGNACION
                  + FARMER_PAIS_OVERRIDE (Maria/UY: SI tiene fila en
                    ASIGNACION, pero con pais UY -- list_farmers() no la
                    ve porque solo mira AR, hay que sumarla a mano aca).

    Devuelve solo la lista de emails (sin conteo de marcas, porque los de
    alta sin ASIGNACION no tienen ese conteo disponible por esta via -- para
    su cantidad de marcas hay que mirar load_detalle_portfolio).
    """
    asig_emails = {e for e, _ in list_farmers()}
    activos = (asig_emails - EQUIPO_BAJA) | EQUIPO_ALTA_SIN_ASIGNACION | set(FARMER_PAIS_OVERRIDE.keys())
    return sorted(activos)


def farmers_por_pais(pais):
    """
    Lista de farmers activos cuyo pais (via farmer_pais) coincide con el
    pedido. Usado para la vista de Supervisor (mapa de Cono Sur): al
    clickear un pais, se agregan Brand Coverage / Contact Performance /
    Conversion solo de los farmers de ese pais.
    """
    return sorted(f for f in list_farmers_activos() if farmer_pais(f) == pais)



def farmer_display(email):
    local = str(email).split("@")[0]
    return " ".join(p.capitalize() for p in local.replace(".", " ").split())


def farmer_initials(email):
    """sabas.ramirez@rappi.com -> SR"""
    parts = str(email).split("@")[0].replace(".", " ").split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


# Excepción puntual a la regla por default (usuario antes del @) --
# pedido explícito de Sabas (agosto 2026): la clave de Fabián como
# Supervisor queda fija en "wingsup2026", no "fabian.ayala". Es la única
# excepción hoy; se resolvió como diccionario (no como caso especial
# hardcodeado dentro de check_password) por si en el futuro hiciera falta
# agregar otra cuenta con clave fija sin tener que tocar la lógica de
# nuevo.
SUPERVISOR_PASSWORD_OVERRIDE = {
    "fabian.ayala@rappi.com": "wingsup2026",
}


def check_password(email, password):
    """Password = la parte antes del @, en minusculas. No es autenticacion real,
    es identificacion con un segundo campo. Ver aviso en README.

    (Se probó agregar cambio de contraseña -- agosto 2026 -- pero se
    revirtió por pedido explícito de Sabas: la única excepción real es
    fabian.ayala, cuya clave de Supervisor quedó fija en "wingsup2026" en
    vez de "fabian.ayala", ver SUPERVISOR_PASSWORD_OVERRIDE mas abajo.)
    """
    local = str(email).strip().lower().split("@")[0]
    override = SUPERVISOR_PASSWORD_OVERRIDE.get(str(email).strip().lower())
    if override:
        return str(password).strip().lower() == override
    return str(password).strip().lower() == local


# =========================
# ADS
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_ads():
    """
    Booking y Revenue de ADS: fuente oficial es EXPORT ADS, no la hoja ADS
    cruda. "Bookings Totales Corregidos" ya viene ajustado por Rappi segun los
    dias que la campana estuvo inactiva -- la hoja ADS (BOOKINGS NET) no tiene
    ese ajuste y da numeros distintos para la misma marca.

    OJO CON LA MONEDA: EXPORT ADS viene en USD (confirmado multiplicando por
    ARS_PER_USD=1400 y comparando el orden de magnitud resultante contra
    Growth OS). Se convierte a ARS aca mismo antes de devolver el DataFrame,
    asi el resto de la app no tiene que acordarse de la conversion.

    ROAS sigue viniendo de la hoja ADS porque EXPORT ADS no lo trae.
    """
    roas_df = _read("ads")
    roas_map = {}
    if not roas_df.empty:
        c_code = pick_col(roas_df, "CODE", "brand id")
        c_roas = pick_col(roas_df, "ROAS")
        if c_code and c_roas:
            roas_df = _drop_junk(roas_df, c_code)
            roas_df["key"] = roas_df[c_code].apply(brand_key)
            roas_df["roas"] = roas_df[c_roas].apply(to_num)
            roas_map = roas_df.groupby("key")["roas"].mean().to_dict()

    df = _read("export_ads")
    if df.empty:
        _issue("EXPORT ADS", "Hoja vacia o no encontrada")
        return pd.DataFrame()

    c_brand = pick_col(df, "BRAND", "brand id")
    if not c_brand:
        _issue("EXPORT ADS", "No encuentro BRAND")
        return pd.DataFrame()

    df = _drop_junk(df, c_brand)
    c_book = pick_col(df, "Bookings Totales Corregidos")
    c_rev  = pick_col(df, "Revenue Real")
    c_att_book = pick_col(df, "% Att. Bookings")
    c_att_rev  = pick_col(df, "% Att. Revenue Real")

    out = pd.DataFrame()
    out["key"]       = df[c_brand].apply(brand_key)
    out["bookings"]  = (df[c_book].apply(to_num) if c_book else 0.0)
    out["revenue"]   = (df[c_rev].apply(to_num) if c_rev else 0.0)
    out["att_booking"] = df[c_att_book].apply(to_num) if c_att_book else 0.0
    out["att_revenue"] = df[c_att_rev].apply(to_num) if c_att_rev else 0.0

    out = out[out["key"] != ""]
    out = out.groupby("key", as_index=False).sum(numeric_only=True)
    # EXPORT ADS viene en USD. Convertimos a ARS para que Booking/Revenue se
    # muestren en la misma moneda que el resto de la ficha (GMV, AOV, etc).
    out["bookings"] = out["bookings"] * ARS_PER_USD
    out["revenue"] = out["revenue"] * ARS_PER_USD
    out["roas"] = out["key"].map(roas_map).fillna(0.0)
    out["sales"] = 0.0  # se mantiene por compatibilidad, EXPORT ADS no lo trae
    return out


# =========================
# AVAILABILITY — diario por store, se agrega a marca
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_availability():
    df = _read("ava")
    if df.empty:
        return df

    c_id   = pick_col(df, "Brand ID")
    c_conf = pick_col(df, "Configured Hours")
    c_avl  = pick_col(df, "Available Hours")
    if not c_id:
        _issue("AVA", "No encuentro Brand ID")
        return pd.DataFrame()

    tmp = pd.DataFrame()
    tmp["key"]  = df[c_id].apply(brand_key)
    tmp["conf"] = df[c_conf].apply(to_num) if c_conf else 0.0
    tmp["avl"]  = df[c_avl].apply(to_num) if c_avl else 0.0
    tmp = tmp[tmp["key"] != ""]

    g = tmp.groupby("key", as_index=False)[["conf", "avl"]].sum()
    # Ponderado por horas configuradas: promediar porcentajes le daria demasiado
    # peso a stores chicos con pocas horas.
    g["availability"] = (g["avl"] / g["conf"] * 100).where(g["conf"] > 0, 0)
    g["lost_hours"]   = (g["conf"] - g["avl"]).clip(lower=0)
    return g[["key", "availability", "lost_hours"]]


@st.cache_data(ttl=86400, show_spinner=False)
def store_to_brand():
    """
    {store_key: brand_key} — sale de AVA, la unica hoja con ambos IDs.

    BUG REAL CORREGIDO (agosto 2026): "Brand ID" y "Store_ID" en AVA son
    numeros PELADOS, sin prefijo de pais (ej. Store_ID=111287.0 para una
    tienda de Uruguay). brand_key() sin contexto de pais cae al default
    global (PAIS="AR"), asi que las 2.947 filas de UY en AVA se estaban
    convirtiendo TODAS a keys "AR..." -- se perdian (no matcheaban contra
    ninguna tienda/marca real de UY) o, peor, podian colisionar con una
    tienda/marca de Argentina que compartiera el mismo numero.

    Fix: AVA SI trae una columna "Country" explicita por fila (a
    diferencia de DETALLE, que no la tenia y necesito _ciudad_a_pais como
    respaldo) -- se usa directo para anteponer el pais real de cada fila
    antes de armar la key, en vez de dejar que brand_key() adivine con el
    default.

    Impacto real medido: con este fix, TOP PRODUCTS pasa de 0 marcas de
    Uruguay reconocidas a la cobertura real de UY que trae el export.
    """
    df = _read("ava")
    if df.empty:
        return {}
    c_b, c_s = pick_col(df, "Brand ID"), pick_col(df, "Store_ID")
    c_pais = pick_col(df, "Country", "country", "pais")
    if not (c_b and c_s):
        return {}
    df = df.dropna(subset=[c_b, c_s]).drop_duplicates(subset=[c_s])

    if c_pais:
        paises = df[c_pais].astype(str).str.strip().str.upper()

        def _key_con_pais_ava(valor, pais):
            solo_num = re.search(r"(\d+)", str(valor))
            if not solo_num:
                return ""
            pais_ok = pais if re.match(r"^[A-Z]{2}$", str(pais)) else PAIS
            return f"{pais_ok}{int(solo_num.group(1))}"

        store_keys = [
            _key_con_pais_ava(v, p) for v, p in zip(df[c_s], paises)
        ]
        brand_keys = [
            _key_con_pais_ava(v, p) for v, p in zip(df[c_b], paises)
        ]
        return dict(zip(store_keys, brand_keys))

    # Sin columna Country (no deberia pasar con el export actual, pero por
    # si el formato cambia de nuevo): comportamiento viejo, default AR.
    return dict(zip(df[c_s].apply(brand_key), df[c_b].apply(brand_key)))


# =========================
# MARKDOWN / MARKDOWN PRO
# =========================

def _load_md(kind):
    df = _read(kind)
    if df.empty:
        return df
    c_id = pick_col(df, "BRAND ID")
    if not c_id:
        _issue(SHEETS[kind], "No encuentro BRAND ID")
        return pd.DataFrame()

    df = _drop_junk(df, c_id)
    if kind == "md_pro":
        specs = [("gmv", "GMV TOTAL $"), ("markdown", "MARKDOWN PRO USR $"),
                 ("sales", "SALES MD PRIME"), ("campaigns", "CAMPAIGNS PRO #"),
                 ("coinv", "Coinvestment MD Prime")]
        c_roi = pick_col(df, "ROI MD PRIME")
    else:
        specs = [("gmv", "GMV TOTAL $"), ("markdown", "MARKDOWN $"),
                 ("sales", "SALES MD $"), ("campaigns", "Campaings #"),
                 ("coinv", "MD CO-INVESTMENT $")]
        c_roi = pick_col(df, "ROI")

    out = pd.DataFrame()
    out["key"] = df[c_id].apply(brand_key)
    for name, cand in specs:
        c = pick_col(df, cand)
        out[name] = df[c].apply(to_num) if c else 0.0
    out["_roi_w"] = (df[c_roi].apply(to_num) if c_roi else 0.0) * out["markdown"]

    out = out[out["key"] != ""]
    g = out.groupby("key", as_index=False).sum(numeric_only=True)
    # ROI ponderado por inversion, no promedio simple.
    g["roi"] = (g["_roi_w"] / g["markdown"]).where(g["markdown"] > 0, 0)
    return g[["key", "gmv", "markdown", "sales", "campaigns", "coinv", "roi"]]


@st.cache_data(ttl=86400, show_spinner=False)
def load_md():
    return _load_md("md")


@st.cache_data(ttl=86400, show_spinner=False)
def load_md_pro():
    return _load_md("md_pro")


# =========================
# DETALLE — GMV, AOV, Categoria (ya viene agregado a nivel marca)
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def _numero_a_pais():
    """
    (Auditoria de rendimiento agosto 2026: esta funcion NO tenia cache y
    releia ASIGNACION completa en cada llamada -- 1.76s por llamada, y se
    llama desde _load_detalle_like, que corre para DETALLE y LAST GMV.)

    Mapa {numero_id: pais} construido desde ASIGNACION (que SI trae el
    pais explicito en COUNTRY_BRAND_ID, ej. "UY13823"). Necesario porque
    el export nuevo de DETALLE trae "Brand" como "13823 - Nombre", SIN
    prefijo de pais -- brand_key() sola no puede distinguir un numero UY
    de uno AR ahi, y por default asumiria PAIS="AR" para todos, mezclando
    la cartera de Maria (UY) con Argentina.

    Colision conocida: 2 numeros (de ~2900 marcas) existen en mas de un
    pais en el export actual (13945, 13962). Para esos, gana el que
    aparece primero al recorrer ASIGNACION -- riesgo aceptado, no hay forma
    de distinguirlos sin mas contexto y son 2 casos sobre casi 3000.
    """
    asig_raw = _read("asignacion")
    if asig_raw.empty:
        return {}
    c_id = pick_col(asig_raw, "COUNTRY_BRAND_ID", "brand id", "bid")
    if not c_id:
        return {}
    mapa = {}
    for raw_id in asig_raw[c_id].dropna():
        text = str(raw_id).strip().upper()
        m = re.search(r"^([A-Z]{2})(\d+)$", text) or re.search(r"^([A-Z]{2})\s*-?\s*(\d+)", text)
        if m:
            numero = str(int(m.group(2)))
            mapa.setdefault(numero, m.group(1))
    return mapa


# Respaldo para cuando _numero_a_pais() no resuelve nada (caso CL, agosto
# 2026): CL no tiene NINGUNA fila en ASIGNACION todavia -- a diferencia de
# UY, que si tenia 180 filas ahi -- asi que el mapa por numero queda vacio
# para todas sus marcas y sin esto caerian al default PAIS="AR", mezclando
# Santiago/Viña del Mar/Concepcion con la cartera Argentina real (bug
# detectado con data real: "AR10044" en Santiago de Chile).
#
# Nota: "Los Angeles" aca es la comuna real de la Region del Biobio, Chile
# -- no la ciudad de EEUU -- por si alguien lo mira de nuevo mas adelante
# y le llama la atencion.
_CIUDAD_A_PAIS = {
    # Argentina
    "buenos aires": "AR", "cordoba": "AR", "la plata": "AR", "rosario": "AR",
    "mar del plata": "AR", "san luis": "AR", "parana": "AR", "neuquen": "AR",
    "santafe": "AR", "posadas": "AR", "mendoza": "AR", "la rioja": "AR",
    "san juan": "AR", "resistencia": "AR", "san miguel de tucuman": "AR",
    "tandil": "AR", "rio cuarto": "AR", "santiago del estero": "AR",
    "bahia blanca": "AR", "corrientes": "AR", "villa carlos paz": "AR",
    "salta": "AR", "san salvador de jujuy": "AR", "bariloche": "AR",
    # Chile
    "santiago de chile": "CL", "vina del mar": "CL", "concepcion": "CL",
    "antofagasta": "CL", "la serena": "CL", "rancagua": "CL", "iquique": "CL",
    "temuco": "CL", "puerto montt": "CL", "copiapo": "CL", "talca": "CL",
    "los angeles": "CL", "chillan": "CL", "arica": "CL", "valdivia": "CL",
    "curico": "CL", "quillota": "CL", "calama": "CL", "puerto varas": "CL",
    # Uruguay
    "montevideo": "UY",
}


def _ciudad_a_pais(ciudad):
    """normalize() saca acentos/mayusculas antes de buscar en _CIUDAD_A_PAIS."""
    if not ciudad:
        return None
    return _CIUDAD_A_PAIS.get(normalize(str(ciudad)).strip())




def _load_detalle_like(kind):
    """
    DETALLE y LAST GMV. Soporta dos formatos de export, detectados por
    columnas presentes:

    FORMATO VIEJO (Brand_ID, Brand_Name, Categoria, Ciudad, Farmer, N_Stores,
    GMV, Ordenes, AOV) -- todo explicito, una fila = una marca ya agregada.

    FORMATO NUEVO (Territorio, Ciudad, Categoria, Brand, Store, Correo, GMV,
    Ordenes) -- "Brand" trae "12345 - Nombre" (el ID va embebido, brand_key
    ya lo extrae solo); no hay Brand_ID ni AOV; una fila = una tienda, puede
    haber varias filas por marca (multi-local), asi que GMV/Ordenes se
    agregan sumando por marca y N_Stores se deriva contando "Store" unicos.
    Trae ademas "Correo" (email del farmer): se expone como "farmer_detalle"
    para poder armar cartera de farmers que aun no tienen fila en ASIGNACION
    (ver load_detalle_portfolio). El pie de pagina tipo "Filtros aplicados"
    que este export deja en Territorio ya lo saca _drop_junk mas abajo via _read.
    """
    df = _read(kind)
    if df.empty:
        return df

    c_id_viejo = pick_col(df, "Brand_ID", "brand id")
    c_brand_nuevo = pick_col(df, "Brand") if not c_id_viejo else None
    c_id = c_id_viejo or c_brand_nuevo
    if not c_id:
        _issue(SHEETS[kind], "No encuentro Brand_ID ni Brand")
        return pd.DataFrame()

    c_cat = pick_col(df, "Categoria", "categoría")
    c_gmv = pick_col(df, "GMV")
    c_ord = pick_col(df, "Ordenes", "órdenes")
    c_ciudad = pick_col(df, "Ciudad", "city")
    c_aov = pick_col(df, "AOV")  # solo formato viejo
    c_stores = pick_col(df, "N_Stores", "n stores", "stores") if c_id_viejo else None
    c_store_nombre = pick_col(df, "Store") if c_brand_nuevo else None  # formato nuevo: nombre de tienda, para contar
    c_correo = pick_col(df, "Correo", "farmer", "email") if c_brand_nuevo else None  # formato nuevo trae farmer aca

    raw = pd.DataFrame()
    if c_id_viejo:
        # Formato viejo: el ID ya trae el pais explicito (ej. "UY13823"),
        # brand_key() lo resuelve solo sin ambiguedad.
        raw["key"] = df[c_id_viejo].apply(brand_key)
    else:
        # Formato nuevo: "Brand" = "13823 - Nombre", SIN prefijo de pais.
        #
        # IMPORTANTE (bug real encontrado con data real, agosto 2026): el
        # numero de "Brand" NO es unico entre paises en este export -- ej.
        # "14164" es "Soylu Gluten Free" en Buenos Aires (AR, real en
        # ASIGNACION) Y "Señora Mila" en Montevideo (UY, marca de Maria) al
        # mismo tiempo, en filas distintas. Cruzar solo por numero contra
        # ASIGNACION (_numero_a_pais) puede pegarle el pais equivocado a
        # una fila cuyo numero coincide con el de OTRA marca en otro pais.
        #
        # Por eso el pais se resuelve en este orden, de mas a menos confiable:
        #   1) _ciudad_a_pais(): la Ciudad es un dato DE ESA FILA especifica
        #      (Santiago de Chile, Montevideo, Buenos Aires...) y no depende
        #      del numero, asi que no sufre la colision. Gana siempre que
        #      la ciudad matchee algo conocido.
        #   2) _numero_a_pais(): cruce contra ASIGNACION, solo como respaldo
        #      cuando la ciudad viene vacia/no catalogada (ej. "N/A").
        #   3) PAIS global, ultimo recurso si ninguno de los dos resuelve.
        mapa_pais = _numero_a_pais()
        col_ciudad_tmp = df[c_ciudad].astype(str).str.strip() if c_ciudad else pd.Series([""] * len(df), index=df.index)

        def _key_con_pais(idx, texto):
            solo_num = re.search(r"(\d+)", str(texto))
            if not solo_num:
                return ""
            numero = solo_num.group(1)
            pais = _ciudad_a_pais(col_ciudad_tmp.get(idx, "")) or mapa_pais.get(numero) or PAIS
            return f"{pais}{int(numero)}"

        raw["key"] = pd.Series(
            [_key_con_pais(idx, val) for idx, val in df[c_id].items()], index=df.index
        )
    raw = raw[raw["key"] != ""]
    raw["categoria_detalle"] = df.loc[raw.index, c_cat].astype(str).str.strip() if c_cat else ""
    raw["gmv"] = df.loc[raw.index, c_gmv].apply(to_num) if c_gmv else 0.0
    raw["ordenes"] = df.loc[raw.index, c_ord].apply(to_num) if c_ord else 0.0
    raw["ciudad"] = df.loc[raw.index, c_ciudad].astype(str).str.strip() if c_ciudad else ""

    if c_id_viejo:
        # Formato viejo: ya viene agregado a nivel marca, una fila = una marca.
        raw["aov"] = df.loc[raw.index, c_aov].apply(to_num) if c_aov else 0.0
        raw["n_stores"] = df.loc[raw.index, c_stores].apply(to_num) if c_stores else 0.0
        raw["farmer_detalle"] = ""
        raw["brand_name_detalle"] = ""
        out = raw.drop_duplicates(subset=["key"]).reset_index(drop=True)
    else:
        # Formato nuevo: una fila = una tienda. Se agrega por marca.
        # brand_name_detalle: "72087 - Ayguacamolee" -> "Ayguacamolee" (se
        # quita el prefijo numerico y el separador; si no matchea el patron
        # se deja el texto tal cual, mejor eso que perder el nombre).
        raw["farmer_detalle"] = (
            df.loc[raw.index, c_correo].astype(str).str.strip().str.lower() if c_correo else ""
        )
        raw["store_nombre"] = df.loc[raw.index, c_store_nombre].astype(str).str.strip() if c_store_nombre else ""
        raw_brand_text = df.loc[raw.index, c_brand_nuevo].astype(str).str.strip()
        raw["brand_name_detalle"] = raw_brand_text.str.replace(r"^\d+\s*-\s*", "", regex=True).str.strip()

        agg = raw.groupby("key").agg(
            categoria_detalle=("categoria_detalle", "first"),
            gmv=("gmv", "sum"),
            ordenes=("ordenes", "sum"),
            ciudad=("ciudad", "first"),
            farmer_detalle=("farmer_detalle", "first"),
            brand_name_detalle=("brand_name_detalle", "first"),
            n_stores=("store_nombre", "nunique"),
        ).reset_index()
        agg["aov"] = (agg["gmv"] / agg["ordenes"]).where(agg["ordenes"] > 0, 0.0)
        out = agg

    return out.drop_duplicates(subset=["key"]).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
@st.cache_data(ttl=86400, show_spinner=False)
def load_pitchdata():
    """
    {key: {microzona, telefono, contacto, take_rate, link, ultima_conexion,
    ultima_orden}} -- una fila por STORE (no por marca), a diferencia del
    resto de las hojas de Wingman que ya vienen a nivel Brand. Se agrega
    directamente el dict por Store ID (numero puro, sin prefijo de pais --
    ver brand_key sobre solo el numero) porque el cruce real hacia una
    marca necesita pasar por DETALLE (Brand -> lista de Store), que puede
    tener varias tiendas por marca -- eso lo resuelve tienda_referencia_for
    más abajo, no esta función.

    Hoja nueva (vigésima segunda vuelta, pedido explícito de Sabas):
    antes vivía en un archivo Excel aparte (Librfffffo1.xlsx) que Sabas
    subió para validar el cruce a mano -- ahora está pegada como hoja
    PITCHDATA del Excel grande. Columnas reales: Store ID, Nombre,
    Ciudad, Microzona, Última Conexión, %Take Rate, Nombre contacto
    store, Teléfono store, Última Orden, Link Tienda.
    """
    df = _read("pitchdata")
    if df.empty:
        return {}
    c_store = pick_col(df, "Store ID", "store id")
    c_micro = pick_col(df, "Microzona")
    c_conn  = pick_col(df, "Última Conexión", "ultima conexion")
    c_take  = pick_col(df, "%Take Rate", "take rate")
    c_cont  = pick_col(df, "Nombre contacto store", "nombre contacto")
    c_tel   = pick_col(df, "Teléfono store", "telefono store")
    c_ord   = pick_col(df, "Última Orden", "ultima orden")
    c_link  = pick_col(df, "Link Tienda", "link tienda")
    if not c_store:
        return {}

    out = {}
    for _, r in df.iterrows():
        raw_id = r.get(c_store)
        m = re.search(r"(\d+)", str(raw_id or ""))
        if not m:
            continue
        sid = int(m.group(1))
        out[sid] = {
            "microzona": str(r.get(c_micro) or "").strip() if c_micro else "",
            "ultima_conexion": r.get(c_conn) if c_conn else None,
            "take_rate": to_num(r.get(c_take), default=None) if c_take else None,
            "contacto": str(r.get(c_cont) or "").strip() if c_cont else "",
            "telefono": str(r.get(c_tel) or "").strip() if c_tel else "",
            "ultima_orden": r.get(c_ord) if c_ord else None,
            "link": str(r.get(c_link) or "").strip() if c_link else "",
        }
    return out


@st.cache_data(ttl=86400, show_spinner=False)
def load_toprest():
    """
    {key: {tier_actual, mes_actual, tier_anterior, mes_anterior}} -- por
    Store ID (mismo patrón que load_pitchdata, una fila por tienda).

    Hoja nueva (vigésima segunda vuelta, pedido explícito de Sabas):
    antes vivía en TOPREST.xlsx, ahora pegada como hoja TOPREST del Excel
    grande. Columnas reales: Store ID, Store Name, Top Res ACTUAL, Mes
    ACTUAL, Top Res ANTERIOR, Mes ANTERIOR. Top Res ACTUAL/ANTERIOR vienen
    con el tier PRECEDIDO por un número + guion ("1.-Oro", "2.-Plata",
    "3.-Basico", "4.-Alerta") -- se guarda tal cual, el número al inicio
    ya funciona como el orden de mejor a peor sin tener que armar un
    mapeo aparte en el código.
    """
    df = _read("toprest")
    if df.empty:
        return {}
    c_store = pick_col(df, "Store ID", "store id")
    c_actual = pick_col(df, "Top Res ACTUAL", "top res actual")
    c_mes_actual = pick_col(df, "Mes ACTUAL", "mes actual")
    c_anterior = pick_col(df, "Top Res ANTERIOR", "top res anterior")
    c_mes_anterior = pick_col(df, "Mes ANTERIOR", "mes anterior")
    if not c_store:
        return {}

    out = {}
    for _, r in df.iterrows():
        raw_id = r.get(c_store)
        m = re.search(r"(\d+)", str(raw_id or ""))
        if not m:
            continue
        sid = int(m.group(1))
        tier_actual = str(r.get(c_actual) or "").strip() if c_actual else ""
        tier_anterior = str(r.get(c_anterior) or "").strip() if c_anterior else ""
        out[sid] = {
            "tier_actual": tier_actual if tier_actual and tier_actual.lower() != "none" else "",
            "mes_actual": r.get(c_mes_actual) if c_mes_actual else None,
            "tier_anterior": tier_anterior if tier_anterior and tier_anterior.lower() != "none" else "",
            "mes_anterior": r.get(c_mes_anterior) if c_mes_anterior else None,
        }
    return out


def tienda_referencia_for(brand_key_str, farmer_email=None):
    """
    Encuentra la Store ID "de referencia" de una marca para leer PITCHDATA
    (contacto, link, microzona) -- pedido explícito de Sabas (vigésima
    segunda vuelta), mismo criterio para las 3 cosas:
      1) La tienda de DETALLE cuyo Teléfono store (normalizado, últimos
         10 dígitos) coincide con el PHONE ALIADO de ASIGNACION.
      2) Si ninguna coincide, cualquiera de las tiendas de DETALLE
         asignadas al mismo Farmer que la marca (ya filtra por Farmer
         real, nunca se cuela una tienda de otro).
      3) Si la marca no tiene ninguna tienda en DETALLE, no hay
         referencia -- devuelve None, sin inventar nada.

    Devuelve el Store ID (numero) de referencia, o None.
    """
    return _tienda_referencia_for_impl(brand_key_str)


def _normalizar_telefono_10(v):
    """Últimos 10 dígitos -- comparación robusta entre formatos de
    teléfono distintos (+54, 54, 549, 011, etc.), mismo criterio ya
    validado a mano por Sabas en el análisis de teléfonos múltiples."""
    if v is None or str(v).strip().upper() in ("", "#N/D", "NAN"):
        return None
    s = re.sub(r"\D", "", str(v))
    if len(s) < 8:
        return None
    return s[-10:] if len(s) >= 10 else s


@st.cache_data(ttl=86400, show_spinner=False)
def _detalle_brand_to_stores():
    """{brand_key: [store_id_num, ...]} y {brand_key: farmer_email} -- del
    Brand/Store crudos de DETALLE (num, sin prefijo pais), para uso
    interno de tienda_referencia_for. Separado de load_detalle() (que ya
    agrega por marca con otras columnas) para no tocar esa función."""
    df = _read("detalle")
    if df.empty:
        return {}, {}
    c_brand = pick_col(df, "Brand")
    c_store = pick_col(df, "Store")
    c_mail = pick_col(df, "Correo", "Email")
    if not (c_brand and c_store):
        return {}, {}

    brand_to_stores = {}
    brand_to_farmer = {}
    for _, r in df.iterrows():
        brand_txt, store_txt = r.get(c_brand), r.get(c_store)
        if not brand_txt or not store_txt:
            continue
        m_brand = re.match(r"^(\d+)", str(brand_txt).strip())
        m_store = re.match(r"^(\d+)", str(store_txt).strip())
        if not (m_brand and m_store):
            continue
        bkey = brand_key(m_brand.group(1))
        brand_to_stores.setdefault(bkey, []).append(int(m_store.group(1)))
        if c_mail:
            farmer = r.get(c_mail)
            if farmer:
                brand_to_farmer[bkey] = str(farmer).strip().lower()
    return brand_to_stores, brand_to_farmer


def _tienda_referencia_for_impl(brand_key_str):
    brand_to_stores, brand_to_farmer = _detalle_brand_to_stores()
    stores = brand_to_stores.get(brand_key_str, [])
    if not stores:
        return None

    pitch = load_pitchdata()

    # Paso 1: telefono de ASIGNACION para esta marca
    tel_asig = _telefono_asignacion_for(brand_key_str)
    tel_asig_norm = _normalizar_telefono_10(tel_asig)
    if tel_asig_norm:
        for sid in stores:
            data = pitch.get(sid)
            if data and _normalizar_telefono_10(data.get("telefono")) == tel_asig_norm:
                return sid

    # Paso 2: cualquiera del mismo Farmer (ya filtrado -- brand_to_farmer
    # viene de DETALLE, que es Store->Farmer real, no hace falta re-chequear).
    for sid in stores:
        if sid in pitch:
            return sid
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def _telefono_asignacion_by_key():
    """{brand_key: telefono_crudo} de ASIGNACION (PHONE ALIADO) -- helper
    interno para tienda_referencia_for, separado para no duplicar la
    lectura de ASIGNACION que ya hace portfolio_for."""
    df = _read("asignacion")
    if df.empty:
        return {}
    c_id = pick_col(df, "COUNTRY_BRAND_ID")
    c_tel = pick_col(df, "PHONE ALIADO")
    if not (c_id and c_tel):
        return {}
    out = {}
    for _, r in df.iterrows():
        bid = r.get(c_id)
        if bid is None:
            continue
        out[brand_key(bid)] = r.get(c_tel)
    return out


def _telefono_asignacion_for(brand_key_str):
    return _telefono_asignacion_by_key().get(brand_key_str)


@st.cache_data(ttl=86400, show_spinner=False)
def load_detalle():
    return _load_detalle_like("detalle")


@st.cache_data(ttl=86400, show_spinner=False)
def load_last_gmv():
    """GMV/AOV del mes anterior, para calcular variacion vs mes actual."""
    return _load_detalle_like("last_gmv")


@st.cache_data(ttl=86400, show_spinner=False)
def load_previous_gmv():
    """
    GMV/AOV de hace DOS meses (no del mes anterior -- ese es LAST GMV).
    Ej.: si DETALLE es septiembre, LAST GMV es agosto y PREVIOUS GMV es
    julio. Usada junto con LAST GMV y DETALLE para armar la comparativa
    de 3 meses reales en las cards de GMV/AOV (pedido explicito de
    Sabas, septiembre 2026): antes esas cards solo mostraban 2 puntos
    (Anterior/Actual = mes pasado vs mes en curso); ahora muestran 3
    meses reales nombrados por el mes calendario que representan.
    """
    return _load_detalle_like("previous_gmv")


_MESES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def etiquetas_3_meses():
    """
    Nombres cortos en español de los 3 meses que arma la comparativa de
    GMV/AOV: (mes de PREVIOUS GMV, mes de LAST GMV, mes de DETALLE) --
    hace-2-meses, mes-pasado, mes-en-curso, en ese orden.

    Se derivan del mes calendario REAL de hoy (pedido explicito de
    Sabas, septiembre 2026), no de un valor fijo en el codigo ni de una
    columna de fecha en el Excel (ninguna de las 3 hojas trae una) --
    asi el proximo mes, sin tocar nada, la comparativa rota sola: hoy
    (septiembre) muestra Jul/Ago/Sep: el 1 de octubre, con el mismo
    codigo sin cambios, va a mostrar Ago/Sep/Oct.
    """
    hoy = pd.Timestamp.now().normalize()
    mes_actual = hoy.month
    mes_last = mes_actual - 1 if mes_actual > 1 else 12
    mes_previous = mes_last - 1 if mes_last > 1 else 12
    return _MESES_ES[mes_previous], _MESES_ES[mes_last], _MESES_ES[mes_actual]


def load_detalle_portfolio(farmer_email):
    """
    Base de cartera para farmers de EQUIPO_ALTA_SIN_ASIGNACION (los 6 de
    Fabian que aun no tienen fila en ASIGNACION). Arma un dataframe con las
    MISMAS columnas que load_asignacion() devuelve, para que portfolio_for()
    pueda seguir su misma cadena de merges sin ramas especiales.

    Limitaciones respecto a ASIGNACION real (documentar en README cuando se
    suba a produccion):
      - telefono/mail de contacto de la marca: no disponibles, quedan "".
      - coinversion/coinv_group_key/coinv_has: no disponibles (DETALLE no
        trae el grupo), quedan None/False para toda marca -- pedido
        explicito de Sabas (agosto 2026), no romper nada, solo no calcular.
      - Cobertura: solo marcas con actividad/GMV en el corte de DETALLE
        actual, no el universo completo de cartera del farmer (mismo
        matiz que ya aplicaba a las 752/562 marcas "huerfanas" detectadas
        entre ASIGNACION y DETALLE para el equipo original).

    Cuando llegue la ASIGNACION real para estos 6, esta funcion deja de
    usarse para ellos (portfolio_for vuelve a la rama normal).
    """
    det = load_detalle()
    if det.empty:
        return det

    email = str(farmer_email).strip().lower()
    df = det[det["farmer_detalle"] == email].copy()
    if df.empty:
        return df

    out = pd.DataFrame()
    out["key"] = df["key"]
    out["brand_id"] = df["key"]  # no tenemos el id "crudo" del export viejo, se usa la key canonica
    out["brand_name"] = df["brand_name_detalle"]
    out["telefono"] = ""
    out["mail"] = ""
    out["farmer"] = email
    out["coinversion"] = ""
    out["nkey"] = out["brand_name"].apply(name_key)
    out["coinv_group_key"] = None
    out["coinv_has"] = False

    return out.drop_duplicates(subset=["key"]).reset_index(drop=True)


# =========================
# PERFECT STORE — gauge Menu (ya viene agregado a nivel marca)
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_perfect_store():
    """
    PERFECT STORE cambio de formato (detectado en la auditoria de agosto
    2026, bug real): antes traia "Brand_ID" a nivel MARCA con columnas
    "Global_Metric"/"Purchasing_Exp"; el export actual trae
    "Country Store ID" a nivel TIENDA, con nombres sin guion bajo
    ("Global Metric", "Purchasing Experience") y valores como TEXTO con
    formato europeo + emoji ("47,4%  ❌") -- to_num ya los parsea bien.

    Consecuencia del bug: pick_col no encontraba "Brand_ID", la funcion
    devolvia DataFrame vacio, y TODA la card de Menu del 360 Action
    mostraba "Sin datos de catalogo" para las 250 marcas de cada Farmer.

    Fix: se soportan AMBOS formatos. Si viene el nuevo (por tienda), se
    cruza store->brand con store_to_brand() y se AGREGA a nivel marca
    promediando las tiendas de cada marca (una marca multi-local tiene un
    Perfect Store por local; el promedio simple es el criterio mas
    razonable sin una columna de peso por tienda).

    Cobertura conocida del cruce: ~63% de las tiendas de PERFECT STORE
    matchean contra AVA (3.572 de 5.633). El resto son tiendas que no
    figuran en AVA -- no es un bug de esta funcion, es cobertura del
    export. Mejor 63% que el 0% que habia antes.
    """
    df = _read("perfect_store")
    if df.empty:
        return df

    c_id_marca  = pick_col(df, "Brand_ID", "brand id")
    c_id_tienda = pick_col(df, "Country Store ID", "country store id") if not c_id_marca else None
    c_id = c_id_marca or c_id_tienda
    if not c_id:
        _issue("PERFECT STORE", "No encuentro Brand_ID ni Country Store ID")
        return pd.DataFrame()

    c_pct   = pick_col(df, "Perfect_Store_Pct")
    c_glob  = pick_col(df, "Global_Metric", "Global Metric")
    c_photo = pick_col(df, "Photos")
    c_purch = pick_col(df, "Purchasing_Exp", "Purchasing Experience")
    c_miss  = pick_col(df, "Missing_Products", "Missing Products")

    out = pd.DataFrame()
    out["key"]               = df[c_id].apply(brand_key)
    out["menu_global"]       = df[c_glob].apply(to_num) if c_glob else 0.0
    out["menu_photos"]       = df[c_photo].apply(to_num) if c_photo else 0.0
    out["menu_purchase"]     = df[c_purch].apply(to_num) if c_purch else 0.0
    out["menu_missing"]      = df[c_miss].apply(to_num) if c_miss else 0.0
    # El formato nuevo no trae Perfect_Store_Pct propio: se usa Global
    # Metric como proxy (es la metrica compuesta de Perfect Store).
    out["perfect_store_pct"] = df[c_pct].apply(to_num) if c_pct else out["menu_global"]

    out = out[out["key"] != ""]

    if c_id_tienda:
        s2b = store_to_brand()
        out["key"] = out["key"].map(s2b)
        out = out[out["key"].notna()]
        num_cols = ["perfect_store_pct", "menu_global", "menu_photos", "menu_purchase", "menu_missing"]
        out = out.groupby("key", as_index=False)[num_cols].mean()

    return out.drop_duplicates(subset=["key"]).reset_index(drop=True)


# =========================
# CVR% y TRAFFIC — cruzan por NOMBRE, no por ID
# =========================

def _load_by_name(kind, value_name):
    """Ambas hojas: Metrica | Brand Name | Valor | vs LM (%), header en fila 2."""
    df = _read(kind, header=1)
    if df.empty:
        return df
    if len(df.columns) < 4:
        _issue(SHEETS[kind], "Esperaba 4 columnas (Metrica/Brand Name/Valor/vs LM)")
        return pd.DataFrame()

    df = df.iloc[:, :4].copy()
    df.columns = ["metrica", "brand_name", "valor", "vs_lm"]
    df = _drop_junk(df, "brand_name")

    out = pd.DataFrame()
    out["nkey"] = df["brand_name"].apply(name_key)
    out[value_name] = df["valor"].apply(to_num)
    out[f"{value_name}_delta"] = df["vs_lm"].apply(to_num)

    out = out[out["nkey"] != ""]
    return out.drop_duplicates(subset=["nkey"]).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def load_cvr():
    return _load_by_name("cvr", "cvr")


@st.cache_data(ttl=86400, show_spinner=False)
def load_traffic():
    """
    OJO CON LA UNIDAD: la hoja TRAFFIC trae el dato MENSUAL, no semanal (aunque
    Growth OS lo trata como semanal en varios lugares — confirmado por Sabas,
    quien conoce la fuente real del export). Se divide entre 4 aca mismo para
    que el resto de la app (Funnel de Analytics, Ads Plan) siempre reciba el
    valor semanal real, sin tener que acordarse de dividir en cada lugar que
    lo usa.
    """
    df = _load_by_name("traffic", "traffic")
    if df.empty:
        return df
    df["traffic"] = df["traffic"] / 4
    return df


# =========================
# LTOR + CATEGORIA (hoja MD NAMES)
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_ltor():
    df = _read("md_names")
    if df.empty:
        return df
    c_name = pick_col(df, "Brand Name")
    c_ltor = pick_col(df, "LTOR Class")
    c_cat  = pick_col(df, "Category")
    if not c_name:
        return pd.DataFrame()

    df = _drop_junk(df, c_name)
    out = pd.DataFrame()
    out["nkey"]      = df[c_name].apply(name_key)
    out["ltor"]      = df[c_ltor].astype(str).str.strip() if c_ltor else ""
    out["categoria"] = df[c_cat].astype(str).str.strip() if c_cat else ""
    out = out[out["nkey"] != ""]
    return out.drop_duplicates(subset=["nkey"]).reset_index(drop=True)


def _is_pro_campaign_name(text):
    """Misma heuristica que Growth OS: 'pro'/'prime'/'exclusivo pro' en el
    nombre de la campana la clasifica como MD PRO en vez de MD normal."""
    low = normalize(text)
    return bool(
        re.search(r"\bpro\b", low)
        or "exclusivo pro" in low
        or "primec" in low
        or re.search(r"\bprime\b", low)
    )


@st.cache_data(ttl=86400, show_spinner=False)
def md_campaign_names():
    """
    {key: {'md': 'Nombre1 | Nombre2', 'md_pro': '...'}} -- una marca puede
    tener varias campanas activas en MD NAMES, por eso NO se deduplica por
    marca como load_ltor. Se muestran hasta 2 nombres por palanca, igual que
    Growth OS. Sin match = '-'.

    BUG REAL CORREGIDO (vigésima segunda vuelta, pedido explícito de Sabas
    -- "revisé y estaba filtrando mal, actualizando una data que no se usa
    para nada"): MD NAMES nunca trajo "Brand Name" como nombre de columna
    (columnas reales: Country/Wealthy/Category/Campaign ID/Name/Segment/
    Tier Classification/Markdown LMTD/Markdown MTD/Delta/Delta Net) --
    pick_col(df, "Brand Name") devolvía None SIEMPRE, así que la función
    retornaba {} en cada llamada sin que ningún error lo mostrara: el
    resultado era que TODA la cartera mostraba "Campaign -" sin importar
    la promo real, y una marca podía verse "Inactive" (según MD/MD PRO,
    que sí calculan bien) mientras en Manager sí tenía nombre de campaña
    real -- porque esa campaña vivía en MD NAMES, una hoja que Wingman
    nunca llegó a leer de verdad. El comentario viejo en portfolio_for()
    ("MD NAMES no trae Brand ID") documentaba el motivo original del
    diseño por nombre, pero ya no es cierto: el export actual de MD NAMES
    SÍ trae Brand ID (confirmado con el archivo real que Sabas subió,
    columnas Country/Wealthy/Category/Brand ID/Store ID/Campaign ID/
    Name/...). Fix: cruzar por key (brand_key sobre Brand ID) en vez de
    por nkey (nombre normalizado) -- mismo patrón que ya usan MD/MD PRO
    (_load_md, columna BRAND ID) y el resto del sistema, mucho más
    confiable que el cruce por texto de nombre (que fallaba silenciosamente
    ante acentos/mayúsculas/espacios distintos entre hojas). Si algún día
    Brand ID volviera a faltar (por si el export cambia de nuevo), cae de
    vuelta al cruce por nombre como respaldo, para no romper por completo
    si la estructura del Excel cambia otra vez sin aviso.
    """
    df = _read("md_names")
    if df.empty:
        return {}
    c_id   = pick_col(df, "Brand ID", "brand id")
    c_name = pick_col(df, "Brand Name")
    c_camp = pick_col(df, "Name", "campaign name", "promo", "promotion")
    if not c_camp:
        return {}
    if not (c_id or c_name):
        return {}

    if c_id:
        df = _drop_junk(df, c_id)
        df["match_key"] = df[c_id].apply(brand_key)
    else:
        df = _drop_junk(df, c_name)
        df["match_key"] = df[c_name].apply(name_key)
    df = df[df["match_key"] != ""]

    out = {}
    for match_key, g in df.groupby("match_key"):
        names = []
        for v in g[c_camp].tolist():
            text = str(v).strip()
            if text and text.lower() not in ("nan", "-") and text not in names:
                names.append(text)
        pro_names = [n for n in names if _is_pro_campaign_name(n)]
        md_names_ = [n for n in names if not _is_pro_campaign_name(n)]
        md_display = " | ".join(md_names_[:2]) if md_names_ else (names[0] if names else "-")
        pro_display = " | ".join(pro_names[:2]) if pro_names else "-"
        out[match_key] = {"md": md_display, "md_pro": pro_display}
    return out


# =========================
# TOP PRODUCTS — por store, se mapea a marca via AVA
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_top_products():
    """
    Carga TOP PRODUCTS. Acepta DOS formatos posibles de la hoja, porque el
    archivo cambió de formato en una sesión de filtrado (de "una fila por
    store, hay que cruzar con AVA para saber la marca" a "ya viene una fila
    por marca con Brand_ID directo"):

      - Formato NUEVO (actual): Brand_ID | Brand_Name | Farmer | Ranking |
        Product_Name | ... -- ya viene cruzado por marca, no hace falta AVA.
      - Formato VIEJO (legacy): COUNTRY_STORE_ID | NAME | VPD | CVR |
        RANKING -- a nivel store, se cruza con store_to_brand() (via AVA).

    El bug real que esto corrige: se actualizó el dato (formato nuevo) sin
    actualizar este loader (que seguía esperando el formato viejo) -- el
    resultado era el aviso "Falta COUNTRY_STORE_ID o NAME" en producción,
    y el Campaign Designer sin Top 3 Productos para ninguna marca.
    """
    df = _read("top_prod")
    if df.empty:
        return df

    c_bid   = pick_col(df, "Brand_ID", "brand id")
    c_bname = pick_col(df, "Product_Name", "product_name")

    if c_bid and c_bname:
        # ── Formato NUEVO: ya viene por marca, Brand_ID directo ──
        c_vpd  = pick_col(df, "VPD")
        c_cvr  = pick_col(df, "CVR")
        c_rank = pick_col(df, "Ranking", "ranking", "rank")

        df = _drop_junk(df, c_bid)
        out = pd.DataFrame()
        out["key"]     = df[c_bid].apply(brand_key)
        out["product"] = df[c_bname].astype(str).str.strip()
        out["vpd"]     = df[c_vpd].apply(to_num) if c_vpd else 0.0
        out["cvr"]     = df[c_cvr].apply(to_num) if c_cvr else 0.0
        out["ranking"] = df[c_rank].apply(to_num) if c_rank else 99.0
        return out[out["key"] != ""].reset_index(drop=True)

    # ── Formato VIEJO: a nivel store, cruzar con AVA ──
    c_store = pick_col(df, "COUNTRY_STORE_ID", "store id")
    c_name  = pick_col(df, "NAME", "product")
    c_vpd   = pick_col(df, "VPD")
    c_cvr   = pick_col(df, "CVR")
    c_rank  = pick_col(df, "RANKING", "rank")
    if not (c_store and c_name):
        _issue("TOP PRODUCTS", "Falta Brand_ID/Product_Name (formato nuevo) o COUNTRY_STORE_ID/NAME (formato viejo)")
        return pd.DataFrame()

    df = _drop_junk(df, c_store)
    smap = store_to_brand()

    out = pd.DataFrame()
    out["key"]     = df[c_store].apply(brand_key).map(smap)
    out["product"] = df[c_name].astype(str).str.strip()
    out["vpd"]     = df[c_vpd].apply(to_num) if c_vpd else 0.0
    out["cvr"]     = df[c_cvr].apply(to_num) if c_cvr else 0.0
    out["ranking"] = df[c_rank].apply(to_num) if c_rank else 99.0

    out = out[out["key"].notna()]
    return out[out["key"] != ""].reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def top_products_map(limit=3):
    """{brand_key: [(producto, vpd, cvr), ...]} — top N por ranking."""
    df = load_top_products()
    if df.empty:
        return {}
    return {
        key: list(zip(g.head(limit)["product"], g.head(limit)["vpd"], g.head(limit)["cvr"]))
        for key, g in df.sort_values("ranking").groupby("key")
    }


# =========================
# PRIORITY DATA
# =========================

METRIC_LABELS = {
    "disponibilidad (availability)": "Disponibilidad",
    "catalogo (catalog quality)":    "Catalogo",
    "pdf menu":                      "PDF Menu",
    "ads":                           "Ads",
    "reclamos (defect)":             "Reclamos",
    "promos (markdown)":             "Promos",
    "promos pro (markdown pro)":     "Promos Pro",
    "cancelaciones (cancel)":        "Cancelaciones",
    "tiempo de espera rt (rtwt)":    "Tiempo de espera",
    "churn":                         "Churn",
}

# Bucket por palanca (para el aterrizaje: OPS/Menu/Markdown/MD PRO/Ads).
# Growth OS tenia un bug aca: probaba "md" antes que "pro", y "Promos Pro
# (Markdown Pro)" contiene la palabra "markdown", asi que TODO MD PRO caia
# como MD normal (0 cuentas en el filtro MD PRO). Se corrige evaluando PRO
# primero.
def _priority_bucket(metric_norm):
    if "prime" in metric_norm or ("pro" in metric_norm and "promos pro" in metric_norm) or "markdown pro" in metric_norm:
        return "mdpro"
    if any(t in metric_norm for t in ("disponibilidad", "availability", "rtwt", "espera",
                                       "cancel", "reclamo", "defect", "churn")):
        return "ops"
    if any(t in metric_norm for t in ("catalogo", "pdf menu", "menu")):
        return "menu"
    if "markdown" in metric_norm or "promo" in metric_norm:
        return "md"
    if "ads" in metric_norm:
        return "ads"
    return "otro"


# Clasificacion fina, misma logica que _classify_priority_lever de Growth OS.
# Distinta del bucket de arriba: el bucket agrupa para el aterrizaje (5
# categorias), esto da el detalle exacto que necesitan las tarjetas tacticas
# de 360 Action (10 categorias, cada una con su propio mensaje/formula).
def _classify_priority_kind(metric_norm):
    if any(t in metric_norm for t in ("rtwt", "wait", "espera", "repartidor", "rider", "courier", "driver", "tiempo")):
        return "ops_wait_time"
    if any(t in metric_norm for t in ("reclamo", "reclam", "claim", "complaint", "queja")):
        return "ops_claims"
    if "cancel" in metric_norm:
        return "ops_cancellations"
    if any(t in metric_norm for t in ("defect", "defecto", "dr ")):
        return "ops_defects"
    if any(t in metric_norm for t in ("disponibilidad", "availability", "ava", "offline", "conexion", "online")):
        return "ops_availability"
    if any(t in metric_norm for t in ("ops", "operacion", "operativo", "churn")):
        return "ops_other"
    if any(t in metric_norm for t in ("foto", "photo", "imagen")):
        return "menu_photos"
    if any(t in metric_norm for t in ("purchasing", "experiencia", "purchase", "compra")):
        return "menu_purchase_experience"
    if "pdf" in metric_norm:
        return "menu_pdf"
    if any(t in metric_norm for t in ("missing", "faltante", "producto", "catalogo", "menu")):
        return "menu_catalog"
    if "prime" in metric_norm or "markdown pro" in metric_norm or "promos pro" in metric_norm:
        return "md_pro"
    if "markdown" in metric_norm or "promo" in metric_norm:
        return "md"
    if "ads" in metric_norm:
        return "ads"
    return "general"


def _clasificar_accion_priority(descripcion):
    """
    Clasifica el texto de "Descripción" de una fila de PRIORITY DATA (Metric
    = Ads / Promos (Markdown) / Promos Pro) en la accion que pide, para las
    cards de MD y Ads del 360 Action (pedido explicito de Sabas, agosto 2026):

      - Empieza con "Adquisición"  -> ("Adquisición", con nota Campaign Designer)
      - Empieza con "Upselling"    -> ("Upselling", con nota Campaign Designer)
      - Empieza con "Optimización" (con o sin el texto extra que a veces trae,
        ej. "Optimización: Presupuesto No consumido...") -> ("Optimización", SIN nota)
      - Cualquier otro texto (Reactivación, Retención, combinaciones tipo
        "Reactivación/Retención (Últimas 2W y Próximas 2W)") -> se muestra tal
        cual viene, SIN nota -- pedido explicito de Sabas de no forzarlo a
        ninguna de las 3 categorias de arriba.

    Devuelve (label, mostrar_nota_campaign_designer).
    """
    texto = str(descripcion).strip()
    if not texto or texto.lower() in ("nan", "none", "-"):
        return ("", False)

    low = normalize(texto)
    if low.startswith("adquisicion"):
        return ("Adquisición", True)
    if low.startswith("upselling"):
        return ("Upselling", True)
    if low.startswith("optimizacion"):
        return ("Optimización", False)
    return (texto, False)


def _extract_priority_pct_rate(descr):
    """Saca el promedio de los % mencionados en un texto de descripcion, como
    '8% tasa' o '49 reclamos · 8% tasa'. Devuelve fraccion (0.08), no 8."""
    if not descr:
        return 0.0
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", str(descr))
    if not matches:
        return 0.0
    vals = []
    for m in matches:
        try:
            vals.append(float(m.replace(",", ".")))
        except (TypeError, ValueError):
            continue
    return (sum(vals) / len(vals) / 100.0) if vals else 0.0


@st.cache_data(ttl=86400, show_spinner=False)
def load_priority():
    """
    PRIORITY DATA cambio de formato en agosto 2026: la columna de ID paso de
    "BID" (id puro, ej. "AR95711") a "Brand" (id + nombre embebido, ej.
    "AR95711 - ¡hey Pizza!", igual que Brand en DETALLE) -- brand_key() ya
    sabe extraer el numero+pais de ese texto sin cambios. "Descripcion" paso
    de ser columna opcional (no existia en exports viejos) a existir siempre
    con tilde ("Descripción").

    "Promo vencida" / "Promo por vencer" (columnas nuevas, corte de
    septiembre 2026 -- pedido explícito de Sabas: "revisa el archivo
    actualizado... la hoja de Priority Data trae unas nuevas columnas"):
    antes NO existían en el Wingman -- ver la investigación de Anthropic
    sobre Smart Priorities, que las documentaba como limitación conocida
    ("SIN DATOS. Esta información proviene de la hoja SP del archivo
    fuente de Sabas... que no tiene equivalente en el Wingman"). Cada
    celda no es un booleano SI/NO como el resto de esta hoja: es una
    lista de IDs de campaña separados por salto de línea ("\\n"), ej.
    "3421100\\n3306280\\n3306279" -- varias promos vencidas/por vencer a
    la vez para la misma marca. Se guardan tal cual vienen (sin parsear
    los IDs individuales ni contarlos), para que quien las consuma decida
    cómo mostrarlas -- "—" (no "") cuando la celda viene vacía, mismo
    placeholder que el resto de pills de esta app.

    "Último Contacto" (pedido explícito de Sabas, trigésima quinta
    vuelta: "vas a tomar el último contacto... y lo vas a añadir en la
    esquina superior derecha de la carta de cabecera"): viene como
    serial de fecha de Excel (float, ej. 46274.0 -- días desde
    1899-12-30), NO como texto ni datetime -- confirmado contra el
    workbook real, columna 100% float en las 27219 filas. Se parsea acá
    con ese epoch fijo a un Timestamp real (NaT si la celda viene vacía),
    para que quien lo consuma (ultimo_contacto_for) no tenga que repetir
    la conversión. Esta misma columna, sin parsear, era la limitación
    documentada como "SIN DATO EN FORMATO TEXTO... se dejó en blanco para
    evitar mostrar un valor mal formateado" en la investigación de
    Anthropic sobre Smart Priorities -- ya no aplica, el dato llega bien
    y se puede formatear.
    """
    df = _read("priority")
    if df.empty:
        return df
    c_id   = pick_col(df, "Brand", "BID", "brand id")
    c_met  = pick_col(df, "Metric")
    c_val  = pick_col(df, "Prioridad BD", "prioridad")
    c_desc = pick_col(df, "Descripción", "Descripcion", "description")
    c_vencida = pick_col(df, "Promo vencida")
    c_por_vencer = pick_col(df, "Promo por vencer")
    c_ultimo = pick_col(df, "Último Contacto", "Ultimo Contacto")
    if not (c_id and c_met):
        _issue("PRIORITY DATA", "Falta Brand/BID o Metric")
        return pd.DataFrame()

    df = _drop_junk(df, c_id)
    out = pd.DataFrame()
    out["key"]    = df[c_id].apply(brand_key)
    out["metric"] = df[c_met].astype(str).str.strip()
    out["value"]  = df[c_val].apply(to_num) if c_val else 0.0
    out["descripcion"] = df[c_desc].astype(str).str.strip() if c_desc else ""
    out["promo_vencida"] = (
        df[c_vencida].fillna("").astype(str).str.strip()
        if c_vencida else ""
    )
    out["promo_por_vencer"] = (
        df[c_por_vencer].fillna("").astype(str).str.strip()
        if c_por_vencer else ""
    )
    out["ultimo_contacto"] = (
        pd.to_datetime(df[c_ultimo], unit="D", origin="1899-12-30", errors="coerce")
        if c_ultimo else pd.NaT
    )

    out = out[(out["key"] != "") & (out["metric"].str.lower() != "total")]
    out["descripcion"] = out["descripcion"].replace({"nan": ""})
    out["label"]  = out["metric"].apply(lambda m: METRIC_LABELS.get(normalize(m), str(m).strip()))
    out["bucket"] = out["metric"].apply(lambda m: _priority_bucket(normalize(m)))
    out["kind"]   = out["metric"].apply(lambda m: _classify_priority_kind(normalize(m)))
    return out.reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def load_coinversion_md():
    """
    "Coinversion MD" y "STATUS Brand" de PRIORITY DATA solo vienen
    poblados en la fila donde Metric="Total" de cada marca -- en el resto
    de las filas (Churn, Reclamos, PDF Menu, etc.) vienen vacios. Por eso
    esto se lee del crudo de PRIORITY DATA (no de load_priority(), que ya
    descarta la fila "Total" para el listado de metricas individuales).

    Logica pedida por Sabas (agosto 2026), replicando el criterio de la
    card "COINVERSIÓN MD" del 360 Action de Growth OS:
      - Coinversion MD != "SI" exacto (vacio, "No", cualquier otra cosa)
        -> coinv_md_status = False, status_label = "No".
      - Coinversion MD == "SI" -> coinv_md_status = True, y status_label
        sale de STATUS Brand (via _parse_status_grupo + COINV_GROUPS,
        mismo vocabulario que la coinversion de ASIGNACION: Prioritized,
        Rest, Churn Prevention, etc.). Si STATUS Brand viene vacio a
        pesar de Coinversion MD="SI" (caso raro, no visto en el export
        actual), status_label queda "Sí" a secas -- mejor eso que None
        en la UI.

    NOTA de nombre: la columna se llama "coinv_md_status" (no "coinv_md")
    a proposito -- portfolio_for() ya tiene una columna "coinv_md" que sale
    de load_md() (el MONTO de coinversion de Markdown en $, dato distinto
    a este booleano de "tiene coinversion activa segun PRIORITY DATA").
    Un merge con el mismo nombre ahi hubiera generado columnas _x/_y
    silenciosamente. Bug real encontrado al validar este cambio.

    "Promo vencida" / "Promo por vencer" existen en el export pero NO se
    usan aca -- pedido explicito de Sabas de dejarlas fuera de esta card.
    """
    df = _read("priority")
    if df.empty:
        return pd.DataFrame(columns=["key", "coinv_md_status", "status_label"])

    c_id  = pick_col(df, "Brand", "BID", "brand id")
    c_met = pick_col(df, "Metric")
    c_coinv = pick_col(df, "Coinversion MD", "coinversión md")
    c_status = pick_col(df, "STATUS Brand", "status brand")
    if not (c_id and c_met):
        return pd.DataFrame(columns=["key", "coinv_md_status", "status_label"])

    df = _drop_junk(df, c_id)
    total_rows = df[df[c_met].astype(str).str.strip().str.lower() == "total"].copy()

    out = pd.DataFrame()
    out["key"] = total_rows[c_id].apply(brand_key)
    out = out[out["key"] != ""]

    coinv_raw = total_rows.loc[out.index, c_coinv] if c_coinv else pd.Series("", index=out.index)
    out["coinv_md_status"] = coinv_raw.astype(str).str.strip().str.upper() == "SI"

    status_raw = total_rows.loc[out.index, c_status] if c_status else pd.Series("", index=out.index)

    def _label(coinv_md_status, raw_status):
        if not coinv_md_status:
            return "No"
        gkey = _parse_status_grupo(raw_status)
        if gkey and gkey in COINV_GROUPS:
            return COINV_GROUPS[gkey]["label"]
        return "Sí"

    out["status_label"] = [
        _label(cm, st_raw) for cm, st_raw in zip(out["coinv_md_status"], status_raw)
    ]
    return out.drop_duplicates(subset=["key"]).reset_index(drop=True)



@st.cache_data(ttl=86400, show_spinner=False)
def priority_map():
    df = load_priority()
    if df.empty:
        return {}
    return {
        k: list(zip(g["label"], g["value"]))
        for k, g in df.sort_values("value", ascending=False).groupby("key")
    }


def _health_tag(score):
    """Mismos umbrales que Growth OS: 85/70/50, con etiqueta en español."""
    if score >= 85:
        return "HEALTHY"
    if score >= 70:
        return "WATCH"
    return "ALERT"


def signals_for_brand(key):
    """Todas las señales de Priority Data para una marca, agrupadas por kind
    (el detalle fino, no el bucket resumido del aterrizaje)."""
    df = load_priority()
    if df.empty:
        return []
    rows = df[df["key"] == key]
    return rows.to_dict("records")


def ops_tactical_card(key, availability_pct, lost_hours, gmv_ars=0, aov_ars=0, ordenes_mes=0, gmv_last_ars=0):
    """
    Card OPS de 360 Action -- pedido explicito de Sabas (agosto 2026, quinto
    ajuste). SIEMPRE 4 items, en este nuevo orden fijo: Disponibilidad,
    Cancelaciones, Tiempo de espera, Reclamos (antes: Disponibilidad,
    Reclamos, Cancelaciones, Tiempo de espera).

    -- Disponibilidad --
    Regla de color fija, sin cambios: <80% ALERT, 80-90% WATCH, >=90%
    HEALTHY. Disponibilidad NUNCA se autoescala por acompañamiento de otras
    metricas (a diferencia de Cancelaciones/Tiempo de espera/Reclamos) --
    pero SI cuenta como "señal activa" para escalar a esas otras 3.

    Insight nuevo (reemplaza el calculo viejo basado en gmv_last_ars, que
    ademas nunca se estaba pasando en el call-site real de wingmanapp.py --
    bug encontrado en esta misma sesion, por eso el texto de "$ perdido"
    nunca se mostraba en produccion). Siempre que availability_pct < 90%
    (cubre WATCH y ALERT), se agrega "Dejaste de captar X pedidos -- eso
    son $Y que no entraron por no llegar minimo al 90%", calculado asi:
        pedidos_perdidos = ordenes_mes * (90 / availability_pct - 1)
        perdida_pesos    = pedidos_perdidos * aov_ars
    Ancla al 90% (la meta), NO al 100% (eso se probo y se descarto en esta
    misma sesion) -- decision explicita de Sabas. Si ordenes_mes o aov_ars
    vienen en 0, la formula ya da 0 pedidos / 0 pesos sola, sin necesitar
    un caso especial -- confirmado explicitamente por Sabas que ese
    comportamiento es el deseado. gmv_ars/gmv_last_ars quedan en la firma
    solo por compatibilidad con el call-site -- ya NO se usan para este
    calculo.

    -- Cancelaciones / Reclamos --
    Paso 1 (color propio, sin mirar a las demas):
      - Sin fila en Priority Data -> neutral ("sin alerta presente").
      - Con fila, tasa = 0% -> HEALTHY ("Sin cancelaciones"/"Sin reclamos").
      - Con fila, tasa >0% hasta 10% -> WATCH.
      - Con fila, tasa >10% -> ALERT (fijo, no depende de acompañamiento).
    Paso 2 (escalacion, SOLO si quedo en WATCH tras el Paso 1): si
    cualquiera de las otras 3 metricas (Disponibilidad, Tiempo de espera, y
    la otra de Cancelaciones/Reclamos) esta activa (WATCH o ALERT en su
    propio Paso 1 -- se compara contra el estado BASE de las demas, no el
    ya escalado, para evitar dependencia circular entre Cancelaciones y
    Reclamos) -> escala a ALERT. Esto resuelve, por diseño, la duda tecnica
    que habia quedado pendiente de una sesion anterior sobre si el chequeo
    de acompañamiento debia depender del orden de renderizado: aca se
    compara siempre contra el set completo de 4 metricas, nunca solo
    contra las que ya se armaron antes en la lista.

    Insight nuevo (reemplaza las notas fijas de absorcion "el aliado
    absorbe el 50%/65%", que quedan eliminadas por completo): se agrega
    siempre que la tasa sea >0% (WATCH o ALERT, con o sin escalar):
      - Cancelaciones: "Revisa el motivo mas frecuente. Recuerda que es
        perdida doble: se pierde la venta y se pierde el impuesto y la
        comision de una venta facturada que nunca entra a la caja."
      - Reclamos: "Revisa el motivo de las reclamaciones. Recuerda que
        esto disminuye la posibilidad de recompra del usuario."

    -- Tiempo de espera --
    Sin fila -> neutral ("sin alerta presente"). Con fila, sola (ninguna
    otra de las 4 activa) -> WATCH. Con fila, acompañada de cualquier otra
    activa -> ALERT. Mismo criterio de comparacion contra el set completo
    de 4 (no solo contra lo ya renderizado antes) que Cancelaciones/
    Reclamos. Insight nuevo, siempre que haya fila (sin importar si el
    resultado final es WATCH o ALERT): "Recuerda que cada segundo de
    retraso altera tu operacion y aumenta tu riesgo de reclamaciones."

    Estado de la card completa = el PEOR de los 4, ya con la escalacion
    del Paso 2 aplicada ("un solo rojo domina toda la card"). Los items
    neutros (None) no suman ni restan estado.

    pct siempre None en el retorno -- sin cambio respecto a antes.
    """
    signals = signals_for_brand(key)
    por_kind = {}
    for s in signals:
        if s["kind"].startswith("ops") and s["kind"] != "ops_availability":
            por_kind.setdefault(s["kind"], s)  # una fila por kind esperado; si hay mas, la primera

    # ── PASO 1: estado base + texto de cada una de las 4, sin mirar a las demas ──

    # 1. Disponibilidad
    if not availability_pct or availability_pct <= 0:
        disp_estado, disp_texto = None, "Disponibilidad — sin datos disponibles"
    else:
        if availability_pct >= 90:
            disp_estado = "HEALTHY"
            disp_texto = f"Disponibilidad {availability_pct:.0f}%"
        elif availability_pct >= 80:
            disp_estado = "WATCH"
            disp_texto = f"Disponibilidad {availability_pct:.0f}% — por debajo del 90%"
        else:
            disp_estado = "ALERT"
            disp_texto = f"Disponibilidad {availability_pct:.0f}% — muy por debajo del 90%"

        if availability_pct < 90:
            # Formula ancla al 90% (la meta), no al 100% -- ver docstring.
            # Se calcula el crudo sin redondear primero y se redondea solo
            # al final de cada numero mostrado, para no encadenar
            # redondeos y perder precision en la plata.
            raw_pedidos = ordenes_mes * (90 / availability_pct - 1)
            pedidos_perdidos = round(raw_pedidos)
            perdida_pesos = round(raw_pedidos * aov_ars)
            disp_texto += (
                f" Dejaste de captar {pedidos_perdidos} pedidos — eso son "
                f"{fmt_ars(perdida_pesos)} que no entraron por no llegar mínimo al 90%."
            )

    # 2. Cancelaciones, 4. Reclamos -- mismo Paso 1, distinto kind/insight
    def _paso1_tasa(kind):
        s = por_kind.get(kind)
        if s is None:
            return None, 0.0
        rate = _extract_priority_pct_rate(s.get("descripcion", ""))
        if rate <= 0:
            return "HEALTHY", 0.0
        return ("ALERT" if rate > 0.10 else "WATCH"), rate

    canc_estado, canc_rate = _paso1_tasa("ops_cancellations")
    recl_estado, recl_rate = _paso1_tasa("ops_claims")

    # 3. Tiempo de espera -- Paso 1 (sin escalar todavia). Priority Data
    # solo trae esta fila cuando el tiempo esta elevado -- no hay caso real
    # de "fila presente pero tiempo normal" confirmado en la fuente, asi
    # que la sola presencia ya es señal.
    s_wait = por_kind.get("ops_wait_time")
    wait_hay_fila = s_wait is not None
    wait_descr = s_wait.get("descripcion", "") if s_wait else ""

    # ── PASO 2: escalacion por acompañamiento -- se compara SIEMPRE contra
    # el estado BASE (Paso 1) de las otras 3, nunca contra el ya escalado
    # ni contra el orden de renderizado -- evita dependencia circular entre
    # Cancelaciones y Reclamos, y hace el resultado independiente del orden
    # en que se muestran los 4 items en la card. ──

    def _activa(estado):
        return estado in ("WATCH", "ALERT")

    if canc_estado == "WATCH" and (_activa(disp_estado) or wait_hay_fila or _activa(recl_estado)):
        canc_estado_final = "ALERT"
    else:
        canc_estado_final = canc_estado

    if recl_estado == "WATCH" and (_activa(disp_estado) or wait_hay_fila or _activa(canc_estado)):
        recl_estado_final = "ALERT"
    else:
        recl_estado_final = recl_estado

    if wait_hay_fila:
        otra_activa = _activa(disp_estado) or _activa(canc_estado) or _activa(recl_estado)
        wait_estado_final = "ALERT" if otra_activa else "WATCH"
    else:
        wait_estado_final = None

    # ── Textos finales -- el texto de cada item NO cambia por la
    # escalacion del Paso 2 (solo cambia el estado usado para el tag
    # agregado), mismo criterio que ya tenia el codigo viejo para Tiempo
    # de espera. ──

    if canc_estado is None:
        canc_texto = "Cancelaciones — sin alerta presente"
    elif canc_estado == "HEALTHY":
        canc_texto = "Sin cancelaciones"
    else:
        canc_texto = (
            f"Cancelaciones {canc_rate * 100:.0f}% — Revisa el motivo más frecuente. "
            f"Recuerda que es pérdida doble: se pierde la venta y se pierde el "
            f"impuesto y la comisión de una venta facturada que nunca entra a la caja."
        )

    if recl_estado is None:
        recl_texto = "Reclamos — sin alerta presente"
    elif recl_estado == "HEALTHY":
        recl_texto = "Sin reclamos"
    else:
        recl_texto = (
            f"Reclamos {recl_rate * 100:.0f}% — Revisa el motivo de las reclamaciones. "
            f"Recuerda que esto disminuye la posibilidad de recompra del usuario."
        )

    if not wait_hay_fila:
        wait_texto = "Tiempo de espera del repartidor — sin alerta presente"
    else:
        wait_texto = "Tiempo de espera del repartidor elevado"
        if wait_descr:
            wait_texto += f" — {wait_descr}"
        wait_texto += (
            " Recuerda que cada segundo de retraso altera tu operación y "
            "aumenta tu riesgo de reclamaciones."
        )

    # Orden final fijo: Disponibilidad, Cancelaciones, Tiempo de espera, Reclamos.
    # Sin emoji concatenado al texto (sexta vuelta, pedido explícito de
    # Sabas): el bullet circular monocromático se agrega en el render
    # (wingmanapp.py, _action_mini), no acá -- antes el emoji Unicode
    # (📶🛑⏱️⚠️) iba pegado al string.
    items = [
        (disp_texto, disp_estado),
        (canc_texto, canc_estado_final),
        (wait_texto, wait_estado_final),
        (recl_texto, recl_estado_final),
    ]

    # Estado de la card completa: el peor de los 4, ya con la escalacion
    # del Paso 2 aplicada -- "sin datos"/"sin alerta" (None) es neutro, no
    # cuenta ni para bien ni para mal.
    estados_reales = [e for _, e in items if e is not None]
    if "ALERT" in estados_reales:
        tag = "ALERT"
    elif "WATCH" in estados_reales:
        tag = "WATCH"
    elif "HEALTHY" in estados_reales:
        tag = "HEALTHY"
    else:
        tag = "HEALTHY"  # las 4 sin datos: no hay nada que reportar, se trata como sano

    bullets = [texto for texto, _ in items]
    detail = " · ".join(bullets)

    if tag == "ALERT":
        titulo_top = "Validar fricción operativa antes de escalar tráfico"
    elif tag == "WATCH":
        titulo_top = "Hay puntos de OPS a revisar"
    else:
        titulo_top = "OPS saludable"

    # "items": ahora una lista de (texto, estado) -- antes solo texto
    # plano, sin el estado individual de cada bullet (sexta vuelta,
    # pedido explícito de Sabas: el render necesita saber cuál de los 4
    # está en ALERT/WATCH para ponerlo en negrita y cuál está sano/sin
    # dato para dejarlo en texto normal, igual que el Insight de
    # Markdown/Ads).
    return {"title": titulo_top, "detail": detail, "items": items, "tag": tag, "pct": None}


def menu_tactical_card(key, perfect_store_pct, photos_pct, purchase_pct, missing_pct):
    """
    Card Menu de 360 Action -- pedido explicito de Sabas (agosto 2026,
    quinto ajuste). Nuevo orden fijo: Missing Products, Fotos, Experiencia
    de compra, PDF Menu (antes: Fotos, Experiencia de compra, Missing
    Products, PDF Menu).

    Missing Products AHORA SI tiene estado/color propio -- cambio real de
    comportamiento, pedido explicito de Sabas (antes era puramente
    informativo, sin estado, porque su escala real es 0-223 y no un
    porcentaje -- eso no cambio, solo se le agrego una regla de estado
    sobre esa misma escala de conteo, no de %):
      - 0 (o sin dato) -> HEALTHY, "Metrica sana y competitiva".
      - 1 a 10 -> WATCH.
      - Mas de 10 -> ALERT.
      Insight (>=1, mismo texto tanto en WATCH como en ALERT): "Ventas y
      trafico perdido por productos ocultos".

    Fotos / Experiencia de compra: umbral de ALERT movido de 70% a 75%
    (cambio real de umbral, pedido explicito de Sabas -- antes 70-89% era
    WATCH y <70% era ALERT; ahora 75-89% es WATCH y <75% es ALERT):
      - >=90% -> HEALTHY, "Metrica sana y competitiva".
      - 75% a 89% -> WATCH.
          Fotos: "Revisar y optimizar fotografias para mejorar conversión".
          Experiencia: "Aumenta tu posibilidad de venta cruzada y
          crecimiento de AOV".
      - <75% -> ALERT.
          Fotos: "Corregir urgente, no se le muestra al usuario lo que se
          está ofreciendo".
          Experiencia: "Muy bajo rendimiento esperado en venta cruzada y
          crecimiento de AOV" (sin la frase "aumento de ticket promedio"
          -- se saco por redundante con "crecimiento de AOV", correccion
          explicita de Sabas).
      Sin dato (0/None) sigue neutral ("sin datos disponibles"), SIN
      cambio -- a diferencia de Missing Products, Sabas no pidio tratar
      "sin dato" como HEALTHY para estas dos metricas.

    PDF Menu: texto reemplazado por completo (ya NO "PDF Menu
    desactualizado — actualización urgente"):
      - No se necesita -> HEALTHY, "No se necesita".
      - Se necesita -> WATCH, "Verifica actualización de catálogo
        reciente".

    Estado de la card completa (pedido explicito de Sabas, mismo principio
    de escalacion por acompañamiento que OPS, pero sin el caso especial de
    Disponibilidad -- las 4 metricas de Menu son simetricas entre si, asi
    que basta con CONTAR cuantas quedaron en WATCH, no hace falta que cada
    una "mire" individualmente a las demas):
      - Cualquiera de las 4 en ALERT -> card ALERT (fijo, un rojo domina).
      - Ninguna ALERT pero 2 o mas en WATCH -> card ALERT (escalacion).
      - Exactamente 1 en WATCH -> card WATCH.
      - Las 4 sanas/sin dato -> card HEALTHY.
    Igual que en OPS, la escalacion solo afecta el tag agregado de la
    card -- el texto de cada bullet individual no cambia.

    health_score se sigue calculando igual (misma formula de Growth OS)
    pero sigue sin mostrarse -- pct siempre None en el retorno.
    """
    _signals = signals_for_brand(key)
    pdf_signal = any(s["kind"] == "menu_pdf" for s in _signals)

    photos_frac = (photos_pct or 0) / 100
    purchase_frac = (purchase_pct or 0) / 100
    perfect_bonus = (perfect_store_pct or 0) / 100
    menu_health = max(0, min(100, (photos_frac * 42) + (purchase_frac * 42) + (perfect_bonus * 16)))  # noqa: F841 (se calcula, no se muestra -- ver docstring)

    # ── 1. Missing Products (ahora con estado propio, ver docstring) ──
    mp_count = missing_pct or 0
    if mp_count <= 0:
        mp_estado = "HEALTHY"
        mp_texto = f"Missing Products: {mp_count:.0f} — Métrica sana y competitiva"
    else:
        mp_estado = "ALERT" if mp_count > 10 else "WATCH"
        mp_texto = f"Missing Products: {mp_count:.0f} — Ventas y tráfico perdido por productos ocultos"

    # ── 2. Fotos, 3. Experiencia de compra (umbral 90/75, "sin dato" sin cambio) ──
    def _estado_y_texto(nombre, pct, nota_watch, nota_alert):
        if not pct or pct <= 0:
            return f"{nombre} — sin datos disponibles", None
        if pct >= 90:
            return f"{nombre} {pct:.0f}% — Métrica sana y competitiva", "HEALTHY"
        if pct >= 75:
            return f"{nombre} {pct:.0f}% — {nota_watch}", "WATCH"
        return f"{nombre} {pct:.0f}% — {nota_alert}", "ALERT"

    fotos_texto, fotos_estado = _estado_y_texto(
        "Fotos", photos_pct,
        "Revisar y optimizar fotografías para mejorar conversión",
        "Corregir urgente, no se le muestra al usuario lo que se está ofreciendo",
    )
    exp_texto, exp_estado = _estado_y_texto(
        "Experiencia de compra", purchase_pct,
        "Aumenta tu posibilidad de venta cruzada y crecimiento de AOV",
        "Muy bajo rendimiento esperado en venta cruzada y crecimiento de AOV",
    )

    # ── 4. PDF Menú (texto reemplazado por completo) ──
    if pdf_signal:
        pdf_estado = "WATCH"
        pdf_texto = "PDF Menú — Verifica actualización de catálogo reciente"
    else:
        pdf_estado = "HEALTHY"
        pdf_texto = "PDF Menú — No se necesita"

    # Orden final fijo: Missing Products, Fotos, Experiencia de compra,
    # PDF Menú. Sin emoji concatenado (sexta vuelta, pedido explícito de
    # Sabas): mismo criterio que ops_tactical_card, el bullet circular se
    # agrega en el render.
    items = [
        (mp_texto, mp_estado),
        (fotos_texto, fotos_estado),
        (exp_texto, exp_estado),
        (pdf_texto, pdf_estado),
    ]

    # Estado de la card completa: cualquier ALERT domina; sin ALERT, 2+
    # en WATCH escala a ALERT; exactamente 1 en WATCH se queda en WATCH.
    estados_reales = [e for _, e in items if e is not None]
    n_watch = estados_reales.count("WATCH")
    if "ALERT" in estados_reales:
        tag = "ALERT"
    elif n_watch >= 2:
        tag = "ALERT"
    elif n_watch == 1:
        tag = "WATCH"
    elif "HEALTHY" in estados_reales:
        tag = "HEALTHY"
    else:
        tag = "HEALTHY"

    bullets_menu = [texto for texto, _ in items]
    title = " · ".join(bullets_menu)
    detail = (
        "Corregir antes de escalar tráfico o activar pauta."
        if tag != "HEALTHY" else "Catálogo saludable, sin issues detectados."
    )
    # "items": ahora (texto, estado) por bullet -- mismo criterio que
    # ops_tactical_card (ver comentario ahí, sexta vuelta).
    return {"title": title, "detail": detail, "items": items, "tag": tag, "pct": None}


def _priority_descripcion_for(key, kind):
    """
    Descripción de la fila de PRIORITY DATA para esta marca y este kind
    ("md", "md_pro" o "ads"). Si hay mas de una fila para el mismo kind
    (no deberia pasar, PRIORITY DATA trae 1 fila por Metric por marca),
    se toma la primera -- mejor eso que concatenar textos que no calzan.
    """
    for s in signals_for_brand(key):
        if s.get("kind") == kind:
            return s.get("descripcion", "")
    return ""


def _priority_promos_for(key, kind):
    """
    Promo vencida / Promo por vencer de PRIORITY DATA para esta marca y
    este kind ("md" o "md_pro" -- pedido explícito de Sabas, trigésima
    quinta vuelta: "todas las tarjetas de Markdown en 360 Action van a
    tener ese ítem", Markdown y Markdown Pro por separado, cada una con
    su propio dato, mismo split que ya usa _priority_descripcion_for
    contra Metric="Promos (Markdown)" / "Promos Pro (Markdown Pro)").

    Devuelve (vencida, por_vencer) -- cada uno el texto crudo de la celda
    ("" si no hay fila para este kind o la celda viene vacía, NUNCA "nan").
    """
    for s in signals_for_brand(key):
        if s.get("kind") == kind:
            return s.get("promo_vencida", "") or "", s.get("promo_por_vencer", "") or ""
    return "", ""


def ultimo_contacto_for(key):
    """
    Fecha del último contacto con esta marca -- pedido explícito de Sabas
    (trigésima quinta vuelta): "vas a tomar la fecha de último contacto,
    y lo vas a añadir en la esquina superior derecha de la carta de
    cabecera... 9 de septiembre del 2026", no el serial crudo.

    PRIORITY DATA trae "Último Contacto" repetido en CADA fila de esa
    marca (una por palanca -- Ads, Promos, Disponibilidad, etc., cada una
    con SU PROPIA fecha de último contacto sobre ese tema puntual), no
    consolidado en un solo lugar. Acá se toma el MÁXIMO (la fecha más
    reciente) entre todas las filas de la marca -- es el contacto más
    reciente con el aliado en general, sin importar sobre qué palanca fue
    -- confirmado contra el workbook real que este máximo coincide
    siempre con el de la fila Total de PRIORITY DATA (que load_priority()
    descarta a propósito para el resto de usos de esta hoja), así que no
    hace falta leer esa fila aparte.

    Devuelve un pd.Timestamp, o None si la marca no tiene ninguna fecha
    registrada (NO se inventa "sin datos" con texto -- el caller decide
    si omite el dato por completo en ese caso).
    """
    fechas = [s.get("ultimo_contacto") for s in signals_for_brand(key)]
    fechas = [f for f in fechas if pd.notna(f)]
    if not fechas:
        return None
    return max(fechas)


_MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def fmt_fecha_es(ts):
    """
    "09 de septiembre del 2026" -- pedido explícito de Sabas: "no me lo
    vas a colocar así en número como 08-09-2026... sino 9 de septiembre
    del 2026" (trigésima quinta vuelta), corregido en la trigésima sexta
    a "09 de septiembre... 09 y 2026 en número" -- SÍ lleva cero a la
    izquierda en el día (a diferencia del primer pedido, que decía "9"
    sin cero -- este formato con cero es el vigente). Usado en la
    esquina de la card de cabecera de Ficha de Marca. None/NaT -> "" (el
    caller decide si omite el bloque entero en vez de mostrar una cadena
    vacía con su propia etiqueta al lado).
    """
    if ts is None or pd.isna(ts):
        return ""
    return f"{ts.day:02d} de {_MESES_ES[ts.month]} del {ts.year}"


def fmt_fecha_ddmmaaaa(ts):
    """
    "09/09/2026" -- pedido explícito de Sabas (trigésima sexta vuelta,
    para la columna "Último contacto" de la tabla Smart Priorities, a
    diferencia de fmt_fecha_es que se usa en la card de cabecera): "ahí
    sí la vas a colocar en formato fecha. Es decir, día, slash, número
    del mes, slash, número del año". Ambos con cero a la izquierda.
    None/NaT -> "—" (mismo placeholder que el resto de columnas de esta
    tabla cuando no hay dato -- ver smart_priorities_for).
    """
    if ts is None or pd.isna(ts):
        return "—"
    return f"{ts.day:02d}/{ts.month:02d}/{ts.year}"


def md_tactical_card(key, active, roi, campaign_name, mdpro=False):
    """
    Card Markdown (o Markdown Pro si mdpro=True) de 360 Action.

    Pedido explicito de Sabas (agosto 2026): en vez de dar un consejo
    generico tipo "Proponé un upselling simbólico..." cuando MD esta
    activo, se lee directamente que accion pide Priority Data para esta
    marca (columna Descripción de la fila Metric=Promos (Markdown) /
    Promos Pro): Adquisición, Optimización, Upselling, o el texto tal cual
    si es otra cosa (Reactivación, Retención, etc. -- ver
    _clasificar_accion_priority). Si es Adquisición o Upselling, se agrega
    la nota "Revisá Campaign Designer para definir estrategia"; si es
    Optimización u otro texto, no.

    Sin señal en Priority Data para esta marca: se mantiene el criterio
    viejo, sin inventar consejo -- solo "Seguimiento" (si ya hay campaña
    activa) o "Sin campaña aún" (si no hay).

    Ítems de Promos (pedido explícito de Sabas, trigésima sexta vuelta,
    corrigiendo el diseño anterior: "como estás colocando promos vencidas
    como un ítem, promos por vencer debe ser otro ítem también. No debe
    ser un ítem completo para las dos"): DOS ítems independientes, no uno
    combinado -- "Promos vencidas" y "Promos por vencer" son entradas
    separadas en "items", cada una con su propia regla FIJA:
      - "Promo vencida" sin dato -> ("Promos vencidas", "", "HEALTHY")
        (chulito). Con dato -> ("Promos vencidas", "<ids tal cual, \\n ->
        \", \">", "ALERT") -- SIEMPRE alerta si hay dato, fijo.
      - "Promo por vencer" sin dato -> ("Promos por vencer", "",
        "HEALTHY") (chulito). Con dato -> ("Promos por vencer", "<ids>",
        "WATCH") -- SIEMPRE watch si hay dato, fijo. Independiente de si
        "Promo vencida" también tiene dato o no -- ya no se combinan en
        un solo texto como en el diseño anterior.
      Formato de cada tupla: (titulo, contenido, estado) -- 3 elementos,
      NO 2 como el resto de "items" de OPS/Menú (ver _bullet_html/
      _action_mini en wingmanapp.py, que distingue por longitud de
      tupla). Pedido explícito: "lo único que va en negrita es el
      título... los números de los códigos van en gris normal, sin
      negrita" -- por eso el título y el contenido van en campos
      separados, para que el render les dé peso distinto SIEMPRE
      (incluso en ALERT/WATCH), a diferencia del resto de items de esta
      app donde todo el texto entra o sale de negrita junto.
      El PEOR estado entre estos dos items entra en el cálculo del tag
      final de la card completa, mismo criterio YA usado en
      ops_tactical_card ("el peor de los items domina") -- una promo
      vencida por sí sola alcanza para subir toda la card a ALERT aunque
      el resto (Adquisición/Optimización/Seguimiento) hubiera dado
      HEALTHY.
    """
    kind = "md_pro" if mdpro else "md"
    nombre = "Markdown Pro" if mdpro else "Markdown"
    descripcion = _priority_descripcion_for(key, kind)
    accion, mostrar_nota = _clasificar_accion_priority(descripcion)

    promo_vencida, promo_por_vencer = _priority_promos_for(key, kind)
    if promo_vencida:
        item_vencida = ("Promos vencidas", promo_vencida.replace("\n", ", "), "ALERT")
    else:
        item_vencida = ("Promos vencidas", "", "HEALTHY")
    if promo_por_vencer:
        item_por_vencer = ("Promos por vencer", promo_por_vencer.replace("\n", ", "), "WATCH")
    else:
        item_por_vencer = ("Promos por vencer", "", "HEALTHY")
    promo_items = [item_vencida, item_por_vencer]
    promo_estado_peor = "ALERT" if promo_vencida else ("WATCH" if promo_por_vencer else "HEALTHY")

    def _peor_tag(tag_base, tag_promo):
        orden = {"ALERT": 3, "WATCH": 2, "HEALTHY": 1, "INACTIVE": 0}
        return tag_base if orden.get(tag_base, 0) >= orden.get(tag_promo, 0) else tag_promo

    if not accion:
        if active:
            tag = _peor_tag("HEALTHY", promo_estado_peor)
            return {"title": nombre, "detail": "Seguimiento", "tag": tag, "items": promo_items}
        # Sin campaña activa Y Priority Data no la pide -- pedido
        # explícito de Sabas (agosto 2026): estado neutro INACTIVE (gris),
        # no WATCH, con la nota especifica. La promo vencida/por vencer
        # igual puede escalar esto -- una marca inactiva en Ads/MD puede
        # perfectamente tener una campaña vieja que quedó vencida.
        tag = _peor_tag("INACTIVE", promo_estado_peor)
        return {
            "title": f"{nombre} · Inactivo",
            "detail": "No hay prioridad comercial ahora, pero revisa qué le puedes ofrecer al aliado.",
            "tag": tag,
            "items": promo_items,
        }

    title = f"{nombre} · {accion}"
    detail = accion
    if active and roi:
        detail += f" · ROI {fmt_roi(roi)}"
    if campaign_name and campaign_name != "-":
        detail += f" · Campaña: {campaign_name}."
    if mostrar_nota:
        detail += " Revisá Campaign Designer para definir estrategia."
    tag_base = "WATCH" if accion in ("Adquisición", "Optimización") else "HEALTHY"
    tag = _peor_tag(tag_base, promo_estado_peor)
    return {"title": title, "detail": detail, "tag": tag, "items": promo_items}


def ads_tactical_card(key, active, roas, bookings_ars, currency="ARS"):
    """
    Card Ads de 360 Action. Mismo criterio que md_tactical_card (pedido
    explicito de Sabas, agosto 2026): se lee la Descripción real de la fila
    Metric=Ads en Priority Data (Adquisición/Optimización/Upselling/otro,
    ver _clasificar_accion_priority) en vez de un mensaje generico. Con
    Adquisición o Upselling se agrega la nota de Campaign Designer.

    Sin señal en Priority Data para esta marca: igual que antes, sin
    inventar consejo -- solo "Seguimiento" o "Sin campaña aún".
    """
    descripcion = _priority_descripcion_for(key, "ads")
    accion, mostrar_nota = _clasificar_accion_priority(descripcion)

    if not accion:
        if active:
            return {"title": "Ads", "detail": "Seguimiento", "tag": "HEALTHY"}
        # Sin campaña activa Y Priority Data no la pide -- mismo criterio
        # que Markdown, pedido explícito de Sabas (agosto 2026).
        return {
            "title": "Ads · Inactivo",
            "detail": "No hay prioridad comercial ahora, pero revisa qué le puedes ofrecer al aliado.",
            "tag": "INACTIVE",
        }

    title = f"Ads · {accion}"
    if active:
        detail = f"{accion} · Booking {fmt_money(bookings_ars, currency)} · ROI {fmt_roi(roas)}"
    else:
        detail = f"{accion} · Sin pauta activa este mes"
    if mostrar_nota:
        detail += " Revisá Campaign Designer para definir estrategia."
    tag = "WATCH" if accion in ("Adquisición", "Optimización") else "HEALTHY"
    return {"title": title, "detail": detail, "tag": tag}


BUCKET_LABELS = {
    "ops": "⚙️ OPS", "menu": "🍔 Menu", "md": "🏷️ Markdown",
    "mdpro": "👑 MD PRO", "ads": "🚀 Ads",
}


@st.cache_data(ttl=86400, show_spinner=False)
def priority_overview_counts(farmer_email=None):
    """Cuentas de marcas por palanca. Si se pasa farmer, filtra a su cartera."""
    df = load_priority()
    if df.empty:
        return {k: 0 for k in BUCKET_LABELS}
    if farmer_email:
        keys = set(portfolio_for(farmer_email)["key"])
        df = df[df["key"].isin(keys)]
    counts = df[df["bucket"].isin(BUCKET_LABELS)].groupby("bucket")["key"].nunique()
    return {k: int(counts.get(k, 0)) for k in BUCKET_LABELS}


@st.cache_data(ttl=86400, show_spinner=False)
def priority_table(farmer_email, bucket=None):
    """
    Tabla de aterrizaje: una fila por marca con al menos una señal en `bucket`
    (o en cualquier bucket si es None), ordenada por score de mayor a menor.
    """
    asig = portfolio_for(farmer_email)
    if asig.empty:
        return pd.DataFrame()

    df = load_priority()
    if df.empty:
        return pd.DataFrame()

    df = df[df["key"].isin(set(asig["key"]))]
    if bucket:
        df = df[df["bucket"] == bucket]
    if df.empty:
        return pd.DataFrame()

    names = dict(zip(asig["key"], asig["brand_name"]))
    ids   = dict(zip(asig["key"], asig["brand_id"]))

    rows = []
    for key, g in df.sort_values("value", ascending=False).groupby("key"):
        top = g.iloc[0]
        signals = " | ".join(f"{r.label} ({r.value:.2f})" for r in g.head(4).itertuples())
        rows.append({
            "key": key,
            "brand_id": ids.get(key, key),
            "brand_name": names.get(key, key),
            "score": g["value"].sum(),
            "main_signal": top["label"],
            "signals": signals,
        })
    out = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


# =========================
# SEASONAL EVENTS
# =========================

@st.cache_data(ttl=86400, show_spinner=False)
def load_seasonal():
    return _read("seasonal")


# =========================
# CHURN — estado por marca (PW1 / Prevention W2 / Prevention W3 / Churn)
# =========================
# La hoja trae varias semanas por marca (una fila por semana en que aparecio
# con riesgo). Nos quedamos con el estado de la semana MAS RECIENTE por marca,
# no todas las filas -- una marca puede pasar de PW1 a Churn entre semanas.

CHURN_LABELS = {
    "pw1": "PW1",
    "prevention w2": "PW2",
    "prevention w3": "PW3",
    "churn": "Churn",
}


@st.cache_data(ttl=86400, show_spinner=False)
def load_churn():
    df = _read("churn")
    if df.empty:
        return df

    c_id    = pick_col(df, "COUNTRY_BRAND_ID", "brand id")
    c_week  = pick_col(df, "WEEK")
    c_state = pick_col(df, "Estado Actual", "estado actual")
    if not (c_id and c_state):
        _issue("CHURN", "No encuentro COUNTRY_BRAND_ID o Estado Actual")
        return pd.DataFrame()

    out = pd.DataFrame()
    out["key"]   = df[c_id].apply(brand_key)
    out["week"]  = pd.to_datetime(df[c_week], errors="coerce") if c_week else pd.NaT
    out["state"] = df[c_state].astype(str).str.strip()

    out = out[out["key"] != ""]
    out["label"] = out["state"].apply(lambda s: CHURN_LABELS.get(normalize(s), s))

    # Estado mas reciente por marca (mayor WEEK). Si WEEK falta, se queda con
    # la ultima fila que aparezca para esa marca.
    out = out.sort_values("week").drop_duplicates(subset="key", keep="last")
    return out[["key", "label"]].reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def churn_map():
    """{brand_key: 'PW1'|'PW2'|'PW3'|'Churn'} -- solo marcas con riesgo activo."""
    df = load_churn()
    if df.empty:
        return {}
    return dict(zip(df["key"], df["label"]))


def brand_coverage_for(farmer_emails):
    """
    Brand Coverage · Live de uno o varios Farmers: % de la cartera combinada
    con cada palanca activa/en riesgo. Mismo criterio que Growth OS
    (get_live_campaign_coverage_counts).

    farmer_emails: un email (str) para el caso de siempre (un Farmer), o una
    lista de emails para la vista de Supervisor (agregado por pais via
    farmers_por_pais). Los portfolio_for de cada farmer se CONCATENAN antes
    de calcular los % -- no se promedian los % ya calculados de cada farmer
    por separado, porque eso pesaria igual a un farmer con 20 marcas que a
    uno con 250 (promedio de promedios, matematicamente incorrecto).

    6 donuts: Ads, Markdown, Markdown PRO, PW1, PW2, Churn.
    OJO: PW2 hoy siempre da 0% -- el export actual de la hoja CHURN solo trae
    los estados PW1 y Churn, ningun caso real de PW2/PW3 todavia (confirmado
    en sesiones anteriores). No es un bug, es que el dato no existe aun.

    Blindado con try/except: un Excel real puede traer la hoja CHURN con
    columnas/formato distinto al que se probó en desarrollo (bug real
    reportado: AttributeError en produccion que no se pudo reproducir en
    local con el mismo archivo -- puede ser una version de pandas distinta
    en el servidor, o una fila/valor inesperado en el Excel real). Mejor
    mostrar el dashboard con 0% que tumbar toda la pantalla de Management
    Dashboard por un problema en un solo calculo.
    """
    base = {
        "total": 0,
        "ads": 0, "md": 0, "mdpro": 0, "pw1": 0, "pw2": 0, "churn": 0,
        "ads_n": 0, "md_n": 0, "mdpro_n": 0, "pw1_n": 0, "pw2_n": 0, "churn_n": 0,
    }
    try:
        emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
        portfolios = [portfolio_for(e) for e in emails]
        portfolios = [p for p in portfolios if not p.empty]
        if not portfolios:
            return base
        p = pd.concat(portfolios, ignore_index=True) if len(portfolios) > 1 else portfolios[0]

        total = len(p)
        cmap = churn_map()
        churn_estado = p["key"].map(cmap).astype(object)

        ads_mask   = p["bookings"] > 0
        md_mask    = p["markdown_md"] > 0
        mdpro_mask = p["markdown_mdpro"] > 0
        pw1_mask   = churn_estado == "PW1"
        pw2_mask   = churn_estado == "PW2"
        churn_mask = churn_estado == "Churn"

        return {
            "total": total,
            "ads":   float(ads_mask.mean()),
            "md":    float(md_mask.mean()),
            "mdpro": float(mdpro_mask.mean()),
            "pw1":   float(pw1_mask.mean()),
            "pw2":   float(pw2_mask.mean()),
            "churn": float(churn_mask.mean()),
            # Conteos absolutos -- para mostrar "34% · 84 marcas" debajo de
            # cada donut, no solo el porcentaje (pedido explícito de Sabas).
            "ads_n":   int(ads_mask.sum()),
            "md_n":    int(md_mask.sum()),
            "mdpro_n": int(mdpro_mask.sum()),
            "pw1_n":   int(pw1_mask.sum()),
            "pw2_n":   int(pw2_mask.sum()),
            "churn_n": int(churn_mask.sum()),
        }
    except Exception as e:
        _issue("Brand Coverage", f"No pude calcular Brand Coverage para {farmer_emails}: {e}")
        return base


@st.cache_data(ttl=86400, show_spinner=False)
def load_productivity():
    """
    Hoja PRODUCTIVITY: un registro de contacto/gestión por marca/semana, con
    Farmer, canal, si fue efectivo, y el detalle de gestión de Ads/Markdown
    de ese día. Fuente real de Contact Performance (mismo criterio que
    Growth OS -- _load_productivity_contact_stats) y de las conversiones
    de Ads/MD (ver conversion_for()).
    """
    df = _read("productivity")
    if df.empty:
        return df

    c_farmer = pick_col(df, "Farmer")
    c_medio  = pick_col(df, "Medio de Contacto")
    c_cont   = pick_col(df, "¿Contactado?", "Contactado")
    c_date   = pick_col(df, "Date")
    if not (c_farmer and c_medio and c_cont):
        _issue("PRODUCTIVITY", "Falta Farmer, Medio de Contacto o ¿Contactado?")
        return pd.DataFrame()

    c_ads       = pick_col(df, "Ads")
    c_tipo_ads  = pick_col(df, "Tipo Ads")
    c_never_ads = pick_col(df, "Tipo Never Ads")
    c_md        = pick_col(df, "Markdown")
    c_md_ok     = pick_col(df, "¿Se aceptó lo ofrecido?", "Se aceptó lo ofrecido")

    out = pd.DataFrame()
    out["farmer"]     = df[c_farmer].astype(str).str.strip().str.lower()
    out["medio"]      = df[c_medio].astype(str).str.strip().str.lower()
    out["contactado"] = df[c_cont].astype(str).str.strip().str.upper()
    out["date"]       = pd.to_datetime(df[c_date], errors="coerce") if c_date else pd.NaT
    out["ads"]        = df[c_ads].astype(str).str.strip().str.upper() if c_ads else ""
    out["tipo_ads"]   = df[c_tipo_ads].astype(str).str.strip() if c_tipo_ads else ""
    out["never_ads"]  = df[c_never_ads].astype(str).str.strip().str.lower() if c_never_ads else ""
    out["md"]         = df[c_md].astype(str).str.strip().str.upper() if c_md else ""
    out["md_aceptado"] = df[c_md_ok].astype(str).str.strip() if c_md_ok else ""
    for c in ("tipo_ads", "never_ads", "md_aceptado"):
        out[c] = out[c].replace({"nan": "", "none": "", "None": "", "NaN": ""})

    out = out[out["farmer"] != ""]
    return out.reset_index(drop=True)


def _effective_start_of_month(d):
    """
    Devuelve el inicio de mes a usar como corte para conversion_for y
    contact_performance_for. Por default es el mes calendario actual
    (comportamiento original). Si ese mes no tiene NINGUNA fila con fecha
    dentro de él (Excel todavía no actualizado, ej. 1° de agosto con solo
    julio cargado), cae automáticamente al mes de la fecha más reciente
    presente en `d`, en vez de dejar el corte en 0 gestiones.

    `d` debe ser el dataframe YA filtrado por farmer, con columna "date"
    (Timestamp o NaT). No filtra `d`, solo decide qué fecha de corte usar.
    """
    now_start = pd.Timestamp.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    dates = d["date"].dropna()
    if dates.empty:
        return now_start

    has_current_month = (dates >= now_start).any()
    if has_current_month:
        return now_start

    latest = dates.max()
    return latest.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# Feriados NACIONALES que caen en día hábil (L-V) y por lo tanto hay que
# restar del conteo -- pedido explícito de Sabas (agosto 2026, séptimo
# ajuste): "17 de agosto fue feriado en Argentina, no hábil, rompe las
# cuentas". Por país -- Wingman opera Cono Sur (AR/CL/UY) y NO todos
# comparten el mismo feriado el mismo día (confirmado explícito: "rómpelo
# SOLO para Argentina"). Si en algún momento hace falta un feriado de
# CL o UY, se agrega como una clave más de este mismo dict, sin tocar
# la lógica de _pace_dias_habiles.
FERIADOS_POR_PAIS = {
    "AR": {
        pd.Timestamp("2026-08-17"),  # Paso a la Inmortalidad del Gral. San Martín (trasladado)
    },
}


def _pace_dias_habiles(start_of_month, pais=None):
    """
    Días hábiles (lunes a viernes, menos feriados nacionales de
    FERIADOS_POR_PAIS) transcurridos y totales del mes de start_of_month
    -- para la barra de "Pace" de Contact Performance (pedido explícito
    de Sabas, agosto 2026).

    `pais` (nuevo, séptimo ajuste): si se pasa, se restan del conteo los
    feriados de FERIADOS_POR_PAIS[pais] que caigan en el rango. Sin
    `pais` (default None), el comportamiento es igual que antes de este
    ajuste -- L-V puro, sin feriados -- para no romper ningún call-site
    que todavía no pasa el país explícito.

    "Transcurridos" cuenta hasta AYER, no hasta hoy -- pedido explícito
    de Sabas (agosto 2026, sexto ajuste): "el día de hoy no cuenta como
    transcurrido hasta que termine, se ve reflejado recién al día
    siguiente". Antes contaba hasta hoy inclusive, lo que mezclaba
    gestiones de un día TODAVÍA EN CURSO (parcial, ej. las 10pm de
    Colombia todavía no es medianoche en el reloj del Farmer) con el
    resto de días ya cerrados -- el ritmo quedaba inflado o distorsionado
    por un día que aún no había terminado de acumular datos reales.

    Caso límite (pedido explícito): si hoy es el PRIMER día hábil del mes,
    "hasta ayer" daría 0 -- se usa 1 como mínimo (excepción solo para
    este caso, para no dividir por cero), no se abre ninguna otra
    excepción.

    "Totales" depende de si start_of_month es el MES CALENDARIO ACTUAL o
    un mes ya cerrado (mostrado por fallback de _effective_start_of_month
    cuando el mes en curso aun no tiene datos, ej. 2 de agosto mostrando
    julio completo):
      - Mes actual: días hábiles desde el 1 hasta AYER inclusive (ver
        arriba), mínimo 1.
      - Mes cerrado (start_of_month < mes calendario actual): el mes
        completo ya pasó, transcurridos = totales -- el pace es
        simplemente el resultado final, sin proyección (pedido explícito
        de Sabas: "mostrar el pace igual, con base en los días que tuvo
        julio completo").
    """
    hoy = pd.Timestamp.now().normalize()
    ayer = hoy - pd.Timedelta(days=1)
    fin_mes = (start_of_month + pd.offsets.MonthEnd(0)).normalize()
    es_mes_actual = start_of_month.year == hoy.year and start_of_month.month == hoy.month

    feriados = FERIADOS_POR_PAIS.get(pais, set()) if pais else set()

    def _bdate_range_sin_feriados(desde, hasta):
        rango = pd.bdate_range(desde, hasta)
        if feriados:
            rango = rango[~rango.isin(feriados)]
        return rango

    totales = len(_bdate_range_sin_feriados(start_of_month, fin_mes))
    if es_mes_actual:
        limite = min(ayer, fin_mes)
        transcurridos = len(_bdate_range_sin_feriados(start_of_month, limite)) if limite >= start_of_month else 0
        transcurridos = max(transcurridos, 1)  # minimo 1 -- evita division por cero el primer dia habil del mes
    else:
        transcurridos = totales

    return transcurridos, totales


def pace_color(pace_pct):
    """Verde >94%, azul 90-94%, rojo <90% -- pedido explícito de Sabas.
    Usado por Contactos Efectivos. Para Adquisición/Upselling Ads, ver
    pace_color_ads_upsell (semáforo distinto, agosto 2026, octava
    vuelta)."""
    if pace_pct > 94:
        return "green"
    if pace_pct >= 90:
        return "blue"
    return "red"


def pace_color_ads_upsell(pace_pct):
    """
    Semáforo de RITMO propio de "Adquisición Ads" y "Upselling Ads"
    (agosto 2026, octava vuelta -- pedido explícito de Sabas): rojo <80%,
    azul 81-90%, verde 91-105%, MORADO >105% (un cuarto nivel que
    pace_color no tiene, para distinguir un ritmo sobresaliente del
    simplemente "en línea"). Deliberadamente SEPARADA de pace_color (que
    sigue con su semáforo de 3 colores: rojo<90/azul90-94/verde>94) --
    Sabas confirmó explícitamente que Contactos Efectivos NO cambia, solo
    estas dos columnas/donuts. No reemplazar pace_color en las llamadas
    de Adquisición/Upselling por accidente en el futuro; son funciones
    intencionalmente distintas con umbrales distintos.
    """
    if pace_pct > 105:
        return "purple"
    if pace_pct >= 91:
        return "green"
    if pace_pct >= 81:
        return "blue"
    return "red"


@st.cache_data(ttl=86400, show_spinner=False)
def load_prod_target():
    """
    PROD TARGET: target mensual de contactos/gestiones por Farmer. Formato
    real (agosto 2026): fila 1 es "MONTH | | | fecha" (no es header), el
    header real esta en la fila 2 -- se lee con skiprows=1.

    Filas de "Total" (subtotal por lider/pais) se descartan -- solo importa
    la fila por FARMER individual.

    IMPORTANTE: el export trae a Oscar Pedraza como lider separado de su
    propio grupo (12 farmers AR+UY), pero en Wingman TODOS estan bajo
    Fabián como unico supervisor (pedido explicito de Sabas, agosto 2026:
    "es dato crudo de Rappi, ignora la separación Oscar/Fabián"). Por eso
    esta funcion NO expone ni usa la columna LÍDER -- el target se toma
    igual sin importar si el export dice que reporta a Oscar o a Fabián.

    Tambien incluye a arnold.camino y claudia.pineda (en EQUIPO_BAJA, sin
    acceso a Wingman) -- se filtran solos al cruzar contra farmers activos
    en target_for(), no hace falta filtrarlos aca.
    """
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame(columns=["farmer", "target"])
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS["prod_target"], skiprows=1)
    except Exception as e:
        _issue(SHEETS["prod_target"], e)
        return pd.DataFrame(columns=["farmer", "target"])
    if df.empty:
        return pd.DataFrame(columns=["farmer", "target"])

    c_farmer = pick_col(df, "FARMER", "farmer")
    c_target = pick_col(df, "Tgt. Monthly", "tgt monthly", "target")
    if not (c_farmer and c_target):
        _issue(SHEETS["prod_target"], "Falta FARMER o Tgt. Monthly")
        return pd.DataFrame(columns=["farmer", "target"])

    out = pd.DataFrame()
    out["farmer"] = df[c_farmer]
    out["target"] = df[c_target].apply(to_num)
    out = out[out["farmer"].notna()]
    out["farmer"] = out["farmer"].astype(str).str.strip().str.lower()
    out = out[out["farmer"].str.match(r"^[\w.\-]+@[\w.\-]+\.\w+$", na=False)]  # exige que TODA la celda sea un email valido (no que solo lo contenga -- el pie de pagina "Filtros aplicados..." tambien contiene @rappi.com adentro del texto)
    return out.drop_duplicates(subset=["farmer"]).reset_index(drop=True)


def target_for(farmer_emails):
    """
    Target mensual combinado para un farmer o lista de farmers (mismo
    patron que brand_coverage_for/contact_performance_for). Suma el target
    de cada uno -- para un Farmer individual es simplemente su propio
    target.
    """
    tgt = load_prod_target()
    if tgt.empty:
        return 0
    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    return float(tgt[tgt["farmer"].isin(emails)]["target"].sum())


@st.cache_data(ttl=86400, show_spinner=False)
def load_export_ads_relation():
    """
    EXPORT ADS RELATION: mismo export que EXPORT ADS KAM pero a nivel
    BRAND (una fila por marca, no un agregado por Farmer) -- fuente para
    "Adquisición Ads" (pedido explícito de Sabas, agosto 2026, reemplaza
    la columna "Conversión Ads" en Rendimiento País/Farmer).

    Header: KAM, BRAND, Bookings Totales, Bookings Totales Corregidos,
    Bookings Reales (Sin Bookings Gratis), Bookings Reales Corregidos
    (Sin Bookings Gratis), Targets Bookings, ... Trae una fila "Total" por
    KAM y una fila "Total" general al cierre -- se descartan junto con el
    pie de pagina de filtros (mismo criterio que el resto de exports).

    Una marca es "adquisición pendiente" (todavia no convertida este mes)
    si Targets Bookings > 0 Y las 4 columnas de Bookings (Totales,
    Totales Corregidos, Reales sin gratis, Reales Corregidos sin gratis)
    estan en 0 -- confirmado con Sabas cruzando manualmente contra
    ASIGNACION antes de que este export trajera el KAM directo.
    """
    cols = ["farmer", "brand", "bookings_totales", "bookings_totales_corr",
            "bookings_reales", "bookings_reales_corr", "target_bookings"]
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS["export_ads_relation"])
    except Exception as e:
        _issue(SHEETS["export_ads_relation"], e)
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)

    c_farmer = pick_col(df, "KAM", "farmer")
    c_brand  = pick_col(df, "BRAND", "brand")
    c_b_tot  = pick_col(df, "Bookings Totales")
    c_b_totc = pick_col(df, "Bookings Totales Corregidos")
    c_b_real = pick_col(df, "Bookings Reales (Sin Bookings Gratis)")
    c_b_realc = pick_col(df, "Bookings Reales Corregidos (Sin Bookings Gratis)")
    c_tgt_b  = pick_col(df, "Targets Bookings", "target bookings")
    if not (c_farmer and c_brand and c_tgt_b):
        _issue(SHEETS["export_ads_relation"], "Falta KAM, BRAND o Targets Bookings")
        return pd.DataFrame(columns=cols)

    out = pd.DataFrame()
    out["farmer"] = df[c_farmer]
    out["brand"] = df[c_brand]
    out["bookings_totales"] = df[c_b_tot].apply(to_num) if c_b_tot else 0.0
    out["bookings_totales_corr"] = df[c_b_totc].apply(to_num) if c_b_totc else 0.0
    out["bookings_reales"] = df[c_b_real].apply(to_num) if c_b_real else 0.0
    out["bookings_reales_corr"] = df[c_b_realc].apply(to_num) if c_b_realc else 0.0
    out["target_bookings"] = df[c_tgt_b].apply(to_num)

    out = out[out["farmer"].notna() & out["brand"].notna()]
    out["farmer"] = out["farmer"].astype(str).str.strip().str.lower()
    # descarta filas "Total" (por KAM y la general de cierre) y el pie de
    # pagina de filtros -- mismo criterio que el resto de exports: exige
    # que TODA la celda de farmer sea un email valido.
    out = out[out["farmer"].str.match(r"^[\w.\-]+@[\w.\-]+\.\w+$", na=False)]
    out = out[out["brand"].astype(str).str.strip().str.lower() != "total"]
    return out.reset_index(drop=True)


def _dias_habiles_totales_mes():
    """
    Días hábiles TOTALES del mes calendario actual (L-V, sin festivos) --
    usado como PISO mínimo para las metas de Adquisición/Upselling Ads
    (pedido explícito de Sabas, agosto 2026): "un mínimo diario por cada
    día hábil del mes", para que ningún farmer reciba una meta
    artificialmente baja (ej. Fanny con solo 5 marcas necesarias para
    cerrar su gap) que no representa trabajo real de un mes completo.

    Reusa _pace_dias_habiles con el 1° del mes actual -- toma solo el
    segundo valor (totales), no el de transcurridos.
    """
    inicio_mes = pd.Timestamp.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _, totales = _pace_dias_habiles(inicio_mes, pais=PAIS)
    return totales


def _camino_mas_corto(d, tipo):
    """
    Dado el dataframe YA FILTRADO por farmer(s) de load_export_ads_relation,
    devuelve la cantidad MÍNIMA de marcas de `tipo` ("adquisicion" o
    "upsell") necesarias para cerrar el gap USD real del farmer (Target -
    Bookings Reales Corregidos, sobre TODA la cartera), priorizando
    siempre las marcas de MAYOR gap individual primero -- mismo criterio
    de "camino más corto" validado con Sabas para Lucho y Diana antes de
    llevarlo a código.

    Combina candidatos de AMBOS tipos (adquisición + upsell) en un solo
    ranking por gap descendente para decidir cuántas marcas hacen falta
    en TOTAL, y de ese conjunto cuenta cuántas son del `tipo` pedido --
    así "cuántas adquisiciones necesito" y "cuántos upsells necesito" son
    consistentes entre sí (sumados dan el mismo camino completo), en vez
    de calcular cada meta de forma aislada contra el gap total completo
    (lo cual doblaría el conteo -- ver conversación agosto 2026 donde se
    detectó que sumar el gap de adquisición + upsell por separado no
    cuadraba con el gap real total, por el solapamiento de marcas que
    sobre-cumplen compensando a otras).
    """
    if d.empty:
        return 0

    target_total = d["target_bookings"].sum()
    real_total = d["bookings_reales_corr"].sum()
    gap_total = target_total - real_total
    if gap_total <= 0:
        return 0

    es_adq = (
        (d["target_bookings"] > 0)
        & (d["bookings_totales"] == 0)
        & (d["bookings_totales_corr"] == 0)
        & (d["bookings_reales"] == 0)
        & (d["bookings_reales_corr"] == 0)
    )
    adq = d[es_adq].copy()
    adq["gap"] = adq["target_bookings"]
    adq["tipo"] = "adquisicion"

    es_ups = (d["bookings_reales_corr"] > 0) & (d["bookings_reales_corr"] < d["target_bookings"])
    ups = d[es_ups].copy()
    ups["gap"] = ups["target_bookings"] - ups["bookings_reales_corr"]
    ups["tipo"] = "upsell"

    combo = pd.concat([adq[["gap", "tipo"]], ups[["gap", "tipo"]]])
    if combo.empty:
        return 0
    combo = combo.sort_values("gap", ascending=False).reset_index(drop=True)
    combo["acumulado"] = combo["gap"].cumsum()

    alcanzadas = combo[combo["acumulado"] <= gap_total]
    n_necesarias = len(alcanzadas) + 1 if len(alcanzadas) < len(combo) else len(combo)
    subset = combo.iloc[:n_necesarias]

    return int((subset["tipo"] == tipo).sum())


@st.cache_data(ttl=86400, show_spinner=False)
def load_checkout():
    """
    CHECKOUT: registro de conversiones REALES de Ads este mes, una fila
    por marca cerrada -- fuente del NUMERADOR de "Adquisición Ads" y
    "Upselling Ads" (pedido explícito de Sabas, agosto 2026, cuarta
    vuelta -- reemplaza a PRODUCTIVITY como fuente del numerador de
    Adquisición, que hasta ahora usaba Never Ads convertidos).

    Columnas reales: Mes, Fecha, Semana, FARMER, Tipo de Contratacion
    (Upsell/Adquisicion), Brand ID, Coinversion, Presupuesto, Cargado en
    Manager.

    "Cargado en Manager" es solo trazabilidad para que el supervisor
    audite despues (numero = ya cargado en el Manager de Rappi, vacío =
    todavía no) -- NO afecta el conteo, toda fila de CHECKOUT es una
    conversión real independiente de si ya se cargó formalmente
    (confirmado explícitamente por Sabas, agosto 2026).

    "Fecha"/"Semana" vienen como enteros que NO corresponden a un serial
    de fecha de Excel estándar (46089 convierte a marzo 2026, no a
    agosto pese a que "Mes" dice "Agosto") -- confirmado con Sabas que no
    hay que resolver ese desfase: la hoja ya viene pre-filtrada al mes
    vigente por Rappi, así que NO se filtra por fecha/mes aquí, se cuenta
    toda la hoja tal cual.
    """
    cols = ["farmer", "tipo", "brand_id"]
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS["checkout"])
    except Exception as e:
        _issue(SHEETS["checkout"], e)
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)

    c_farmer = pick_col(df, "FARMER", "farmer")
    c_tipo   = pick_col(df, "Tipo de Contratacion", "Tipo de Contratación", "tipo de contratacion")
    c_brand  = pick_col(df, "Brand ID", "brand id")
    if not (c_farmer and c_tipo):
        _issue(SHEETS["checkout"], "Falta FARMER o Tipo de Contratacion")
        return pd.DataFrame(columns=cols)

    out = pd.DataFrame()
    out["farmer"] = df[c_farmer]
    out["tipo"] = df[c_tipo]
    out["brand_id"] = df[c_brand] if c_brand else None

    out = out[out["farmer"].notna() & out["tipo"].notna()]
    out["farmer"] = out["farmer"].astype(str).str.strip().str.lower()
    out = out[out["farmer"].str.match(r"^[\w.\-]+@[\w.\-]+\.\w+$", na=False)]  # exige que TODA la celda sea un email valido
    out["tipo"] = out["tipo"].astype(str).str.strip().str.lower()  # "Upsell"->"upsell", "Adquisicion"->"adquisicion"
    return out.reset_index(drop=True)


def adquisicion_ads_target_for(farmer_emails):
    """
    DENOMINADOR de "Adquisición Ads" (pedido explícito de Sabas, agosto
    2026, segunda vuelta -- reemplaza el criterio anterior de "todas las
    marcas en estado de adquisición pendiente").

    Ya NO es el conteo bruto de marcas en 0 -- es la cantidad MÍNIMA de
    adquisiciones necesarias para cerrar el gap USD real del farmer (ver
    _camino_mas_corto), con un PISO de un cierre por día hábil del mes
    (_dias_habiles_totales_mes) para que ningún farmer reciba una meta
    artificialmente chica que no representa un mes completo de trabajo
    (ej. un farmer con gap pequeño y pocas marcas de mucho valor no debe
    recibir meta de 5 -- el piso lo sube al mínimo de negocio).
    """
    rel = load_export_ads_relation()
    if rel.empty:
        return _dias_habiles_totales_mes()
    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    d = rel[rel["farmer"].isin(emails)]
    necesarias = _camino_mas_corto(d, "adquisicion")
    return max(necesarias, _dias_habiles_totales_mes())


def upselling_ads_target_for(farmer_emails):
    """
    DENOMINADOR de "Upselling Ads" (pedido explícito de Sabas, agosto
    2026) -- misma lógica que adquisicion_ads_target_for pero contando
    las marcas de tipo "upsell" del camino más corto. Mismo piso de un
    cierre por día hábil del mes.
    """
    rel = load_export_ads_relation()
    if rel.empty:
        return _dias_habiles_totales_mes()
    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    d = rel[rel["farmer"].isin(emails)]
    necesarias = _camino_mas_corto(d, "upsell")
    return max(necesarias, _dias_habiles_totales_mes())


def _checkout_count_for(farmer_emails, tipo):
    """
    Cuenta filas de CHECKOUT para un farmer/lista de farmers y un `tipo`
    ("adquisicion" o "upsell") -- función compartida por
    adquisicion_ads_for y upselling_ads_for para no duplicar el filtro.

    RECONSTRUIDA (correctivo, pedido explícito de Sabas tras detectar
    que "Adquisición Ads" y "Upselling Ads" mostraban 0/22-0% para casi
    todos los farmers en la tabla real): esta función se perdió en el
    mismo incidente de eliminación de Trabajables que rompió
    wingmanapp.py -- el try/except de adquisicion_ads_for/
    upselling_ads_for capturaba el NameError resultante en silencio y
    devolvía adq_n=0/ups_n=0 en cada llamada, sin traceback visible (a
    diferencia del NameError de wingmanapp.py, que sí rompía la
    pantalla). Recuperada tal cual del archivo de referencia que Sabas
    volvió a subir.
    """
    chk = load_checkout()
    if chk.empty:
        return 0
    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    d = chk[chk["farmer"].isin(emails) & (chk["tipo"] == tipo)]
    return len(d)


def adquisicion_ads_for(farmer_emails):
    """
    "Adquisición Ads": reemplaza a "Conversión Ads" en Rendimiento
    País/Farmer (pedido explícito de Sabas, agosto 2026).

    NUMERADOR (agosto 2026, cuarta vuelta -- CORREGIDO): ya NO sale de
    PRODUCTIVITY/Never Ads -- sale de CHECKOUT (load_checkout), contando
    filas con Tipo de Contratacion="Adquisicion" para el farmer. Cada
    fila de CHECKOUT es una conversión real confirmada; no se filtra por
    "Cargado en Manager" (ese campo es solo trazabilidad para auditoría
    del supervisor, confirmado explícitamente por Sabas -- no afecta el
    conteo). CHECKOUT ya viene pre-filtrada al mes vigente por Rappi, así
    que tampoco se filtra aquí por fecha.

    Historial del numerador (para no repetir el mismo error dos veces):
    1ra versión: TODOS los pitches Never Ads de PRODUCTIVITY (conviertan
    o no) -- INCORRECTO, medía intento no adquisición real.
    2da versión: Never Ads CONVERTIDOS de PRODUCTIVITY (excluyendo "No
    activo") -- correcto en su momento, pero PRODUCTIVITY mide gestión
    manual del farmer, no el checkout real de Rappi.
    3ra versión (actual): CHECKOUT -- fuente de verdad del sistema, ya no
    depende de que el farmer haya registrado bien su gestión en
    PRODUCTIVITY.

    DENOMINADOR: sale de adquisicion_ads_target_for() -- camino más corto
    para cerrar el gap real, con piso de días hábiles del mes. Ver
    _camino_mas_corto. (El denominador NO cambia con este ajuste, solo
    el numerador.)

    "adq_pct" se devuelve como RITMO/PACE proyectado (dias habiles, mismo
    criterio que Contactos Efectivos), no como avance directo.
    """
    base = {"adq_n": 0, "adq_target": 0, "adq_pct": 0.0}
    try:
        target = adquisicion_ads_target_for(farmer_emails)
        base["adq_target"] = target

        adq_n = _checkout_count_for(farmer_emails, "adquisicion")

        inicio_mes = pd.Timestamp.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        primer_email = farmer_emails if isinstance(farmer_emails, str) else next(iter(farmer_emails), None)
        pais = farmer_pais(primer_email) if primer_email else PAIS
        transcurridos, totales = _pace_dias_habiles(inicio_mes, pais=pais)
        adq_pct = (adq_n / transcurridos) * totales / target * 100 if target > 0 else 0.0

        return {"adq_n": adq_n, "adq_target": target, "adq_pct": adq_pct}
    except Exception as e:
        _issue("Adquisición Ads", f"No pude calcular adquisición Ads para {farmer_emails}: {e}")
        return base


def upselling_ads_for(farmer_emails):
    """
    "Upselling Ads": columna hermana de "Adquisición Ads" en Rendimiento
    País/Farmer (pedido explícito de Sabas, agosto 2026).

    NUMERADOR (agosto 2026, cuarta vuelta -- ya CONECTADO): sale de
    CHECKOUT (load_checkout), contando filas con Tipo de
    Contratacion="Upsell" para el farmer. Mismo criterio que Adquisición
    Ads -- ver _checkout_count_for y el docstring de adquisicion_ads_for
    para el detalle completo de por qué CHECKOUT y no PRODUCTIVITY.

    DENOMINADOR: sale de upselling_ads_target_for() -- camino más corto
    de marcas tipo "upsell" para cerrar el gap real, con piso de días
    hábiles del mes. Mismo criterio que Adquisición Ads.

    "ups_pct" se devuelve como RITMO/PACE proyectado (dias habiles),
    mismo criterio que Adquisición Ads y Contactos Efectivos.
    """
    base = {"ups_n": 0, "ups_target": 0, "ups_pct": 0.0}
    try:
        target = upselling_ads_target_for(farmer_emails)
        base["ups_target"] = target

        ups_n = _checkout_count_for(farmer_emails, "upsell")

        inicio_mes = pd.Timestamp.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        primer_email = farmer_emails if isinstance(farmer_emails, str) else next(iter(farmer_emails), None)
        pais = farmer_pais(primer_email) if primer_email else PAIS
        transcurridos, totales = _pace_dias_habiles(inicio_mes, pais=pais)
        ups_pct = (ups_n / transcurridos) * totales / target * 100 if target > 0 else 0.0

        return {"ups_n": ups_n, "ups_target": target, "ups_pct": ups_pct}
    except Exception as e:
        _issue("Upselling Ads", f"No pude calcular upselling Ads para {farmer_emails}: {e}")
        return base


@st.cache_data(ttl=86400, show_spinner=False)
def load_export_ads_kam():
    """
    EXPORT ADS KAM: Bookings/Revenue de Ads en USD por Farmer, con targets
    y % de cumplimiento (Attainment) ya calculados por Rappi. Header
    limpio en la fila 1 (a diferencia de PROD TARGET / EXPORT MD KAM, que
    necesitan skiprows=1).

    Igual que PROD TARGET: el export trae la separacion Oscar/Fabián por
    LIDER y una fila de "Total" general -- se descartan filas sin farmer
    valido, y esta funcion no expone LIDER (mismo criterio: en Wingman
    todos estan bajo Fabián, pedido explicito de Sabas agosto 2026).

    Los % de Attainment (att_bookings_pct, att_revenue_pct) ya vienen
    calculados en el Excel en formato decimal (1.12 = 112%), no hay que
    recalcularlos -- solo convertir a %.
    """
    cols = ["farmer", "target_bookings", "att_bookings_pct", "target_revenue", "att_revenue_pct"]
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS["export_ads_kam"])
    except Exception as e:
        _issue(SHEETS["export_ads_kam"], e)
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)

    c_farmer = pick_col(df, "KAM", "farmer")
    c_tgt_b  = pick_col(df, "Targets Bookings", "target bookings")
    c_att_b  = pick_col(df, "% Att. Bookings", "att bookings")
    c_tgt_r  = pick_col(df, "Target Revenue", "target revenue")
    c_att_r  = pick_col(df, "% Att. Revenue Real", "att revenue real")
    if not c_farmer:
        _issue(SHEETS["export_ads_kam"], "No encuentro columna KAM/farmer")
        return pd.DataFrame(columns=cols)

    out = pd.DataFrame()
    out["farmer"] = df[c_farmer]
    out["target_bookings"] = df[c_tgt_b].apply(to_num) if c_tgt_b else 0.0
    out["att_bookings_pct"] = df[c_att_b].apply(to_num) if c_att_b else 0.0
    out["target_revenue"] = df[c_tgt_r].apply(to_num) if c_tgt_r else 0.0
    out["att_revenue_pct"] = df[c_att_r].apply(to_num) if c_att_r else 0.0

    out = out[out["farmer"].notna()]
    out["farmer"] = out["farmer"].astype(str).str.strip().str.lower()
    out = out[out["farmer"].str.match(r"^[\w.\-]+@[\w.\-]+\.\w+$", na=False)]  # exige que TODA la celda sea un email valido (no que solo lo contenga -- el pie de pagina "Filtros aplicados..." tambien contiene @rappi.com adentro del texto)
    return out.drop_duplicates(subset=["farmer"]).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def load_export_md_kam():
    """
    EXPORT MD KAM: penetracion de Markdown (% del GMV en promo) por
    Farmer, MD Total y MD PRO por separado, con target de penetracion y
    Attainment ya calculados. Header real en la fila 2 -- skiprows=1
    (mismo formato que PROD TARGET).

    La columna "ATT %" se repite dos veces (una para MD Total, otra para
    MD PRO) -- la segunda trae un caracter invisible pegado al nombre
    ("ATT %ㅤ") en el export real. Se accede por POSICION dentro del
    bloque de columnas, no por pick_col(nombre), para no depender de que
    ese caracter se mantenga igual en el proximo export.
    """
    cols = ["farmer", "md_total_pct", "tgt_md_total_pct", "att_md_total_pct",
            "md_pro_pct", "tgt_md_pro_pct", "att_md_pro_pct"]
    if not os.path.exists(WORKBOOK):
        _issue("workbook", f"Falta {os.path.basename(WORKBOOK)} en data/")
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_excel(WORKBOOK, sheet_name=SHEETS["export_md_kam"], skiprows=1)
    except Exception as e:
        _issue(SHEETS["export_md_kam"], e)
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)

    col_list = list(df.columns)
    if len(col_list) < 9:
        _issue(SHEETS["export_md_kam"], "Formato inesperado (menos de 9 columnas)")
        return pd.DataFrame(columns=cols)

    # Orden fijo confirmado en el export real: BRAND_OWNER_EMAIL, MD TOTAL
    # ($), MD TOTAL (%), TGT % MD TOTAL, ATT %, MD PRO ($), MD PRO (%),
    # TGT % MD PRO, ATT % (con caracter invisible).
    c_farmer, _, c_md_pct, c_tgt_md, c_att_md, _, c_pro_pct, c_tgt_pro, c_att_pro = col_list[:9]

    out = pd.DataFrame()
    out["farmer"] = df[c_farmer]
    out["md_total_pct"] = df[c_md_pct].apply(to_num)
    out["tgt_md_total_pct"] = df[c_tgt_md].apply(to_num)
    out["att_md_total_pct"] = df[c_att_md].apply(to_num)
    out["md_pro_pct"] = df[c_pro_pct].apply(to_num)
    out["tgt_md_pro_pct"] = df[c_tgt_pro].apply(to_num)
    out["att_md_pro_pct"] = df[c_att_pro].apply(to_num)

    out = out[out["farmer"].notna()]
    out["farmer"] = out["farmer"].astype(str).str.strip().str.lower()
    out = out[out["farmer"].str.match(r"^[\w.\-]+@[\w.\-]+\.\w+$", na=False)]  # exige que TODA la celda sea un email valido (no que solo lo contenga -- el pie de pagina "Filtros aplicados..." tambien contiene @rappi.com adentro del texto)
    return out.drop_duplicates(subset=["farmer"]).reset_index(drop=True)


def _dias_calendario_mes(emails):
    """
    (dias_transcurridos, dias_totales) en DIAS CALENDARIO (no habiles) del
    mes efectivo de PRODUCTIVITY para este/estos farmer(s) -- extraido de
    ads_kam_for para reusar en el calculo de bookings_pace_pct y en
    comision_ads_proyectada_for. Mes cerrado (fallback a un mes pasado):
    transcurridos = totales, sin proyeccion (mismo criterio que el resto
    de "ritmo" en Wingman).

    "Transcurridos" cuenta hasta AYER, no hasta hoy -- mismo criterio que
    _pace_dias_habiles (pedido explícito de Sabas, agosto 2026, sexto
    ajuste): el día de hoy recién se refleja mañana, cuando ya cerró
    completo. Mínimo 1 para evitar división por cero en el primer día del
    mes.
    """
    prod = load_productivity()
    if prod.empty:
        return None, None
    d_prod = prod[prod["farmer"].isin(emails)]
    if d_prod.empty:
        return None, None
    start_of_month = _effective_start_of_month(d_prod)
    hoy = pd.Timestamp.now().normalize()
    ayer = hoy - pd.Timedelta(days=1)
    fin_mes = (start_of_month + pd.offsets.MonthEnd(0)).normalize()
    es_mes_actual = start_of_month.year == hoy.year and start_of_month.month == hoy.month
    dias_totales = fin_mes.day
    if es_mes_actual:
        dias_transcurridos = max(min(ayer.day, dias_totales) if ayer >= start_of_month else 0, 1)
    else:
        dias_transcurridos = dias_totales
    return dias_transcurridos, dias_totales


def att_esperado_hoy_pct(farmer_email):
    """
    Att% que HOY debería tener cualquier marca de este farmer, según el
    calendario (reparto lineal del mes: dias_transcurridos/dias_totales *
    100) -- pedido explícito de Sabas (agosto 2026, decimonovena vuelta)
    para la card "Palancas" de la ficha de marca (Ads: "Active 🚀"), que
    hasta ahora comparaba el Att% acumulado de la marca contra un umbral
    fijo (90%) sin tener en cuenta el punto del mes en el que estamos --
    mismo problema ya resuelto para Objetivo Ads Revenue en la tabla de
    Rendimiento País/Farmer (ver ads_kam_for), esta función expone el
    mismo cálculo de "Att esperado" para usarlo también a nivel de UNA
    marca individual (no el agregado del farmer completo).

    Recibe un solo email (no lista) porque esta card es siempre de un
    farmer puntual (el dueño de la marca que se está viendo). Devuelve
    None si no hay gestiones de PRODUCTIVITY para ese farmer este mes
    (mismo fallback que _dias_calendario_mes).
    """
    dias_transcurridos, dias_totales = _dias_calendario_mes({str(farmer_email).strip().lower()})
    if not dias_transcurridos or not dias_totales:
        return None
    return dias_transcurridos / dias_totales * 100



def ads_kam_for(farmer_emails):
    """
    Cumplimiento de Ads (Bookings y Revenue) para uno o varios Farmers,
    para la tabla "Rendimiento País" (pedido explícito de Sabas, agosto
    2026, reemplaza las columnas PW1/PW2/Churn).

    ESCALA DE RETORNO: att_bookings_pct, revenue_pace_pct y
    bookings_pace_pct ya vienen en escala 0-100 (112.4 = 112.4%), NO como
    fraccion 0-1 -- no multiplicar por 100 de nuevo al mostrarlos en la
    UI. (md_kam_for, en cambio, SI devuelve fraccion 0-1 -- son
    convenciones distintas entre las dos funciones, documentado aca para
    no confundirlas.)

    att_bookings_pct: cumplimiento DIRECTO del Excel (no proyectado) --
    esta es la columna que se muestra en Rendimiento País/Farmer.
    bookings_pace_pct: el mismo Bookings pero PROYECTADO por dias
    calendario transcurridos -- se agrega para comision_ads_proyectada_for
    (pedido explicito de Sabas, agosto 2026: "los ads por dias calendario
    en revenue" aplica igual a bookings para la proyeccion de comision).

    Revenue: se pide "ritmo" -- proyeccion segun DIAS CALENDARIO (no
    hábiles, a diferencia del ritmo de Contactos Efectivos) transcurridos
    del mes. El Excel actual (EXPORT ADS KAM) ya viene filtrado a julio
    COMPLETO (confirmado en el pie de pagina del export: "Date el o
    después del 01/07/2026 y antes del 01/08/2026"), asi que hoy el ritmo
    = el Attainment tal cual (mes cerrado, sin proyeccion posible, mismo
    criterio que ya se aplico a Contactos Efectivos). Cuando el Excel
    traiga un corte parcial de agosto, esta funcion detecta el mes real
    de _effective_start_of_month(PRODUCTIVITY) y proyecta: revenue_pace =
    att_revenue_pct * dias_totales / dias_transcurridos.

    Con varios farmers (vista Supervisor por pais): SUMA los targets y
    los % de cumplimiento reales (bookings/target y revenue/target
    agregados), no promedia los Attainment de cada uno -- mismo criterio
    que brand_coverage_for/contact_performance_for.
    """
    base = {"att_bookings_pct": None, "target_bookings": 0.0,
            "revenue_pace_pct": None, "target_revenue": 0.0,
            "bookings_pace_pct": None}
    kam = load_export_ads_kam()
    if kam.empty:
        return base

    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    d = kam[kam["farmer"].isin(emails)]
    if d.empty:
        return base

    target_bookings = float(d["target_bookings"].sum())
    target_revenue = float(d["target_revenue"].sum())
    # Bookings reales agregados = target * Att% de cada fila, sumado --
    # asi el % combinado pondera por tamaño de target, no promedia parejo
    # a un farmer chico con uno grande.
    bookings_reales = float((d["target_bookings"] * d["att_bookings_pct"]).sum())
    revenue_real = float((d["target_revenue"] * d["att_revenue_pct"]).sum())

    att_bookings_pct = (bookings_reales / target_bookings * 100) if target_bookings > 0 else None
    att_revenue_pct = (revenue_real / target_revenue * 100) if target_revenue > 0 else None

    dias_transcurridos, dias_totales = _dias_calendario_mes(emails)
    revenue_pace_pct = att_revenue_pct
    bookings_pace_pct = att_bookings_pct
    # att_*_esperado_pct (agosto 2026, decimoctava vuelta -- pedido
    # explícito de Sabas): "el Att% que HOY debería tener" según el
    # calendario (reparto lineal del mes: dias_transcurridos/dias_totales
    # * 100) -- el denominador de la nueva pill "Att real / Att esperado
    # - Pace%". Sabas señaló que mostrar solo el pace final (ej. "69%")
    # confunde al farmer: un 69% se lee como "voy bien" aunque el
    # farmer no tenga referencia de qué % correspondía a este punto del
    # mes -- mostrando explícitamente "18% / 21% - 86%" el farmer ve de
    # un vistazo que va CASI al día, no que "solo lleva 18%". Att
    # esperado y Att real dividido entre sí (att_real/att_esperado*100)
    # da EXACTAMENTE el mismo pace_pct que ya se calculaba antes (mismo
    # álgebra, confirmado numéricamente con Sabas para sabas.ramirez:
    # 65.99% en ambos casos) -- no es una fórmula nueva, es la misma
    # descompuesta en sus dos partes para mostrarlas.
    #
    # REVENUE, 1 día MENOS que Bookings (agosto 2026, vigésima cuarta
    # vuelta -- pedido explícito de Sabas: "ese archivo específico se
    # actualiza a día vencido" -- EXPORT ADS KAM trae Revenue con un día
    # de rezago adicional respecto a Bookings/PRODUCTIVITY, así que el
    # "días transcurridos" para el pace de Revenue debe ser 1 menos que
    # el que ya usa Bookings/att_esperado_hoy_pct/Contactos Efectivos.
    # Bookings NO cambia -- Sabas confirmó explícitamente "solo Objetivo
    # Ads Revenue", Bookings sigue con dias_transcurridos normal. Piso de
    # 1 para no dividir por cero el primer día hábil del mes (mismo
    # criterio que _dias_calendario_mes ya usa para el caso general).
    dias_transcurridos_revenue = max(dias_transcurridos - 1, 1) if dias_transcurridos else dias_transcurridos
    att_bookings_esperado_pct = None
    att_revenue_esperado_pct = None
    if dias_transcurridos:
        if att_revenue_pct is not None:
            revenue_pace_pct = att_revenue_pct * dias_totales / dias_transcurridos_revenue
            att_revenue_esperado_pct = dias_transcurridos_revenue / dias_totales * 100
        if att_bookings_pct is not None:
            bookings_pace_pct = att_bookings_pct * dias_totales / dias_transcurridos
            att_bookings_esperado_pct = dias_transcurridos / dias_totales * 100

    return {
        "att_bookings_pct": att_bookings_pct,
        "att_bookings_esperado_pct": att_bookings_esperado_pct,
        "target_bookings": target_bookings,
        "revenue_pace_pct": revenue_pace_pct,
        "att_revenue_pct": att_revenue_pct,
        "att_revenue_esperado_pct": att_revenue_esperado_pct,
        "target_revenue": target_revenue,
        "bookings_pace_pct": bookings_pace_pct,
    }


USD_A_COP = 3500  # tasa fija pedida por Sabas (agosto 2026), sin API de tipo de cambio.


def comision_ads_proyectada_for(farmer_email):
    """
    Proyección de la comisión "Revenue Share ADS" de Growth OS -- pedido
    explícito de Sabas (agosto 2026, séptimo ajuste), para mostrar debajo
    de Rendimiento Farmer en su Gestión General.

    IMPORTANTE (bug real corregido, agosto 2026): Growth OS paga esta
    comisión sobre REVENUE, no sobre Bookings -- confirmado leyendo
    app_glass.py: ads_result/ads_target salen de la hoja "Earnings"
    (columnas fila 2, col 1-2), que son los campos editables de
    "ADS Target (USD)" / "ADS Result (USD)" bajo el título "Revenue Share
    ADS". Wingman no tiene la hoja "Earnings" de Growth OS -- se usa
    target_revenue/revenue_pace_pct de EXPORT ADS KAM como la mejor
    aproximación disponible.

    Modelo de 3 buckets progresivos sobre Revenue en USD, replicado
    IDÉNTICO al de Growth OS (ver app_glass.py, sección "Revenue Share
    ADS" del Earnings Calculator):
      bucket1 = max(min(result, target) - target*0.9, 0) * 0.10   (90-100%)
      bucket2 = max(min(result, target*1.2) - target, 0) * 0.20   (100-120%)
      bucket3 = max(result - target*1.2, 0) * 0.30                (>120%)
      total = min(bucket1+bucket2+bucket3, 2000 USD)              (cap mensual)

    PROYECCIÓN "PISO" (séptimo ajuste, pedido explícito): antes, si el
    ritmo real de Revenue estaba por debajo del 90% del target, los 3
    buckets daban 0 y la card mostraba "USD $0" sin más contexto -- no le
    decía al Farmer cuánto SÍ podría estar ganando. Ahora siempre se
    calcula también la comisión que correspondería al 91% del target
    (91%, no 90.0% exacto: la fórmula real de Growth OS exige SUPERAR
    estrictamente el 90%, justo en el 90% el bucket1 da $0 -- 91% es el
    primer punto entero donde ya se genera comisión real, confirmado
    explícitamente con Sabas) como "piso", y se muestra el MÁXIMO entre
    ese piso y la proyección real -- nunca se muestra menos que lo que se
    ganaría llegando al 91%, y si el ritmo real ya lo supera, se muestra
    ese número real (más alto).

    NOTAS DE BLOQUEO (séptimo ajuste, pedido explícito): se evalúan por
    separado y se listan TODAS las que apliquen (si dos o más metricas
    estan flojas a la vez, se muestran las dos notas juntas, no solo la
    peor):
      - Bookings de Ads <90% de ritmo -> "Toca acelerar en adquisición
        de bookings".
      - Revenue de Ads <90% de ritmo -> "Revisar CPC y AVA para corregir
        bajo revenue".
      - MD Total <90% -> nota de MD (ya existía).
      - Contactos Efectivos <90% de ritmo -> nota de Contactos (ya existía).
    Estas notas son las mismas 3 condiciones que definen si la comisión
    REAL de Growth OS se desbloquea o no (target de Ads Revenue al 90%,
    MD Total >=90%, Contactos Efectivos >=90% -- confirmado explícitamente
    con Sabas) -- la comisión que se muestra es el POTENCIAL alcanzable,
    no una garantía de cobro mientras alguna de las 3 esté en rojo.

    Devuelve None si no hay target de Ads (Revenue) o de Contactos
    Efectivos disponible para este farmer (no se puede proyectar nada
    sin base).
    """
    ads = ads_kam_for(farmer_email)
    if ads["target_revenue"] <= 0 or ads["revenue_pace_pct"] is None:
        return None

    target = ads["target_revenue"]
    revenue_pace_pct = ads["revenue_pace_pct"]
    result_real = target * revenue_pace_pct / 100
    # BUG REAL CORREGIDO: la fórmula de Growth OS exige SUPERAR
    # estrictamente el 90% (bucket1 = min(result,target) - target*0.9,
    # que da exactamente 0 en el 90% justo, no un valor positivo chico).
    # "91% del target" es el primer punto entero por encima del 90% donde
    # ya se genera comisión real -- confirmado explícitamente con Sabas
    # como el piso a usar (91%, no 90.0% exacto que daría USD $0 igual).
    result_piso = target * 0.91

    def _buckets(result):
        b1 = max(min(result, target) - target * 0.9, 0) * 0.10
        b2 = max(min(result, target * 1.2) - target, 0) * 0.20
        b3 = max(result - target * 1.2, 0) * 0.30
        return b1, b2, b3

    b1_real, b2_real, b3_real = _buckets(result_real)
    total_real = b1_real + b2_real + b3_real

    b1_piso, b2_piso, b3_piso = _buckets(result_piso)
    total_piso = b1_piso + b2_piso + b3_piso

    # Se muestra siempre el mejor de los dos escenarios -- "nunca menos
    # que el piso del 90%", y si el ritmo real ya lo supera, se muestra
    # el real (mas alto). Nunca se mezclan buckets de un escenario con
    # otro: se elige un escenario completo, no el maximo bucket por
    # bucket (eso podria dar un numero que ningun escenario real produce).
    if total_real >= total_piso:
        bucket1, bucket2, bucket3, es_piso = b1_real, b2_real, b3_real, False
    else:
        bucket1, bucket2, bucket3, es_piso = b1_piso, b2_piso, b3_piso, True

    total_usd_uncapped = bucket1 + bucket2 + bucket3
    total_usd = min(total_usd_uncapped, 2000.0)
    topeado_por_cap = total_usd_uncapped > 2000.0

    md = md_kam_for(farmer_email)
    att_md_pct = md["att_md_total_pct"] * 100 if md["att_md_total_pct"] is not None else None

    cp = contact_performance_for(farmer_email)
    target_contactos = target_for(farmer_email)
    contactos_pace_pct = None
    if target_contactos > 0:
        prod = load_productivity()
        email_norm = str(farmer_email).strip().lower()
        d_prod = prod[prod["farmer"] == email_norm] if not prod.empty else prod
        if not d_prod.empty:
            start_of_month = _effective_start_of_month(d_prod)
            dias_transcurridos, dias_totales = _pace_dias_habiles(start_of_month, pais=farmer_pais(farmer_email))
            if dias_transcurridos > 0:
                proyeccion_contactos = cp["total_effective"] / dias_transcurridos * dias_totales
                contactos_pace_pct = proyeccion_contactos / target_contactos * 100

    # Bookings de Ads: mismo ritmo que ya calcula ads_kam_for (por dias
    # calendario), evaluado con el mismo umbral de 90% que el resto.
    bookings_pace_pct = ads.get("bookings_pace_pct")

    # Notas de bloqueo -- TODAS las que apliquen, no solo la peor (pedido
    # explícito de Sabas: "si los dos están rotos se muestran las dos
    # notas").
    metricas_flojas = []
    bloqueos_ads = []
    if bookings_pace_pct is not None and bookings_pace_pct < 90:
        bloqueos_ads.append("Toca acelerar en adquisición de bookings")
    if revenue_pace_pct < 90:
        bloqueos_ads.append("Revisar CPC y AVA para corregir bajo revenue")
    if contactos_pace_pct is not None and contactos_pace_pct < 90:
        metricas_flojas.append("Contactos Efectivos")
    if att_md_pct is not None and att_md_pct < 90:
        metricas_flojas.append("MD Total")

    return {
        "bucket1_usd": bucket1, "bucket2_usd": bucket2, "bucket3_usd": bucket3,
        "total_usd_uncapped": total_usd_uncapped,
        "total_usd": total_usd,
        "es_piso": es_piso,  # True si lo mostrado es la proyección mínima al 90%, no el ritmo real
        "total_cop": total_usd * USD_A_COP,
        "topeado_por_cap": topeado_por_cap,
        "target_revenue": target,
        "revenue_pace_result": result_piso if es_piso else result_real,
        "revenue_pace_pct": revenue_pace_pct,
        "bookings_pace_pct": bookings_pace_pct,
        "contactos_pace_pct": contactos_pace_pct,
        "att_md_pct": att_md_pct,
        "metricas_flojas": metricas_flojas,
        "bloqueos_ads": bloqueos_ads,
    }


def md_kam_for(farmer_emails):
    """
    Cumplimiento de Markdown (Total y PRO) para uno o varios Farmers, para
    la tabla "Rendimiento País" (pedido explícito de Sabas, agosto 2026).

    Igual que ads_kam_for: con varios farmers se SUMAN los montos
    implicitos (aproximados via % * algun denominador comun no
    disponible) -- como EXPORT MD KAM no trae el GMV base de cada fila,
    la agregacion multi-farmer usa PROMEDIO PONDERADO por target (mismo
    espiritu que ads_kam_for: no le da a un farmer chico el mismo peso
    que a uno grande, aproximado con el % target de cada uno como proxy
    de tamaño de cartera).
    """
    base = {"md_total_pct": None, "tgt_md_total_pct": None, "att_md_total_pct": None,
            "md_pro_pct": None, "tgt_md_pro_pct": None, "att_md_pro_pct": None}
    kam = load_export_md_kam()
    if kam.empty:
        return base

    emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
    emails = {str(e).strip().lower() for e in emails}
    d = kam[kam["farmer"].isin(emails)]
    if d.empty:
        return base

    if len(d) == 1:
        row = d.iloc[0]
        return {
            "md_total_pct": float(row["md_total_pct"]), "tgt_md_total_pct": float(row["tgt_md_total_pct"]),
            "att_md_total_pct": float(row["att_md_total_pct"]),
            "md_pro_pct": float(row["md_pro_pct"]), "tgt_md_pro_pct": float(row["tgt_md_pro_pct"]),
            "att_md_pro_pct": float(row["att_md_pro_pct"]),
        }

    # Varios farmers: promedio ponderado por target (proxy de tamaño de
    # cartera, ya que esta hoja no trae GMV base por fila).
    w = d["tgt_md_total_pct"].clip(lower=0.0001)
    wp = d["tgt_md_pro_pct"].clip(lower=0.0001)
    return {
        "md_total_pct": float((d["md_total_pct"] * w).sum() / w.sum()),
        "tgt_md_total_pct": float((d["tgt_md_total_pct"] * w).sum() / w.sum()),
        "att_md_total_pct": float((d["att_md_total_pct"] * w).sum() / w.sum()),
        "md_pro_pct": float((d["md_pro_pct"] * wp).sum() / wp.sum()),
        "tgt_md_pro_pct": float((d["tgt_md_pro_pct"] * wp).sum() / wp.sum()),
        "att_md_pro_pct": float((d["att_md_pro_pct"] * wp).sum() / wp.sum()),
    }


def contact_performance_for(farmer_emails):
    """
    Contact Performance de uno o varios Farmers: contactos efectivos desde
    el 1 del mes actual, desglosados por canal. Mismo criterio que Growth OS
    (_load_productivity_contact_stats): ¿Contactado?=SI es efectivo, =NO es
    "No Contactado". Canales: Amazon Connect->llamadas, WhatsApp/Treble->chats,
    Videoconferencia->meets.

    farmer_emails: un email (str) para el caso de siempre, o una lista de
    emails para la vista de Supervisor (agregado por pais).

    Blindado con try/except por la misma razon que brand_coverage_for: un
    Excel real puede traer PRODUCTIVITY con un formato levemente distinto
    al probado en desarrollo, y esta card no debe tumbar toda la pantalla
    de Management Dashboard si algo falla acá.

    Fallback de mes (agregado tras detectar el corte en 0 el 1° de agosto
    con el Excel todavía en julio): si el mes calendario actual no tiene
    ninguna gestión registrada, se usa automáticamente el mes más reciente
    que sí tenga datos, en vez de mostrar la card en 0. Con varios farmers,
    el mes efectivo se calcula sobre el conjunto combinado (si CUALQUIERA
    de ellos tiene datos del mes actual, se usa el mes actual para todos).
    El dict de retorno incluye "period_label" con la fecha real usada.

    Pace (pedido explícito de Sabas, agosto 2026): ritmo proyectado de
    contactos efectivos vs el target del mes, medido en días hábiles (ver
    _pace_dias_habiles). pace_pct = (efectivos / dias_habiles_transcurridos)
    * dias_habiles_totales / target * 100 -- "si sigo a este ritmo, ¿qué
    % del target voy a cerrar?". Si el mes efectivo ya cerró (fallback a un
    mes pasado), dias_transcurridos = dias_totales, así que pace_pct
    termina siendo simplemente el % de cumplimiento real, sin proyección
    -- pedido explícito de Sabas ("mostrar el pace igual, con base en los
    días que tuvo julio completo"). Sin target disponible o sin días
    hábiles transcurridos (mes recién arrancando, aun no hay ningún día
    hábil), pace_pct queda en None -- la UI decide si ocultarlo.
    """
    base = {"total_effective": 0, "calls": 0, "chats": 0, "meets": 0, "not_contacted": 0,
            "period_label": pd.Timestamp.now().replace(day=1).strftime("%d %b"),
            "pace_pct": None, "dias_transcurridos": 0, "dias_totales": 0}
    try:
        df = load_productivity()
        if df.empty:
            return base

        emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
        emails = {str(e).strip().lower() for e in emails}
        d = df[df["farmer"].isin(emails)].copy()
        if d.empty:
            return base

        start_of_month = _effective_start_of_month(d)
        if d["date"].notna().any():
            d = d[d["date"].isna() | (d["date"] >= start_of_month)]

        not_contacted = int((d["contactado"] == "NO").sum())
        eff = d[d["contactado"] == "SI"]

        calls = int(eff["medio"].str.contains("amazon connect|amazon", na=False).sum())
        chats = int(eff["medio"].str.contains("whatsapp|treble", na=False).sum())
        meets = int(eff["medio"].str.contains("videoconferencia|videoconf|video", na=False).sum())

        total_effective = len(eff)
        primer_email = farmer_emails if isinstance(farmer_emails, str) else next(iter(farmer_emails), None)
        pais = farmer_pais(primer_email) if primer_email else PAIS
        dias_transcurridos, dias_totales = _pace_dias_habiles(start_of_month, pais=pais)
        target = target_for(farmer_emails)
        pace_pct = None
        if target > 0 and dias_transcurridos > 0:
            proyeccion = (total_effective / dias_transcurridos) * dias_totales
            pace_pct = round(proyeccion / target * 100)

        return {
            "total_effective": total_effective,
            "calls": calls,
            "chats": chats,
            "meets": meets,
            "not_contacted": not_contacted,
            "period_label": start_of_month.strftime("%d %b"),
            "pace_pct": pace_pct,
            "dias_transcurridos": dias_transcurridos,
            "dias_totales": dias_totales,
        }
    except Exception as e:
        _issue("Contact Performance", f"No pude calcular Contact Performance para {farmer_emails}: {e}")
        return base


def conversion_for(farmer_emails):
    """
    Conversión de Ads y Markdown de uno o varios Farmers, acumulado desde
    el 1 del mes actual (mismo criterio de fecha que contact_performance_for)
    -- NO es un corte diario, es el acumulado del mes que se recalcula cada
    vez que hay datos nuevos (pedido explícito de Sabas: "no lo vas a
    mostrar diario, vas a mostrarlo acumulado, pero con actualización diaria").

    farmer_emails: un email (str) para el caso de siempre, o una lista de
    emails para la vista de Supervisor (agregado por pais).

    Markdown: conviene "Markdown"="SI" (se hizo la gestión) Y
    "¿Se aceptó lo ofrecido?"="Sí" (el aliado aceptó). La base del % es el
    total de gestiones de Markdown realizadas ese mes, NO el total de
    marcas de la cartera -- son gestiones, no marcas (confirmado con Sabas
    que esta diferencia de base con PW1/PW2/Churn está bien así).

    Ads: la base es SOLO el universo "Never Ads" (marcas que NO tenían Ads
    activo antes de esta gestión) -- "Tipo Ads"="Never Ads". Dentro de esas,
    convierte (adquisición real) si "Tipo Never Ads" es "Con coinversión" o
    "Sin coinversión"; NO convierte si es "No activo". Comparación en
    minúsculas porque el Excel real trae inconsistencia de mayúsculas
    ("Con Coinversión" vs "Sin coinversión").

    IMPORTANTE (corrección pedida por Sabas, agosto 2026): "Seguimiento",
    "Upselling", "Down Selling" y "Reactivación" son gestiones sobre
    marcas que YA tenían Ads activo -- no son adquisición de campaña
    nueva, y por eso NO entran ni a la base ni al numerador de esta
    métrica. Antes se incluían (base = todo Ads="SI"), lo que inflaba la
    conversión mezclando mantenimiento de Ads ya activo con adquisición
    real: julio daba 68% (50/73) mezclado, cuando la adquisición real
    Never Ads era 8% (2/25). "Conversión Ads" ahora es estrictamente
    "de las marcas sin Ads que gestioné, cuántas adquirí".

    Blindado con try/except, mismo criterio que brand_coverage_for y
    contact_performance_for: no debe tumbar Management Dashboard si el
    Excel real trae algo distinto a lo esperado.

    Fallback de mes (agregado tras detectar el corte en 0 el 1° de agosto
    con el Excel todavía en julio): si el mes calendario actual no tiene
    ninguna gestión registrada, se usa automáticamente el mes más reciente
    que sí tenga datos. "period_label" en el retorno lleva la fecha real
    usada, para que la UI no diga "Desde 01 Aug" mostrando datos de julio.
    """
    base = {"ads_total": 0, "ads_conv": 0, "ads_pct": 0.0, "md_total": 0, "md_conv": 0, "md_pct": 0.0,
            "period_label": pd.Timestamp.now().replace(day=1).strftime("%d %b")}
    try:
        df = load_productivity()
        if df.empty:
            return base

        emails = [farmer_emails] if isinstance(farmer_emails, str) else list(farmer_emails)
        emails = {str(e).strip().lower() for e in emails}
        d = df[df["farmer"].isin(emails)].copy()
        if d.empty:
            return base

        start_of_month = _effective_start_of_month(d)
        if d["date"].notna().any():
            d = d[d["date"].isna() | (d["date"] >= start_of_month)]

        # ── Ads (solo adquisición real: universo Never Ads) ──
        never_ads_gestiones = d[(d["ads"] == "SI") & (d["tipo_ads"] == "Never Ads")]
        ads_total = len(never_ads_gestiones)
        no_activo = never_ads_gestiones["never_ads"].str.lower() == "no activo"
        ads_conv = int((~no_activo).sum())
        ads_pct = (ads_conv / ads_total) if ads_total > 0 else 0.0

        # ── Markdown ──
        md_gestiones = d[d["md"] == "SI"]
        md_total = len(md_gestiones)
        md_conv = int((md_gestiones["md_aceptado"].str.lower() == "sí").sum())
        md_pct = (md_conv / md_total) if md_total > 0 else 0.0

        return {
            "ads_total": ads_total, "ads_conv": ads_conv, "ads_pct": ads_pct,
            "md_total": md_total, "md_conv": md_conv, "md_pct": md_pct,
            "period_label": start_of_month.strftime("%d %b"),
        }
    except Exception as e:
        _issue("Conversión Ads/MD", f"No pude calcular conversión para {farmer_emails}: {e}")
        return base


# =========================
# VISTA CONSOLIDADA
# =========================

_PORTFOLIO_COLUMNS = [
    "key", "brand_id", "brand_name", "telefono", "mail", "farmer", "coinversion",
    "nkey", "coinv_group_key", "coinv_has", "bookings", "revenue", "att_booking",
    "att_revenue", "roas", "sales", "availability", "lost_hours", "gmv_md",
    "markdown_md", "sales_md", "campaigns_md", "coinv_md", "roi_md", "gmv_mdpro",
    "markdown_mdpro", "sales_mdpro", "campaigns_mdpro", "coinv_mdpro", "roi_mdpro",
    "penetracion_md", "penetracion_mdpro", "campaign_md", "campaign_mdpro", "cvr",
    "cvr_delta", "traffic", "traffic_delta", "categoria", "gmv", "ordenes", "ciudad",
    "farmer_detalle", "brand_name_detalle", "n_stores", "aov", "gmv_last", "aov_last",
    "ordenes_last", "gmv_prev2", "aov_prev2", "ordenes_prev2",
    "gmv_delta", "aov_delta", "ordenes_delta", "perfect_store_pct", "menu_global", "menu_photos",
    "menu_purchase", "menu_missing", "coinv_md_status", "coinv_md_label", "gmv_rank",
    "churn_status",
]


def _portfolio_vacio():
    """
    DataFrame vacío (0 filas) pero con TODAS las columnas que
    portfolio_for() garantiza cuando sí tiene data (bug real corregido,
    agosto 2026: antes, un farmer sin ninguna marca en su fuente base
    -ej. EQUIPO_ALTA_SIN_ASIGNACION sin filas en DETALLE ese corte, caso
    real: los 10 de Chile en un Excel donde DETALLE dejó de traerlos-
    hacía que portfolio_for cortara temprano devolviendo solo las
    columnas parciales de la base cruda. Cualquier código que accediera a
    portfolio["perfect_store_pct"] o similar tiraba KeyError en vez de
    simplemente ver "0 marcas").
    """
    return pd.DataFrame(columns=_PORTFOLIO_COLUMNS)


@st.cache_data(ttl=86400, show_spinner=False)
def dias_transcurridos_mes_actual():
    """
    Dias calendario transcurridos del mes en curso, contados hasta AYER (no
    hasta hoy) -- mismo criterio ya usado en portfolio_for() para
    gmv_delta (pedido explicito de Sabas, agosto 2026: el dia de hoy
    recien se refleja mañana, cuando ya cerro completo -- evita que un
    dia EN CURSO, parcialmente cargado, infle o distorsione cualquier
    proyeccion). Minimo 1, para evitar division por cero el primer dia
    del mes.

    Extraida como funcion reutilizable (agosto 2026, septimo ajuste) para
    que Ads Plan (Campaign Designer) use EXACTAMENTE la misma logica que
    ya usa gmv_delta en portfolio_for(), sin duplicar el calculo -- antes
    vivia solo inline dentro de portfolio_for.
    """
    hoy = pd.Timestamp.now().normalize()
    ayer = hoy - pd.Timedelta(days=1)
    return max(ayer.day, 1) if ayer.month == hoy.month else 1


def portfolio_for(farmer_email):
    """Cartera de un Farmer con toda la data cruzada.

    Para los 6 de Fabian sin fila propia en ASIGNACION (EQUIPO_ALTA_SIN_ASIGNACION),
    la base sale de DETALLE via load_detalle_portfolio en vez de ASIGNACION.
    De ahi en mas la funcion sigue exactamente la misma cadena de merges;
    ver limitaciones (sin telefono/mail, sin coinversion) documentadas en
    load_detalle_portfolio.

    Para farmers con pais distinto de AR (FARMER_PAIS_OVERRIDE, hoy solo
    Maria/UY), ASIGNACION se filtra por su pais real en vez de "AR" -- sus
    marcas SI tienen fila en ASIGNACION (a diferencia de los 6 de Fabian),
    solo que con prefijo de pais distinto. Todos los montos ($) de esta
    ficha quedan en la moneda nativa de ese pais (farmer_moneda), sin
    conversion a ARS ni a USD.
    """
    email = str(farmer_email).strip().lower()

    if email in EQUIPO_ALTA_SIN_ASIGNACION:
        df = load_detalle_portfolio(email)
        if df.empty:
            return _portfolio_vacio()
    else:
        asig = load_asignacion(pais=farmer_pais(email))
        if asig.empty:
            return _portfolio_vacio()

        df = asig[asig["farmer"] == email].copy()
        if df.empty:
            return _portfolio_vacio()

    # ── Cruces por ID ──
    for loader, cols in [
        (load_ads,          ["bookings", "revenue", "sales", "roas", "att_booking", "att_revenue"]),
        (load_availability, ["availability", "lost_hours"]),
    ]:
        src = loader()
        if src.empty:
            for c in cols:
                df[c] = 0.0
        else:
            df = df.merge(src, on="key", how="left")

    for loader, suffix in [(load_md, "md"), (load_md_pro, "mdpro")]:
        src = loader()
        base = ["gmv", "markdown", "sales", "campaigns", "coinv", "roi"]
        if src.empty:
            for c in base:
                df[f"{c}_{suffix}"] = 0.0
        else:
            src = src.rename(columns={c: f"{c}_{suffix}" for c in src.columns if c != "key"})
            df = df.merge(src, on="key", how="left")

    # Penetracion = MARKDOWN $ / GMV $ de la propia hoja MD, calculada en vivo
    # (misma logica que Growth OS: la columna de penetracion de la hoja no
    # siempre es consistente con D y E, así que se recalcula para tener una
    # unica fuente de verdad).
    df["penetracion_md"] = (df["markdown_md"] / df["gmv_md"]).where(df["gmv_md"] > 0, 0.0)
    df["penetracion_mdpro"] = (df["markdown_mdpro"] / df["gmv_mdpro"]).where(df["gmv_mdpro"] > 0, 0.0)

    # Nombres de campaña MD/MD PRO -- cruzados por Brand ID (key), no por
    # nombre de marca -- fix del bug real de md_campaign_names() de más
    # arriba (MD NAMES sí trae Brand ID en el export actual).
    camp_map = md_campaign_names()
    df["campaign_md"] = df["key"].map(lambda k: camp_map.get(k, {}).get("md", "-"))
    df["campaign_mdpro"] = df["key"].map(lambda k: camp_map.get(k, {}).get("md_pro", "-"))

    # ── Cruces por nombre ──
    for loader, cols in [
        (load_cvr,     ["cvr", "cvr_delta"]),
        (load_traffic, ["traffic", "traffic_delta"]),
    ]:
        src = loader()
        if src.empty:
            for c in cols:
                df[c] = 0.0
        else:
            df = df.merge(src, on="nkey", how="left")

    ltor = load_ltor()
    if ltor.empty:
        df["categoria"] = ""
    else:
        # Solo se usa "categoria" (para benchmarks de CVR/Traffic). LTOR Tier no
        # entra a la ficha: Sabas confirmo que esa columna se carga a mano y no
        # hay fuente confiable para mostrarla.
        df = df.merge(ltor[["nkey", "categoria"]], on="nkey", how="left")

    # DETALLE: GMV / AOV / Ordenes / Categoria / N_Stores / Ciudad (cruza por ID, ya viene agregado a marca)
    detalle = load_detalle()
    if detalle.empty:
        for c in ("gmv", "ordenes", "aov", "n_stores"):
            df[c] = 0.0
        for c in ("categoria_detalle", "ciudad"):
            df[c] = ""
    else:
        df = df.merge(detalle, on="key", how="left")
    # DETALLE trae categoria mas confiable (mismo mes que GMV) que MD NAMES.
    # Si la tenemos, pisa a la de MD NAMES.
    df["categoria"] = df["categoria_detalle"].where(
        df["categoria_detalle"].astype(str).str.strip() != "", df["categoria"]
    )
    df = df.drop(columns=["categoria_detalle"])

    # LAST GMV: mismo GMV/AOV pero del mes anterior, para calcular variacion.
    # Tambien trae Ordenes (septiembre 2026, cuarta vuelta -- pedido
    # explícito de Sabas: "Órdenes" pasa a tener su propia card con
    # comparativa de 3 meses, igual que GMV/AOV -- misma hoja, mismo
    # merge, solo se suma la columna que antes no se usaba de acá).
    last_gmv = load_last_gmv()
    if last_gmv.empty:
        df["gmv_last"] = 0.0
        df["aov_last"] = 0.0
        df["ordenes_last"] = 0.0
    else:
        last_slim = last_gmv[["key", "gmv", "aov", "ordenes"]].rename(
            columns={"gmv": "gmv_last", "aov": "aov_last", "ordenes": "ordenes_last"}
        )
        df = df.merge(last_slim, on="key", how="left")
    df["gmv_last"] = df["gmv_last"].fillna(0)
    df["aov_last"] = df["aov_last"].fillna(0)
    df["ordenes_last"] = df["ordenes_last"].fillna(0)

    # PREVIOUS GMV: mismo GMV/AOV pero de hace DOS meses (no confundir con
    # LAST GMV, que es el mes inmediato anterior) -- para la comparativa de
    # 3 meses reales en las cards de GMV/AOV (septiembre 2026). Ordenes
    # idem (cuarta vuelta, mismo pedido que arriba).
    previous_gmv = load_previous_gmv()
    if previous_gmv.empty:
        df["gmv_prev2"] = 0.0
        df["aov_prev2"] = 0.0
        df["ordenes_prev2"] = 0.0
    else:
        previous_slim = previous_gmv[["key", "gmv", "aov", "ordenes"]].rename(
            columns={"gmv": "gmv_prev2", "aov": "aov_prev2", "ordenes": "ordenes_prev2"}
        )
        df = df.merge(previous_slim, on="key", how="left")
    df["gmv_prev2"] = df["gmv_prev2"].fillna(0)
    df["aov_prev2"] = df["aov_prev2"].fillna(0)
    df["ordenes_prev2"] = df["ordenes_prev2"].fillna(0)

    # gmv_delta: RITMO, no acumulado crudo (bug real corregido, agosto
    # 2026). Antes comparaba GMV acumulado del mes en curso contra el GMV
    # COMPLETO del mes anterior sin ajustar por cuantos dias llevaba
    # cargados cada uno -- con DETALLE en 2 dias de agosto y LAST GMV en
    # 31 dias de julio, esto daba caidas falsas de -80/-90% que asustaban
    # sin decir nada real ("vendiste el 21% de julio" en vez de "a este
    # ritmo vas a cerrar en X% de julio"). Ahora se proyecta el GMV actual
    # a mes completo (por DIAS CALENDARIO transcurridos, pedido explícito
    # de Sabas -- las ventas no paran el fin de semana) y se compara esa
    # proyeccion contra el GMV real del mes anterior.
    #
    # "Dias transcurridos" = HOY (dia real del sistema), NO el mes efectivo
    # de PRODUCTIVIDAD -- DETALLE no trae fecha por fila, y confirmado con
    # Sabas que DETALLE puede estar en un mes mas nuevo que PRODUCTIVITY
    # (ej. DETALLE ya con 2 dias de agosto cargados mientras PRODUCTIVITY
    # seguia en julio completo), asi que prestar el mes de PRODUCTIVITY
    # daria un factor de proyeccion de 1.0 (sin proyectar nada) en ese
    # caso -- decision explicita de Sabas: asumir que DETALLE representa
    # "del 1 del mes actual hasta AYER" (no hasta hoy -- ver nota
    # siguiente).
    #
    # "Dias transcurridos" cuenta hasta AYER, no hasta hoy -- pedido
    # explícito de Sabas (agosto 2026, sexto ajuste), mismo criterio que
    # _pace_dias_habiles/_dias_calendario_mes: el día de hoy recién se
    # refleja mañana, cuando ya cerró completo -- evita que un día EN
    # CURSO (parcialmente cargado) infle o distorsione la proyección.
    # Mínimo 1 para evitar división por cero el primer día del mes.
    hoy_gmv = pd.Timestamp.now().normalize()
    dias_totales_gmv = (hoy_gmv + pd.offsets.MonthEnd(0)).day
    # dias_transcurridos_gmv ahora viene de dias_transcurridos_mes_actual()
    # (extraida arriba, agosto 2026 septimo ajuste) -- misma logica exacta
    # de antes, ya no duplicada inline aca.
    dias_transcurridos_gmv = dias_transcurridos_mes_actual()

    factor_proyeccion = dias_totales_gmv / dias_transcurridos_gmv
    gmv_proyectado = df["gmv"] * factor_proyeccion

    df["gmv_delta"] = ((gmv_proyectado - df["gmv_last"]) / df["gmv_last"]).where(df["gmv_last"] > 0, 0.0)
    # AOV es un PROMEDIO (ticket promedio), no un acumulado -- un AOV
    # calculado sobre 2 dias es comparable a uno de 31 dias sin proyectar
    # nada, así que aov_delta sigue siendo la variacion cruda de siempre.
    df["aov_delta"] = ((df["aov"] - df["aov_last"]) / df["aov_last"]).where(df["aov_last"] > 0, 0.0)
    # Órdenes SÍ es un acumulado (como GMV, no como AOV) -- crece dia a
    # dia dentro del mes, así que usa el mismo factor_proyeccion de
    # ritmo que GMV (pedido explícito de Sabas, septiembre 2026, cuarta
    # vuelta: comparar ordenes crudas de 2 dias contra el mes completo
    # anterior daria la misma caida falsa que tenia GMV antes del fix de
    # ritmo de agosto 2026).
    ordenes_proyectado = df["ordenes"] * factor_proyeccion
    df["ordenes_delta"] = ((ordenes_proyectado - df["ordenes_last"]) / df["ordenes_last"]).where(df["ordenes_last"] > 0, 0.0)

    # PERFECT STORE: gauge Menu
    pstore = load_perfect_store()
    if pstore.empty:
        for c in ("perfect_store_pct", "menu_global", "menu_photos", "menu_purchase", "menu_missing"):
            df[c] = 0.0
    else:
        df = df.merge(pstore, on="key", how="left")

    df["categoria"] = df["categoria"].fillna("").replace({"nan": ""})
    df["ciudad"] = df["ciudad"].fillna("").replace({"nan": ""})
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(0)

    # Coinversion MD (card "COINVERSIÓN MD" del 360 Action): sale de
    # PRIORITY DATA, no de ASIGNACION -- ver load_coinversion_md para la
    # logica (Coinversion MD != "SI" exacto -> "No"; si es "SI", se lee
    # STATUS Brand). Sin registro en PRIORITY DATA = "No" por default,
    # mismo criterio que "sin coinversion confirmada".
    #
    # coinv_md_status (no "coinv_md"): df ya trae "coinv_md" desde load_md
    # (monto de coinversion de Markdown en $, dato distinto a este
    # booleano). Nombrarla igual generaba un merge silencioso a coinv_md_x
    # / coinv_md_y en vez de fallar -- bug real encontrado al validar.
    coinv_md_data = load_coinversion_md()
    if coinv_md_data.empty:
        df["coinv_md_status"] = False
        df["coinv_md_label"] = "No"
    else:
        df = df.merge(coinv_md_data, on="key", how="left")
        df["coinv_md_status"] = df["coinv_md_status"].fillna(False)
        df["coinv_md_label"] = df["status_label"].fillna("No")
        df = df.drop(columns=["status_label"])

    # Ranking de GMV DENTRO de esta cartera especifica (no global): #1 es la
    # marca que mas GMV representa para este Farmer, no para todo el equipo.
    df = df.sort_values("gmv", ascending=False).reset_index(drop=True)
    df["gmv_rank"] = range(1, len(df) + 1)
    df.loc[df["gmv"] <= 0, "gmv_rank"] = 0  # sin GMV = sin ranking valido

    # Churn Status por marca. Sin registro en la hoja CHURN = sin riesgo activo,
    # se muestra como "Disponible" (chulito verde), no como dato faltante.
    cmap = churn_map()
    df["churn_status"] = df["key"].map(cmap).fillna("Disponible")

    return df.sort_values("brand_name").reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def category_benchmarks():
    """
    {categoria: (cvr_promedio, traffic_promedio)} sobre marcas con categoria.

    Reescrita por completo (septiembre 2026, bug real corregido): antes
    cruzaba ASIGNACION + LTOR (categoria via load_ltor(), que lee la hoja
    MD NAMES buscando columnas "Brand Name"/"LTOR Class"/"Category"). El
    export de MD NAMES cambio de formato -- ya no trae esas columnas (hoy
    trae Country/Category/Campaign ID/Name/Segment/Tier Classification,
    donde "Name" es el nombre de la CAMPAÑA de MD, no el de la marca) --
    asi que load_ltor() venia devolviendo SIEMPRE vacio, y category_
    benchmarks() cortaba en el primer if devolviendo {} para TODAS las
    categorias (reportado por Sabas: "Tráfico benchmark categoría: s/d"
    en una marca que sí tenía tráfico real cargado).

    Fix: usa la categoria de DETALLE (via brand_name_detalle -> nkey), la
    misma fuente que portfolio_for() ya usa como "mas confiable" para
    categoria (ver comentario en portfolio_for: "DETALLE trae categoria
    mas confiable -- mismo mes que GMV -- que MD NAMES"). Bench sobre
    TODO el universo de marcas con dato (no solo la cartera de un
    farmer), igual que antes.
    """
    det = load_detalle()
    if det.empty or "categoria_detalle" not in det.columns:
        return {}

    df = det[det["brand_name_detalle"].astype(str).str.strip() != ""].copy()
    df["nkey"] = df["brand_name_detalle"].apply(name_key)
    df = df[df["nkey"] != ""]

    for src in (load_cvr(), load_traffic()):
        if not src.empty:
            df = df.merge(src, on="nkey", how="left")

    out = {}
    for cat, g in df.groupby("categoria_detalle"):
        if not str(cat).strip():
            continue
        c = g["cvr"][g["cvr"] > 0] if "cvr" in g else pd.Series(dtype=float)
        t = g["traffic"][g["traffic"] > 0] if "traffic" in g else pd.Series(dtype=float)
        out[cat] = (float(c.mean()) if len(c) else 0.0,
                    float(t.mean()) if len(t) else 0.0)
    return out


def _funnel_diagnosis_interno(cvr, traffic, aov, gmv, bench_cvr, bench_traffic, ordenes_mes=0):
    """
    Diagnostico de Funnel Traffic & Conversion vs Benchmark. Mismo arbol de
    decision que Growth OS (bloque _d4_*): tolerancia del 85% del benchmark
    para considerar "ok" cada metrica (no exige superarlo estrictamente).

    Devuelve dict con: headline, color, texto combinado, pitch ("como
    decirselo al aliado"), y los valores de traffic/cvr semanal para mostrar.

    INSIGHT DE INCREMENTAL -- reescrito por completo (agosto 2026, sexto
    ajuste, pedido explicito de Sabas). Antes se proyectaba con trafico
    SEMANAL x4 x bench_cvr x aov (metodologia distinta a la que usa el
    resto de la app), y ademas necesitaba aov>0 para activarse -- por eso
    en la practica casi nunca se veia en pantalla. Ahora usa exactamente
    la misma fuente que ya usa Disponibilidad en 360 Action (ordenes_mes +
    AOV, el mismo par de datos que ya se ve en la card GMV de Home), asi
    que toda la app queda consistente con una sola metodologia de
    "pedidos/pesos incrementales": ratio de mejora x ordenes_mes, nunca
    trafico semanal proyectado.

      - Problema: Conversion (trafico sano, CVR bajo):
          pedidos_incremental = ordenes_mes x (bench_cvr / cvr - 1)
          gmv_incremental     = pedidos_incremental x aov

      - Problema: Trafico (CVR sano, trafico bajo) -- ESTE INSIGHT NO
        EXISTIA ANTES, se agrega nuevo (pedido explicito de Sabas):
          pedidos_incremental = ordenes_mes x (bench_traffic / traffic - 1)
          gmv_incremental     = pedidos_incremental x aov

      - Problema doble (ambos frentes rotos) -- insight en 2 pasos, mas
        largo que los otros dos (pedido explicito de Sabas): primero
        cuanto se gana arreglando SOLO conversion (manteniendo el trafico
        actual), y despues cuanto se gana EXTRA si ademas se arregla el
        trafico:
          pedidos_A      = ordenes_mes x (bench_cvr / cvr - 1)          # solo conversion
          gmv_A          = pedidos_A x aov
          pedidos_ambos  = ordenes_mes x (bench_traffic/traffic) x (bench_cvr/cvr) - ordenes_mes
          gmv_extra_trafico = (pedidos_ambos x aov) - gmv_A             # lo adicional de tambien arreglar trafico

    Mismo resguardo que ya se aplica en Disponibilidad (360 Action): si
    ordenes_mes o aov vienen en 0, la formula da 0 pedidos/0 pesos sola,
    sin necesitar un caso especial -- el insight simplemente no aporta
    numero, pero el resto del texto (headline, comparacion vs benchmark)
    se sigue mostrando igual. El parametro "gmv" queda en la firma solo
    por compatibilidad con el call-site -- ya NO se usa para este calculo
    (antes alimentaba la formula vieja de gmv_at_bench - gmv).
    """
    traffic_ok = bench_traffic > 0 and traffic > 0 and traffic >= bench_traffic * 0.85
    cvr_ok = bench_cvr > 0 and cvr > 0 and cvr >= bench_cvr * 0.85
    has_traffic = traffic > 0
    has_cvr = cvr > 0
    cvr_above_bench = has_cvr and bench_cvr > 0 and cvr >= bench_cvr

    cvr_disp = f"{cvr * 100:.1f}%" if has_cvr else "s/d"
    bench_cvr_disp = f"{bench_cvr * 100:.1f}%" if bench_cvr > 0 else "s/d"
    traffic_disp = f"{traffic:,.0f}".replace(",", ".") if has_traffic else "s/d"
    bench_traffic_disp = f"{bench_traffic:,.0f}".replace(",", ".") if bench_traffic > 0 else "s/d"

    def _incremental_por_cvr():
        """pedidos/gmv incremental corrigiendo SOLO conversion (ratio vs bench_cvr)."""
        if ordenes_mes > 0 and has_cvr and bench_cvr > 0 and cvr > 0:
            pedidos = ordenes_mes * (bench_cvr / cvr - 1)
            return pedidos, pedidos * aov
        return 0.0, 0.0

    def _incremental_por_trafico():
        """pedidos/gmv incremental corrigiendo SOLO trafico (ratio vs bench_traffic)."""
        if ordenes_mes > 0 and has_traffic and bench_traffic > 0 and traffic > 0:
            pedidos = ordenes_mes * (bench_traffic / traffic - 1)
            return pedidos, pedidos * aov
        return 0.0, 0.0

    if not has_traffic and not has_cvr:
        return {
            "headline": "Sin datos suficientes", "color": "#9098A3",
            "texto": "No hay tráfico ni conversión registrados esta semana. Activa ads para empezar a generar ambas métricas de forma medible.",
            "pitch": "Activa ads para empezar a generar tráfico y CVR medibles — sin eso no podemos calcular dónde está la oportunidad real.",
            "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
            "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
        }
    if cvr_above_bench and not has_traffic:
        return {
            "headline": "Conversión fuerte, falta tráfico medible", "color": "#F74D04",
            "texto": f"Tu CR ({cvr_disp}) ya está sobre el benchmark de tu categoría ({bench_cvr_disp}), pero no hay tráfico registrado esta semana para medir el volumen.",
            "pitch": f"Tu tienda convierte mejor que el promedio ({cvr_disp} vs {bench_cvr_disp}). El problema no es la tienda — necesitamos activar ads para medir y escalar el tráfico real.",
            "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
            "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
        }
    if not traffic_ok and not cvr_ok:
        # Problema doble: insight en 2 pasos (mas largo, pedido explicito
        # de Sabas) -- primero solo conversion, despues el extra de
        # tambien arreglar trafico.
        pedidos_a, gmv_a = _incremental_por_cvr()
        pedidos_ambos = 0.0
        if ordenes_mes > 0 and has_traffic and has_cvr and bench_traffic > 0 and bench_cvr > 0 and traffic > 0 and cvr > 0:
            pedidos_ambos = ordenes_mes * (bench_traffic / traffic) * (bench_cvr / cvr) - ordenes_mes
        gmv_extra_trafico = max((pedidos_ambos * aov) - gmv_a, 0)
        extra = (
            f" Podrías acceder a ~{fmt_ars(round(gmv_a))} corrigiendo la conversión, "
            f"y a ~{fmt_ars(round(gmv_extra_trafico))} más si corriges el tráfico también."
            if gmv_a > 0 else ""
        )
        return {
            "headline": "Problema doble", "color": "#EF4444",
            "texto": f"Dos frentes abiertos: tráfico de {traffic_disp} vs benchmark {bench_traffic_disp}, y conversión de {cvr_disp} vs {bench_cvr_disp}.{extra}",
            "pitch": f"Dos frentes abiertos: tráfico de {traffic_disp} vs benchmark {bench_traffic_disp} y CVR de {cvr_disp} vs {bench_cvr_disp}.{extra} La prioridad es primero limpiar la tienda y después escalar tráfico — al revés es tirar plata.",
            "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
            "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
        }
    if not traffic_ok:
        pedidos_t, gmv_t = _incremental_por_trafico()
        extra = f" Si llegaras al benchmark de tráfico, sumarías ~{round(pedidos_t)} pedidos más al mes — eso son ~{fmt_ars(round(gmv_t))} adicionales." if gmv_t > 0 else ""
        return {
            "headline": "Problema: Tráfico", "color": "#F74D04",
            "texto": f"Tu conversión ({cvr_disp}) está sobre el benchmark ({bench_cvr_disp}), pero el tráfico ({traffic_disp}) está por debajo del benchmark de categoría ({bench_traffic_disp}).{extra}",
            "pitch": f"Tu tienda convierte al {cvr_disp} — está por encima del promedio de tu categoría. El problema es que ves {traffic_disp} visitas por semana contra un benchmark de {bench_traffic_disp}.{extra}",
            "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
            "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
        }
    if not cvr_ok:
        pedidos_c, gmv_c = _incremental_por_cvr()
        extra = f" Si llegaras al benchmark de conversión, sumarías ~{round(pedidos_c)} pedidos más al mes — eso son ~{fmt_ars(round(gmv_c))} adicionales." if gmv_c > 0 else ""
        return {
            "headline": "Problema: Conversión", "color": "#F74D04",
            "texto": f"Tu tráfico ({traffic_disp}) está en línea con el benchmark ({bench_traffic_disp}), pero tu conversión ({cvr_disp}) está por debajo del promedio de categoría ({bench_cvr_disp}).{extra}",
            "pitch": f"Tienes {traffic_disp} visitas por semana — el tráfico no es el problema. Pero tu tienda convierte al {cvr_disp} cuando el promedio de tu categoría es {bench_cvr_disp}.{extra}",
            "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
            "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
        }
    return {
        "headline": "Ambas métricas OK", "color": "#22C55E",
        "texto": f"Tráfico ({traffic_disp}) y conversión ({cvr_disp}) están alineados o por encima del benchmark de categoría ({bench_traffic_disp} / {bench_cvr_disp}).",
        "pitch": f"Tráfico en {traffic_disp}/sem y CVR en {cvr_disp} — ambas métricas sobre el benchmark de tu categoría. Estás en condiciones de escalar: más presupuesto en ads se convierte directo en GMV.",
        "traffic_disp": traffic_disp, "bench_traffic_disp": bench_traffic_disp,
        "cvr_disp": cvr_disp, "bench_cvr_disp": bench_cvr_disp,
    }


def funnel_diagnosis(cvr, traffic, aov, gmv, bench_cvr, bench_traffic, ordenes_mes=0):
    """
    Wrapper público de _funnel_diagnosis_interno: agrega "cvr_above_bench"
    al resultado -- pedido explícito de Sabas (agosto 2026): la baldosa
    de "Conversión de la marca" en el funnel SVG debe pintarse gris si la
    conversión real está por debajo del benchmark de categoría (mostrando
    "CR baja" adentro), o verde si está en o por encima (mostrando "CR
    sana") -- antes siempre se pintaba verde sin importar el resultado.

    cvr_above_bench acá es la comparación DIRECTA (cvr >= bench_cvr, sin
    la tolerancia del 85% que usa _funnel_diagnosis_interno para decidir
    el headline/color general del diagnóstico combinado) -- son dos
    criterios distintos a propósito: el headline general es más permisivo
    (tolera hasta 15% por debajo como "ok"), pero la baldosa puntual de
    conversión debe reflejar la comparación real y exacta contra el
    benchmark, sin margen.

    ordenes_mes (agosto 2026, sexto ajuste): nuevo parámetro, mismo dato
    que ya usa Disponibilidad en 360 Action (row.ordenes) -- alimenta los
    insights de incremental de pedidos/pesos, ver docstring de
    _funnel_diagnosis_interno para el detalle de las 3 fórmulas.
    """
    resultado = _funnel_diagnosis_interno(cvr, traffic, aov, gmv, bench_cvr, bench_traffic, ordenes_mes)
    resultado["cvr_above_bench"] = bool(cvr > 0 and bench_cvr > 0 and cvr >= bench_cvr)
    # traffic_above_bench (agosto 2026, séptima vuelta): mismo criterio
    # exacto (comparación directa, sin la tolerancia del 85% del
    # diagnóstico general) pero para la baldosa de "Tráfico de la marca"
    # -- pedido explícito de Sabas: rojo + "Tráfico bajo" si está por
    # debajo del benchmark, verde + "Tráfico sano" si está en o por
    # encima (antes esta baldosa era siempre azul fijo, sin reflejar el
    # resultado real, igual que le pasaba antes a la de Conversión).
    resultado["traffic_above_bench"] = bool(traffic > 0 and bench_traffic > 0 and traffic >= bench_traffic)
    return resultado


def incremental_vs_mes_anterior(traffic, traffic_delta, cvr, cvr_delta, aov, ordenes_mes):
    """
    Pedidos/GMV incremental si NO se hubiera perdido tráfico y/o conversión
    vs el MES ANTERIOR (no vs benchmark de categoría -- para eso está
    _incremental_por_trafico/_incremental_por_cvr dentro de
    _funnel_diagnosis_interno, que alimentan la card del Funnel).

    Mismo mecanismo exacto que esas dos funciones (mismo resguardo: si
    ordenes_mes o aov vienen en 0, o no hay delta valido, da 0 sin caso
    especial), pero la referencia es el valor de HACE UN MES (derivado de
    traffic_delta/cvr_delta, que ya vienen del "vs LM (%)" de las hojas
    TRAFFIC/CVR%), no el benchmark de categoria (pedido explicito de
    Sabas, septiembre 2026 -- card "Tráfico & Conversión vs mes
    anterior").

    Solo tiene sentido corregir una caida (delta < 0) -- si el mes subio,
    no hay "pedidos perdidos" que recuperar, ese caso da 0 pesos/pedidos
    (la card ya muestra la suba en verde, no necesita ademas un numero
    de incremental que no aplica).

    valor_anterior se despeja de: valor_actual = valor_anterior * (1 + delta)
    -> valor_anterior = valor_actual / (1 + delta). Si delta <= -1 (caida
    del 100% o mas, ej. cvr_delta=-1.0 cuando la marca se quedo sin CVR
    esta semana), el despeje no es fiable (division por cero o valor
    anterior negativo) -- se resguarda devolviendo 0 en vez de un numero
    inventado.

    Devuelve dict: pedidos_trafico, gmv_trafico, pedidos_cvr, gmv_cvr,
    traffic_anterior, cvr_anterior (estos dos ultimos, 0.0 si no se
    pudieron calcular -- ver resguardo arriba).
    """
    def _valor_anterior(valor_actual, delta):
        if valor_actual > 0 and delta is not None and delta > -1:
            return valor_actual / (1 + delta)
        return 0.0

    def _incremental(valor_actual, valor_anterior):
        if ordenes_mes > 0 and valor_actual > 0 and valor_anterior > valor_actual:
            pedidos = ordenes_mes * (valor_anterior / valor_actual - 1)
            return pedidos, pedidos * aov
        return 0.0, 0.0

    traffic_anterior = _valor_anterior(traffic, traffic_delta)
    cvr_anterior = _valor_anterior(cvr, cvr_delta)

    pedidos_trafico, gmv_trafico = _incremental(traffic, traffic_anterior)
    pedidos_cvr, gmv_cvr = _incremental(cvr, cvr_anterior)

    return {
        "traffic_anterior": traffic_anterior,
        "cvr_anterior": cvr_anterior,
        "pedidos_trafico": pedidos_trafico,
        "gmv_trafico": gmv_trafico,
        "pedidos_cvr": pedidos_cvr,
        "gmv_cvr": gmv_cvr,
    }


# ── Campaign Designer ──
ADS_CPC_ARS = 950            # costo por clic/visita
ADS_EROSION_SEMANAL = 0.08   # erosion de conversion por semana en el blend a 4 semanas -- constante
                              # INTERNA (agosto 2026, septimo ajuste, pedido explicito de Sabas):
                              # nunca se muestra en ningun texto/tooltip de la UI.

# % sugerido de inversion segun el rango de ventas mensuales (GMV del mes
# anterior completo) -- tabla de Sabas (agosto 2026, septimo ajuste),
# reemplaza el ADS_PRESSURE_PCT fijo del 18% que se usaba antes. Cada
# tupla es (techo del rango, % sugerido); se recorre de menor a mayor y
# se usa el primer techo que la marca no supera.
ADS_PRESSURE_TIERS = [
    (145_000, 0.20),
    (725_000, 0.17),
    (1_450_000, 0.15),
    (7_250_000, 0.10),
    (float("inf"), 0.06),
]


def ads_pressure_pct_for(gmv_last):
    """% sugerido de inversion para esta marca, segun en que tramo de
    ADS_PRESSURE_TIERS cae su GMV del mes anterior completo."""
    for techo, pct in ADS_PRESSURE_TIERS:
        if gmv_last <= techo:
            return pct
    return ADS_PRESSURE_TIERS[-1][1]


def gmv_ultima_semana(gmv_mes_actual, dias_transcurridos):
    """
    Deriva un GMV semanal a partir del GMV del mes en curso (el mismo dato
    que ya muestra la card GMV de Home, acumulado 'hasta ayer') -- pedido
    explicito de Sabas: NO tomar ese acumulado como si ya fuera una
    semana, sino sacar el promedio diario real (con los dias que
    efectivamente transcurrieron, mismo criterio ya validado de
    dias_transcurridos_mes_actual()) y multiplicarlo por 7.

    SIN USO DESDE la vigésima segunda vuelta (pedido explícito de Sabas):
    ads_plan() ya no llama a esta función -- pasó a usar gmv_last / 4
    (ver el "BUG REAL CORREGIDO" en el docstring de ads_plan) en vez del
    ritmo del mes actual que esta función calculaba. Se deja definida sin
    uso por si se necesita en el futuro, no se elimina.
    """
    dias = max(dias_transcurridos, 1)
    return (gmv_mes_actual / dias) * 7 if gmv_mes_actual > 0 else 0.0


def ads_plan(gmv_last, gmv_mes_actual, dias_transcurridos, cvr, aov):
    """
    Ads Plan (agosto 2026, septimo ajuste -- reescrito por completo,
    pedido explicito de Sabas; reemplaza el modelo plano de 18% del GMV
    del mes anterior ÷ 4 semanas).

    Presupuesto semana 1 = % sugerido (ver ads_pressure_pct_for, tabla por
    GMV del mes anterior completo) x GMV semanal derivado del MISMO GMV
    del mes anterior (gmv_last ÷ 4) -- ver "BUG REAL CORREGIDO" abajo, esto
    reemplazó al ritmo del mes actual. Ya NO se distingue Adquisicion vs
    Upselling -- siempre se devuelve el presupuesto recomendado completo
    para la marca, tenga o no Ads activo hoy (pedido explicito de Sabas:
    esa decision queda en criterio del Farmer, no en la formula).

    BUG REAL CORREGIDO (vigésima segunda vuelta, pedido explícito de
    Sabas): antes, el monto en pesos del presupuesto salía del ritmo del
    MES ACTUAL EN CURSO (gmv_ultima_semana: gmv_mes_actual ÷ días
    transcurridos × 7), mientras que el % de la tabla salía del GMV del
    MES ANTERIOR completo (gmv_last) -- dos fuentes de GMV distintas
    mezcladas en la misma fórmula. Ahora ambos pasos (elegir el % Y
    calcular el monto) usan el MISMO gmv_last (mes anterior completo),
    simplemente dividido entre 4 en vez de proyectado por ritmo diario.
    gmv_mes_actual y dias_transcurridos quedan en la firma sin usarse (no
    se tocó el punto de llamada en wingmanapp.py, que sigue pasando los
    mismos 5 argumentos) -- si se quiere, se pueden quitar de la firma en
    una limpieza futura, pero dejarlos no rompe nada ni cambia el
    resultado.

    Proyeccion con erosion (mecanismo NUEVO, no existia antes en
    Wingman): se asume el MISMO presupuesto semanal sostenido durante 4
    semanas, con la conversion erosionando ADS_EROSION_SEMANAL cada
    semana -- constante interna, nunca se muestra en la UI. Semana 1 es
    la base, sin erosion. El ROAS de 4 semanas es el blend real de las 4
    (GMV incremental total / presupuesto total de las 4 semanas), por eso
    sale mas bajo que el ROAS de semana 1 sola.

    Para cada semana n (n=1..4):
      cvr_n     = cvr x (1 - ADS_EROSION_SEMANAL)^(n-1)
      visitas_n = presupuesto_semana1 / ADS_CPC_ARS   (mismo presupuesto todas las semanas)
      pedidos_n = visitas_n x cvr_n
      gmv_n     = pedidos_n x aov
    """
    out = {
        "pct": 0.0, "gmv_semana": 0.0, "presupuesto_semana1": 0.0,
        "roas_1sem": 0.0, "roas_4sem": 0.0,
        "gmv_inc_1sem": 0.0, "pedidos_inc_1sem": 0.0,
        "gmv_inc_4sem": 0.0, "pedidos_inc_4sem": 0.0,
        "has_projection": False,
    }
    if gmv_last <= 0:
        return out

    pct = ads_pressure_pct_for(gmv_last)
    gmv_sem = gmv_last / 4
    presupuesto = round(pct * gmv_sem / 1000) * 1000

    out["pct"] = pct
    out["gmv_semana"] = gmv_sem
    out["presupuesto_semana1"] = presupuesto

    if presupuesto <= 0 or cvr <= 0 or aov <= 0:
        return out

    visitas_semana = presupuesto / ADS_CPC_ARS
    gmv_total_4sem = 0.0
    pedidos_total_4sem = 0.0
    for n in range(1, 5):
        cvr_n = cvr * ((1 - ADS_EROSION_SEMANAL) ** (n - 1))
        pedidos_n = visitas_semana * cvr_n
        gmv_n = pedidos_n * aov
        if n == 1:
            out["pedidos_inc_1sem"] = pedidos_n
            out["gmv_inc_1sem"] = gmv_n
        gmv_total_4sem += gmv_n
        pedidos_total_4sem += pedidos_n

    out["gmv_inc_4sem"] = gmv_total_4sem
    out["pedidos_inc_4sem"] = pedidos_total_4sem
    out["roas_1sem"] = out["gmv_inc_1sem"] / presupuesto if presupuesto > 0 else 0.0
    presupuesto_4sem = presupuesto * 4
    out["roas_4sem"] = gmv_total_4sem / presupuesto_4sem if presupuesto_4sem > 0 else 0.0
    out["has_projection"] = True
    return out


def markdown_plan_by_cvr(cvr):
    """
    Markdown Plan · regla por tramo de conversion (agosto 2026, septimo
    ajuste: escalera corrida +5 puntos completos, pedido explicito de
    Sabas -- misma logica de tramos de CVR, solo cambia el % de
    descuento):
      CVR < 10%        -> 30% OFF + 10% PRO  (antes 25%)
      10% <= CVR < 15%  -> 25% OFF + 5% PRO   (antes 20%)
      CVR >= 15%        -> 20% OFF + 5% PRO   (antes 15%)
    Siempre se muestran los 3 productos principales, sin importar el tramo.
    """
    if cvr < 0.10:
        return {"discount": 30, "pro_extra": 10, "tramo": "CVR por debajo del 10%"}
    if cvr < 0.15:
        return {"discount": 25, "pro_extra": 5, "tramo": "CVR entre 10% y 15%"}
    return {"discount": 20, "pro_extra": 5, "tramo": "CVR de 15% o más"}


def coinversion_markdown_plan(cvr, coinv_group_key):
    """
    Markdown Plan con coinversion. Si la marca tiene un grupo de coinversion
    habilitado (coinv_has=True en load_asignacion), la promo SIEMPRE es 30%
    OFF -- no la regla de 15/20/25 por tramo de CVR. El PRO extra si sigue
    el mismo criterio de CVR que ya usamos (10/5/5).

    El reparto Aliado:Rappi se calcula sobre el DESCUENTO TOTAL combinado
    (30% + PRO extra), no por separado -- pedido explicito de Sabas: "no
    haces la division del 30 y el 5 por aparte, sino el 30 y 5 por ciento
    total, dices cuanto termina colocando el aliado y cuanto Rappi".

    Devuelve None si el grupo no existe o no tiene coinversion (Churn).
    """
    if not coinv_group_key or coinv_group_key not in COINV_GROUPS:
        return None
    grupo = COINV_GROUPS[coinv_group_key]
    if not grupo["has_coinv"]:
        return None

    pro_extra = 10 if cvr < 0.10 else 5
    descuento_total = 30 + pro_extra
    r_aliado, r_rappi = grupo["ratio_aliado"], grupo["ratio_rappi"]
    pct_aliado = descuento_total * r_aliado / (r_aliado + r_rappi)
    pct_rappi = descuento_total * r_rappi / (r_aliado + r_rappi)

    return {
        "discount": 30,
        "pro_extra": pro_extra,
        "descuento_total": descuento_total,
        "grupo_label": grupo["label"],
        "grupo_icon": grupo["icon"],
        "ratio": grupo["ratio"],
        "pct_aliado": pct_aliado,
        "pct_rappi": pct_rappi,
    }


def _fmt_fecha_relativa(fecha):
    """
    < 72h desde ahora -> chulito; > 72h -> alerta; sin fecha -> guion --
    pedido explícito de Sabas (vigésima segunda vuelta). "Ahora" es
    datetime.now() en hora local del servidor (mismo criterio que el
    resto de Wingman usa para "hoy"/"días transcurridos").
    """
    if fecha is None:
        return "-"
    try:
        ahora = datetime.now()
        if isinstance(fecha, datetime):
            delta = ahora - fecha
        else:
            delta = ahora - datetime.combine(fecha, datetime.min.time())
        horas = delta.total_seconds() / 3600
        return "✅" if 0 <= horas <= 72 else "🚨"
    except Exception:
        return "-"


_TIER_ICON = {
    "1": "🥇", "2": "🥈", "3": "🥉", "4": "🚨",
}


def _tier_icon_for(tier_texto):
    """'1.-Oro' -> 🥇, '2.-Plata' -> 🥈, '3.-Basico' -> 🥉, '4.-Alerta' -> 🚨,
    sin dato -> sin ícono (string vacío)."""
    if not tier_texto:
        return ""
    primer_char = tier_texto.strip()[:1]
    return _TIER_ICON.get(primer_char, "")


def pitchdata_for_brand(brand_key_str):
    """
    Todos los datos derivados de PITCHDATA/TOPREST para UNA marca --
    pedido explícito de Sabas (vigésima segunda vuelta), función central
    que wingmanapp.py consume para la cabecera de Ficha de Marca, OPS
    General (Top Res) y la barra de contactos de Outreach. Nunca
    revienta si falta algún dato -- todo tiene un default seguro.

    Devuelve:
      microzonas_texto: "Palermo / Belgrano / Centro" (limpias,
        deduplicadas, en el orden en que aparecen las tiendas de la
        marca en DETALLE) -- "" si no hay ninguna.
      encargado: nombre de contacto de la tienda de referencia (ver
        tienda_referencia_for) -- "" si no hay.
      link: Link Tienda de la tienda de referencia -- "" si no hay.
      conexion_icono / ordenes_icono: "✅"/"🚨"/"-" según _fmt_fecha_relativa
        sobre la Última Conexión/Última Orden de la tienda de referencia.
      take_rate: % de comisión (float 0-1) de la tienda de referencia, o
        None si no hay dato -- el caller decide cómo mostrarlo (pedido
        explícito: se muestra tal cual venga, incluso si es negativo).
      telefonos_extra / correos_extra: listas de teléfonos/correos que
        NO son el que ya se muestra en la cabecera -- para la barra de
        Outreach. Sin duplicados (mismo número en formato distinto no
        cuenta 2 veces, normalizado a últimos 10 dígitos).
      top_res: dict con tier_actual/mes_actual/tier_anterior/mes_anterior
        de la tienda de referencia, con íconos de medalla ya resueltos
        -- "Sin dato" en vez del tier cuando falta, pedido explícito.
    """
    out = {
        "microzonas_texto": "", "encargado": "", "link": "",
        "conexion_icono": "-", "ordenes_icono": "-", "take_rate": None,
        "telefonos_extra": [], "correos_extra": [],
        "top_res": {"tier_actual": "Sin dato", "icono_actual": "", "mes_actual": "",
                    "tier_anterior": "Sin dato", "icono_anterior": "", "mes_anterior": ""},
    }

    brand_to_stores, _ = _detalle_brand_to_stores()
    stores = brand_to_stores.get(brand_key_str, [])
    if not stores:
        return out

    pitch = load_pitchdata()
    toprest = load_toprest()

    # Microzonas: todas las de las tiendas de la marca, limpias y
    # deduplicadas, en el orden en que aparecen -- pedido explícito.
    vistas = []
    for sid in stores:
        data = pitch.get(sid)
        if data and data.get("microzona"):
            limpia = limpiar_microzona(data["microzona"])
            if limpia and limpia not in vistas:
                vistas.append(limpia)
    out["microzonas_texto"] = " / ".join(vistas)

    # Tienda de referencia: resuelve encargado, link, conexión/órdenes,
    # take rate y Top Res -- mismo criterio para las 5 cosas.
    ref_sid = _tienda_referencia_for_impl(brand_key_str)
    if ref_sid is not None:
        ref_data = pitch.get(ref_sid, {})
        out["encargado"] = ref_data.get("contacto", "") or ""
        out["link"] = ref_data.get("link", "") or ""
        out["conexion_icono"] = _fmt_fecha_relativa(ref_data.get("ultima_conexion"))
        out["ordenes_icono"] = _fmt_fecha_relativa(ref_data.get("ultima_orden"))
        out["take_rate"] = ref_data.get("take_rate")

        ref_top = toprest.get(ref_sid)
        if ref_top:
            mes_actual_txt = _MESES_ES.get(ref_top["mes_actual"].month, "").upper() if ref_top.get("mes_actual") else ""
            mes_anterior_txt = _MESES_ES.get(ref_top["mes_anterior"].month, "").upper() if ref_top.get("mes_anterior") else ""
            tier_actual = ref_top.get("tier_actual") or ""
            tier_anterior = ref_top.get("tier_anterior") or ""
            out["top_res"] = {
                "tier_actual": tier_actual if tier_actual else "Sin dato",
                "icono_actual": _tier_icon_for(tier_actual),
                "mes_actual": mes_actual_txt,
                "tier_anterior": tier_anterior if tier_anterior else "Sin dato",
                "icono_anterior": _tier_icon_for(tier_anterior),
                "mes_anterior": mes_anterior_txt,
            }

    # Teléfonos/correos adicionales: todos los de TODAS las tiendas de la
    # marca (no solo la de referencia), que no sean el que ya se muestra
    # en la cabecera (el de ASIGNACION) -- pedido explícito: no perder
    # ningún número/correo. El correo de ASIGNACION se agrega aparte por
    # el caller (viene de otra fuente, no de PITCHDATA).
    tel_asig_norm = _normalizar_telefono_10(_telefono_asignacion_for(brand_key_str))
    vistos_tel = set()
    if tel_asig_norm:
        vistos_tel.add(tel_asig_norm)
    telefonos_extra = []
    for sid in stores:
        data = pitch.get(sid)
        if not data or not data.get("telefono"):
            continue
        norm = _normalizar_telefono_10(data["telefono"])
        if norm and norm not in vistos_tel:
            vistos_tel.add(norm)
            telefonos_extra.append(data["telefono"])
    out["telefonos_extra"] = telefonos_extra
    # PITCHDATA no trae correo por tienda (solo Nombre contacto store) --
    # correos_extra queda vacía por ahora; el caller agrega el de
    # ASIGNACION. Si en el futuro PITCHDATA suma una columna de correo
    # por tienda, se completa acá con el mismo patrón que telefonos_extra.
    return out


def outreach_hallazgos(key, availability_pct, perfect_store_pct, photos_pct, purchase_pct,
                        markdown_active, ads_active):
    """
    Todos los hallazgos del 360 para el mensaje de Outreach -- no solo el
    primero. Mismo orden de revision que Growth OS (OPS -> Menu -> Markdown
    -> Ads), pero acá se listan TODOS los que aplican, no se corta en el
    primero (pedido explicito de Sabas: "todos los hallazgos deben decirse
    en el outreach"). Texto corto y generico por palanca, no el titulo largo
    de la card de 360 Action.

    Devuelve lista de strings. Vacia si no hay ningun hallazgo negativo (en
    ese caso el llamador arma el mensaje de seguimiento, sin frente).
    """
    hallazgos = []
    signals = signals_for_brand(key)

    # OPS: cualquier señal de riesgo (reclamos/cancelaciones/defectos/espera/
    # churn) con valor > umbral, o disponibilidad baja -- se listan todas las
    # que apliquen, no solo la mas fuerte.
    ops_signals = [s for s in signals if s["kind"].startswith("ops") and s["kind"] != "ops_availability"]
    labels_ops = {
        "ops_wait_time": "tiempo de espera elevado",
        "ops_claims": "reclamos por encima de lo esperado",
        "ops_cancellations": "cancelaciones que frenan la eficiencia",
        "ops_defects": "calidad del producto",
        "ops_other": "riesgo de desconexión (Churn)",
    }
    vistos = set()
    for s in sorted(ops_signals, key=lambda s: s["value"], reverse=True):
        if s["value"] > 0.05 and s["kind"] not in vistos:
            hallazgos.append(labels_ops.get(s["kind"], "un tema operativo"))
            vistos.add(s["kind"])
    if availability_pct and 0 < availability_pct < 90:
        hallazgos.append("tienda con horario o disponibilidad reducida")

    # Menu: fotos/experiencia de compra por debajo de umbral, y PDF Menu
    # desactualizado (mismo bug que en menu_tactical_card: esta función
    # tampoco consultaba la señal real de Priority Data para PDF Menu).
    if photos_pct and photos_pct < 90:
        hallazgos.append("fotos del menú por debajo del estándar")
    if purchase_pct and purchase_pct < 90:
        hallazgos.append("experiencia de compra por debajo del estándar")
    if any(s["kind"] == "menu_pdf" for s in signals):
        hallazgos.append("PDF del menú desactualizado")

    # Markdown y Ads: sin campaña/pauta activa.
    if not markdown_active:
        hallazgos.append("sin promoción (Markdown) activa hoy")
    if not ads_active:
        hallazgos.append("sin pauta (Ads) activa hoy")

    return hallazgos


def data_issues():
    return st.session_state.get("data_issues", {})


# =========================
# VISTA SUPERVISOR (Fabián, único supervisor de todo Cono Sur, agosto 2026)
# =========================

SUPERVISOR_EMAILS = {"fabian.ayala@rappi.com"}

PAISES_CONO_SUR = [
    {"code": "AR", "label": "Argentina"},
    {"code": "CL", "label": "Chile"},
    {"code": "UY", "label": "Uruguay"},
]


def is_supervisor(email):
    return str(email).strip().lower() in SUPERVISOR_EMAILS


@st.cache_data(ttl=86400, show_spinner=False)
def portfolio_supervisor():
    """
    Cartera COMPLETA para el Buscador de Marcas del Supervisor: concatena
    portfolio_for(e) de los 27 farmers activos (los 3 países juntos), sin
    restricción -- el supervisor puede buscar cualquier marca de cualquier
    farmer. A diferencia de brand_coverage_for/contact_performance_for (que
    reciben la lista de un país a la vez), esto siempre trae TODO el equipo,
    porque el buscador no está atado al mapa/país seleccionado.

    Se agrega columna "farmer_owner" (a qué farmer pertenece cada marca) y
    "farmer_moneda" (su moneda nativa), ya que el supervisor ve marcas de
    varias monedas a la vez -- cada ficha debe mostrarse en la moneda de
    SU dueño, no en una moneda fija.
    """
    farmers = list_farmers_activos()
    portfolios = []
    for email in farmers:
        p = portfolio_for(email)
        if p.empty:
            continue
        p = p.copy()
        p["farmer_owner"] = email
        p["farmer_moneda"] = farmer_moneda(email)
        portfolios.append(p)
    if not portfolios:
        return pd.DataFrame()
    return pd.concat(portfolios, ignore_index=True)


def tabla_farmers_por_pais(pais):
    """
    Tabla de la vista de Supervisor: una fila por Farmer del país pedido,
    con Contactos Efectivos + Adquisición Ads + Upselling Ads + Conversión
    MD + PW1/PW2/Churn, ordenada de mayor a menor CUMPLIMIENTO del target
    (no por cantidad bruta de contactos -- ver nota en el cuerpo de la
    funcion).

    IMPORTANTE (corrección agosto 2026, tercera vuelta): "Adquisición Ads"
    y la nueva "Upselling Ads" (upselling_ads_for) ya NO usan como
    denominador el conteo bruto de marcas pendientes -- usan el "camino
    más corto" para cerrar el gap real en USD (Target - Bookings Reales
    Corregidos), priorizando las marcas de mayor gap individual primero,
    con un PISO de un cierre por día hábil del mes (ningún farmer recibe
    meta menor a eso, ver _dias_habiles_totales_mes). El NUMERADOR de
    Adquisición sigue viniendo de PRODUCTIVITY (Never Ads CONVERTIDOS,
    excluyendo "No activo"). El NUMERADOR de Upselling está PENDIENTE de
    una hoja alimentadora nueva -- siempre llega en 0 por ahora (ver
    upselling_ads_for). Conversión MD no cambió, sigue viniendo de
    conversion_for. PW1/PW2/Churn siguen viniendo de brand_coverage_for
    -- esos no tenían el problema, son % de cartera en ambos lugares.

    Cada fila sale de contact_performance_for/brand_coverage_for/
    conversion_for con UN solo email (no la lista agregada) -- la tabla es
    el desglose individual dentro del país, el agregado del país completo
    va aparte en los donuts de arriba (con la lista completa de
    farmers_por_pais).
    """
    farmers = farmers_por_pais(pais)
    filas = []
    for email in farmers:
        cp = contact_performance_for(email)
        bc = brand_coverage_for(email)
        conv = conversion_for(email)
        adq = adquisicion_ads_for(email)
        ups = upselling_ads_for(email)
        target = target_for(email)
        # BUG REAL CORREGIDO (agosto 2026): "cumplimiento_pct" usaba el
        # acumulado crudo (total_effective/target*100) en vez del RITMO
        # que contact_performance_for ya calcula (pace_pct, proyectado por
        # días hábiles transcurridos) -- con el mes recién arrancando
        # (ej. 1-2 días cargados), el acumulado crudo da un % chiquito que
        # no representa el ritmo real del farmer, y ademas ESTE numero es
        # el que ordena toda la tabla -- con el bug, el orden tambien
        # salía mal (todos con % parecidos y chicos en vez de reflejar
        # quién viene mejor posicionado). Sin target cargado o sin pace
        # calculable (mes sin ningún día hábil transcurrido todavía) se
        # deja en -1 para que caiga al final, mismo criterio que antes.
        if target > 0 and cp.get("pace_pct") is not None:
            cumplimiento = cp["pace_pct"]
        elif target > 0:
            cumplimiento = cp["total_effective"] / target * 100
        else:
            cumplimiento = -1
        filas.append({
            "farmer": email,
            "contactos_efectivos": cp["total_effective"],
            "target": target,
            "cumplimiento_pct": cumplimiento,
            "ads_pct": adq["adq_pct"], "ads_n": adq["adq_n"], "ads_total": adq["adq_target"],
            "ups_pct": ups["ups_pct"], "ups_n": ups["ups_n"], "ups_total": ups["ups_target"],
            "md_pct": conv["md_pct"], "md_n": conv["md_conv"], "md_total": conv["md_total"],
            "pw1_pct": bc["pw1"], "pw1_n": bc["pw1_n"],
            "pw2_pct": bc["pw2"], "pw2_n": bc["pw2_n"],
            "churn_pct": bc["churn"], "churn_n": bc["churn_n"],
            "total_marcas": bc["total"],
        })
    out = pd.DataFrame(filas)
    if out.empty:
        return out
    return out.sort_values("cumplimiento_pct", ascending=False).reset_index(drop=True)


# =========================
# TRACKING DE LOGIN/LOGOUT (pedido explícito de Sabas, agosto 2026)
# =========================
#
# Tabla de 4 columnas -- Farmer, Última entrada, Tiempo de uso, Última
# salida -- SOLO el último valor por farmer (no historial acumulado, "no
# saturar ni guardar histórico"). Visible únicamente para el Supervisor,
# debajo de la tabla de Rendimiento País.
#
# Persistencia: el disco de Streamlit Cloud se resetea con cada redeploy
# o reinicio del servidor por inactividad -- un archivo local no
# sobrevive eso. Se usa GitHub como almacenamiento vía su API REST (leer
# + actualizar un archivo chico, "data/login_log.csv", en el mismo repo
# donde ya vive el código) -- eso SÍ persiste, porque no depende del
# disco del servidor. Necesita un Personal Access Token de GitHub
# (permiso "repo") guardado como secreto de Streamlit Cloud:
#   GITHUB_TOKEN = "ghp_..."
#   GITHUB_REPO  = "usuario/repo"
# Sin esos secretos configurados, el tracking queda desactivado
# silenciosamente (no rompe el resto de la app) -- ver _github_configurado().

LOGIN_LOG_PATH = "data/login_log.csv"
_LOGIN_LOG_COLUMNS = ["farmer", "ultima_entrada", "tiempo_uso_min", "ultima_salida"]


def _login_log_df_vacio():
    """DataFrame vacío con los dtypes correctos YA forzados (no solo las
    columnas) -- para que el primer login del sistema (archivo aún
    inexistente en GitHub) no arranque con columnas float64 por
    inferencia vacía, mismo bug que _forzar_dtypes_login_log corrige al
    releer un CSV existente."""
    df = pd.DataFrame(columns=_LOGIN_LOG_COLUMNS)
    return _forzar_dtypes_login_log(df)


def _forzar_dtypes_login_log(df):
    """
    Fuerza el dtype correcto de cada columna del login_log, sin importar
    qué haya inferido pandas al leer el CSV -- bug real corregido (agosto
    2026): con "ultima_salida"/"ultima_entrada" vacías (recién logueado,
    aún sin salir), pandas infiere esas columnas como float64 (todo NaN,
    sin ningún string real para deducir que deberían ser texto). Al
    intentar después escribir un string de fecha ahí (registrar_logout),
    pandas rechaza la asignación con TypeError.
    """
    df = df.copy()
    for c in ("farmer", "ultima_entrada", "ultima_salida"):
        df[c] = df[c].astype(object).where(df[c].notna(), None)
    df["tiempo_uso_min"] = pd.to_numeric(df["tiempo_uso_min"], errors="coerce")
    return df


def _github_configurado():
    """True si los secretos de GitHub están disponibles -- si no, todo el
    módulo de tracking se desactiva sin romper el resto de Wingman."""
    try:
        return bool(st.secrets.get("GITHUB_TOKEN")) and bool(st.secrets.get("GITHUB_REPO"))
    except Exception:
        return False


def _github_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    }


def _github_get_file():
    """
    Trae (dataframe, sha) del CSV de login_log en GitHub. sha es requerido
    por la API de GitHub para poder ACTUALIZAR el archivo (evita
    sobreescribir un cambio concurrente sin saberlo -- "compare-and-swap"
    optimista). Si el archivo no existe todavía (primera vez que se usa
    el tracker), devuelve un DataFrame vacío con las columnas correctas y
    sha=None (GitHub crea el archivo nuevo en ese caso).

    BUG REAL CORREGIDO (agosto 2026): si la fila de un farmer tiene
    "ultima_salida" vacía (recién hizo login, todavía no salió), esa
    columna se guarda como CSV con celda vacía -- al releerla, pandas
    infiere que la columna ENTERA es float64 (no tiene ningún string real
    ahí para deducir que debería ser texto). Cuando registrar_logout
    intentaba después escribir un string de fecha en esa celda
    (df.loc[...] = "2026-08-04 19:05:00"), pandas rechazaba la asignación
    con TypeError: "Invalid value ... for dtype 'float64'" -- reproducido
    y confirmado el mecanismo exacto. Se fuerza el dtype correcto de cada
    columna (texto para farmer/fechas, numérico para tiempo_uso_min) apenas
    se lee el CSV, sin importar qué haya inferido pandas.
    """
    import base64
    import requests

    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{LOGIN_LOG_PATH}"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=8)
        if resp.status_code == 404:
            return _login_log_df_vacio(), None
        resp.raise_for_status()
        data = resp.json()
        contenido = base64.b64decode(data["content"]).decode("utf-8")
        df = pd.read_csv(pd.io.common.StringIO(contenido))
        for c in _LOGIN_LOG_COLUMNS:
            if c not in df.columns:
                df[c] = None
        df = df[_LOGIN_LOG_COLUMNS]
        return _forzar_dtypes_login_log(df), data["sha"]
    except Exception as e:
        _issue("login_log (leer)", e)
        return _login_log_df_vacio(), None


def _github_put_file(df, sha, mensaje_commit):
    """Sube el CSV actualizado a GitHub (crea el archivo si sha es None,
    lo actualiza si ya existía). Silencioso ante errores -- un fallo acá
    no debe tumbar el login/logout real del Farmer."""
    import base64
    import requests

    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{LOGIN_LOG_PATH}"
    contenido_csv = df.to_csv(index=False)
    contenido_b64 = base64.b64encode(contenido_csv.encode("utf-8")).decode("utf-8")
    payload = {"message": mensaje_commit, "content": contenido_b64}
    if sha:
        payload["sha"] = sha
    try:
        resp = requests.put(url, headers=_github_headers(), json=payload, timeout=8)
        resp.raise_for_status()
        return True
    except Exception as e:
        _issue("login_log (escribir)", e)
        return False


def registrar_login(farmer_email):
    """
    Marca la hora de entrada de este farmer/supervisor -- pedido
    explícito de Sabas (agosto 2026). Solo actualiza "ultima_entrada"; el
    "tiempo_uso_min" se calcula recién en registrar_logout (necesita
    saber cuándo entró Y cuándo salió). Se llama justo después de un
    login exitoso.

    Guarda también la hora de entrada en st.session_state (no solo en
    GitHub) -- así registrar_logout puede calcular el tiempo de uso sin
    tener que volver a leer el archivo remoto para buscar "cuándo entró".
    """
    if not _github_configurado():
        return
    ahora = pd.Timestamp.now()
    st.session_state["_login_ts"] = ahora.isoformat()

    df, sha = _github_get_file()
    email = str(farmer_email).strip().lower()
    hora_fmt = ahora.strftime("%Y-%m-%d %H:%M:%S")

    if email in df["farmer"].values:
        df.loc[df["farmer"] == email, "ultima_entrada"] = hora_fmt
    else:
        nueva = pd.DataFrame([{
            "farmer": email, "ultima_entrada": hora_fmt,
            "tiempo_uso_min": None, "ultima_salida": None,
        }])
        df = pd.concat([df, nueva], ignore_index=True)

    _github_put_file(df, sha, f"login: {email} @ {hora_fmt}")


def registrar_logout(farmer_email):
    """
    Marca la hora de salida y calcula el tiempo de uso de esta sesión
    (salida - entrada, en minutos) -- pedido explícito de Sabas (agosto
    2026). Se llama al presionar "Salir".
    """
    if not _github_configurado():
        return
    ahora = pd.Timestamp.now()
    email = str(farmer_email).strip().lower()
    hora_fmt = ahora.strftime("%Y-%m-%d %H:%M:%S")

    tiempo_uso_min = None
    login_ts = st.session_state.get("_login_ts")
    if login_ts:
        try:
            entrada = pd.Timestamp(login_ts)
            tiempo_uso_min = round((ahora - entrada).total_seconds() / 60, 1)
        except Exception:
            pass

    df, sha = _github_get_file()
    if email in df["farmer"].values:
        df.loc[df["farmer"] == email, "ultima_salida"] = hora_fmt
        if tiempo_uso_min is not None:
            df.loc[df["farmer"] == email, "tiempo_uso_min"] = tiempo_uso_min
    else:
        nueva = pd.DataFrame([{
            "farmer": email, "ultima_entrada": None,
            "tiempo_uso_min": tiempo_uso_min, "ultima_salida": hora_fmt,
        }])
        df = pd.concat([df, nueva], ignore_index=True)

    _github_put_file(df, sha, f"logout: {email} @ {hora_fmt}")


def load_login_log():
    """
    Tabla completa de login/logout para la vista del Supervisor -- una
    fila por farmer con su ÚLTIMO valor conocido (no historial). Devuelve
    DataFrame vacío (no None) si el tracking no está configurado o el
    archivo aún no existe, para que la UI pueda mostrar "sin datos" sin
    tener que manejar un caso None aparte.
    """
    if not _github_configurado():
        return _login_log_df_vacio()
    df, _sha = _github_get_file()
    return df


def _leer_estrategia_acq(kind):
    """
    Lee una hoja de estrategia ACQ (formato compartido por ADS nominal
    ACQ, ADS monetario ACQ y MD nominal ACQ: 4 filas de header apiladas
    -- ESTRATEGIA_* / MONTH / WEEK / columna real) y devuelve
    (df, fila_estrategia, fila_header, col_owner, col_brand, n_cols).
    Usado por rendimiento_comercial_ads_for (Cierre de Ads, ambas hojas)
    y rendimiento_comercial_md_for (Cierre de MD, cuadragésima vuelta:
    "el cerrado... lo tomas de la hoja de MD nominal ACQ") -- antes
    duplicado dentro de cada función, ahora compartido a nivel de módulo.

    None si la hoja falta o no tiene al menos las 4 filas de header.
    """
    df = _read(kind, header=None)
    if df.empty or len(df) < 4:
        return None
    fila_estrategia = df.iloc[0]
    fila_header = df.iloc[3]
    n_cols = len(fila_header)
    col_owner = next((i for i in range(n_cols) if str(fila_header.iloc[i]).strip().upper() == "OWNER"), None)
    col_brand = next((i for i in range(n_cols) if str(fila_header.iloc[i]).strip().upper() == "BRAND ID-NAME"), None)
    return df, fila_estrategia, fila_header, col_owner, col_brand, n_cols


@st.cache_data(ttl=86400, show_spinner=False)
def rendimiento_comercial_ads_for(farmer_email):
    """
    Funnel de Rendimiento Comercial · Ads -- pedido explícito de Sabas
    (vigésima quinta vuelta), calculado a partir de datos reales, no
    inventados: Base -> Contactados (Rechazado / Palanca no mencionada /
    Cerrado) -> Cierre, con Cierre como subconjunto REAL de Contactados
    (no un conteo aparte, a diferencia de un diseño anterior descartado
    -- ver la sesión larga de validación con Sabas).

    @st.cache_data(ttl=86400) (pedido explícito de Sabas, trigésima
    primera vuelta: "revisa el tema del caché para que todo cargue con
    la máxima velocidad posible") -- mismo patrón que ya usa el resto de
    esta capa (load_*), aplicado acá por primera vez a una función "_for"
    porque es la única que recorre varias hojas completas con iterrows
    (DETALLE, OPP START, EXPORT ADS RELATION, PRODUCTIVITY, ADS nominal
    ACQ, ADS monetario ACQ) en CADA click de UI dentro de Rendimiento
    Comercial (cambiar de bloque, cambiar de tab, cambiar de Farmer) --
    _read() ya cachea la LECTURA de cada hoja en Parquet, pero no evita
    repetir ese recorrido Python entero cada vez. Con este decorador, dos
    llamadas seguidas con el mismo farmer_email devuelven el resultado ya
    calculado sin tocar ninguna hoja.

    Diferencia real frente a _read(): _read() invalida su cache SOLO
    cuando el mtime del XLSX cambia (se regenera solo al subir un Excel
    nuevo). Este decorador usa un TTL fijo de 24h, igual que el resto de
    load_* de este archivo -- no detecta un Excel nuevo por sí solo. Si
    se sube un Excel nuevo y hace falta ver el funnel actualizado ANTES
    de que pasen 24h, hay que reiniciar la app (o agregar un botón de
    "refrescar datos" que llame a st.cache_data.clear() -- no existe
    ninguno en la app hoy, ni para esta función ni para las demás load_*
    que ya usan el mismo TTL fijo).

    Fuentes:
      - Base: hoja OPP START (reemplaza EXPORT ADS -- es un snapshot fijo
        de "inicio de mes", no del día de hoy, así que las marcas que
        cierran DURANTE el mes siguen apareciendo en la base del período
        en vez de desaparecer del conjunto en cuanto cierran). Columna
        "Bookings Totales Corregidos" == 0 -> entra a la base. > 0 ->
        excluida (ya tenía actividad, no es adquisición nueva real).
      - Contactados / Rechazado: hoja PRODUCTIVITY, columnas "¿Contactado?"
        (SI) y "Tipo Never Ads" ("No activo" -- pedido explícito: "todo lo
        que sea no activo de Never Ads cuenta como rechazado"). Esto NO
        cambió en la cuadragésima vuelta -- Sabas solo pidió cambiar la
        fuente del bloque de Cierre, no la de Contactados.
      - Cierre (NÚMERO): hoja ADS nominal ACQ (antes "ADS COMERCIAL",
        solo renombrada -- pedido explícito, cuadragésima vuelta), máximo
        de "ATT ESTRATEGIA" bajo estrategia ACQUIRE entre las 4 semanas
        del mes.
      - Cierre (DETALLE + VALOR por marca): hoja ADS monetario ACQ
        (pedido explícito, cuadragésima vuelta: "esa hoja checkout ya no
        la revisa... ahora va a estar revisando la de ads nominal ACQ...
        para el total adquirido y del valor adquirido por marca... lo va
        a tomar de ads monetario ACQ" -- reemplaza a CHECKOUT). Columna
        REVENUE (bajo estrategia ACQUIRE) de la semana más reciente del
        mes, en USD, convertida a ARS a 1.500 ARS/USD (pedido explícito:
        "1500 pesos. No 1517" -- misma tasa que fmt_target usa para
        Targets Bookings).
      - Target por marca: hoja EXPORT ADS RELATION, columna
        "Targets Bookings" -- "—" si la marca no aparece ahí.

    Devuelve dict con:
      base / contactado / cierre: listas de {id, nombre, target, estado}
        (cierre trae {id, nombre, valor} en vez de target/estado).
      counts: {base, contactado, no_contactado, sin_gestionar, rechazado,
        palanca_no_mencionada, cerrado} -- ya listos para las barras,
        sin que el caller tenga que recalcular nada.

    Nunca revienta: si alguna hoja falta o está vacía, devuelve el
    esqueleto con listas vacías y counts en 0, igual que el resto de
    funciones de esta capa.
    """
    vacio = {
        "base": [], "contactado": [], "cierre": [],
        "counts": {"base": 0, "contactado": 0, "no_contactado": 0, "sin_gestionar": 0,
                   "rechazado": 0, "palanca_no_mencionada": 0, "cerrado": 0},
    }

    df_opp = _read("opp_start")
    if df_opp.empty:
        return vacio
    c_kam = pick_col(df_opp, "KAM")
    c_brand = pick_col(df_opp, "BRAND", "Brand")
    c_book = pick_col(df_opp, "Bookings Totales Corregidos")
    if not (c_kam and c_brand and c_book):
        return vacio

    df_det = _read("detalle")
    brand_a_key, brand_a_nombre = {}, {}
    if not df_det.empty:
        c_det_brand = pick_col(df_det, "Brand")
        c_det_correo = pick_col(df_det, "Correo", "Email")
        if c_det_brand and c_det_correo:
            for _, r in df_det.iterrows():
                brand_txt, correo = r.get(c_det_brand), r.get(c_det_correo)
                if not brand_txt or correo != farmer_email:
                    continue
                m = re.match(r"^(\d+)\s*-\s*(.+)$", str(brand_txt).strip())
                if m:
                    num = int(m.group(1))
                    brand_a_key[num] = brand_key(num)
                    brand_a_nombre[num] = m.group(2).strip()

    if not brand_a_key:
        return vacio

    # Base: bookings == 0 exacto en OPP START (None tratado igual que 0,
    # sin dato no descalifica) -- pedido explícito: bookings > 0 real
    # SÍ descalifica (ya tenía actividad, no es adquisición nueva).
    brand_bookings_inicio = {}
    for _, r in df_opp.iterrows():
        kam, brand = r.get(c_kam), r.get(c_brand)
        if kam != farmer_email or not brand or str(brand).strip() == "Total":
            continue
        m = re.match(r"^(\d+)", str(brand).strip())
        if m:
            brand_bookings_inicio[int(m.group(1))] = to_num(r.get(c_book), default=None)

    base_nums = set()
    for num in brand_a_key:
        bk = brand_bookings_inicio.get(num)
        if bk is None or bk == 0:
            base_nums.add(num)

    # Target por marca (EXPORT ADS RELATION)
    df_rel = _read("export_ads_relation")
    brand_target = {}
    if not df_rel.empty:
        c_rel_farmer = pick_col(df_rel, "KAM", "OWNER", "FARMER")
        c_rel_brand = pick_col(df_rel, "BRAND ID-NAME", "BRAND")
        c_rel_target = pick_col(df_rel, "Targets Bookings")
        if c_rel_farmer and c_rel_brand and c_rel_target:
            for _, r in df_rel.iterrows():
                farmer, brand = r.get(c_rel_farmer), r.get(c_rel_brand)
                if farmer != farmer_email or not brand or str(brand).strip() == "Total":
                    continue
                m = re.match(r"^(\d+)", str(brand).strip())
                if m:
                    brand_target[int(m.group(1))] = to_num(r.get(c_rel_target), default=None)

    def fmt_target(num):
        t = brand_target.get(num)
        # Target convertido a ARS (pedido explícito de Sabas, vigésima
        # octava vuelta: "convertilos a pesos argentinos poniendolo a
        # 1500 ARS x USD") -- Targets Bookings de EXPORT ADS RELATION
        # viene en USD, igual que el resto de esa hoja.
        return "—" if t is None else f"${t * 1500:,.0f}"

    # Contactados / Rechazado (PRODUCTIVITY)
    df_prod = _read("productivity")
    contactadas_si, tiene_registro, tiene_rechazo = set(), set(), set()
    if not df_prod.empty:
        c_code = pick_col(df_prod, "Code")
        c_prod_farmer = pick_col(df_prod, "Farmer", "KAM")
        c_contactado = pick_col(df_prod, "¿Contactado?", "Contactado")
        c_tipo_never = pick_col(df_prod, "Tipo Never Ads")
        if c_code and c_prod_farmer:
            for _, r in df_prod.iterrows():
                farmer = r.get(c_prod_farmer)
                code = r.get(c_code)
                if farmer != farmer_email or not code:
                    continue
                k = brand_key(code)
                tiene_registro.add(k)
                if c_contactado and str(r.get(c_contactado) or "").strip().upper() == "SI":
                    contactadas_si.add(k)
                if c_tipo_never and str(r.get(c_tipo_never) or "").strip() == "No activo":
                    tiene_rechazo.add(k)

    # Cierre: NÚMERO desde ADS nominal ACQ (antes "ADS COMERCIAL", solo
    # cambió de nombre -- pedido explícito de Sabas, cuadragésima vuelta:
    # "ads comercial ahora se llama ads nominal ACQ") -- MÁXIMO de "ATT
    # ESTRATEGIA" (ACQUIRE) entre las 4 semanas del mes, no la última
    # columna a ciegas (el acumulado semana a semana normalmente ya es
    # creciente, pero tomar el máximo real es más robusto que asumir que
    # la última semana siempre es la más alta). La estructura de esta
    # hoja es distinta a todas las demás: 4 filas de "header" apiladas
    # (ESTRATEGIA_ADS / MONTH / WEEK / columna real), por eso se lee con
    # header=None y se arma el mapeo a mano, en vez de con pick_col()
    # como el resto.
    #
    # El DETALLE de la tabla (cuáles marcas, con nombre y valor) YA NO
    # sale de CHECKOUT (pedido explícito de Sabas, cuadragésima vuelta:
    # "esa hoja checkout ya no la revisa") -- pasa a salir de ADS
    # monetario ACQ, columna REVENUE de la semana más reciente del mes
    # (mismo criterio que ya usamos para leer esa hoja manualmente:
    # última columna REVENUE del bloque de 4 semanas, acumulado MTD). Si
    # el número de ADS nominal ACQ es mayor a la cantidad de marcas con
    # revenue > 0 que ADS monetario ACQ identifica para este Farmer, se
    # completa con filas "Sin dato disponible en Ads monetario ACQ" (
    # mismo criterio de relleno que antes tenía CHECKOUT) en vez de
    # inventar marcas que no existen.
    parsed_nominal = _leer_estrategia_acq("ads_comercial")
    cierre_total_ads_comercial = 0
    if parsed_nominal is not None:
        df_adscom, fila_estrategia, fila_header, col_owner, _, n_cols = parsed_nominal
        cols_att_acquire = [
            i for i in range(n_cols)
            if str(fila_header.iloc[i]).strip() == "ATT ESTRATEGIA"
            and str(fila_estrategia.iloc[i]).strip().upper() == "ACQUIRE"
        ]
        if col_owner is not None and cols_att_acquire:
            for i in range(4, len(df_adscom)):
                fila = df_adscom.iloc[i]
                owner = fila.iloc[col_owner]
                if owner != farmer_email:
                    continue
                valores_semana = [to_num(fila.iloc[c], default=0) for c in cols_att_acquire]
                cierre_total_ads_comercial = int(max(valores_semana)) if valores_semana else 0
                break

    # Detalle de marcas + valor (ADS monetario ACQ) -- para saber CUÁLES
    # marcas y cuánto revenue trajeron, ya no CUÁNTAS en total (ese
    # número ya viene fijo de ADS nominal ACQ arriba). Revenue de la
    # ÚLTIMA columna REVENUE (semana más reciente, acumulado MTD),
    # convertido de USD a ARS a 1.500 ARS/USD (pedido explícito de
    # Sabas, cuadragésima vuelta: "1500 pesos. No 1517" -- misma tasa
    # que ya usa fmt_target más abajo para Targets Bookings, NO la de
    # 1.517 usada en el análisis puntual de un chat anterior).
    TASA_USD_ARS = 1500
    parsed_monetario = _leer_estrategia_acq("ads_monetario_acq")
    cerradas_valor = {}
    if parsed_monetario is not None:
        df_adsmon, fila_estrategia_m, fila_header_m, col_owner_m, col_brand_m, n_cols_m = parsed_monetario
        cols_revenue = [
            i for i in range(n_cols_m)
            if str(fila_header_m.iloc[i]).strip() == "REVENUE"
            and str(fila_estrategia_m.iloc[i]).strip().upper() == "ACQUIRE"
        ]
        if col_owner_m is not None and col_brand_m is not None and cols_revenue:
            col_revenue_reciente = cols_revenue[-1]
            for i in range(4, len(df_adsmon)):
                fila = df_adsmon.iloc[i]
                owner = fila.iloc[col_owner_m]
                if owner != farmer_email:
                    continue
                brand_txt = fila.iloc[col_brand_m]
                if not brand_txt or str(brand_txt).strip() == "Total":
                    continue
                # BUG REAL CORREGIDO antes de entregar: a diferencia de
                # DETALLE (que trae "101312 - Nombre", sin prefijo de
                # país), esta hoja trae "AR101312 - Nombre" -- el número
                # va DESPUÉS de las letras de país, no al inicio del
                # string. El regex sin prefijo dejaba 0 matches (90
                # filas de owner, 0 en cerradas_valor) porque ninguna
                # marca real empieza directamente con un dígito acá.
                m = re.match(r"^[A-Za-z]*(\d+)", str(brand_txt).strip())
                if not m:
                    continue
                revenue_usd = to_num(fila.iloc[col_revenue_reciente], default=0.0)
                if revenue_usd > 0:
                    num = int(m.group(1))
                    cerradas_valor[num] = cerradas_valor.get(num, 0.0) + revenue_usd * TASA_USD_ARS

    base_rows, contactado_rows, cierre_rows = [], [], []
    rechazado_n = pnm_n = cerrado_n = no_contactado_n = sin_gestionar_n = 0

    for num in base_nums:
        key = brand_a_key[num]
        nombre = brand_a_nombre[num]
        if key in contactadas_si:
            estado_base = "Contactado"
        elif key in tiene_registro:
            estado_base = "No Contactado"
            no_contactado_n += 1
        else:
            estado_base = "Sin Gestionar"
            sin_gestionar_n += 1
        base_rows.append({"id": key, "nombre": nombre, "target": fmt_target(num), "estado": estado_base})

        if key not in contactadas_si:
            continue
        if num in cerradas_valor:
            estado_c = "Cerrado"
            cierre_rows.append({"id": key, "nombre": nombre, "valor": f"${cerradas_valor[num]:,.0f}"})
        elif key in tiene_rechazo:
            estado_c = "Rechazado"
            rechazado_n += 1
        else:
            estado_c = "Palanca no mencionada"
            pnm_n += 1
        contactado_rows.append({"id": key, "nombre": nombre, "target": fmt_target(num), "estado": estado_c})

    # Orden descendente por target (pedido explícito de Sabas: "en ambos
    # bloques vas a organizar las listas en orden descendente según
    # Target") -- se ordena por el valor NUMÉRICO crudo (brand_target,
    # en USD, antes del *1500 y del formato "$X" de fmt_target), no por
    # el string ya formateado. Sin target ("—", o sea None) va al final.
    id_a_num = {v: k for k, v in brand_a_key.items()}
    base_rows.sort(key=lambda r: brand_target.get(id_a_num.get(r["id"]), -1) if brand_target.get(id_a_num.get(r["id"])) is not None else -1, reverse=True)
    contactado_rows.sort(key=lambda r: brand_target.get(id_a_num.get(r["id"]), -1) if brand_target.get(id_a_num.get(r["id"])) is not None else -1, reverse=True)

    # El NÚMERO de cerrado es el de ADS nominal ACQ (fijo, ya calculado
    # arriba), no len(cierre_rows) -- mismo criterio que ya existía con
    # ADS COMERCIAL/CHECKOUT, ahora aplicado a las hojas renombradas. Si
    # ADS monetario ACQ identificó MENOS marcas concretas (con revenue >
    # 0, dentro de la base de este Farmer) que ese número, se completa
    # con filas de relleno "Sin dato disponible en Ads monetario ACQ" en
    # vez de mostrar una tabla más corta que el número grande sin
    # ninguna explicación. Si ADS monetario ACQ tiene MÁS marcas que el
    # número de ADS nominal ACQ (fuentes desalineadas), se muestran
    # todas igual -- nunca se ocultan datos reales para forzar que el
    # conteo cuadre.
    cerrado_n = cierre_total_ads_comercial
    faltantes = cerrado_n - len(cierre_rows)
    if faltantes > 0:
        for _ in range(faltantes):
            cierre_rows.append({"id": "—", "nombre": "Sin dato disponible en Ads monetario ACQ", "valor": "—"})

    def _valor_ordenable(r):
        v = r["valor"]
        if v == "—":
            return -1
        return float(v.replace("$", "").replace(",", ""))

    cierre_rows.sort(key=_valor_ordenable, reverse=True)
    contactado_n = rechazado_n + pnm_n + cerrado_n

    return {
        "base": base_rows, "contactado": contactado_rows, "cierre": cierre_rows,
        "counts": {
            "base": len(base_rows), "contactado": contactado_n,
            "no_contactado": no_contactado_n, "sin_gestionar": sin_gestionar_n,
            "rechazado": rechazado_n, "palanca_no_mencionada": pnm_n, "cerrado": cerrado_n,
        },
    }


@st.cache_data(ttl=86400, show_spinner=False)
def rendimiento_comercial_md_for(farmer_email):
    """
    Funnel de Rendimiento Comercial · Markdown -- pedido explícito de
    Sabas (vigésima octava vuelta): mismo esqueleto que
    rendimiento_comercial_ads_for, pero con fuentes propias de MD, sin
    target por marca (pedido explícito: "en las tablas de MD no hay
    target... con la sola pill del status basta") y sin fila de Total
    en Cierre (pedido explícito: "la fila Total solo aplica a Ads").

    @st.cache_data(ttl=86400) -- mismo motivo y mismas limitaciones que
    en rendimiento_comercial_ads_for (ver docstring de esa función):
    evita repetir el recorrido con iterrows sobre MD START y PRODUCTIVITY
    en cada click de UI.

    Fuentes:
      - Base: hoja MD START (snapshot fijo de inicio de mes, mismo
        criterio que OPP START para Ads), columna "MARKDOWN $" == 0 (o
        sin dato) -> entra a la base.
      - Contactados / No Contactado / Sin Gestionar: hoja PRODUCTIVITY,
        columna "¿Contactado?" (SI/NO -- mismo campo que usa
        rendimiento_comercial_ads_for, corresponde 1:1 con "Fase" =
        "Follow-UP finalizado"/"Aliado no contactado"). Sin Gestionar =
        la marca no tiene ninguna fila en PRODUCTIVITY para este Farmer.
      - Rechazado / Palanca no mencionada (dentro de las Contactadas):
        pedido explícito de Sabas (trigésima segunda vuelta) -- exige
        "Markdown" == SI Y "¿Es seguimiento MD?" == NO en la misma fila
        (si es seguimiento, esa fila no cuenta para esta parte, aunque
        la marca siga siendo Contactada). Rechazado = "No aceptó
        ninguno"; cualquier otro valor (incluido vacío) -> Palanca no
        mencionada. Esto NO cambió en la cuadragésima vuelta -- Sabas
        confirmó explícitamente "Productivity solo lo vas a quitar en
        el bloque de cerrado... contactado va a seguir tomando su
        productivity normal".
      - Cerrado (dentro de las Contactadas): YA NO sale de PRODUCTIVITY
        (pedido explícito, cuadragésima vuelta: "el cerrado ya no lo
        tomas de productivity, sino que lo tomas de la hoja de MD
        nominal ACQ") -- una marca Contactada se marca Cerrado si tiene
        "ATT ESTRATEGIA" == 1 (bajo estrategia ACQUIRE) en la columna de
        la semana más reciente del mes en MD nominal ACQ. El NÚMERO
        grande del bloque de Cierre usa el mismo mecanismo que ya existe
        para Ads nominal ACQ: máximo de "ATT ESTRATEGIA" entre las 4
        semanas del mes, no len(cierre_rows) a ciegas.
      - Sin target: EXPORT ADS RELATION es específico de Ads, no hay
        equivalente de MD -- se omite el campo "target" de las filas
        (a diferencia de Ads, que sí lo trae).
      - Sin valor en pesos: MD no tiene hoja monetaria equivalente a ADS
        monetario ACQ (confirmado por Sabas, cuadragésima vuelta) -- las
        filas de cierre traen solo {id, nombre}, nunca "valor".

    Devuelve el mismo esqueleto que Ads, sin "target" en las filas y sin
    valor en pesos en cierre (solo {id, nombre} ahí, ya que no hay plata
    por marca -- "con la sola pill del status basta" se resuelve en el
    caller usando el mismo estado "Cerrado" que ya viene en
    contactado_rows, no hace falta una tabla de cierre aparte con
    columna de valor).
    """
    vacio = {
        "base": [], "contactado": [], "cierre": [],
        "counts": {"base": 0, "contactado": 0, "no_contactado": 0, "sin_gestionar": 0,
                   "rechazado": 0, "palanca_no_mencionada": 0, "cerrado": 0},
    }

    df_mdstart = _read("md_start")
    if df_mdstart.empty:
        return vacio
    c_brand = pick_col(df_mdstart, "BRAND ID", "BRAND")
    c_md = pick_col(df_mdstart, "MARKDOWN $")
    if not (c_brand and c_md):
        return vacio

    df_det = _read("detalle")
    brand_a_key, brand_a_nombre = {}, {}
    if not df_det.empty:
        c_det_brand = pick_col(df_det, "Brand")
        c_det_correo = pick_col(df_det, "Correo", "Email")
        if c_det_brand and c_det_correo:
            for _, r in df_det.iterrows():
                brand_txt, correo = r.get(c_det_brand), r.get(c_det_correo)
                if not brand_txt or correo != farmer_email:
                    continue
                m = re.match(r"^(\d+)\s*-\s*(.+)$", str(brand_txt).strip())
                if m:
                    num = int(m.group(1))
                    brand_a_key[num] = brand_key(num)
                    brand_a_nombre[num] = m.group(2).strip()

    if not brand_a_key:
        return vacio

    # Base: MARKDOWN $ == 0 exacto en MD START (None tratado igual que 0)
    # -- una marca puede tener varias filas (varios stores), se suma por
    # marca antes de comparar, mismo criterio que _load_md ya usa para
    # la hoja MD de hoy.
    brand_markdown_inicio = {}
    for _, r in df_mdstart.iterrows():
        brand = r.get(c_brand)
        if not brand:
            continue
        m = re.match(r"^(\d+)", str(brand).strip())
        if m:
            num = int(m.group(1))
            brand_markdown_inicio[num] = brand_markdown_inicio.get(num, 0.0) + to_num(r.get(c_md), default=0.0)

    base_nums = {num for num in brand_a_key if brand_markdown_inicio.get(num, 0) == 0}

    # Contactados / No Contactado / Sin Gestionar -- pedido explícito de
    # Sabas (trigésima segunda vuelta, corrección sobre el criterio
    # anterior): esto se decide por "¿Contactado?" (Fase = "Follow-UP
    # finalizado" -> SI / "Aliado no contactado" -> NO, correspondencia
    # 1:1 confirmada contra el workbook real), el MISMO campo que ya usa
    # rendimiento_comercial_ads_for -- NO por si se habló de Markdown en
    # particular. Antes esta función usaba "Markdown" == SI para decidir
    # Contactado en la BASE, lo cual mezclaba dos preguntas distintas
    # ("¿hubo follow-up con la marca?" vs. "¿ese follow-up tocó el tema
    # Markdown?") y podía dejar como "No Contactado"/"Sin Gestionar" a
    # una marca que sí tuvo follow-up pero donde Markdown no vino al
    # caso.
    #
    # Cerrado / Rechazado / Palanca no mencionada -- eso sí exige AMBAS
    # condiciones dentro de las Contactadas (pedido explícito: "Markdown
    # debe estar en sí, seguimiento debe estar en no... si es seguimiento
    # no cuenta, queda fuera"): "Markdown" == SI (de verdad se habló de
    # Markdown en esa gestión) Y "¿Es seguimiento MD?" == NO (es la
    # gestión original, no un follow-up de una campaña ya en curso). Una
    # marca Contactada que no cumple esta segunda condición (Markdown=NO,
    # o es un seguimiento) sigue contando como "Contactado" en la base,
    # pero no entra a evaluarse aquí -- ni suma a Rechazado, ni a
    # Palanca no mencionada. Esto NO cambió en la cuadragésima vuelta --
    # ver docstring: Sabas confirmó explícitamente que Productivity sigue
    # siendo la fuente de Contactado/Rechazado/Palanca no mencionada, y
    # que el cambio de fuente es EXCLUSIVO del estado Cerrado.
    df_prod = _read("productivity")
    contactadas_si, tiene_registro, tiene_rechazo = set(), set(), set()
    if not df_prod.empty:
        c_code = pick_col(df_prod, "Code")
        c_prod_farmer = pick_col(df_prod, "Farmer", "KAM")
        c_contactado = pick_col(df_prod, "¿Contactado?", "Contactado")
        c_md_val = pick_col(df_prod, "Markdown")
        c_seguimiento_md = pick_col(df_prod, "¿Es seguimiento MD?")
        c_aceptado = pick_col(df_prod, "¿Se aceptó lo ofrecido?")
        if c_code and c_prod_farmer:
            for _, r in df_prod.iterrows():
                farmer = r.get(c_prod_farmer)
                code = r.get(c_code)
                if farmer != farmer_email or not code:
                    continue
                k = brand_key(code)
                tiene_registro.add(k)
                contactado = c_contactado and str(r.get(c_contactado) or "").strip().upper() == "SI"
                if contactado:
                    contactadas_si.add(k)
                    md_si = c_md_val and str(r.get(c_md_val) or "").strip().upper() == "SI"
                    no_es_seguimiento = (
                        not c_seguimiento_md
                        or str(r.get(c_seguimiento_md) or "").strip().upper() == "NO"
                    )
                    if md_si and no_es_seguimiento:
                        aceptado = str(r.get(c_aceptado) or "").strip().lower() if c_aceptado else ""
                        if aceptado == "no aceptó ninguno":
                            tiene_rechazo.add(k)

    # Cerrado -- YA NO sale de PRODUCTIVITY (pedido explícito de Sabas,
    # cuadragésima vuelta, ver docstring): una marca Contactada se marca
    # Cerrado si tiene "ATT ESTRATEGIA" == 1 (bajo estrategia ACQUIRE) en
    # la columna de la semana MÁS RECIENTE del mes en MD nominal ACQ --
    # mismo criterio de "última semana" que ya usamos al leer esta hoja
    # manualmente en el chat (a diferencia del NÚMERO total de Ads, que
    # usa el MÁXIMO entre semanas -- acá alcanza con la última porque
    # solo se necesita el estado on/off más reciente por marca, no un
    # total agregado).
    cerrado_md_nominal = set()
    parsed_md_nominal = _leer_estrategia_acq("md_nominal_acq")
    if parsed_md_nominal is not None:
        df_mdnom, fila_estrategia_n, fila_header_n, col_owner_n, col_brand_n, n_cols_n = parsed_md_nominal
        cols_att_acquire_n = [
            i for i in range(n_cols_n)
            if str(fila_header_n.iloc[i]).strip() == "ATT ESTRATEGIA"
            and str(fila_estrategia_n.iloc[i]).strip().upper() == "ACQUIRE"
        ]
        if col_owner_n is not None and col_brand_n is not None and cols_att_acquire_n:
            col_reciente_n = cols_att_acquire_n[-1]
            for i in range(4, len(df_mdnom)):
                fila = df_mdnom.iloc[i]
                owner = fila.iloc[col_owner_n]
                if owner != farmer_email:
                    continue
                brand_txt = fila.iloc[col_brand_n]
                if not brand_txt or str(brand_txt).strip() == "Total":
                    continue
                # Mismo bug/fix que en ADS monetario ACQ arriba: el
                # texto trae el prefijo de país antes del número
                # ("AR101312 - Nombre"), el regex tiene que tolerarlo.
                m = re.match(r"^[A-Za-z]*(\d+)", str(brand_txt).strip())
                if m and to_num(fila.iloc[col_reciente_n], default=0) == 1:
                    cerrado_md_nominal.add(brand_key(int(m.group(1))))

    base_rows, contactado_rows = [], []
    rechazado_n = pnm_n = cerrado_n = no_contactado_n = sin_gestionar_n = 0

    for num in base_nums:
        key = brand_a_key[num]
        nombre = brand_a_nombre[num]
        if key in contactadas_si:
            estado_base = "Contactado"
        elif key in tiene_registro:
            estado_base = "No Contactado"
            no_contactado_n += 1
        else:
            estado_base = "Sin Gestionar"
            sin_gestionar_n += 1
        base_rows.append({"id": key, "nombre": nombre, "estado": estado_base})

        if key not in contactadas_si:
            continue
        if key in cerrado_md_nominal:
            estado_c = "Cerrado"
            cerrado_n += 1
        elif key in tiene_rechazo:
            estado_c = "Rechazado"
            rechazado_n += 1
        else:
            estado_c = "Palanca no mencionada"
            pnm_n += 1
        contactado_rows.append({"id": key, "nombre": nombre, "estado": estado_c})

    # Sin target en MD -- no hay orden por target posible ("con la sola
    # pill del status basta", pedido explícito). Se deja el orden en el
    # que se recorrió base_nums (sin garantía de orden específico, ya
    # que no hay un criterio numérico para ordenar).
    contactado_n = rechazado_n + pnm_n + cerrado_n
    cierre_rows = [r for r in contactado_rows if r["estado"] == "Cerrado"]

    return {
        "base": base_rows, "contactado": contactado_rows, "cierre": cierre_rows,
        "counts": {
            "base": len(base_rows), "contactado": contactado_n,
            "no_contactado": no_contactado_n, "sin_gestionar": sin_gestionar_n,
            "rechazado": rechazado_n, "palanca_no_mencionada": pnm_n, "cerrado": cerrado_n,
        },
    }


@st.cache_data(ttl=86400, show_spinner=False)
def smart_priorities_for(farmer_email):
    """
    Orden Smart Priorities de la cartera de un Farmer -- pedido explícito
    de Sabas (trigésima tercera vuelta): "quiero que esa primera ficha
    lleve el orden exacto de Smart Priorities... brand ID, brand name y
    el puntaje de prioridad... organizado en orden descendente según el
    puntaje".

    IMPORTANTE (aclarado con Sabas en la misma vuelta, tras investigar):
    el cálculo COMPLETO de Smart Priorities (pesos editables por Churn/
    Adq.Ads/Adq.MD/Upsell/Reajuste MD/Operativa/Promo x vencer/PDF Menu,
    panel de parámetros, umbrales P1-P4) vive en un Excel aparte
    (PORTAFOLIO_SEPT_SR.xlsx y sus proxies por Farmer), NO en este
    Wingman -- reconstruir esa fórmula acá sería inventar un cálculo
    paralelo que podría desalinearse del original con cada cambio de
    pesos. Por pedido explícito de Sabas, esta función usa el puntaje YA
    CALCULADO que SÍ llega al Wingman: la hoja PRIORITY DATA trae, para
    cada marca, una fila con Metric="Total" cuya columna "Prioridad BD"
    es ese mismo puntaje consolidado (confirmado: mismo campo que ya usa
    load_coinversion_md() para Coinversión MD/STATUS Brand, ambos viven
    solo en esa fila Total de cada marca). No hay panel de pesos editable
    acá -- si los pesos cambian en el Excel fuente, el número que se lee
    acá cambia solo en el próximo corte de datos, sin que Wingman toque
    la fórmula.

    farmer_email: cartera de un solo Farmer (a diferencia de otras
    funciones "_for" de este archivo que aceptan lista -- pedido
    explícito de Sabas: "elegir Farmer primero, como ya funciona en
    Rendimiento Comercial", un ranking a la vez, no el equipo mezclado).

    Universo de marcas: DETALLE (mismo criterio que el resto de
    Rendimiento Comercial/Ficha de Marca) -- correo del Farmer. El
    puntaje se cruza por "key" (AR+numero) contra la fila Total de
    PRIORITY DATA para cada una de esas marcas. Una marca de la cartera
    sin fila Total en PRIORITY DATA (corte de datos incompleto para esa
    marca) se omite del ranking -- no se inventa un puntaje 0 que la
    mostraría empatada al final con marcas que sí tienen 0 real.

    Retorna una lista de dicts {"id", "nombre", "puntaje", "ads", "md",
    "churn", "ultimo_contacto"}, ya ordenada puntaje descendente (pedido
    explícito: "organizado en orden descendente según el puntaje de
    prioridad").

    "ultimo_contacto" (pedido explícito de Sabas, trigésima sexta vuelta:
    "la última columna debe ser último contacto con la fecha... en
    formato fecha") -- ya viene como texto "DD/MM/AAAA" (ver
    fmt_fecha_ddmmaaaa y ultimo_contacto_for), "—" si la marca no tiene
    ninguna fecha registrada en Priority Data.

    "ads" / "md" / "churn" -- pedido explícito de Sabas (trigésima
    cuarta vuelta): "vamos a añadir dos columnas más... Ads... Markdown...
    Churn... ya nosotros tenemos ciertos criterios para determinar cuándo
    una marca es adquisición y cuándo una marca es upselling".

    "ads" (Adquisición / Upselling / Seguimiento) -- MISMO criterio EXACTO
    que ya usa _camino_mas_corto() para "Adquisición Ads"/"Upselling Ads"
    (Rendimiento País/Farmer), a nivel de marca individual, leído de
    load_export_ads_relation():
      - Adquisición: Targets Bookings > 0 Y las 4 columnas de Bookings
        (Totales, Totales Corregidos, Reales sin gratis, Reales
        Corregidos sin gratis) están en 0 -- la marca nunca tuvo Ads.
      - Upselling: Bookings Reales Corregidos > 0 Y < Targets Bookings --
        ya tiene Ads pero no llega al target.
      - Seguimiento: cualquier otro caso (ya cumplió/superó el target, o
        sin fila en EXPORT ADS RELATION para esta marca -- sin dato no
        es lo mismo que "sin Ads", así que no se asume Adquisición).

    "md" (Adquisición / Reajuste / Seguimiento -- pedido explícito de
    Sabas, corrigiendo en la misma vuelta: "para Markdown es adquisición,
    reajuste y seguimiento", NO "upselling") -- leído de load_md()
    (GMV TOTAL $ y MARKDOWN $ ya agregados por marca, sumando todas sus
    tiendas):
      - Adquisición: MARKDOWN $ == 0 -- la marca nunca tuvo Markdown.
      - Reajuste: MARKDOWN $ > 0 Y penetración (MARKDOWN $ / GMV TOTAL $)
        < 10% -- mismo umbral de penetración que Smart Priorities usa
        para "Reajuste MD" en el Excel fuente (ver docstring de la
        función, "Pesos por defecto... Reajuste MD 10" en la
        investigación de Anthropic sobre ese workbook), reconstruido acá
        porque ese cálculo no vive en ningún otro lugar de este Wingman.
      - Seguimiento: markdown activo con penetración >= 10%, o sin fila
        en MD para esta marca (0 GMV con 0 markdown cuenta como
        Adquisición vía la rama de arriba, no cae acá).

    "churn" (PW1 / PW2 / PW3 / Churn / Tienda activa) -- MISMO criterio
    EXACTO que ya usa portfolio_for() para "churn_status": churn_map()
    (hoja CHURN, estado más reciente por marca vía mayor WEEK). Una marca
    sin riesgo activo (no aparece en churn_map()) muestra "Tienda activa"
    (pedido explícito), igual que portfolio_for() usa "Disponible" como
    default -- mismo estado, nombre distinto porque acá se está
    describiendo la marca en el contexto de esta tabla, no de Brand
    Coverage.
    """
    df_det = _read("detalle")
    if df_det.empty:
        return []
    c_det_brand = pick_col(df_det, "Brand")
    c_det_correo = pick_col(df_det, "Correo", "Email")
    if not (c_det_brand and c_det_correo):
        return []

    brand_a_key, brand_a_nombre = {}, {}
    for _, r in df_det.iterrows():
        brand_txt, correo = r.get(c_det_brand), r.get(c_det_correo)
        if not brand_txt or correo != farmer_email:
            continue
        m = re.match(r"^(\S+)\s*-\s*(.+)$", str(brand_txt).strip())
        if not m:
            continue
        key = brand_key(m.group(1))
        if not key:
            continue
        brand_a_key[key] = key
        brand_a_nombre[key] = m.group(2).strip()

    if not brand_a_key:
        return []

    # Fila Total de PRIORITY DATA -- mismo patrón que load_coinversion_md()
    # (ver docstring arriba): se lee del crudo, no de load_priority(), que
    # descarta esta fila a propósito para el listado de métricas
    # individuales.
    df_prio = _read("priority")
    if df_prio.empty:
        return []
    c_id = pick_col(df_prio, "Brand", "BID", "brand id")
    c_met = pick_col(df_prio, "Metric")
    c_val = pick_col(df_prio, "Prioridad BD", "prioridad")
    if not (c_id and c_met and c_val):
        return []

    df_prio = _drop_junk(df_prio, c_id)
    total_rows = df_prio[df_prio[c_met].astype(str).str.strip().str.lower() == "total"]

    puntaje_por_key = {}
    for _, r in total_rows.iterrows():
        key = brand_key(r.get(c_id))
        if key:
            puntaje_por_key[key] = to_num(r.get(c_val), default=0.0)

    filas = []
    for key in brand_a_key:
        if key not in puntaje_por_key:
            continue
        filas.append({"id": key, "nombre": brand_a_nombre[key], "puntaje": puntaje_por_key[key]})

    # ── Ads (Adquisición / Upselling / Seguimiento) -- ver docstring ──
    df_ear = load_export_ads_relation()
    ads_estado = {}
    if not df_ear.empty:
        farmer_norm = str(farmer_email).strip().lower()
        d = df_ear[df_ear["farmer"] == farmer_norm]
        for _, r in d.iterrows():
            key = brand_key(r.get("brand"))
            if not key:
                continue
            tgt = r.get("target_bookings", 0.0)
            bt = r.get("bookings_totales", 0.0)
            btc = r.get("bookings_totales_corr", 0.0)
            br = r.get("bookings_reales", 0.0)
            brc = r.get("bookings_reales_corr", 0.0)
            if tgt > 0 and bt == 0 and btc == 0 and br == 0 and brc == 0:
                ads_estado[key] = "Adquisición"
            elif brc > 0 and brc < tgt:
                ads_estado[key] = "Upselling"
            else:
                ads_estado[key] = "Seguimiento"

    # ── Markdown (Adquisición / Reajuste / Seguimiento) -- ver docstring ──
    df_md = load_md()
    md_estado = {}
    if not df_md.empty:
        for _, r in df_md.iterrows():
            key = r.get("key")
            if not key:
                continue
            gmv = r.get("gmv", 0.0)
            mkd = r.get("markdown", 0.0)
            if mkd == 0:
                md_estado[key] = "Adquisición"
            elif gmv > 0 and (mkd / gmv) < 0.10:
                md_estado[key] = "Reajuste"
            else:
                md_estado[key] = "Seguimiento"

    # ── Churn (PW1 / PW2 / PW3 / Churn / Tienda activa) -- ver docstring ──
    cmap = churn_map()

    for f in filas:
        f["ads"] = ads_estado.get(f["id"], "—")
        f["md"] = md_estado.get(f["id"], "—")
        f["churn"] = cmap.get(f["id"], "Tienda activa")
        # "ultimo_contacto" (pedido explícito de Sabas, trigésima sexta
        # vuelta: "la última columna debe ser último contacto con la
        # fecha... en formato fecha... día/mes/año") -- ya formateado
        # con fmt_fecha_ddmmaaaa (no fmt_fecha_es, ese es para la card de
        # cabecera con el mes en texto) para que la UI lo muestre tal
        # cual, sin repetir el parseo del serial de Excel en dos lugares.
        f["ultimo_contacto"] = fmt_fecha_ddmmaaaa(ultimo_contacto_for(f["id"]))

    filas.sort(key=lambda f: -f["puntaje"])
    return filas

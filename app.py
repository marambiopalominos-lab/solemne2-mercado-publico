
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

URL = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={TICKET}&cantidad=20"

# ── Carga de datos con caché y manejo de errores ─────────────────────────────
@st.cache_data(ttl=3600)
def cargar_datos():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("Listado"):
            return None, "La API no devolvió datos."
        return data["Listado"], None
    except Exception as e:
        return None, str(e)

with st.spinner("Cargando datos desde Mercado Público..."):
    listado, error = cargar_datos()

if error or not listado:
    st.warning("⚠️ No se pudo conectar con la API en este momento. Intenta recargar la página.")
    st.stop()

# ── Procesamiento de datos ────────────────────────────────────────────────────
df = pd.DataFrame(listado).drop_duplicates(subset=["CodigoExterno"])
df["Nombre"] = df["Nombre"].astype(str)
estados = {1:"Borrador", 2:"Publicada", 3:"Cerrada", 4:"Desierta",
           5:"Adjudicada", 6:"En proceso", 7:"Revocada", 8:"Suspendida"}
df["Estado"] = df["CodigoEstado"].map(estados)
df["FechaCierre"] = pd.to_datetime(df["FechaCierre"], format="mixed")

# ── Sidebar con filtros y métricas ────────────────────────────────────────────
with st.sidebar:
    st.subheader("🔍 Filtrar licitaciones")
    busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: suministro, servicio, combustible...")

    estados_disponibles = ["Todos"] + list(df["Estado"].dropna().unique())
    filtro_estado = st.selectbox("Filtrar por estado:", estados_disponibles)

    st.subheader("📅 Filtrar por Fecha de Cierre")
    fecha_minima = df["FechaCierre"].min().date()
    fecha_maxima = df["FechaCierre"].max().date()
    fecha_inicio = st.date_input("Fecha de Inicio", value=fecha_minima, min_value=fecha_minima, max_value=fecha_maxima)
    fecha_fin    = st.date_input("Fecha de Fin",    value=fecha_maxima, min_value=fecha_minima, max_value=fecha_maxima)

    st.subheader("📊 Métricas Clave")
    st.metric("Total Licitaciones", len(df))
    st.metric("Adjudicadas",        len(df[df["Estado"] == "Adjudicada"]))
    st.metric("En Proceso",         len(df[df["Estado"] == "En proceso"]))

# ── Aplicar filtros ───────────────────────────────────────────────────────────
df_filtrado = df.copy()

if busqueda:
    df_filtrado = df_filtrado[df_filtrado["Nombre"].str.contains(busqueda, case=False, na=False)]
    if len(df_filtrado) == 0:
        st.warning(f"⚠️ No se encontraron licitaciones para: **{busqueda}**")
        st.stop()

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]

df_filtrado = df_filtrado[
    (df_filtrado["FechaCierre"].dt.date >= fecha_inicio) &
    (df_filtrado["FechaCierre"].dt.date <= fecha_fin)
]

if len(df_filtrado) == 0:
    st.warning("⚠️ No hay licitaciones que coincidan con los filtros aplicados.")
    st.stop()

# ── Sección de Análisis dinámico ──────────────────────────────────────────────
st.divider()
st.subheader("💡 Análisis de los Datos")

total          = len(df_filtrado)
estado_frecuente = df_filtrado["Estado"].value_counts().idxmax()
pct_frecuente    = df_filtrado["Estado"].value_counts(normalize=True).max() * 100
n_adj          = len(df_filtrado[df_filtrado["Estado"] == "Adjudicada"])
n_proceso      = len(df_filtrado[df_filtrado["Estado"] == "En proceso"])
pct_adj        = n_adj    / total * 100
pct_proc       = n_proceso / total * 100
hoy            = date.today()
proximos_7     = df_filtrado[
    (df_filtrado["FechaCierre"].dt.date >= hoy) &
    (df_filtrado["FechaCierre"].dt.date <= hoy + timedelta(days=7))
]
n_proximos     = len(proximos_7)
prox_cierre    = df_filtrado[df_filtrado["FechaCierre"].dt.date >= hoy]["FechaCierre"].min()
prox_cierre_str = prox_cierre.strftime("%d/%m/%Y") if pd.notna(prox_cierre) else "N/A"

# Métricas con porcentaje
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Total analizado",    total)
col_b.metric("Adjudicadas",        f"{n_adj} ({pct_adj:.1f}%)")
col_c.metric("En Proceso",         f"{n_proceso} ({pct_proc:.1f}%)")
col_d.metric("Cierran en 7 días",  n_proximos)

# Interpretación automática en texto
st.info(
    f"📌 **Hallazgos principales:** De las **{total} licitaciones** analizadas, "
    f"el estado más frecuente es **{estado_frecuente}** con el **{pct_frecuente:.1f}%** del total. "
    f"Solo el **{pct_adj:.1f}%** ({n_adj}) han sido adjudicadas, mientras que el "
    f"**{pct_proc:.1f}%** ({n_proceso}) aún se encuentran en proceso de evaluación. "
    f"Existen **{n_proximos} licitaciones** que cierran en los próximos 7 días, "
    f"siendo la más próxima el **{prox_cierre_str}**. "
    f"Esto refleja la alta actividad del mercado público chileno y la importancia de "
    f"monitorear constantemente las fechas de cierre para no perder oportunidades de postulación."
)

# ── Tabla de resultados ───────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Resultados")
st.dataframe(df_filtrado[["CodigoExterno", "Nombre", "Estado", "FechaCierre"]], use_container_width=True)

csv = df_filtrado.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Descargar datos filtrados en CSV",
    data=csv,
    file_name="licitaciones_filtradas.csv",
    mime="text/csv",
)

# ── Gráficos ──────────────────────────────────────────────────────────────────
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Cantidad de Licitaciones por Estado")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.countplot(data=df_filtrado, x="Estado", ax=ax1, palette="viridis",
                  order=df_filtrado["Estado"].value_counts().index)
    ax1.set_title("Licitaciones por Estado")
    ax1.set_xlabel("Estado")
    ax1.set_ylabel("Cantidad")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig1)

with col2:
    st.subheader("🥧 Distribución Porcentual por Estado")
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    df_filtrado["Estado"].value_counts().plot(
        kind="pie", ax=ax2, autopct="%1.1f%%", startangle=90, cmap="viridis"
    )
    ax2.set_title("Distribución de Licitaciones por Estado")
    ax2.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig2)

st.divider()

st.subheader("🗓️ Licitaciones por Fecha de Cierre")
licitaciones_por_fecha = df_filtrado["FechaCierre"].dt.date.value_counts().sort_index()
fig3, ax3 = plt.subplots(figsize=(12, 6))
sns.barplot(x=licitaciones_por_fecha.index, y=licitaciones_por_fecha.values, ax=ax3, palette="magma")
ax3.set_title("Cantidad de Licitaciones por Fecha de Cierre")
ax3.set_xlabel("Fecha de Cierre")
ax3.set_ylabel("Número de Licitaciones")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
st.pyplot(fig3)

# ── Pie de página ─────────────────────────────────────────────────────────────
st.divider()
st.caption(f"📅 Datos actualizados al {date.today().strftime('%d/%m/%Y')} · Fuente: API Mercado Público Chile")

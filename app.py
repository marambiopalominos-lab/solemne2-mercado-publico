
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

# ── Paleta de colores consistente ──────────────────────────────────────────────
COLORES = {
    "Adjudicada":  "#2ecc71",
    "Publicada":   "#3498db",
    "En proceso":  "#f39c12",
    "Suspendida":  "#e74c3c",
    "Cerrada":     "#9b59b6",
    "Desierta":    "#95a5a6",
    "Revocada":    "#e67e22",
    "Borrador":    "#1abc9c",
}

# ── Buscador ───────────────────────────────────────────────────────────────────
st.subheader("🔍 Buscar licitaciones por rubro")
busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: suministro, servicio, combustible...")

URL = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={TICKET}"

with st.spinner("Cargando datos..."):
    response = requests.get(URL)
    data = response.json()

if not data.get("Listado"):
    st.error("Error al cargar datos")
    st.stop()

df = pd.DataFrame(data["Listado"]).drop_duplicates(subset=["CodigoExterno"])
estados = {1:"Borrador",2:"Publicada",3:"Cerrada",4:"Desierta",
           5:"Adjudicada",6:"En proceso",7:"Revocada",8:"Suspendida"}
df["Estado"] = df["CodigoEstado"].map(estados)
df["FechaCierre"] = pd.to_datetime(df["FechaCierre"])

if busqueda:
    df = df[df["Nombre"].str.contains(busqueda, case=False, na=False)]
    if len(df) == 0:
        st.warning(f"⚠️ No se encontraron licitaciones para: **{busqueda}**")
        st.stop()

# ── Métricas ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Total Licitaciones", len(df))
col2.metric("Adjudicadas", len(df[df["Estado"]=="Adjudicada"]))
col3.metric("En Proceso", len(df[df["Estado"]=="En proceso"]))

st.divider()

# ── Tabla filtrada ─────────────────────────────────────────────────────────────
st.subheader("📋 Resultados")
estados_disponibles = ["Todos"] + list(df["Estado"].dropna().unique())
filtro = st.selectbox("Filtrar por estado:", estados_disponibles)
df_filtrado = df[df["Estado"] == filtro] if filtro != "Todos" else df
st.dataframe(df_filtrado[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

st.divider()

# ── Helper: estilo base para todos los gráficos ────────────────────────────────
def estilo_base(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dddddd")
    ax.spines["bottom"].set_color("#dddddd")
    ax.tick_params(colors="#555555", labelsize=10)
    ax.set_facecolor("#fafafa")

# ── Gráfico 1: Barras mejorado ─────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Licitaciones por Estado")
    conteo = df["Estado"].value_counts()
    colores_barras = [COLORES.get(e, "#cccccc") for e in conteo.index]

    fig1, ax1 = plt.subplots(figsize=(6, 4))
    fig1.patch.set_facecolor("#fafafa")
    bars = ax1.bar(conteo.index, conteo.values, color=colores_barras,
                   edgecolor="white", linewidth=1.2, zorder=3)

    # Etiquetas de valor encima de cada barra
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.08,
                 str(int(h)), ha="center", va="bottom",
                 fontsize=11, fontweight="bold", color="#333333")

    ax1.set_xlabel("Estado", fontsize=11, color="#555555", labelpad=8)
    ax1.set_ylabel("Cantidad", fontsize=11, color="#555555", labelpad=8)
    ax1.set_ylim(0, conteo.max() * 1.25)
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    estilo_base(ax1)
    plt.tight_layout()
    st.pyplot(fig1)

# ── Gráfico 2: Torta mejorada ──────────────────────────────────────────────────
with col2:
    st.subheader("🥧 Distribución por Estado")
    conteo_pie = df["Estado"].value_counts()
    colores_pie = [COLORES.get(e, "#cccccc") for e in conteo_pie.index]
    explode = [0.04] * len(conteo_pie)

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    fig2.patch.set_facecolor("#fafafa")
    wedges, texts, autotexts = ax2.pie(
        conteo_pie.values,
        labels=None,
        autopct="%1.1f%%",
        colors=colores_pie,
        explode=explode,
        startangle=140,
        pctdistance=0.78,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight("bold")
        at.set_color("white")

    # Leyenda externa limpia
    leyenda = [mpatches.Patch(color=COLORES.get(e, "#cccccc"), label=f"{e} ({v})")
               for e, v in zip(conteo_pie.index, conteo_pie.values)]
    ax2.legend(handles=leyenda, loc="lower center", bbox_to_anchor=(0.5, -0.22),
               ncol=2, fontsize=9, frameon=False)
    ax2.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig2)

# ── Gráfico 3: Línea de tiempo de fechas de cierre ────────────────────────────
st.divider()
st.subheader("📅 Línea de tiempo — Fechas de cierre")

df_fechas = df.dropna(subset=["FechaCierre"]).sort_values("FechaCierre")

if not df_fechas.empty:
    fig3, ax3 = plt.subplots(figsize=(12, 3.5))
    fig3.patch.set_facecolor("#fafafa")
    ax3.set_facecolor("#fafafa")

    # Línea base
    fecha_min = df_fechas["FechaCierre"].min()
    fecha_max = df_fechas["FechaCierre"].max()
    ax3.hlines(0, fecha_min, fecha_max, colors="#cccccc", linewidth=1.5, zorder=1)

    # Puntos alternados arriba/abajo para evitar superposición
    niveles = []
    for i in range(len(df_fechas)):
        niveles.append(0.6 if i % 2 == 0 else -0.6)

    for i, (_, row) in enumerate(df_fechas.iterrows()):
        color = COLORES.get(row["Estado"], "#aaaaaa")
        nivel = niveles[i]
        ax3.vlines(row["FechaCierre"], 0, nivel, colors=color, linewidth=1.2, alpha=0.7)
        ax3.plot(row["FechaCierre"], nivel, "o", color=color, markersize=9, zorder=3)
        nombre_corto = row["Nombre"][:28] + "…" if len(row["Nombre"]) > 28 else row["Nombre"]
        va = "bottom" if nivel > 0 else "top"
        offset = 0.06 if nivel > 0 else -0.06
        ax3.text(row["FechaCierre"], nivel + offset, nombre_corto,
                 ha="center", va=va, fontsize=7.5, color="#333333", rotation=0)

    # Leyenda de estados presentes
    estados_presentes = df_fechas["Estado"].unique()
    leyenda3 = [mpatches.Patch(color=COLORES.get(e, "#aaaaaa"), label=e) for e in estados_presentes]
    ax3.legend(handles=leyenda3, loc="upper right", fontsize=9, frameon=False)

    ax3.set_yticks([])
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.spines["left"].set_visible(False)
    ax3.spines["bottom"].set_color("#dddddd")
    ax3.tick_params(axis="x", colors="#555555", labelsize=9)
    plt.tight_layout()
    st.pyplot(fig3)
else:
    st.info("No hay datos de fechas de cierre disponibles.")

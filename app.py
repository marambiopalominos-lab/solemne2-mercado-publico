
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # Importar seaborn

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

URL = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={TICKET}&cantidad=20"

with st.spinner("Cargando datos..."):
    response = requests.get(URL)
    data = response.json()

if not data.get("Listado"):
    st.error("Error al cargar datos")
    st.stop()

df = pd.DataFrame(data["Listado"]).drop_duplicates(subset=["CodigoExterno"])
df["Nombre"] = df["Nombre"].astype(str) # Aseguramos que la columna 'Nombre' sea tipo string
estados = {1:"Borrador",2:"Publicada",3:"Cerrada",4:"Desierta",
           5:"Adjudicada",6:"En proceso",7:"Revocada",8:"Suspendida"}
df["Estado"] = df["CodigoEstado"].map(estados)
df["FechaCierre"] = pd.to_datetime(df["FechaCierre"], format="mixed")

# Sidebar para filtros y métricas
with st.sidebar:
    st.subheader("🔍 Filtrar licitaciones")
    busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: suministro, servicio, combustible...")

    estados_disponibles = ["Todos"] + list(df["Estado"].dropna().unique())
    filtro_estado = st.selectbox("Filtrar por estado:", estados_disponibles)

    st.subheader("📅 Filtrar por Fecha de Cierre")
    fecha_minima = df['FechaCierre'].min().date()
    fecha_maxima = df['FechaCierre'].max().date()

    fecha_inicio = st.date_input("Fecha de Inicio", value=fecha_minima, min_value=fecha_minima, max_value=fecha_maxima)
    fecha_fin = st.date_input("Fecha de Fin", value=fecha_maxima, min_value=fecha_minima, max_value=fecha_maxima)

    st.subheader("📊 Métricas Clave")
    st.metric("Total Licitaciones", len(df))
    st.metric("Adjudicadas", len(df[df["Estado"]=="Adjudicada"])) # Se mantiene la lógica del contador para el sidebar
    st.metric("En Proceso", len(df[df["Estado"]=="En proceso"])) # Agregado para que no se pierda la métrica

# Aplicar filtros
df_filtrado = df.copy()

if busqueda:
    df_filtrado = df_filtrado[df_filtrado["Nombre"].str.contains(busqueda, case=False, na=False)]
    if len(df_filtrado) == 0:
        st.warning(f"⚠️ No se encontraron licitaciones para: **{busqueda}**")
        st.stop()

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]

# Filtrar por rango de fechas
df_filtrado = df_filtrado[(df_filtrado['FechaCierre'].dt.date >= fecha_inicio) & (df_filtrado['FechaCierre'].dt.date <= fecha_fin)]



st.divider()

st.subheader("📋 Resultados")
st.dataframe(df_filtrado[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

# Botón de descarga CSV
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Descargar datos filtrados en CSV",
    data=csv,
    file_name='licitaciones_filtradas.csv',
    mime='text/csv',
)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Cantidad de Licitaciones por Estado")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.countplot(data=df_filtrado, x="Estado", ax=ax1, palette="viridis", order=df_filtrado["Estado"].value_counts().index)
    ax1.set_title("Licitaciones por Estado")
    ax1.set_xlabel("Estado")
    ax1.set_ylabel("Cantidad")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig1)

with col2:
    st.subheader("🥧 Distribución Porcentual por Estado")
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    df_filtrado["Estado"].value_counts().plot(kind="pie", ax=ax2, autopct="%1.1f%%", startangle=90, cmap="viridis")
    ax2.set_title("Distribución de Licitaciones por Estado")
    ax2.set_ylabel("") # Ocultar el label del eje y en el pie chart
    plt.tight_layout()
    st.pyplot(fig2)

st.divider()

st.subheader("🗓️ Licitaciones por Fecha de Cierre")
# Agrupar por fecha de cierre y contar
licitaciones_por_fecha = df_filtrado['FechaCierre'].dt.date.value_counts().sort_index()

# Crear el gráfico de barras
fig3, ax3 = plt.subplots(figsize=(12, 6))
sns.barplot(x=licitaciones_por_fecha.index, y=licitaciones_por_fecha.values, ax=ax3, palette='magma')

ax3.set_title('Cantidad de Licitaciones por Fecha de Cierre')
ax3.set_xlabel('Fecha de Cierre')
ax3.set_ylabel('Número de Licitaciones')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig3)

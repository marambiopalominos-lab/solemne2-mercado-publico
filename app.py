
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # Importar seaborn

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

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

# Sidebar para filtros y métricas
with st.sidebar:
    st.subheader("🔍 Filtrar licitaciones")
    busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: suministro, servicio, combustible...")
    
    estados_disponibles = ["Todos"] + list(df["Estado"].dropna().unique())
    filtro = st.selectbox("Filtrar por estado:", estados_disponibles)

    st.subheader("📊 Métricas Clave")
    st.metric("Total Licitaciones", len(df))
    st.metric("Adjudicadas", len(df[df["Estado"]=="Adjudicada"])) # Se mantiene la lógica del contador para el sidebar
    st.metric("En Proceso", len(df[df["Estado"]=="En proceso"])) # Agregado para que no se pierda la métrica


if busqueda:
    df = df[df["Nombre"].str.contains(busqueda, case=False, na=False)]
    if len(df) == 0:
        st.warning(f"⚠️ No se encontraron licitaciones para: **{busqueda}**")
        st.stop()


df_filtrado = df[df["Estado"] == filtro] if filtro != "Todos" else df
st.divider()

st.subheader("📋 Resultados")
st.dataframe(df_filtrado[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Cantidad de Licitaciones por Estado")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.countplot(data=df, x="Estado", ax=ax1, palette="viridis", order=df["Estado"].value_counts().index)
    ax1.set_title("Licitaciones por Estado")
    ax1.set_xlabel("Estado")
    ax1.set_ylabel("Cantidad")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig1)

with col2:
    st.subheader("🥧 Distribución Porcentual por Estado")
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    df["Estado"].value_counts().plot(kind="pie", ax=ax2, autopct="%1.1f%%", startangle=90, cmap="viridis")
    ax2.set_title("Distribución de Licitaciones por Estado")
    ax2.set_ylabel("") # Ocultar el label del eje y en el pie chart
    plt.tight_layout()
    st.pyplot(fig2)

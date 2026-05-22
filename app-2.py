
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

# BUSCADOR
st.subheader("🔍 Buscar licitaciones por rubro")
busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: construccion, marketing, tecnologia...")

if busqueda:
    URL = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={TICKET}&busqueda={busqueda}"
else:
    URL = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={TICKET}"

with st.spinner("Cargando datos..."):
    response = requests.get(URL)
    data = response.json()
    df = pd.DataFrame(data["Listado"])
    estados = {1:"Borrador",2:"Publicada",3:"Cerrada",4:"Desierta",
               5:"Adjudicada",6:"En proceso",7:"Revocada",8:"Suspendida"}
    df["Estado"] = df["CodigoEstado"].map(estados)
    df["FechaCierre"] = pd.to_datetime(df["FechaCierre"])

# MÉTRICAS
col1, col2, col3 = st.columns(3)
col1.metric("Total Licitaciones", data["Cantidad"])
col2.metric("Adjudicadas", len(df[df["Estado"]=="Adjudicada"]))
col3.metric("En Proceso", len(df[df["Estado"]=="En proceso"]))

st.divider()

# FILTRO POR ESTADO
st.subheader("📋 Resultados")
estados_disponibles = ["Todos"] + list(df["Estado"].dropna().unique())
filtro = st.selectbox("Filtrar por estado:", estados_disponibles)

if filtro != "Todos":
    df_filtrado = df[df["Estado"] == filtro]
else:
    df_filtrado = df

st.dataframe(df_filtrado[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

st.divider()

# GRÁFICOS
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Licitaciones por Estado")
    fig1, ax1 = plt.subplots()
    df["Estado"].value_counts().plot(kind="bar", ax=ax1, color=["#2ecc71","#e74c3c","#3498db"])
    ax1.set_xlabel("Estado")
    ax1.set_ylabel("Cantidad")
    plt.tight_layout()
    st.pyplot(fig1)

with col2:
    st.subheader("🥧 Distribución por Estado")
    fig2, ax2 = plt.subplots()
    df["Estado"].value_counts().plot(kind="pie", ax=ax2, autopct="%1.1f%%",
                                      colors=["#2ecc71","#e74c3c","#3498db"])
    ax2.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig2)

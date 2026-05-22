
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

# BUSCADOR
st.subheader("🔍 Buscar licitaciones por rubro")
busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: construccion, excavadora, marketing...")

# TRAEMOS MÚLTIPLES PÁGINAS
@st.cache_data(ttl=300)
def cargar_datos(ticket):
    todas = []
    for pagina in range(1, 11):  # 10 páginas = hasta 100 licitaciones
        url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}&pagina={pagina}"
        response = requests.get(url)
        data = response.json()
        if data.get("Listado"):
            todas.extend(data["Listado"])
        else:
            break
    return todas

with st.spinner("⏳ Cargando licitaciones desde Mercado Público..."):
    listado = cargar_datos(TICKET)

df = pd.DataFrame(listado)
estados = {1:"Borrador",2:"Publicada",3:"Cerrada",4:"Desierta",
           5:"Adjudicada",6:"En proceso",7:"Revocada",8:"Suspendida"}
df["Estado"] = df["CodigoEstado"].map(estados)
df["FechaCierre"] = pd.to_datetime(df["FechaCierre"])

# FILTRO SOLO LICITACIONES ABIERTAS PARA POSTULAR
hoy = pd.Timestamp.now()
df_abiertas = df[df["FechaCierre"] > hoy]

# TABS - PESTAÑAS
tab1, tab2 = st.tabs(["📋 Abiertas para postular", "📊 Todas las licitaciones"])

with tab1:
    st.subheader("✅ Licitaciones vigentes — puedes postular ahora")
    
    if busqueda:
        df_filtrado = df_abiertas[df_abiertas["Nombre"].str.contains(busqueda, case=False, na=False)]
    else:
        df_filtrado = df_abiertas
    
    if len(df_filtrado) == 0:
        st.warning(f"⚠️ No hay licitaciones abiertas para: **{busqueda}**")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Abiertas para postular", len(df_filtrado))
        col2.metric("Cierre más próximo", df_filtrado["FechaCierre"].min().strftime("%d/%m/%Y"))
        st.dataframe(df_filtrado[["CodigoExterno","Nombre","Estado","FechaCierre"]].sort_values("FechaCierre"), use_container_width=True)

with tab2:
    st.subheader("📊 Análisis general")
    
    if busqueda:
        df_todos = df[df["Nombre"].str.contains(busqueda, case=False, na=False)]
    else:
        df_todos = df

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(df_todos))
    col2.metric("Adjudicadas", len(df_todos[df_todos["Estado"]=="Adjudicada"]))
    col3.metric("Suspendidas", len(df_todos[df_todos["Estado"]=="Suspendida"]))

    st.dataframe(df_todos[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Por Estado")
        fig1, ax1 = plt.subplots()
        df_todos["Estado"].value_counts().plot(kind="bar", ax=ax1)
        plt.tight_layout()
        st.pyplot(fig1)
    with col2:
        st.subheader("🥧 Distribución")
        fig2, ax2 = plt.subplots()
        df_todos["Estado"].value_counts().plot(kind="pie", ax=ax2, autopct="%1.1f%%")
        ax2.set_ylabel("")
        plt.tight_layout()
        st.pyplot(fig2)

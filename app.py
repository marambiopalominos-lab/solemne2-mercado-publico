
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

TICKET = "CA594884-38DC-459B-938D-3580527E59B9"

st.set_page_config(page_title="Licitaciones Chile", page_icon="🏛️", layout="wide")
st.title("🏛️ Dashboard Licitaciones - Mercado Público Chile")
st.markdown("Datos obtenidos en tiempo real desde la API de Mercado Público")

st.subheader("🔍 Buscar licitaciones por rubro")
busqueda = st.text_input("Escribe una palabra clave:", placeholder="Ej: construccion, excavadora, marketing...")

@st.cache_data(ttl=300)
def cargar_datos(ticket):
    todas = []
    # Pedimos específicamente las publicadas (CodigoEstado=2) y en proceso (6)
    for estado_cod in [2, 6]:
        for pagina in range(1, 6):
            url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}&CodigoEstado={estado_cod}&pagina={pagina}"
            response = requests.get(url)
            data = response.json()
            if data.get("Listado"):
                todas.extend(data["Listado"])
            else:
                break
    return todas

with st.spinner("⏳ Cargando licitaciones abiertas..."):
    listado = cargar_datos(TICKET)

if not listado:
    st.error("No se pudieron cargar datos")
    st.stop()

df = pd.DataFrame(listado).drop_duplicates(subset=["CodigoExterno"])
estados = {1:"Borrador",2:"Publicada",3:"Cerrada",4:"Desierta",
           5:"Adjudicada",6:"En proceso",7:"Revocada",8:"Suspendida"}
df["Estado"] = df["CodigoEstado"].map(estados)
df["FechaCierre"] = pd.to_datetime(df["FechaCierre"])

if busqueda:
    df_mostrar = df[df["Nombre"].str.contains(busqueda, case=False, na=False)]
else:
    df_mostrar = df

tab1, tab2 = st.tabs(["✅ Abiertas para postular", "📊 Análisis general"])

with tab1:
    st.subheader("✅ Licitaciones vigentes — puedes postular ahora")
    if len(df_mostrar) == 0:
        st.warning(f"⚠️ No hay licitaciones para: **{busqueda}**")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Licitaciones encontradas", len(df_mostrar))
        col2.metric("Cierre más próximo", df_mostrar["FechaCierre"].min().strftime("%d/%m/%Y"))
        st.dataframe(
            df_mostrar[["CodigoExterno","Nombre","Estado","FechaCierre"]].sort_values("FechaCierre"),
            use_container_width=True
        )

with tab2:
    if len(df_mostrar) == 0:
        st.warning("Sin datos para analizar")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df_mostrar))
        col2.metric("Publicadas", len(df_mostrar[df_mostrar["Estado"]=="Publicada"]))
        col3.metric("En Proceso", len(df_mostrar[df_mostrar["Estado"]=="En proceso"]))

        st.dataframe(df_mostrar[["CodigoExterno","Nombre","Estado","FechaCierre"]], use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Por Estado")
            fig1, ax1 = plt.subplots()
            df_mostrar["Estado"].value_counts().plot(kind="bar", ax=ax1, color=["#2ecc71","#3498db"])
            plt.tight_layout()
            st.pyplot(fig1)
        with col2:
            st.subheader("🥧 Distribución")
            fig2, ax2 = plt.subplots()
            df_mostrar["Estado"].value_counts().plot(kind="pie", ax=ax2, autopct="%1.1f%%")
            ax2.set_ylabel("")
            plt.tight_layout()
            st.pyplot(fig2)

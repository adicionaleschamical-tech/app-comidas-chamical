import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión Caniche Food", page_icon="🍟", layout="centered")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { border: 2px solid #EEE; padding: 15px; border-radius: 15px; margin-bottom: 20px; background-color: #F9F9F9 !important; }
    .btn-active > button { background-color: #E63946 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, conf
    except: return pd.DataFrame(), {}

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
df_prod, conf = cargar_datos()
nombre_negocio = conf.get("Nombre Negocio", "Caniche Food")

# --- LOGIN EN SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Acceso Staff")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingresar"):
            u = st.text_input("Usuario/DNI")
            p = st.text_input("Clave", type="password")
            if st.button("Entrar"):
                if u == "30588807" and p == "124578": st.session_state['rol'] = 'admin'
                elif u == "usuario" and p == "usuario123": st.session_state['rol'] = 'usuario'
                st.rerun()
    else:
        st.write(f"Rol: {st.session_state['rol'].upper()}")
        if st.button("Salir"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTA DE GESTIÓN (ADMIN Y USUARIO) ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title(f"🛠️ Panel de Gestión")
    
    tab_edit, tab_nuevo, tab_local = st.tabs(["✏️ Editar Existentes", "➕ Agregar Producto", "🏠 Datos Local"])

    with tab_edit:
        st.subheader("Lista Actual")
        # El editor permite modificar lo que ya existe
        cols_mostrar = ["PRODUCTO", "CATEGORIA", "PRECIO", "DISPONIBLE"]
        st.data_editor(df_prod[cols_mostrar], use_container_width=True)

    with tab_nuevo:
        st.subheader("Cargar nuevo ítem al menú")
        with st.form("form_nuevo_prod"):
            nuevo_nombre = st.text_input("Nombre del Producto (ej: Hamburguesa Especial)")
            nueva_cat = st.selectbox("Categoría", df_prod['CATEGORIA'].unique() if not df_prod.empty else ["HAMBURGUESAS", "PIZZAS", "BEBIDAS"])
            nuevos_ing = st.text_area("Ingredientes (separados por punto y coma si hay variedades)")
            nuevos_precios = st.text_input("Precios (separados por punto y coma si hay variedades)")
            nueva_img = st.text_input("Link de la Imagen (URL)")
            
            enviar = st.form_submit_button("Registrar Producto")
            if enviar:
                if nuevo_nombre and nuevos_precios:
                    st.success(f"Producto '{nuevo_nombre}' listo para ser añadido al Excel.")
                    st.info("Nota: Para que el cambio sea permanente, debés copiar estos datos a tu Google Sheet.")
                else:
                    st.error("Por favor completa Nombre y Precio.")

    with tab_local:
        if st.session_state['rol'] == 'admin':
            st.write("Configuración General")
            st.write(conf)
        else:
            st.warning("Solo el Admin puede ver esto.")

# --- VISTA CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_negocio}</h1>", unsafe_allow_html=True)
    # (Aquí iría el resto del código del menú que ya tenemos funcionando...)
    st.write("Bienvenido al menú. Seleccioná tu categoría arriba.")

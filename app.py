import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión Caniche Food", page_icon="🍟", layout="centered")

# --- DISEÑO ---
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
        return df_p, df_c, conf
    except: return pd.DataFrame(), pd.DataFrame(), {}

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
df_prod, df_conf_raw, conf = cargar_datos()

# --- LOGIN SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Acceso Staff")
    rol_actual = st.session_state.get('rol', 'cliente')
    
    if rol_actual == 'cliente':
        with st.expander("Ingresar"):
            u_in = st.text_input("Usuario / DNI:", key="u_log")
            p_in = st.text_input("Clave:", type="password", key="p_log")
            if st.button("Entrar"):
                # Credenciales dinámicas desde el Sheet
                if u_in == conf.get("Admin_DNI", "30588807") and p_in == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u_in == conf.get("User", "usuario") and p_in == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Datos incorrectos")
    else:
        st.info(f"Sesión: {str(rol_actual).upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title(f"🛠️ Panel de Gestión")
    tab_prod, tab_conf = st.tabs(["🍔 Productos", "⚙️ Configuración del Local"])

    with tab_prod:
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True, key="ed_admin_p")
        else:
            cols_u = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            st.data_editor(df_prod[cols_u], use_container_width=True, key="ed_user_p")

    with tab_conf:
        st.subheader("Datos de la Marca")
        
        # --- FILTRO DE SEGURIDAD CRÍTICO ---
        if st.session_state['rol'] == 'usuario':
            # El usuario NO puede ver filas que contengan "Admin" o "Pass"
            palabras_prohibidas = ["Admin", "Pass", "User_Pass"]
            mask = ~df_conf_raw.iloc[:, 0].str.contains('|'.join(palabras_prohibidas), case=False, na=False)
            df_visible = df_conf_raw[mask]
            st.write("Editá el nombre, teléfono y delivery de tu negocio:")
            st.data_editor(df_visible, use_container_width=True, key="ed_conf_user")
        else:
            # El Admin ve todo el corazón del sistema
            st.warning("Acceso total a credenciales y tokens.")
            st.data_editor(df_conf_raw, use_container_width=True, key="ed_conf_admin")

# --- VISTA CLIENTE ---
else:
    nombre_n = conf.get("Nombre Negocio", "Caniche Food")
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    st.write("Seleccioná tus productos y realizá el pedido por WhatsApp.")
    # (Aquí continúa el código del menú que ya veníamos usando)

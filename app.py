import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE ENLACES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_PEDIDOS = "1395505058"
GID_CONFIG = "PONE_AQUI_EL_GID_DE_CONFIG" # Buscá el gid en la pestaña CONFIG

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=60)
def cargar_config():
    try:
        resp = requests.get(URL_CONFIG, timeout=10)
        df = pd.read_csv(StringIO(resp.text))
        # Crea un diccionario simple de usar: config['Alias']
        return pd.Series(df.VALOR.values, index=df.PARAMETRO).to_dict()
    except:
        return {}

def formatear_moneda(valor):
    try: return f"${int(valor):,}".replace(",", ".")
    except: return "$0"

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    if isinstance(valor, (int, float)): return int(valor)
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

def obtener_pedidos_frescos():
    try:
        url = f"{URL_PEDIDOS_BASE}&cache_buster={int(time.time())}"
        df = pd.read_csv(url)
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 3. INICIO DE APP ---
conf = cargar_config()
st.set_page_config(page_title=conf.get('NOMBRE_LOCAL', 'Lomitos'), layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'rol' not in st.session_state: st.session_state.rol = 'cliente'

# --- ENCABEZADO ---
st.title(conf.get('NOMBRE_LOCAL', 'Mi Local'))
st.caption(f"📍 {conf.get('Direccion Local', '')}")

# --- 4. LÓGICA DE VISTAS ---

# VISTA: LOGIN ADMIN/USUARIO
if st.session_state.vista == 'login':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    with st.form("login_form"):
        u_dni = st.text_input("DNI de Usuario")
        u_pass = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if u_dni == str(conf.get('Admin_DNI')) and u_pass == str(conf.get('Admin_Pass')):
                st.session_state.rol = 'admin'; st.session_state.vista = 'admin_panel'; st.rerun()
            elif u_dni == str(conf.get('User')) and u_pass == str(conf.get('User_Pass')):
                st.session_state.rol = 'user'; st.session_state.vista = 'admin_panel'; st.rerun()
            else: st.error("Credenciales incorrectas")

# VISTA: PANEL DE ADMINISTRACIÓN
if st.session_state.vista == 'admin_panel':
    st.header("🎛️ Panel de Gestión")
    if st.button("Cerrar Sesión"): st.session_state.vista = 'inicio'; st.session_state.rol = 'cliente'; st.rerun()
    
    df_peds = obtener_pedidos_frescos()
    if not df_peds.empty:
        st.write("### Pedidos Recientes")
        st.dataframe(df_peds.tail(20))
        # Aquí podrías agregar botones para cambiar estados si lo deseas
    else: st.info("No hay pedidos registrados aún.")

# VISTA: INICIO
if st.session_state.vista == 'inicio':
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍔 HACER PEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'; st.rerun()
    with col2:
        if st.button("📦 MI PEDIDO", use_container_width=True):
            st.session_state.vista = 'consultar'; st.rerun()
    
    st.write("---")
    if st.button("🔑 Acceso Personal"): st.session_state.vista = 'login'; st.rerun()

# VISTA: PEDIR (CON COSTO DE DELIVERY)
if st.session_state.vista == 'pedir':
    if st.button("⬅ Menú"): st.session_state.vista = 'inicio'; st.rerun()
    
    # ... (Carga de productos igual que antes) ...
    # Al momento de pagar:
    costo_del = limpiar_precio(conf.get('Costo Delivery', 0))
    
    if st.session_state.carrito:
        # Lógica de carrito...
        metodo = st.radio("Entrega:", ["Retiro", "Delivery"])
        total_final = total_p + (costo_del if metodo == "Delivery" else 0)
        
        if metodo == "Delivery":
            st.write(f"Costo Delivery: {formatear_moneda(costo_del)}")
        
        st.subheader(f"Total a Pagar: {formatear_moneda(total_final)}")
        st.info(f"Alias para transferencia: **{conf.get('Alias', 'No definido')}**")

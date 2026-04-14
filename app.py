import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE ENLACES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_PEDIDOS = "1395505058"
GID_CONFIG = "612320365" 

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=2) # Bajamos a 2 segundos para ver cambios casi en vivo
def cargar_config_debug():
    try:
        # Forzamos un parámetro aleatorio en la URL para evitar que Google Sheets nos de una versión vieja (caché del servidor)
        url_fresca = f"{URL_CONFIG}&cache_buster={int(time.time())}"
        resp = requests.get(url_fresca, timeout=10)
        resp.encoding = 'utf-8'
        
        texto_crudo = resp.text
        df = pd.read_csv(StringIO(texto_crudo), header=None)
        
        config_dict = {}
        for _, row in df.iterrows():
            if pd.notna(row[0]):
                param = str(row[0]).strip()
                valor = str(row[1]).strip() if pd.notna(row[1]) else ""
                config_dict[param] = valor
        
        return config_dict, texto_crudo # Devolvemos el diccionario y el texto original para debug
    except Exception as e:
        return {}, str(e)

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

def formatear_moneda(valor):
    try:
        v = int(float(str(valor).replace('$', '').replace('.', '').replace(',', '').strip()))
        return f"${v:,}".replace(",", ".")
    except: return f"${valor}"

# --- 3. CARGA Y DIAGNÓSTICO ---
conf, debug_txt = cargar_config_debug()

# PANEL DE ERROR (Solo para vos, para ver qué lee la app)
with st.expander("🛠️ PANEL DE DIAGNÓSTICO (DEBUG)"):
    st.write("### Datos Crudos recibidos de Google Sheets:")
    st.code(debug_txt)
    st.write("### Diccionario Procesado:")
    st.write(conf)
    if st.button("🗑️ FORZAR LIMPIEZA DE MEMORIA"):
        st.cache_data.clear()
        st.rerun()

# --- 4. VARIABLES DE LA APP ---
nombre_local = conf.get('Nombre_Local', 'Cargando...')
logo_url = conf.get('Logo_URL', '')
direccion_local = conf.get('Direccion Local', 'No se leyó la dirección')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍟", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 5. CABECERA ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    if logo_url and str(logo_url).startswith("http"):
        try: st.image(logo_url, width=90)
        except: st.markdown("## 🍔")
    else: st.markdown("## 🍔")

with col_tit:
    st.title(nombre_local)
    st.caption(f"📍 {direccion_local}")

st.write("---")

# --- 6. VISTAS ---

# MANTENIMIENTO
if conf.get('MODO_MANTENIMIENTO') == "SI":
    st.error("⚠️ Local cerrado por mantenimiento.")
    if st.button("🔑 Staff"): st.session_state.vista = 'login'; st.rerun()
    st.stop()

# INICIO
if st.session_state.vista == 'inicio':
    c1, c2 = st.columns(2)
    if c1.button("🍔 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("📦 MI PEDIDO", use_container_width=True):
        st.session_state.vista = 'consultar'; st.rerun()
    st.write("---")
    if st.button("🔑 Acceso Personal"): st.session_state.vista = 'login'; st.rerun()

# LOGIN
if st.session_state.vista == 'login':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    u_dni = st.text_input("DNI")
    u_pass = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u_dni == str(conf.get('Admin_DNI')) and u_pass == str(conf.get('Admin_Pass')):
            st.session_state.rol = 'admin'; st.session_state.vista = 'admin_panel'; st.rerun()
        else: st.error("Error de credenciales.")

# PEDIR
if st.session_state.vista == 'pedir':
    if st.button("⬅ Menú"): st.session_state.vista = 'inicio'; st.rerun()
    # (Resto del código de productos igual que antes...)
    st.info("Menú en carga... (Asegurate de tener productos con DISPONIBLE = SI)")

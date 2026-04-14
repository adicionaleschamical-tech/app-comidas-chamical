import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE ENLACES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_PEDIDOS = "1395505058"
GID_CONFIG = "612320365"  # <--- Tu GID de la pestaña CONFIG

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=10)
def cargar_config():
    try:
        resp = requests.get(URL_CONFIG, timeout=10)
        # Cargamos sin encabezados para evitar errores de nombres de columna
        df = pd.read_csv(StringIO(resp.text), header=None)
        
        # Convertimos la Columna 0 (A) en llaves y la Columna 1 (B) en valores
        config_dict = {}
        for _, row in df.iterrows():
            param = str(row[0]).strip()
            valor = str(row[1]).strip()
            config_dict[param] = valor
        return config_dict
    except Exception as e:
        return {}

def formatear_moneda(valor):
    try:
        v = int(float(str(valor).replace('.', '').replace(',', '')))
        return f"${v:,}".replace(",", ".")
    except:
        return f"${valor}"

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    if isinstance(valor, (int, float)): return int(valor)
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

# --- 3. INICIO Y CARGA ---
conf = cargar_config()

# Definimos variables con los nombres EXACTOS que pusiste en el Sheet
nombre_local = conf.get('Nombre_Local', 'Cargando...')
logo_url = conf.get('Logo_URL', '')
direccion = conf.get('Direccion Local', '')

st.set_page_config(page_title=nombre_local, page_icon="🍟", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. ENCABEZADO ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    if logo_url:
        st.image(logo_url, width=100)
with col_tit:
    st.title(nombre_local)
    if direccion:
        st.caption(f"📍 {direccion}")

st.write("---")

# --- 5. VISTAS ---

# MODO MANTENIMIENTO
if conf.get('MODO_MANTENIMIENTO') == "SI":
    st.warning("⚠️ El local se encuentra cerrado por mantenimiento. ¡Volvemos pronto!")
    if st.button("🔑 Acceso Personal"):
        st.session_state.vista = 'login'; st.rerun()
    st.stop()

# VISTA: INICIO
if st.session_state.vista == 'inicio':
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🍔 HACER PEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'; st.rerun()
    with c2:
        if st.button("📦 MI PEDIDO", use_container_width=True):
            st.session_state.vista = 'consultar'; st.rerun()
    st.write("---")
    if st.button("🔑 Acceso Personal"):
        st.session_state.vista = 'login'; st.rerun()

# VISTA: LOGIN
if st.session_state.vista == 'login':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    st.subheader("Ingreso de Personal")
    u_dni = st.text_input("DNI")
    u_pass = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u_dni == conf.get('Admin_DNI') and u_pass == conf.get('Admin_Pass'):
            st.session_state.rol = 'admin'; st.session_state.vista = 'admin_panel'; st.rerun()
        else:
            st.error("Credenciales incorrectas")

# VISTA: PEDIR
if st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("Identificación")
            n = st.text_input("Nombre")
            d = st.text_input("DNI")
            if st.button("Ver Menú"):
                if n and d:
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # Carga de productos
    df_prod = pd.read_csv(URL_PRODUCTOS)
    df_prod.columns = [c.strip().upper() for c in df_prod.columns]

    for idx, row in df_prod.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1.5])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.markdown(f"**{row['PRODUCTO']}**")
                p_unit = limpiar_precio(row['PRECIO'])
                c2.write(formatear_moneda(p_unit))
                
                p_name = row['PRODUCTO']
                cant = st.session_state.carrito.get(p_name, 0)
                
                b1, b_txt, b2 = c3.columns([1, 1, 1])
                if b1.button("➖", key=f"m_{idx}"):
                    if cant > 0:
                        st.session_state.carrito[p_name] -= 1
                        if st.session_state.carrito[p_name] == 0: del st.session_state.carrito[p_name]
                        st.rerun()
                b_txt.markdown(f"<h3 style='text-align:center; margin:0;'>{cant}</h3>", unsafe_allow_html=True)
                if b2.button("➕", key=f"p_{idx}"):
                    st.session_state.carrito[p_name] = cant + 1
                    st.rerun()

    if st.session_state.carrito:
        st.write("---")
        st.header("🛒 Resumen")
        total_acum = 0
        detalle = ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_prod[df_prod['PRODUCTO']==p]['PRECIO'].iloc[0])
            sub = pre * q
            total_acum += sub
            detalle += f"- {q}x {p}\n"
            st.write(f"{q}x {p} ({formatear_moneda(sub)})")
        
        metodo = st.radio("Entrega:", ["Retiro", "Delivery"])
        envio = limpiar_precio(conf.get('Costo Delivery', 0)) if metodo == "Delivery" else 0
        
        total_f = total_acum + envio
        if envio > 0: st.write(f"Costo Delivery: {formatear_moneda(envio)}")
        
        st.markdown(f"## TOTAL: {formatear_moneda(total_f)}")
        st.info(f"💰 Alias: {conf.get('Alias')}")
        
        dire = st.text_input("Dirección:") if metodo == "Delivery" else "Retiro"
        
        if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle, "total":total_f, "dir":dire}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📍 {dire}\n{detalle}\n💰 TOTAL: {formatear_moneda(total_f)}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.session_state.carrito = {}; st.session_state.vista = 'consultar'; st.rerun()

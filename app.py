import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_PEDIDOS = "1395505058" 
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# --- PERSONALIZACIÓN DEL LOCAL ---
NOMBRE_LOCAL = "TU NOMBRE AQUÍ"  # Ej: Lomitos Chamical
LOGO_URL = "https://via.placeholder.com/150" # Reemplaza con el link de tu logo

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title=NOMBRE_LOCAL, page_icon="🍟", layout="centered")

# --- 2. FUNCIONES ---

def formatear_moneda(valor):
    """Convierte números a formato $1.250"""
    try:
        return f"${int(valor):,}".replace(",", ".")
    except:
        return "$0"

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    if isinstance(valor, (int, float)): return int(valor)
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

@st.cache_data(ttl=60)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS, timeout=10)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

def obtener_pedidos_frescos():
    try:
        url_fresca = f"{URL_PEDIDOS_BASE}&cache_buster={int(time.time())}"
        resp = requests.get(url_fresca, timeout=10)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

def enviar_telegram(mensaje, dni):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=EN_CAMINO"
    texto = f"{mensaje}\n\n✅ [ACEPTAR]({link_aceptar}) | 🛵 [ENVIADO]({link_enviar})"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

# --- 3. LÓGICA DE NAVEGACIÓN ---
if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- ENCABEZADO COMÚN ---
col_logo, col_titulo = st.columns([1, 3])
with col_logo:
    st.image(LOGO_URL, width=80)
with col_titulo:
    st.title(NOMBRE_LOCAL)

# --- VISTA: INICIO ---
if st.session_state.vista == 'inicio':
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🍔\nHACER\nPEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'; st.rerun()
    with c2:
        if st.button("📦\nCONSULTAR\nESTADO", use_container_width=True):
            st.session_state.vista = 'consultar'; st.rerun()
    st.stop()

# --- VISTA: HACER PEDIDO ---
if st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("Tus Datos")
            nombre = st.text_input("Nombre y Apellido")
            dni = st.text_input("DNI (solo números)")
            if st.button("Ver Menú"):
                if nombre and dni.isdigit():
                    st.session_state.user_name = nombre; st.session_state.user_dni = dni; st.rerun()
                else: st.error("Ingresá datos válidos.")
        st.stop()

    df_p = cargar_productos()
    
    st.subheader("Menú")
    for idx, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1.5])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.markdown(f"**{row['PRODUCTO']}**")
                precio_num = limpiar_precio(row['PRECIO'])
                c2.write(formatear_moneda(precio_num))
                
                # SELECTOR + / -
                prod_name = row['PRODUCTO']
                cant_actual = st.session_state.carrito.get(prod_name, 0)
                
                col_btn1, col_cant, col_btn2 = c3.columns([1, 1, 1])
                if col_btn1.button("➖", key=f"min_{idx}"):
                    if cant_actual > 0:
                        st.session_state.carrito[prod_name] -= 1
                        if st.session_state.carrito[prod_name] == 0: del st.session_state.carrito[prod_name]
                        st.rerun()
                col_cant.markdown(f"<h3 style='text-align:center; margin:0;'>{cant_actual}</h3>", unsafe_allow_html=True)
                if col_btn2.button("➕", key=f"plus_{idx}"):
                    st.session_state.carrito[prod_name] = cant_actual + 1
                    st.rerun()

    # --- SECCIÓN CARRITO ---
    if st.session_state.carrito:
        st.markdown("---")
        st.header("🛒 Tu Carrito")
        total_pedido = 0
        detalle_texto = ""
        
        for p, q in st.session_state.carrito.items():
            precio_unit = limpiar_precio(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
            subtotal = precio_unit * q
            total_pedido += subtotal
            detalle_texto += f"- {q}x {p}\n"
            
            # Vista del ítem en el carrito
            c_art, c_sub = st.columns([3, 1])
            c_art.write(f"**{q}x** {p}")
            c_sub.write(formatear_moneda(subtotal))
        
        st.markdown(f"### TOTAL: {formatear_moneda(total_pedido)}")
        
        ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        dir_e = st.text_input("Dirección de envío:") if ent == "Delivery" else "Retiro en local"
        
        if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle_texto, "total":total_pedido, "dir":dir_e}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n🪪 DNI: {st.session_state.user_dni}\n📍 {dir_e}\n{detalle_texto}\n💰 *TOTAL: {formatear_moneda(total_pedido)}*"
            enviar_telegram(msg, st.session_state.user_dni)
            st.session_state.carrito = {}; st.session_state.vista = 'consultar'; st.rerun()

# --- VISTA: CONSULTAR ESTADO ---
if st.session_state.vista == 'consultar':
    if st.button("⬅ Menú Principal"): st.session_state.vista = 'inicio'; st.rerun()
    st.subheader("Estado de tu Pedido")
    dni_input = st.text_input("DNI:", value=st.session_state.get('user_dni', ""))
    
    if st.button("🔍 CONSULTAR"):
        df_peds = obtener_pedidos_frescos()
        if not df_peds.empty:
            df_peds['DNI_C'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[.,\s]', '', regex=True).str.strip()
            dni_b = re.sub(r'[^\d]', '', str(dni_input)).strip()
            match = df_peds[df_peds['DNI_C'] == dni_b]
            if not match.empty:
                res = match.iloc[-1]
                st.info(f"Hola **{res['NOMBRE']}**, tu pedido está: **{res['ESTADO'].upper()}**")
                if res['ESTADO'].upper() not in ["ENTREGADO", "FINALIZADO"]:
                    time.sleep(15); st.rerun()
            else: st.warning("No hay pedidos activos para ese DNI.")

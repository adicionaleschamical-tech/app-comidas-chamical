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

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟", layout="centered")

# --- 2. FUNCIONES ---

def limpiar_precio(valor):
    if pd.isna(valor): return 0
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

# --- VISTA: INICIO ---
if st.session_state.vista == 'inicio':
    st.markdown("<h1 style='text-align: center;'>🍟 Pedidos Chamical</h1>", unsafe_allow_html=True)
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
            st.info("⚠️ Usaremos tu DNI para que consultes el estado de tu pedido.")
            nombre = st.text_input("Nombre y Apellido")
            dni = st.text_input("DNI (solo números)")
            if st.button("Ver Menú"):
                if nombre and dni.isdigit():
                    st.session_state.user_name = nombre
                    st.session_state.user_dni = dni
                    st.rerun()
                else: st.error("Por favor, ingresá datos válidos.")
        st.stop()

    df_p = cargar_productos()
    if 'carrito' not in st.session_state: st.session_state.carrito = {}

    for idx, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"**Precio: ${row['PRECIO']}**")
                if c2.button("➕ Agregar", key=f"a_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast(f"Agregado: {row['PRODUCTO']}")

    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Tu Pedido")
        total, detalle = 0, ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
            total += (pre * q)
            st.write(f"**{q}x** {p} (${pre*q:,.0f})")
            detalle += f"- {q}x {p}\n"
        
        ent = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        dir_e = st.text_input("Dirección") if ent == "Delivery" else "Retiro"
        
        if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle, "total":total, "dir":dir_e}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n🪪 DNI: {st.session_state.user_dni}\n📍 {dir_e}\n{detalle}\n💰 *TOTAL: ${total:,.0f}*"
            enviar_telegram(msg, st.session_state.user_dni)
            st.session_state.carrito = {}; st.session_state.vista = 'consultar'; st.rerun()

# --- VISTA: CONSULTAR ESTADO ---
if st.session_state.vista == 'consultar':
    if st.button("⬅ Volver al inicio"): st.session_state.vista = 'inicio'; st.rerun()
    
    st.title("Seguimiento de Pedido")
    dni_input = st.text_input("Ingresá tu DNI:", value=st.session_state.get('user_dni', ""))
    
    if st.button("🔍 CONSULTAR", type="primary", use_container_width=True):
        if dni_input:
            df_peds = obtener_pedidos_frescos()
            if not df_peds.empty:
                # Limpieza de DNI
                df_peds['DNI_CLEAN'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True)
                df_peds['DNI_CLEAN'] = df_peds['DNI_CLEAN'].str.replace(r'[.,\s]', '', regex=True).str.strip()
                dni_busqueda = re.sub(r'[^\d]', '', str(dni_input)).strip()
                
                match = df_peds[df_peds['DNI_CLEAN'] == dni_busqueda]
                
                if not match.empty:
                    res = match.iloc[-1]
                    estado = str(res.get('ESTADO', 'RECIBIDO')).upper()
                    nombre = res.get('NOMBRE', 'Cliente')
                    
                    st.markdown(f"""
                        <div style="padding:20px; border-radius:15px; border:3px solid #E63946; text-align:center; background-color: #ffffff; margin-top:20px;">
                            <h3 style="color: #333;">Hola {nombre}</h3>
                            <p style="color: #666;">Tu último pedido está:</p>
                            <h1 style="color:#E63946; font-size:45px; margin: 0;">{estado}</h1>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if estado not in ["ENTREGADO", "FINALIZADO"]:
                        time.sleep(20); st.rerun()
                else:
                    st.warning("No encontramos pedidos pendientes para este DNI.")

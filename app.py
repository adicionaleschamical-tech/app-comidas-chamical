import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# REEMPLAZA ESTE GID con el de tu pestaña PEDIDOS (ej: 1234567)
GID_PEDIDOS = "TU_GID_AQUI" 

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟")

# --- 2. FUNCIONES DE LIMPIEZA Y ENVÍO ---
def limpiar_precio(valor):
    """Elimina puntos, signos $ y espacios, convirtiendo a entero"""
    if pd.isna(valor): return 0
    # Elimina todo lo que no sea un número
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

def enviar_telegram_confirmacion(mensaje, tel):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=EN_CAMINO"
    
    texto_final = (
        f"{mensaje}\n\n"
        f"✅ [ACEPTAR Y COCINAR]({link_aceptar})\n"
        f"🛵 [PEDIDO EN CAMINO]({link_enviar})"
    )
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto_final, "parse_mode": "Markdown"})

@st.cache_data(ttl=20)
def cargar_datos():
    try:
        df = pd.read_csv(StringIO(requests.get(URL_PRODUCTOS).text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 3. LÓGICA DE SESIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# PANTALLA: LOGIN
if st.session_state.paso == 'login':
    st.title("🍔 Identificación")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono")
    if st.button("Ingresar"):
        if nombre and tel:
            st.session_state.user_name, st.session_state.user_tel = nombre, tel
            st.session_state.paso = 'menu'
            st.rerun()
    st.stop()

# PANTALLA: SEGUIMIENTO
if st.session_state.paso == 'seguimiento':
    st.title("📦 Estado de tu Pedido")
    placeholder = st.empty()
    while True:
        try:
            df_peds = pd.read_csv(StringIO(requests.get(URL_PEDIDOS).text))
            res = df_peds[df_peds['TELEFONO'].astype(str).str.contains(str(st.session_state.user_tel))].iloc[-1]
            estado = res['ESTADO'].upper()
        except: estado = "PENDIENTE"
        
        with placeholder.container():
            st.markdown(f"<div style='text-align:center; padding:20px; border:2px solid red;'><h2>{estado}</h2></div>", unsafe_allow_html=True)
        time.sleep(20)
        st.rerun()

# PANTALLA: MENÚ
st.title("Nuestro Menú")
df_p = cargar_productos()

for idx, row in df_p.iterrows():
    if str(row['DISPONIBLE']).upper() == "SI":
        with st.container(border=True):
            c1, c2 = st.columns([1, 3])
            c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
            c2.subheader(row['PRODUCTO'])
            # Mostramos el precio tal cual viene, pero lo limpiaremos para el cálculo
            st.write(f"Precio: ${row['PRECIO']}")
            if c2.button("Agregar", key=f"btn_{idx}"):
                st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                st.toast(f"Añadido: {row['PRODUCTO']}")

# PANTALLA: CARRITO
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Pedido")
    total = 0
    resumen_txt = ""
    
    for p, q in st.session_state.carrito.items():
        # Buscamos el precio en el DataFrame y lo limpiamos
        fila = df_p[df_p['PRODUCTO'] == p]
        if not fila.empty:
            precio_unitario = limpiar_precio(fila['PRECIO'].iloc[0])
            subtotal = precio_unitario * q
            total += subtotal
            st.write(f"**{q}x** {p} -- ${subtotal:,.0f}")
            resumen_txt += f"- {q}x {p}\n"

    entrega = st.radio("Entrega", ["Retiro", "Delivery"])
    direc = st.text_input("Dirección") if entrega == "Delivery" else "Retiro en local"
    
    st.markdown(f"### TOTAL A PAGAR: ${total:,.0f}")

    if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
        params = {
            "accion": "nuevo",
            "tel": st.session_state.user_tel,
            "nombre": st.session_state.user_name,
            "detalle": resumen_txt,
            "total": total,
            "dir": direc
        }
        # Envía al Apps Script para guardar en el Sheet
        requests.get(URL_APPS_SCRIPT, params=params)
        
        # Envía a Telegram
        msg = f"🍔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n📍 {direc}\n\n{resumen_txt}\n💰 *TOTAL: ${total:,.0f}*"
        enviar_telegram_confirmacion(msg, st.session_state.user_tel)
        
        st.session_state.paso = 'seguimiento'
        st.rerun()

import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# IMPORTANTE: Reemplaza con el GID de tu pestaña PEDIDOS (está en la URL del navegador)
GID_PEDIDOS = "TU_GID_AQUI" 

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟")

# --- FUNCIONES ---
def enviar_telegram_botones(mensaje, tel):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=EN_CAMINO"
    
    texto_final = (
        f"{mensaje}\n\n"
        f"✅ [ACEPTAR Y COCINAR]({link_aceptar})\n"
        f"🛵 [PEDIDO EN CAMINO]({link_enviar})"
    )
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto_final, "parse_mode": "Markdown"})

@st.cache_data(ttl=30)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- SESIÓN Y NAVEGACIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# PANTALLA 1: LOGIN
if st.session_state.paso == 'login':
    st.title("🍔 Bienvenido")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono (ej: 3826123456)")
    if st.button("Ver Menú", use_container_width=True):
        if nombre and len(tel) > 7:
            st.session_state.user_name, st.session_state.user_tel = nombre, tel
            st.session_state.paso = 'menu'
            st.rerun()
        else: st.error("Datos incompletos")
    st.stop()

# PANTALLA 2: SEGUIMIENTO
if st.session_state.paso == 'seguimiento':
    st.title("📦 Seguimiento")
    placeholder = st.empty()
    while True:
        try:
            df = pd.read_csv(StringIO(requests.get(URL_PEDIDOS).text))
            res = df[df['TELEFONO'].astype(str).str.contains(str(st.session_state.user_tel))].iloc[-1]
            estado = res['ESTADO'].upper()
        except: estado = "PENDIENTE"
        
        with placeholder.container():
            st.subheader(f"Hola {st.session_state.user_name}, tu pedido está:")
            st.info(f"🚀 {estado}")
            if estado == "COCINANDO": st.success("👨‍🍳 ¡Ya lo estamos preparando!")
            elif estado == "EN_CAMINO": st.warning("🛵 ¡El repartidor ya salió!")
        time.sleep(20)
        st.rerun()

# PANTALLA 3: MENÚ
st.title(f"Menú de Comidas")
df_p = cargar_productos()
for idx, row in df_p.iterrows():
    if str(row['DISPONIBLE']).upper() == "SI":
        with st.container(border=True):
            col1, col2 = st.columns([1, 3])
            col1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
            col2.subheader(row['PRODUCTO'])
            col2.write(f"$ {row['PRECIO']}")
            if col2.button("➕ Agregar", key=f"btn_{idx}"):
                st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                st.toast("Agregado")

if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Pedido")
    resumen = ""
    total = 0
    for p, q in st.session_state.carrito.items():
        precio = int(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
        total += (precio * q)
        st.write(f"**{q}x** {p} (${precio*q})")
        resumen += f"- {q}x {p}\n"
    
    entrega = st.radio("Entrega", ["Retiro", "Delivery"])
    direc = st.text_input("Dirección") if entrega == "Delivery" else "Retiro en local"
    
    if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
        # AHORA SÍ: ESTA PARTE ESCRIBE EN EL SHEET
        params = {
            "accion": "nuevo",
            "tel": st.session_state.user_tel,
            "nombre": st.session_state.user_name,
            "detalle": resumen,
            "total": total,
            "dir": direc
        }
        requests.get(URL_APPS_SCRIPT, params=params) # Escribir en Excel
        
        msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n📍 {direc}\n\n{resumen}\n💰 *TOTAL: ${total}*"
        enviar_telegram_botones(msg, st.session_state.user_tel) # Enviar a Telegram
        
        st.session_state.paso = 'seguimiento'
        st.rerun()

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
import urllib.parse

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
# Tu URL de Apps Script recién creada
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# URLs de lectura (Asegúrate de que la hoja PEDIDOS esté "Publicada en la Web" como CSV)
# El GID de la hoja PEDIDOS suele ser un número largo (ej: 12345678)
GID_PEDIDOS = "TU_GID_AQUI" 
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟", layout="centered")

# --- 2. FUNCIONES ---
def enviar_telegram_confirmacion(mensaje, tel):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Links que disparan el Apps Script para cambiar el estado
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=EN_CAMINO"
    
    texto_final = (
        f"{mensaje}\n\n"
        f"✅ [ACEPTAR Y COCINAR]({link_aceptar})\n"
        f"🛵 [PEDIDO EN CAMINO]({link_enviar})"
    )
    
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto_final,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })

@st.cache_data(ttl=20)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 3. LÓGICA DE NAVEGACIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# PANTALLA A: LOGIN
if st.session_state.paso == 'login':
    st.title("🍟 Bienvenido")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono (sin 0 ni 15)")
    if st.button("Ingresar al Menú", use_container_width=True):
        if nombre and len(tel) > 7:
            st.session_state.user_name = nombre
            st.session_state.user_tel = tel
            st.session_state.paso = 'menu'
            st.rerun()
        else:
            st.error("Completá los datos correctamente")
    st.stop()

# PANTALLA B: SEGUIMIENTO (Se activa tras pedir)
if st.session_state.paso == 'seguimiento':
    st.title("📦 Seguimiento en tiempo real")
    placeholder = st.empty()
    
    while True:
        try:
            resp = requests.get(URL_PEDIDOS)
            df = pd.read_csv(StringIO(resp.text))
            # Filtramos por el teléfono del usuario actual
            res = df[df['TELEFONO'].astype(str) == str(st.session_state.user_tel)].iloc[-1]
            estado = res['ESTADO'].upper()
        except:
            estado = "PENDIENTE"

        with placeholder.container():
            st.markdown(f"""
                <div style="padding:30px; border-radius:15px; background-color:#fdfdfd; border:3px solid #E63946; text-align:center;">
                    <h2 style="margin:0;">Hola {st.session_state.user_name}</h2>
                    <p style="color:#666;">Tu pedido está:</p>
                    <h1 style="color:#E63946; font-size:45px;">{estado}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            if estado == "COCINANDO":
                st.success("👨‍🍳 ¡El local aceptó tu pedido y está en la cocina!")
            elif estado == "EN_CAMINO":
                st.warning("🛵 ¡Tu pedido ya salió! Atento para recibirlo.")
        
        time.sleep(15)
        st.rerun()

# PANTALLA C: MENÚ (Si no está en seguimiento)
st.title(f"Menú Digital")
df_prod = cargar_productos()

if not df_prod.empty:
    for idx, row in df_prod.iterrows():
        if str(row['DISPONIBLE']).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"$ {row['PRECIO']}")
                if c2.button("➕ Agregar", key=f"add_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast("Agregado")

# CIERRE DE PEDIDO
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Compra")
    detalle_msg = ""
    for p, q in st.session_state.carrito.items():
        st.write(f"**{q}x** {p}")
        detalle_msg += f"- {q}x {p}\n"
    
    entrega = st.radio("Entrega", ["Retiro", "Delivery"])
    direc = st.text_input("Dirección") if entrega == "Delivery" else "Retiro"
    
    if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
        msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n🏠 {direc}\n\n{detalle_msg}"
        enviar_telegram_confirmacion(msg, st.session_state.user_tel)
        # Nota: Aquí deberías guardar también en el Sheet (usando el .json cuando lo tengas)
        st.session_state.paso = 'seguimiento'
        st.rerun()

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs de lectura (Publicadas en la web)
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=TAB_ID_PEDIDOS" # ID de la hoja de pedidos

st.set_page_config(page_title="Pedidos Chamical", layout="centered")

# --- ESTILOS ---
st.markdown("""
    <style>
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #F8F9FA;
        border: 2px solid #E63946;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES ---
@st.cache_data(ttl=10)
def consultar_estado_pedido(tel_usuario):
    """Consulta el estado del pedido directamente en el Sheet"""
    try:
        resp = requests.get(URL_PEDIDOS)
        df = pd.read_csv(StringIO(resp.text))
        # Buscamos la última fila que coincida con el teléfono del usuario
        pedido_usuario = df[df['TELEFONO'].astype(str) == str(tel_usuario)].iloc[-1]
        return pedido_usuario['ESTADO']
    except:
        return "Pendiente"

# --- LÓGICA DE NAVEGACIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'

# PASO 1: LOGIN
if st.session_state.paso == 'login':
    st.title("🍔 Bienvenido")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono")
    if st.button("Ingresar al Menú"):
        if nombre and tel:
            st.session_state.user_name = nombre
            st.session_state.user_tel = tel
            st.session_state.paso = 'menu'
            st.rerun()
    st.stop()

# PASO 2: MENÚ (Simplificado para el ejemplo)
if st.session_state.paso == 'menu':
    st.title(f"Menú de {st.session_state.user_name}")
    # ... Aquí va tu lógica de carrito ...
    if st.button("🚀 Confirmar y Enviar Pedido"):
        # Aquí enviarías a Telegram (como ya lo tenés)
        # IMPORTANTE: El mensaje de Telegram debe avisarte que ya entró.
        st.session_state.paso = 'seguimiento'
        st.rerun()

# PASO 3: SEGUIMIENTO (LA CLAVE)
if st.session_state.paso == 'seguimiento':
    st.title("📦 Seguimiento de tu pedido")
    
    # Este bloque se refresca solo cada 30 segundos
    with st.container():
        estado = consultar_estado_pedido(st.session_state.user_tel)
        
        st.markdown(f"""
            <div class="status-card">
                <h3>Hola {st.session_state.user_name}</h3>
                <p>Tu pedido está actualmente:</p>
                <h1 style="color: #E63946;">{estado.upper()}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        if estado.upper() == "PENDIENTE":
            st.info("🕒 El local está recibiendo tu pedido...")
        elif estado.upper() == "COCINANDO":
            st.success("👨‍🍳 ¡Ya está en la cocina!")
        elif estado.upper() == "EN CAMINO":
            st.warning("🛵 El repartidor está en camino. ¡Atento a la puerta!")

        time.sleep(30) # Espera 30 segundos
        st.rerun() # Refresca la pantalla automáticamente

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

# !!! IMPORTANTE: Cambia el GID por el de tu pestaña PEDIDOS (ej: 45678912)
GID_PEDIDOS = "TU_GID_AQUI" 

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟")

# --- 2. FUNCIONES ---

def limpiar_precio(valor):
    """Convierte precios como '7.000' o '$8.500' en números enteros"""
    if pd.isna(valor): return 0
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

@st.cache_data(ttl=20)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

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

# --- 3. LÓGICA DE SESIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- PANTALLA: LOGIN ---
if st.session_state.paso == 'login':
    st.title("🍔 Bienvenido")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono (ej: 3826123456)")
    if st.button("Ingresar al Menú", use_container_width=True):
        if nombre and len(tel) > 7:
            st.session_state.user_name = nombre
            st.session_state.user_tel = tel
            st.session_state.paso = 'menu'
            st.rerun()
        else:
            st.error("Por favor, ingresa datos válidos.")
    st.stop()

# --- PANTALLA: SEGUIMIENTO ---
if st.session_state.paso == 'seguimiento':
    st.title("📦 Seguimiento de tu Pedido")
    placeholder = st.empty()
    while True:
        try:
            resp_peds = requests.get(URL_PEDIDOS)
            df_peds = pd.read_csv(StringIO(resp_peds.text))
            # Buscar la última fila que coincida con el teléfono
            res = df_peds[df_peds['TELEFONO'].astype(str).str.contains(str(st.session_state.user_tel))].iloc[-1]
            estado = res['ESTADO'].upper()
        except:
            estado = "PENDIENTE"
        
        with placeholder.container():
            st.markdown(f"""
                <div style="padding:20px; border-radius:10px; border:3px solid #E63946; text-align:center;">
                    <h3>Hola {st.session_state.user_name}</h3>
                    <p>Estado de tu pedido:</p>
                    <h1 style="color:#E63946;">{estado}</h1>
                </div>
            """, unsafe_allow_html=True)
            if estado == "COCINANDO": st.success("👨‍🍳 ¡Ya lo estamos preparando!")
            elif estado == "EN_CAMINO": st.warning("🛵 ¡El repartidor ya salió hacia tu casa!")
        
        time.sleep(20)
        st.rerun()

# --- PANTALLA: MENÚ ---
st.title("🍴 Nuestro Menú")
df_p = cargar_productos()

if not df_p.empty:
    for idx, row in df_p.iterrows():
        if str(row['DISPONIBLE']).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"**Precio: ${row['PRECIO']}**")
                if c2.button("➕ Agregar", key=f"btn_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast(f"Agregado: {row['PRODUCTO']}")

# --- CARRITO ---
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Carrito")
    resumen_txt = ""
    total_acumulado = 0
    
    for prod, cant in st.session_state.carrito.items():
        # Obtener precio limpio de la fila correspondiente
        fila = df_p[df_p['PRODUCTO'] == prod]
        if not fila.empty:
            p_unitario = limpiar_precio(fila['PRECIO'].iloc[0])
            subtotal = p_unitario * cant
            total_acumulado += subtotal
            st.write(f"**{cant}x** {prod} -- ${subtotal:,.0f}")
            resumen_txt += f"- {cant}x {prod}\n"

    entrega = st.radio("¿Cómo recibes?", ["Retiro en Local", "Delivery"])
    direc = st.text_input("Dirección de entrega") if entrega == "Delivery" else "Retiro"
    
    st.markdown(f"## TOTAL: ${total_acumulado:,.0f}")

    if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
        if entrega == "Delivery" and not direc:
            st.error("Falta la dirección de entrega")
        else:
            # 1. Enviar al Sheet vía Apps Script
            params = {
                "accion": "nuevo",
                "tel": st.session_state.user_tel,
                "nombre": st.session_state.user_name,
                "detalle": resumen_txt,
                "total": total_acumulado,
                "dir": direc
            }
            requests.get(URL_APPS_SCRIPT, params=params)
            
            # 2. Enviar a Telegram
            msg = f"🍔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n📍 {direc}\n\n{resumen_txt}\n💰 *TOTAL: ${total_acumulado:,.0f}*"
            enviar_telegram_botones(msg, st.session_state.user_tel)
            
            st.session_state.paso = 'seguimiento'
            st.rerun()

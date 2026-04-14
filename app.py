import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs de Google Sheets
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"
# URL para leer los pedidos realizados
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=TAB_ID_PEDIDOS" 

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIONES DE LÓGICA ---
def extraer_numero(precio_str):
    if pd.isna(precio_str): return 0
    solo_digitos = re.sub(r'[^\d]', '', str(precio_str))
    return int(solo_digitos) if solo_digitos else 0

def enviar_telegram_interactivo(mensaje, tel_cliente):
    """Envía el pedido con links de respuesta rápida para el dueño"""
    try:
        # Link para que el dueño le escriba al cliente por WhatsApp con un clic
        url_resp_wa = f"https://wa.me/{tel_cliente}?text=¡Hola! Recibimos tu pedido y ya lo estamos preparando."
        
        mensaje_final = f"{mensaje}\n\n🟢 *ACCIONES:* \n[📲 Responder al Cliente]({url_resp_wa})"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": mensaje_final, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=5)
    except:
        pass

@st.cache_data(ttl=20)
def cargar_datos():
    try:
        resp_p = requests.get(URL_PRODUCTOS, timeout=10)
        df_prod = pd.read_csv(StringIO(resp_p.text))
        df_prod.columns = [c.strip().upper() for c in df_prod.columns]
        
        resp_c = requests.get(URL_CONFIG, timeout=10)
        df_conf = pd.read_csv(StringIO(resp_c.text))
        conf = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_conf.iterrows()}
        return df_prod, conf
    except:
        return pd.DataFrame(), {}

# --- ESTADO DE SESIÓN ---
if 'user_auth' not in st.session_state: st.session_state.user_auth = False
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'pedido_enviado' not in st.session_state: st.session_state.pedido_enviado = False

df_prod, conf = cargar_datos()
nombre_local = conf.get("Nombre Negocio", "Mi Local")

# --- PANTALLA DE ACCESO ---
if not st.session_state.user_auth:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_local}</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("¡Bienvenido! Ingresá tus datos:")
        nombre = st.text_input("Nombre Completo")
        telefono = st.text_input("Teléfono (ej: 3826123456)")
        
        if st.button("Ver Menú", use_container_width=True):
            if nombre and len(telefono) > 7:
                st.session_state.user_name = nombre
                st.session_state.user_tel = telefono
                st.session_state.user_auth = True
                st.rerun()
            else:
                st.error("Datos incompletos")
    st.stop()

# --- INTERFAZ POST-PEDIDO (SEGUIMIENTO) ---
if st.session_state.pedido_enviado:
    st.success(f"¡Gracias {st.session_state.user_name}! Tu pedido fue enviado.")
    st.info("🕒 El comercio está revisando tu pedido. No cierres esta pestaña.")
    
    # Simulación de interacción (Para que sea real, se requiere gspread)
    st.markdown("### 📋 Estado de tu pedido")
    st.write("🟢 **Estado:** Recibido / Pendiente")
    
    if st.button("Hacer otro pedido"):
        st.session_state.pedido_enviado = False
        st.session_state.carrito = {}
        st.rerun()
    st.stop()

# --- MENÚ DE PRODUCTOS ---
st.markdown(f"### 👤 {st.session_state.user_name} | 📞 {st.session_state.user_tel}")
st.title(f"Menú Digital")

# Mostrar productos por categoría
df_vivos = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
cats = df_vivos['CATEGORIA'].unique()
tabs = st.tabs(list(cats))

for i, cat in enumerate(cats):
    with tabs[i]:
        items = df_vivos[df_vivos['CATEGORIA'] == cat]
        for idx, row in items.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(row['PRODUCTO'])
                    p_val = extraer_numero(row['PRECIO'])
                    st.markdown(f"**$ {p_val:,.0f}**")
                    if st.button("➕ Agregar", key=f"btn_{idx}"):
                        item_n = row['PRODUCTO']
                        if item_n in st.session_state.carrito:
                            st.session_state.carrito[item_n]['cant'] += 1
                        else:
                            st.session_state.carrito[item_n] = {'precio': p_val, 'cant': 1}
                        st.toast(f"Agregado: {item_n}")

# --- CARRITO ---
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Carrito")
    total = 0
    for k, v in list(st.session_state.carrito.items()):
        sub = v['precio'] * v['cant']
        total += sub
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{k}**")
        nueva_q = c2.number_input("C", 0, 50, v['cant'], key=f"q_{k}", label_visibility="collapsed")
        if nueva_q != v['cant']:
            if nueva_q == 0: del st.session_state.carrito[k]
            else: st.session_state.carrito[k]['cant'] = nueva_q
            st.rerun()
        c3.write(f"${sub:,.0f}")

    tipo = st.radio("Entrega", ["Retiro en Local", "Delivery"])
    direc = st.text_input("Dirección *") if tipo == "Delivery" else "Retiro en local"
    costo_d = extraer_numero(conf.get("Costo Delivery", "0")) if tipo == "Delivery" else 0
    
    total_final = total + costo_d
    st.markdown(f"## TOTAL: ${total_final:,.0f}")

    if st.button("🚀 ENVIAR PEDIDO AL COMERCIO", type="primary", use_container_width=True):
        if tipo == "Delivery" and not direc:
            st.error("Falta la dirección")
        else:
            # Formatear detalle
            detalle = "\n".join([f"- {v['cant']}x {k}" for k, v in st.session_state.carrito.items()])
            mensaje_t = (
                f"🍔 *NUEVO PEDIDO*\n"
                f"━━━━━━━━━━━━━━\n"
                f"👤 *Cliente:* {st.session_state.user_name}\n"
                f"📞 *Tel:* {st.session_state.user_tel}\n"
                f"🏠 *Dirección:* {direc}\n"
                f"━━━━━━━━━━━━━━\n"
                f"{detalle}\n"
                f"━━━━━━━━━━━━━━\n"
                f"💰 *TOTAL:* ${total_final:,.0f}"
            )
            
            # Enviar a Telegram
            enviar_telegram_interactivo(mensaje_t, st.session_state.user_tel)
            
            # Cambiar estado
            st.session_state.pedido_enviado = True
            st.rerun()

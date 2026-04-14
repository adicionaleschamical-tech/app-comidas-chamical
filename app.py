import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DESDE TU SHEET Y BOT ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365" 
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

# Tokens de tu Bot de Telegram
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs de Google
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(StringIO(resp.text), header=None)
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    if pd.isna(texto): return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, data=payload, timeout=10)
    except: st.error("Error al notificar por Telegram.")

# --- 3. INICIALIZACIÓN ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Mi Comercio')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. VISTAS ---

# --- INICIO ---
if st.session_state.vista == 'inicio':
    st.title(f"🍔 {nombre_local}")
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

# --- RASTREO ---
elif st.session_state.vista == 'rastreo':
    st.subheader("Estado de tu Pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI:")
    if st.button("Consultar"):
        df_peds = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
        df_peds.columns = [c.strip().upper() for c in df_peds.columns]
        dni_l = re.sub(r'[^\d]', '', str(dni_input))
        df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
        res = df_peds[df_peds['DNI_L'] == dni_l].tail(1)
        if not res.empty:
            st.info(f"Hola {res.iloc[0]['NOMBRE']}, tu pedido está: **{res.iloc[0]['ESTADO']}**")
        else: st.warning("No se encontró el DNI.")

# --- MENÚ Y COMPRA ---
elif st.session_state.vista == 'pedir':
    if st.button("⬅ Volver al Inicio"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            n = st.text_input("Nombre completo"); d = st.text_input("DNI")
            if st.button("Ingresar"):
                if n and d.isdigit():
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    df_p = pd.read_csv(f"{URL_PRODUCTOS}&cb={int(time.time())}")
    df_p.columns = [c.strip().upper() for c in df_p.columns]

    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                st.subheader(row['PRODUCTO'])
                v_noms = str(row['VARIEDADES']).split(';')
                v_ings = str(row['INGREDIENTES']).split(';')
                v_pres = str(row['PRECIO']).split(';')

                tabs = st.tabs([v.strip() for v in v_noms])
                for i, tab in enumerate(tabs):
                    with tab:
                        nom_v = v_noms[i].strip()
                        pre_v = limpiar_precio(v_pres[i])
                        st.write(f"_{v_ings[i].strip() if i < len(v_ings) else ''}_")
                        st.write(f"**Precio: {formatear_moneda(pre_v)}**")
                        
                        item_id = f"{row['PRODUCTO']} ({nom_v})"
                        cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                        
                        col1, col2, col3 = st.columns([1,1,1])
                        if col1.button("➖", key=f"m_{item_id}") and cant > 0:
                            st.session_state.carrito[item_id]['cant'] -= 1
                            if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                            st.rerun()
                        col2.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                        if col3.button("➕", key=f"p_{item_id}"):
                            st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre_v}
                            st.rerun()

    # --- CARRITO FLOTANTE ---
    if st.session_state.carrito:
        st.write("---")
        st.header("🛒 Tu Carrito")
        total_pedido = 0
        resumen_texto = ""
        
        for item, info in st.session_state.carrito.items():
            subtotal = info['cant'] * info['precio']
            total_pedido += subtotal
            resumen_texto += f"• {info['cant']}x {item}\n"
            st.write(f"{info['cant']}x {item} — {formatear_moneda(subtotal)}")
        
        envio = st.radio("Método de entrega:", ["Retiro en Local", "Delivery"])
        final = total_pedido + (costo_delivery if envio == "Delivery" else 0)
        st.subheader(f"TOTAL A PAGAR: {formatear_moneda(final)}")
        
        if st.button("🚀 ENVIAR PEDIDO POR TELEGRAM", use_container_width=True, type="primary"):
            # 1. Preparar mensaje para Telegram
            msg = f"🔔 *NUEVO PEDIDO*\n\n👤 *Cliente:* {st.session_state.user_name}\n🆔 *DNI:* {st.session_state.user_dni}\n🛵 *Entrega:* {envio}\n\n*Detalle:*\n{resumen_texto}\n💰 *TOTAL:* {formatear_moneda(final)}"
            
            # 2. Enviar a Google Sheets (para el rastreo)
            try:
                params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":resumen_texto, "total":final, "dir":envio}
                requests.get(URL_APPS_SCRIPT, params=params, timeout=10)
            except: pass
            
            # 3. Enviar a Telegram
            enviar_telegram(msg)
            
            st.success("¡Pedido enviado con éxito!")
            st.session_state.carrito = {}
            time.sleep(2)
            st.session_state.vista = 'inicio'; st.rerun()

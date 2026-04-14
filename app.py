import streamlit as st
import pandas as pd  # <--- Corregido: antes decía 'import pd'
import requests
import time
import re
from io import StringIO
import json

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365" 
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# --- FUNCIONES ---
@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}")
        df = pd.read_csv(StringIO(resp.text), header=None)
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- INICIO ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Lomitos El Caniche')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- NAVEGACIÓN ---
if st.session_state.vista == 'inicio':
    st.title(f"🍔 {nombre_local}")
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

elif st.session_state.vista == 'rastreo':
    st.subheader("Estado de tu pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    dni_in = st.text_input("DNI:")
    if st.button("Buscar"):
        df = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
        df.columns = [c.strip().upper() for c in df.columns]
        dni_l = re.sub(r'[^\d]', '', str(dni_in))
        df['DNI_L'] = df['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
        res = df[df['DNI_L'] == dni_l].tail(1)
        if not res.empty:
            st.info(f"Hola {res.iloc[0]['NOMBRE']}, estado: **{res.iloc[0]['ESTADO']}**")
        else: st.warning("No se encontró el pedido.")

elif st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    if 'user_dni' not in st.session_state:
        n = st.text_input("Nombre"); d = st.text_input("DNI")
        if st.button("Ingresar"):
            if n and d.isdigit():
                st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    df_p = pd.read_csv(f"{URL_PRODUCTOS}&cb={int(time.time())}")
    df_p.columns = [c.strip().upper() for c in df_p.columns]

    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                st.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/300")
                st.subheader(row['PRODUCTO'])
                v_noms = str(row['VARIEDADES']).split(';')
                v_ings = str(row['INGREDIENTES']).split(';')
                v_pres = str(row['PRECIO']).split(';')
                
                tabs = st.tabs([v.strip() for v in v_noms])
                for i, tab in enumerate(tabs):
                    with tab:
                        nom_v = v_noms[i].strip()
                        pre_v = limpiar_precio(v_pres[i])
                        st.write(f"_{v_ings[i].strip()}_")
                        st.write(f"### {formatear_moneda(pre_v)}")
                        item_id = f"{row['PRODUCTO']} ({nom_v})"
                        cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                        c1, c2, c3 = st.columns(3)
                        if c1.button("➖", key=f"m_{item_id}") and cant > 0:
                            st.session_state.carrito[item_id]['cant'] -= 1
                            if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                            st.rerun()
                        c2.write(f"Cant: {cant}")
                        if c3.button("➕", key=f"p_{item_id}"):
                            st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre_v}
                            st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Resumen")
        total_p = 0
        detalle_txt = ""
        for item, datos in st.session_state.carrito.items():
            sub = datos['cant'] * datos['precio']
            total_p += sub
            detalle_txt += f"{datos['cant']}x {item}, "
            st.write(f"**{datos['cant']}x** {item} - {formatear_moneda(sub)}")
        
        metodo = st.radio("Entrega:", ["Retiro", "Delivery"])
        dir_envio = "Retiro en Local"
        if metodo == "Delivery":
            dir_envio = st.text_input("🏠 Dirección:")
            total_p += costo_delivery
            
        if st.button("🚀 CONFIRMAR PEDIDO", use_container_width=True, type="primary"):
            if metodo == "Delivery" and not dir_envio:
                st.error("Falta dirección")
            else:
                # 1. Guardar en Sheets
                params = {"accion": "nuevo", "tel": st.session_state.user_dni, "nombre": st.session_state.user_name, "detalle": detalle_txt, "total": total_p, "dir": dir_envio}
                requests.get(URL_APPS_SCRIPT, params=params)
                
                # 2. Telegram con Botones para el dueño
                keyboard = {
                    "inline_keyboard": [[
                        {"text": "✅ Aceptar", "callback_data": f"est_Preparando_{st.session_state.user_dni}"},
                        {"text": "🛵 En Camino", "callback_data": f"est_Enviado_{st.session_state.user_dni}"},
                        {"text": "🏁 Listo", "callback_data": f"est_Listo_{st.session_state.user_dni}"}
                    ]]
                }
                msg = f"🔔 *PEDIDO*\n👤 {st.session_state.user_name}\n📍 {dir_envio}\n📝 {detalle_txt}\n💰 *TOTAL: {formatear_moneda(total_p)}*"
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                              data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)})
                
                st.success("¡Pedido enviado!")
                st.session_state.carrito = {}; time.sleep(2); st.session_state.vista = 'inicio'; st.rerun()

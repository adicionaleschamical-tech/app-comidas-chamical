import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import json

# --- 1. CONFIGURACIÓN ---
# Asegúrate de que estos IDs coincidan con tu Google Sheet
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

# --- 2. FUNCIONES DE APOYO ---
@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(StringIO(resp.text), header=None)
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "": return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. INICIALIZACIÓN ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Cargando...')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. VISTAS ---

# --- PANTALLA DE INICIO ---
if st.session_state.vista == 'inicio':
    st.title(f"🍔 {nombre_local}")
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR MI DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

# --- PANTALLA DE RASTREO ---
elif st.session_state.vista == 'rastreo':
    st.subheader("Estado de tu pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    dni_input = st.text_input("Ingresá tu DNI:")
    if st.button("Buscar"):
        try:
            df_peds = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
            df_peds.columns = [c.strip().upper() for c in df_peds.columns]
            dni_l = re.sub(r'[^\d]', '', str(dni_input))
            df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
            res = df_peds[df_peds['DNI_L'] == dni_l].tail(1)
            if not res.empty:
                st.success(f"Hola {res.iloc[0]['NOMBRE']}, tu pedido está: **{res.iloc[0]['ESTADO']}**")
            else: st.warning("No se encontró el DNI.")
        except: st.error("Error al conectar con la base de datos.")

# --- PANTALLA DE MENÚ ---
elif st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            n = st.text_input("Nombre completo")
            d = st.text_input("DNI (solo números)")
            if st.button("Ingresar al Menú"):
                if n and d.isdigit():
                    st.session_state.user_name = n
                    st.session_state.user_dni = d
                    st.rerun()
                else: st.error("Por favor completá los datos.")
        st.stop()

    # Carga de Productos
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}")
        df_p = pd.read_csv(StringIO(resp_p.text))
        df_p.columns = [c.strip().upper() for c in df_p.columns]

        for _, row in df_p.iterrows():
            if str(row.get('DISPONIBLE', '')).upper() == "SI":
                with st.container(border=True):
                    # Foto
                    img_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/400x200?text=Sin+Imagen"
                    st.image(img_url, use_container_width=True)
                    st.subheader(row['PRODUCTO'])
                    
                    # Variedades (Seguridad IndexError)
                    v_noms = str(row['VARIEDADES']).split(';')
                    v_ings = str(row['INGREDIENTES']).split(';')
                    v_pres = str(row['PRECIO']).split(';')

                    tabs = st.tabs([v.strip() for v in v_noms])
                    for i, tab in enumerate(tabs):
                        with tab:
                            nom_v = v_noms[i].strip()
                            pre_v = limpiar_precio(v_pres[i]) if i < len(v_pres) else 0
                            
                            if i < len(v_ings):
                                st.info(f"✨ {v_ings[i].strip()}")
                            else:
                                st.info("✨ Sin descripción")
                                
                            st.write(f"### {formatear_moneda(pre_v)}")
                            
                            item_id = f"{row['PRODUCTO']} ({nom_v})"
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            
                            c1, c2, c3 = st.columns([1,1,1])
                            if c1.button("➖", key=f"m_{item_id}") and cant > 0:
                                st.session_state.carrito[item_id]['cant'] -= 1
                                if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                st.rerun()
                            c2.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                            if c3.button("➕", key=f"p_{item_id}"):
                                st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre_v}
                                st.rerun()
    except Exception as e:
        st.error(f"Error al cargar menú: {e}")

    # --- CARRITO Y ENVÍO ---
    if st.session_state.carrito:
        st.markdown("---")
        st.header("🛒 Resumen de tu Pedido")
        
        total_productos = 0
        detalle_para_envio = ""
        for item, datos in st.session_state.carrito.items():
            subtotal = datos['cant'] * datos['precio']
            total_productos += subtotal
            detalle_para_envio += f"• {datos['cant']}x {item}\n"
            st.write(f"**{datos['cant']}x** {item} → {formatear_moneda(subtotal)}")
        
        metodo_entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        direccion = "Retiro en Local"
        cargo_envio = 0
        
        if metodo_entrega == "Delivery":
            cargo_envio = costo_delivery
            direccion = st.text_input("🏠 Dirección de entrega:")
            st.warning(f"Costo de envío: {formatear_moneda(cargo_envio)}")

        total_final = total_productos + cargo_envio
        st.markdown(f"## TOTAL A PAGAR: {formatear_moneda(total_final)}")
        
        if st.button("🚀 CONFIRMAR Y ENVIAR", use_container_width=True, type="primary"):
            if metodo_entrega == "Delivery" and (not direccion or direccion == "Retiro en Local"):
                st.error("Por favor, ingresá una dirección.")
            else:
                # Registro en Sheets
                params = {"accion": "nuevo", "tel": st.session_state.user_dni, "nombre": st.session_state.user_name, "detalle": detalle_para_envio, "total": total_final, "dir": direccion}
                requests.get(URL_APPS_SCRIPT, params=params)
                
                # Telegram con Botones
                keyboard = {
                    "inline_keyboard": [[
                        {"text": "✅ Aceptar", "callback_data": f"est_Preparando_{st.session_state.user_dni}"},
                        {"text": "🛵 En Camino", "callback_data": f"est_Enviado_{st.session_state.user_dni}"},
                        {"text": "🏁 Listo", "callback_data": f"est_Listo_{st.session_state.user_dni}"}
                    ]]
                }
                msg = (f"🔔 *NUEVO PEDIDO*\n\n👤 *Cliente:* {st.session_state.user_name}\n🆔 *DNI:* {st.session_state.user_dni}\n📍 *Dirección:* {direccion}\n\n*Detalle:*\n{detalle_para_envio}\n💰 *TOTAL: {formatear_moneda(total_final)}*")
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                              data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)})
                
                st.success("¡Pedido enviado correctamente!")
                st.session_state.carrito = {}
                time.sleep(2)
                st.session_state.vista = 'inicio'; st.rerun()

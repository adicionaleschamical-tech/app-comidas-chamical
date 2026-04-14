import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365" 
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# --- 2. FUNCIONES ---
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

# --- 3. INICIO ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Lomitos El Caniche')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. NAVEGACIÓN ---
if st.session_state.vista == 'inicio':
    st.title(nombre_local)
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

elif st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.write("### Identificación")
            n = st.text_input("Nombre"); d = st.text_input("DNI (sin puntos)")
            if st.button("Ver Menú"):
                if n and d:
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # --- LISTADO DE PRODUCTOS ---
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}")
        df_p = pd.read_csv(StringIO(resp_p.text))
        df_p.columns = [c.strip().upper() for c in df_p.columns]

        for _, row in df_p.iterrows():
            if str(row.get('DISPONIBLE', '')).upper() == "SI":
                with st.container(border=True):
                    # Título y Foto Principal
                    st.header(row['PRODUCTO'])
                    img_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/300"
                    st.image(img_url, use_container_width=True)
                    
                    # Separación de Variedades
                    v_nombres = [v.strip() for v in str(row['VARIEDADES']).split(';')]
                    v_ingreds = [i.strip() for i in str(row['INGREDIENTES']).split(';')]
                    v_precios = [p.strip() for p in str(row['PRECIO']).split(';')]

                    # CREACIÓN DE BOTONES (TABS) PARA CADA VARIEDAD
                    tabs = st.tabs(v_nombres)
                    
                    for i, tab in enumerate(tabs):
                        with tab:
                            nom_v = v_nombres[i]
                            ing_v = v_ingreds[i] if i < len(v_ingreds) else "Sin descripción"
                            pre_v = limpiar_precio(v_precios[i]) if i < len(v_precios) else 0
                            item_id = f"{row['PRODUCTO']} - {nom_v}"
                            
                            st.write(f"**Ingredientes:** {ing_v}")
                            st.subheader(formatear_moneda(pre_v))
                            
                            # Controles de cantidad
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            col1, col2, col3 = st.columns([1, 1, 1])
                            
                            if col1.button("➖", key=f"m_{item_id}"):
                                if cant > 0:
                                    st.session_state.carrito[item_id]['cant'] -= 1
                                    if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                    st.rerun()
                            
                            col2.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                            
                            if col3.button("➕", key=f"p_{item_id}"):
                                st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre_v}
                                st.rerun()
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")

    # --- BOTÓN FLOTANTE DE RESUMEN ---
    if st.session_state.carrito:
        st.write("---")
        total = sum(v['cant'] * v['precio'] for v in st.session_state.carrito.values())
        st.markdown(f"## Total Carrito: {formatear_moneda(total)}")
        
        if st.button("🚀 CONFIRMAR PEDIDO", use_container_width=True, type="primary"):
            detalle_final = "\n".join([f"{v['cant']}x {k}" for k, v in st.session_state.carrito.items()])
            # Enviar a Google y Telegram
            requests.get(URL_APPS_SCRIPT, params={"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle_final, "total":total, "dir":"Local"})
            st.session_state.carrito = {}
            st.success("¡Pedido enviado correctamente!")
            time.sleep(2)
            st.session_state.vista = 'inicio'
            st.rerun()

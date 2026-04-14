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

st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="wide") # Cambiado a wide para mejor espacio

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
        n = st.text_input("Nombre"); d = st.text_input("DNI")
        if st.button("Ingresar"):
            st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # --- PRODUCTOS ---
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}")
        df_p = pd.read_csv(StringIO(resp_p.text))
        df_p.columns = [c.strip().upper() for c in df_p.columns]

        for _, row in df_p.iterrows():
            if str(row.get('DISPONIBLE', '')).upper() == "SI":
                st.markdown(f"## ─── {row['PRODUCTO']} ───")
                
                # Columnas: Izquierda Foto, Derecha Variedades
                col_foto, col_variedades = st.columns([1, 2])
                
                with col_foto:
                    img_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/300"
                    st.image(img_url, use_container_width=True)

                with col_variedades:
                    # Separamos las listas por punto y coma (;)
                    v_nombres = str(row['VARIEDADES']).split(';')
                    v_ingreds = str(row['INGREDIENTES']).split(';')
                    v_precios = str(row['PRECIO']).split(';')

                    for i in range(len(v_nombres)):
                        nom = v_nombres[i].strip()
                        ing = v_ingreds[i].strip() if i < len(v_ingreds) else ""
                        pre = limpiar_precio(v_precios[i]) if i < len(v_precios) else 0
                        item_id = f"{row['PRODUCTO']} - {nom}"

                        # Cada variedad en su propio recuadro blanco
                        with st.container(border=True):
                            c_info, c_cant = st.columns([2, 1])
                            with c_info:
                                st.markdown(f"**{nom}**")
                                if ing: st.caption(ing)
                                st.markdown(f"**{formatear_moneda(pre)}**")
                            
                            with c_cant:
                                cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                                col_m, col_v, col_p = st.columns([1, 1, 1])
                                if col_m.button("➖", key=f"m_{item_id}"):
                                    if cant > 0:
                                        st.session_state.carrito[item_id]['cant'] -= 1
                                        if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                        st.rerun()
                                col_v.write(f"**{cant}**")
                                if col_p.button("➕", key=f"p_{item_id}"):
                                    st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre}
                                    st.rerun()
    except:
        st.error("No se pudo cargar el menú. Revisá la pestaña Productos.")

    # --- CARRITO ---
    if st.session_state.carrito:
        st.write("---")
        total = sum(v['cant'] * v['precio'] for v in st.session_state.carrito.values())
        st.subheader(f"🛒 Total: {formatear_moneda(total)}")
        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True, type="primary"):
            det = "\n".join([f"{v['cant']}x {k}" for k, v in st.session_state.carrito.items()])
            requests.get(URL_APPS_SCRIPT, params={"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":det, "total":total, "dir":"Local"})
            st.session_state.carrito = {}; st.session_state.vista = 'inicio'; st.success("¡Pedido enviado!"); time.sleep(2); st.rerun()

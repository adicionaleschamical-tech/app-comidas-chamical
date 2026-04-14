import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE ENLACES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365" 
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# --- 2. FUNCIONES DE CARGA ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}")
        df = pd.read_csv(StringIO(resp.text), header=None)
        # Toma el nombre del local y otros datos de la pestaña CONFIG
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. LOGICA DE NAVEGACIÓN ---

conf = cargar_config()
nombre_sitio = conf.get('Nombre_Local', 'Cargando...') # Se saca del Sheet

st.set_page_config(page_title=nombre_sitio, page_icon="🍔")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. VISTAS ---

# --- INICIO ---
if st.session_state.vista == 'inicio':
    st.title(nombre_sitio)
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

# --- RASTREO POR DNI ---
elif st.session_state.vista == 'rastreo':
    st.subheader("Rastreo de Pedidos")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI:")
    if st.button("Buscar Estado"):
        resp = requests.get(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
        df_peds = pd.read_csv(StringIO(resp.text))
        df_peds.columns = [c.strip().upper() for c in df_peds.columns]
        
        # Limpiamos DNI para comparar
        dni_buscado = re.sub(r'[^\d]', '', str(dni_input))
        df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
        
        resultado = df_peds[df_peds['DNI_L'] == dni_buscado].tail(1)
        
        if not resultado.empty:
            res = resultado.iloc[0]
            st.success(f"Hola {res['NOMBRE']}, tu pedido está: **{res['ESTADO']}**")
            st.write(f"Detalle: {res['DETALLE']}")
        else:
            st.warning("No hay pedidos registrados con ese DNI.")

# --- COMPRA CON SELECCIÓN DE VARIEDAD ---
elif st.session_state.vista == 'pedir':
    if st.button("⬅ Atrás"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.write("Identificación de Cliente")
            n = st.text_input("Nombre"); d = st.text_input("DNI")
            if st.button("Ingresar al Menú"):
                if n and d.isdigit():
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # Carga de productos dinámica
    resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}")
    df_p = pd.read_csv(StringIO(resp_p.text))
    df_p.columns = [c.strip().upper() for c in df_p.columns]

    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                st.header(row['PRODUCTO'])
                st.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150", width=150)
                
                # Listas separadas por punto y coma
                v_list = [v.strip() for v in str(row['VARIEDADES']).split(';')]
                i_list = [i.strip() for i in str(row['INGREDIENTES']).split(';')]
                p_list = [p.strip() for p in str(row['PRECIO']).split(';')]

                # Pestañas para cada variedad
                tabs = st.tabs(v_list)
                for i, tab in enumerate(tabs):
                    with tab:
                        st.write(f"**Ingredientes:** {i_list[i] if i < len(i_list) else ''}")
                        precio_v = limpiar_precio(p_list[i]) if i < len(p_list) else 0
                        st.subheader(formatear_moneda(precio_v))
                        
                        item_id = f"{row['PRODUCTO']} - {v_list[i]}"
                        cant = st.session_state.carrito.get(item_id, 0)
                        
                        c1, c2, c3 = st.columns(3)
                        if c1.button("➖", key=f"m_{item_id}"):
                            if cant > 0: st.session_state.carrito[item_id] -= 1; st.rerun()
                        c2.write(f"Cant: {cant}")
                        if c3.button("➕", key=f"p_{item_id}"):
                            st.session_state.carrito[item_id] = cant + 1; st.rerun()

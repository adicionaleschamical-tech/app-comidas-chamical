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

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"

# --- 2. FUNCIONES DE LIMPIEZA ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        resp.encoding = 'utf-8'
        df = pd.read_csv(StringIO(resp.text), header=None)
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    """Extrae solo los números de un texto."""
    if pd.isna(texto): return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. INICIO ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Venta de Comidas')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔")

if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'vista' not in st.session_state: st.session_state.vista = 'inicio'

# --- 4. VISTA PEDIDOS CON VARIEDADES ---

if st.session_state.vista == 'inicio':
    if st.button("🍔 VER MENÚ Y PEDIR", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()

if st.session_state.vista == 'pedir':
    st.title(f"Menú de {nombre_local}")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()

    try:
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&cb={int(time.time())}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]

        for _, row in df_p.iterrows():
            if str(row.get('DISPONIBLE', '')).upper() == "SI":
                with st.container(border=True):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        img = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150"
                        st.image(img, use_container_width=True)

                    with col2:
                        st.subheader(row['PRODUCTO'])
                        
                        # PROCESAR VARIEDADES (Separadas por ;)
                        variedades = str(row['VARIEDADES']).split(';')
                        ingredientes = str(row['INGREDIENTES']).split(';')
                        precios = str(row['PRECIO']).split(';')

                        # Iterar sobre cada variedad de la misma fila
                        for i in range(len(variedades)):
                            v_nombre = variedades[i].strip()
                            v_ingred = ingredientes[i].strip() if i < len(ingredientes) else ""
                            v_precio = limpiar_precio(precios[i]) if i < len(precios) else 0
                            
                            # Identificador único para el carrito
                            item_id = f"{row['PRODUCTO']} ({v_nombre})"
                            
                            with st.expander(f"{v_nombre} - {formatear_moneda(v_precio)}"):
                                if v_ingred:
                                    st.write(f"*{v_ingred}*")
                                
                                # Botonera de cantidad
                                cant = st.session_state.carrito.get(item_id, 0)
                                c_btn1, c_cant, c_btn2 = st.columns([1, 1, 1])
                                
                                if c_btn1.button("➖", key=f"menos_{item_id}"):
                                    if cant > 0:
                                        st.session_state.carrito[item_id] = cant - 1
                                        if st.session_state.carrito[item_id] == 0: del st.session_state.carrito[item_id]
                                        st.rerun()
                                
                                c_cant.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                                
                                if c_btn2.button("➕", key=f"mas_{item_id}"):
                                    st.session_state.carrito[item_id] = cant + 1
                                    st.rerun()

        # BARRA FLOTANTE DE TOTAL
        if st.session_state.carrito:
            st.write("---")
            st.subheader("🛒 Tu Carrito")
            total = 0
            for item, q in st.session_state.carrito.items():
                # Buscamos el precio en el dataframe para el total
                # (Simplificado: el precio se guarda en el carrito o se busca aquí)
                st.write(f"{q}x {item}")
            st.info("Al confirmar, se enviará el detalle por WhatsApp/Telegram.")

    except Exception as e:
        st.error(f"Error en el menú: {e}")

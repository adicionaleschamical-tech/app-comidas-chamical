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

# --- 2. FUNCIONES DE PROCESAMIENTO ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        # Forzamos refresco de caché de Google
        url_fresca = f"{URL_CONFIG}&cb={int(time.time())}"
        resp = requests.get(url_fresca, timeout=10)
        resp.encoding = 'utf-8'
        
        # Leemos el CSV
        df = pd.read_csv(StringIO(resp.text), header=None)
        
        # SEGURIDAD: Verificamos que el DataFrame tenga al menos 2 columnas
        if df.shape[1] < 2:
            st.error("⚠️ Error en la pestaña CONFIG: Se esperaba al menos 2 columnas (Parámetro y Valor).")
            return {}

        config_dict = {}
        for _, row in df.iterrows():
            # Solo procesamos si la fila tiene al menos 2 celdas con datos
            if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                clave = str(row[0]).strip()
                valor = str(row[1]).strip()
                config_dict[clave] = valor
        return config_dict
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        return {}

def cargar_datos(url):
    try:
        resp = requests.get(f"{url}&cb={int(time.time())}", timeout=10)
        resp.encoding = 'utf-8'
        return pd.read_csv(StringIO(resp.text))
    except: return pd.DataFrame()

def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "": return 0
    # Eliminamos todo lo que no sea número
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. INICIALIZACIÓN ---
conf = cargar_config()

# Valores por defecto por si falla la carga
nombre_local = conf.get('Nombre_Local', 'Lomitos El Caniche')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))
direccion_local = conf.get('Direccion Local', '')

st.set_page_config(page_title=nombre_local, page_icon="🍔")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. INTERFAZ ---

st.title(f"🍔 {nombre_local}")
if direccion_local: st.caption(f"📍 {direccion_local}")
st.write("---")

# VISTA: INICIO
if st.session_state.vista == 'inicio':
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR MI DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

# VISTA: RASTREO
elif st.session_state.vista == 'rastreo':
    st.subheader("Estado de tu pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI:", value=st.session_state.get('user_dni', ""))
    if st.button("Buscar"):
        df_peds = cargar_datos(URL_PEDIDOS_BASE)
        if not df_peds.empty:
            df_peds.columns = [c.strip().upper() for c in df_peds.columns]
            dni_busq = re.sub(r'[^\d]', '', str(dni_input))
            # Limpieza de columna DNI
            df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[^\d]', '', regex=True)
            
            res = df_peds[df_peds['DNI_L'] == dni_busq].tail(1)
            if not res.empty:
                st.success(f"Hola {res.iloc[0]['NOMBRE']}, tu pedido está: **{res.iloc[0]['ESTADO']}**")
                st.write(f"Detalle: {res.iloc[0]['DETALLE']}")
            else: st.warning("No hay pedidos con ese DNI.")

# VISTA: PEDIR
elif st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            n = st.text_input("Nombre")
            d = st.text_input("DNI (solo números)")
            if st.button("Continuar"):
                if n and d.isdigit():
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    df_prod = cargar_datos(URL_PRODUCTOS)
    if not df_prod.empty:
        df_prod.columns = [c.strip().upper() for c in df_prod.columns]
        
        for _, row in df_prod.iterrows():
            if str(row.get('DISPONIBLE', '')).upper() == "SI":
                with st.container(border=True):
                    col1, col2 = st.columns([1, 2])
                    col1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                    
                    with col2:
                        st.subheader(row['PRODUCTO'])
                        # Procesar listas separadas por punto y coma
                        vars = str(row['VARIEDADES']).split(';')
                        pres = str(row['PRECIO']).split(';')
                        ings = str(row['INGREDIENTES']).split(';')

                        for i in range(len(vars)):
                            nombre_v = vars[i].strip()
                            # Asignamos precio individual o 0 si no existe
                            precio_v = limpiar_precio(pres[i]) if i < len(pres) else 0
                            ingred_v = ings[i].strip() if i < len(ings) else ""
                            
                            item_id = f"{row['PRODUCTO']} ({nombre_v})"
                            
                            with st.expander(f"{nombre_v} - {formatear_moneda(precio_v)}"):
                                if ingred_v: st.caption(ingred_v)
                                
                                cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                                b1, b_txt, b2 = st.columns([1,1,1])
                                if b1.button("➖", key=f"m_{item_id}"):
                                    if cant > 0:
                                        st.session_state.carrito[item_id]['cant'] = cant - 1
                                        if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                        st.rerun()
                                b_txt.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                                if b2.button("➕", key=f"p_{item_id}"):
                                    st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': precio_v}
                                    st.rerun()

    if st.session_state.carrito:
        st.write("---")
        total_p = sum(d['cant'] * d['precio'] for d in st.session_state.carrito.values())
        metodo = st.radio("Envío:", ["Retiro", "Delivery"])
        final = total_p + (costo_delivery if metodo == "Delivery" else 0)
        
        st.markdown(f"### TOTAL: {formatear_moneda(final)}")
        if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
            detalle = "\n".join([f"- {d['cant']}x {k}" for k, d in st.session_state.carrito.items()])
            
            # Apps Script y Telegram
            try:
                params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle, "total":final, "dir":metodo}
                requests.get(URL_APPS_SCRIPT, params=params)
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": f"🔔 NUEVO: {st.session_state.user_name}\n{detalle}\n💰 {formatear_moneda(final)}", "parse_mode": "Markdown"})
                
                st.session_state.carrito = {}
                st.session_state.vista = 'rastreo'
                st.rerun()
            except:
                st.error("Error al enviar pedido. Intentá de nuevo.")

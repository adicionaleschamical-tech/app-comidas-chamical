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

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        resp.encoding = 'utf-8'
        df = pd.read_csv(StringIO(resp.text), header=None)
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    if pd.isna(texto): return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. PROCESAMIENTO INICIAL ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Lomitos El Caniche')
direccion_local = conf.get('Direccion Local', 'Chamical, La Rioja')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. ENCABEZADO ---
st.title(f"🍔 {nombre_local}")
if direccion_local: st.caption(f"📍 {direccion_local}")
st.write("---")

# --- 5. VISTAS ---

# VISTA: INICIO
if st.session_state.vista == 'inicio':
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

# VISTA: RASTREO POR DNI
if st.session_state.vista == 'rastreo':
    st.subheader("Rastrea tu pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI (sin puntos):")
    if st.button("Buscar Estado"):
        if dni_input:
            try:
                # Buscamos en la pestaña de Pedidos
                resp = requests.get(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
                df_peds = pd.read_csv(StringIO(resp.text))
                df_peds.columns = [c.strip().upper() for c in df_peds.columns]
                
                # Limpiar el DNI de la base y el input para comparar
                dni_buscado = re.sub(r'[^\d]', '', str(dni_input))
                df_peds['DNI_LIMPIO'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[^\d]', '', regex=True)
                
                # Filtrar el último pedido de ese DNI
                resultado = df_peds[df_peds['DNI_LIMPIO'] == dni_buscado].tail(1)
                
                if not resultado.empty:
                    res = resultado.iloc[0]
                    st.success(f"¡Hola {res['NOMBRE']}!")
                    st.info(f"Estado actual: **{res['ESTADO']}**")
                    with st.expander("Ver detalle del pedido"):
                        st.write(res['DETALLE'])
                        st.write(f"**Total: {formatear_moneda(limpiar_precio(res['TOTAL']))}**")
                else:
                    st.warning("No se encontraron pedidos recientes con ese DNI.")
            except Exception as e:
                st.error("Error al conectar con la base de datos.")
        else:
            st.error("Por favor, ingresá un DNI.")

# VISTA: PEDIR (CON VARIEDADES ;)
if st.session_state.vista == 'pedir':
    if st.button("⬅ Volver al Inicio"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.write("Identificate para continuar:")
            n = st.text_input("Nombre Completo")
            d = st.text_input("DNI")
            if st.button("Ingresar"):
                if n and d.isdigit():
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # Carga de Productos
    df_p = pd.read_csv(f"{URL_PRODUCTOS}&cb={int(time.time())}")
    df_p.columns = [c.strip().upper() for c in df_p.columns]

    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                
                with c2:
                    st.markdown(f"### {row['PRODUCTO']}")
                    variedades = str(row['VARIEDADES']).split(';')
                    ingredientes = str(row['INGREDIENTES']).split(';')
                    precios = str(row['PRECIO']).split(';')

                    for i in range(len(variedades)):
                        v_nom = variedades[i].strip()
                        v_ing = ingredientes[i].strip() if i < len(ingredientes) else ""
                        v_pre = limpiar_precio(precios[i]) if i < len(precios) else 0
                        item_id = f"{row['PRODUCTO']} - {v_nom}"
                        
                        with st.expander(f"{v_nom} ({formatear_moneda(v_pre)})"):
                            if v_ing: st.caption(v_ing)
                            
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            col_b1, col_txt, col_b2 = st.columns([1,1,1])
                            if col_b1.button("➖", key=f"m_{item_id}"):
                                if cant > 0:
                                    st.session_state.carrito[item_id]['cant'] = cant - 1
                                    if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                    st.rerun()
                            col_txt.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                            if col_b2.button("➕", key=f"p_{item_id}"):
                                st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': v_pre}
                                st.rerun()

    # CIERRE DE PEDIDO
    if st.session_state.carrito:
        st.write("---")
        st.subheader("🛒 Resumen")
        total_pago = 0
        resumen_texto = ""
        for item, datos in st.session_state.carrito.items():
            sub = datos['cant'] * datos['precio']
            total_pago += sub
            resumen_texto += f"- {datos['cant']}x {item}\n"
            st.write(f"**{datos['cant']}x** {item} ({formatear_moneda(sub)})")
        
        envio_opcion = st.radio("Entrega:", ["Retiro", "Delivery"])
        costo_final_envio = costo_delivery if envio_opcion == "Delivery" else 0
        total_final = total_pago + costo_final_envio
        
        st.markdown(f"## Total: {formatear_moneda(total_final)}")
        st.info(f"💰 Alias: {conf.get('Alias', 'No definido')}")
        
        dir_entrega = st.text_input("Dirección:") if envio_opcion == "Delivery" else "Retiro en local"
        
        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True, type="primary"):
            # 1. Enviar a Google Sheets
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":resumen_texto, "total":total_final, "dir":dir_entrega}
            requests.get(URL_APPS_SCRIPT, params=params)
            
            # 2. Enviar a Telegram
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n🆔 DNI: {st.session_state.user_dni}\n📍 {dir_entrega}\n{resumen_texto}\n💰 TOTAL: {formatear_moneda(total_final)}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            
            st.session_state.carrito = {}
            st.session_state.vista = 'rastreo' # Lo mandamos a ver su pedido
            st.rerun()

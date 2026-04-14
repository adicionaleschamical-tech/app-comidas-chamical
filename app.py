import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
# ID del documento de Google Sheets
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# GID de la pestaña de Pedidos (Extraído de tu URL: 1395505058)
GID_PEDIDOS = "1395505058" 

# Token y Datos de Telegram
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URL de tu Google Apps Script (el que procesa los estados)
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# URLs de exportación CSV
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟", layout="centered")

# --- 2. FUNCIONES DE APOYO ---

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

@st.cache_data(ttl=60)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS, timeout=10)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

def obtener_pedidos_frescos():
    """Descarga los pedidos ignorando el caché de Google Sheets"""
    try:
        url_fresca = f"{URL_PEDIDOS_BASE}&cache_buster={int(time.time())}"
        resp = requests.get(url_fresca, timeout=10)
        if resp.status_code != 200: return pd.DataFrame()
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

def enviar_telegram(mensaje, dni):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=EN_CAMINO"
    texto = f"{mensaje}\n\n✅ [ACEPTAR]({link_aceptar}) | 🛵 [ENVIADO]({link_enviar})"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

# --- 3. LÓGICA DE NAVEGACIÓN ---
if 'vista' not in st.session_state: st.session_state.vista = 'inicio'

# --- PANTALLA 1: INICIO ---
if st.session_state.vista == 'inicio':
    st.markdown("<h1 style='text-align: center;'>🍟 Pedidos Chamical</h1>", unsafe_allow_html=True)
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🍔\nHACER\nPEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'; st.rerun()
    with c2:
        if st.button("📦\nCONSULTAR\nESTADO", use_container_width=True):
            st.session_state.vista = 'consultar'; st.rerun()
    st.stop()

# --- PANTALLA 2: HACER PEDIDO ---
if st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("Identificación")
            st.warning("⚠️ Proporcioná tu DNI real para poder consultar el estado luego.")
            nombre = st.text_input("Nombre y Apellido")
            dni = st.text_input("DNI (solo números)")
            if st.button("Continuar al Menú"):
                if nombre and dni.isdigit():
                    st.session_state.user_name = nombre
                    st.session_state.user_dni = dni
                    st.rerun()
                else: st.error("Completá los datos correctamente.")
        st.stop()

    df_p = cargar_productos()
    if 'carrito' not in st.session_state: st.session_state.carrito = {}

    for idx, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"**Precio: ${row['PRECIO']}**")
                if c2.button("➕ Agregar", key=f"a_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast(f"Agregado: {row['PRODUCTO']}")

    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Resumen")
        total, detalle = 0, ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
            total += (pre * q)
            st.write(f"**{q}x** {p} (${pre*q:,.0f})")
            detalle += f"- {q}x {p}\n"
        
        ent = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        dir_e = st.text_input("Dirección") if ent == "Delivery" else "Retiro"
        
        if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":detalle, "total":total, "dir":dir_e}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n🪪 DNI: {st.session_state.user_dni}\n📍 {dir_e}\n{detalle}\n💰 *TOTAL: ${total:,.0f}*"
            enviar_telegram(msg, st.session_state.user_dni)
            st.session_state.carrito = {}; st.session_state.vista = 'consultar'; st.rerun()

# --- PANTALLA 3: CONSULTAR ESTADO (CON DIAGNÓSTICO) ---
if st.session_state.vista == 'consultar':
    if st.button("⬅ Volver al inicio"): 
        st.session_state.vista = 'inicio'; st.rerun()
    
    st.title("Seguimiento de Pedido")
    dni_input = st.text_input("Ingresá tu DNI:", value=st.session_state.get('user_dni', ""))
    
    # Panel de Diagnóstico para detectar errores de conexión o formato
    with st.expander("🛠️ PANEL TÉCNICO (Si falla la consulta, abrir aquí)"):
        df_debug = obtener_pedidos_frescos()
        if not df_debug.empty:
            st.success("Conexión con el Sheet: OK")
            st.write("Columnas encontradas:", list(df_debug.columns))
            st.write("Últimas filas en el Excel:", df_debug.tail(3))
        else:
            st.error("Error: No se pueden descargar datos. Verificá el GID y la publicación del Sheet.")

    if st.button("🔍 CONSULTAR", type="primary", use_container_width=True):
        if dni_input:
            df_peds = obtener_pedidos_frescos()
            if not df_peds.empty:
                try:
                    # Limpieza agresiva de DNI (Excel y Usuario)
                    df_peds['DNI_CLEAN'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True)
                    df_peds['DNI_CLEAN'] = df_peds['DNI_CLEAN'].str.replace(r'[.,\s]', '', regex=True).str.strip()
                    dni_busqueda = re.sub(r'[^\d]', '', str(dni_input)).strip()
                    
                    # Búsqueda
                    match = df_peds[df_peds['DNI_CLEAN'] == dni_busqueda]
                    
                    if not match.empty:
                        res = match.iloc[-1]
                        estado = str(res.get('ESTADO', 'PENDIENTE')).upper()
                        nombre = res.get('NOMBRE', 'Cliente')
                        
                        st.markdown(f"""
                            <div style="padding:20px; border-radius:15px; border:3px solid #E63946; text-align:center; background-color: #f9f9f9;">
                                <h3>Hola {nombre}</h3>
                                <p>Tu pedido está:</p>
                                <h1 style="color:#E63946; font-size:45px;">{estado}</h1>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if estado not in ["ENTREGADO", "FINALIZADO"]:
                            st.info("🔄 Se actualizará automáticamente cada 20 segundos...")
                            time.sleep(20); st.rerun()
                    else:
                        st.warning(f"No se encontró pedido para el DNI {dni_busqueda}. Verificá el Panel Técnico arriba.")
                except Exception as e:
                    st.error(f"Error procesando datos: {e}")

import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# !!! RECORDÁ CAMBIAR ESTO POR EL GID DE TU PESTAÑA 'PEDIDOS' !!!
GID_PEDIDOS = "TU_GID_AQUI" 

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟", layout="centered")

# --- 2. FUNCIONES ---

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

@st.cache_data(ttl=60)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except: return pd.DataFrame()

def obtener_pedidos_frescos():
    try:
        url_fresca = f"{URL_PEDIDOS_BASE}&cache_buster={int(time.time())}"
        resp = requests.get(url_fresca)
        return pd.read_csv(StringIO(resp.text))
    except: return pd.DataFrame()

def enviar_telegram(mensaje, dni):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # El link de Telegram ahora usa el DNI para buscar y cambiar el estado
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={dni}&estado=EN_CAMINO"
    texto = f"{mensaje}\n\n✅ [ACEPTAR]({link_aceptar}) | 🛵 [ENVIADO]({link_enviar})"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

# --- 3. LÓGICA DE NAVEGACIÓN ---
if 'vista' not in st.session_state: st.session_state.vista = 'inicio'

# --- VISTA: INICIO ---
if st.session_state.vista == 'inicio':
    st.markdown("<h1 style='text-align: center;'>🍟 Bienvido a Pedidos Chamical</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🍔\nHACER\nPEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'
            st.rerun()
            
    with col2:
        if st.button("📦\nCONSULTAR\nESTADO", use_container_width=True):
            st.session_state.vista = 'consultar'
            st.rerun()
    st.stop()

# --- VISTA: HACER PEDIDO ---
if st.session_state.vista == 'pedir':
    if st.button("⬅ Volver"): 
        st.session_state.vista = 'inicio'
        st.rerun()
        
    st.title("Hacé tu pedido")
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("Ingresá tus datos")
            st.info("⚠️ **IMPORTANTE:** Proporcioná tu DNI real. Lo necesitarás para consultar el estado de tu pedido más tarde.")
            nombre = st.text_input("Nombre y Apellido")
            dni = st.text_input("DNI (solo números)")
            if st.button("Continuar al Menú"):
                if nombre and dni.isdigit():
                    st.session_state.user_name = nombre
                    st.session_state.user_dni = dni
                    st.rerun()
                else:
                    st.error("Por favor, ingresá nombre y un DNI válido.")
        st.stop()

    # Mostrar productos
    df_p = cargar_productos()
    if 'carrito' not in st.session_state: st.session_state.carrito = {}

    for idx, row in df_p.iterrows():
        if str(row['DISPONIBLE']).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"**Precio: ${row['PRECIO']}**")
                if c2.button("➕ Agregar", key=f"add_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast("Agregado!")

    # Carrito y Cierre
    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Tu Pedido")
        total, detalle = 0, ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
            total += (pre * q)
            st.write(f"**{q}x** {p} (${pre*q:,.0f})")
            detalle += f"- {q}x {p}\n"
        
        ent = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        dir_envio = st.text_input("Dirección") if ent == "Delivery" else "Retiro"
        
        if st.button("🚀 CONFIRMAR COMPRA", type="primary", use_container_width=True):
            # Guardamos en el Sheet usando DNI en lugar de teléfono
            params = {
                "accion": "nuevo", 
                "tel": st.session_state.user_dni, # El script usa 'tel' pero mandamos el DNI
                "nombre": st.session_state.user_name, 
                "detalle": detalle, 
                "total": total, 
                "dir": dir_envio
            }
            requests.get(URL_APPS_SCRIPT, params=params)
            
            # Notificación a Telegram
            msg = f"🍔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n🪪 DNI: {st.session_state.user_dni}\n📍 {dir_envio}\n\n{detalle}\n💰 *TOTAL: ${total:,.0f}*"
            enviar_telegram(msg, st.session_state.user_dni)
            
            st.success("¡Pedido enviado con éxito!")
            st.session_state.carrito = {}
            st.session_state.vista = 'consultar'
            st.rerun()

# --- VISTA: CONSULTAR ESTADO ---
if st.session_state.vista == 'consultar':
    if st.button("⬅ Volver al inicio"): 
        st.session_state.vista = 'inicio'
        st.rerun()
        
    st.title("Seguimiento de Pedido")
    dni_consulta = st.text_input("Ingresá tu DNI para consultar:", value=st.session_state.get('user_dni', ""))
    
    if dni_consulta:
        df_peds = obtener_pedidos_frescos()
        try:
            # Buscamos por la columna TELEFONO (donde ahora guardamos el DNI)
            res = df_peds[df_peds['TELEFONO'].astype(str).str.contains(str(dni_consulta))].iloc[-1]
            estado = str(res['ESTADO']).upper()
            
            st.markdown(f"""
                <div style="padding:20px; border-radius:15px; border:3px solid #E63946; text-align:center; background-color: #ffffff;">
                    <h3>Hola {res['Nombre']}</h3>
                    <p>Estado de tu pedido:</p>
                    <h1 style="color:#E63946; font-size:45px;">{estado}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            if estado not in ["ENTREGADO", "FINALIZADO"]:
                st.caption("🔄 La página se actualizará automáticamente...")
                time.sleep(20)
                st.rerun()
        except:
            st.warning("No se encontró ningún pedido reciente con ese DNI.")

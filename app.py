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

# !!! RECORDÁ CAMBIAR ESTO POR TU GID REAL !!!
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

def enviar_telegram(mensaje, tel):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=EN_CAMINO"
    texto = f"{mensaje}\n\n✅ [ACEPTAR]({link_aceptar}) | 🛵 [ENVIADO]({link_enviar})"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

# --- 3. BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["🍔 Hacer Pedido", "📦 Consultar Mi Pedido"])

# --- SECTOR: HACER PEDIDO ---
if opcion == "🍔 Hacer Pedido":
    st.title("Hacé tu pedido")
    
    if 'user_name' not in st.session_state:
        with st.container(border=True):
            st.subheader("Identificación")
            nombre = st.text_input("Nombre")
            tel = st.text_input("Teléfono (sin 0 ni 15)")
            if st.button("Empezar a comprar"):
                if nombre and tel:
                    st.session_state.user_name = nombre
                    st.session_state.user_tel = tel
                    st.rerun()
        st.stop()

    # Mostrar Menú
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

    # Carrito
    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Resumen")
        total = 0
        detalle = ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_p[df_p['PRODUCTO']==p]['PRECIO'].iloc[0])
            total += (pre * q)
            st.write(f"**{q}x** {p} (${pre*q:,.0f})")
            detalle += f"- {q}x {p}\n"
        
        ent = st.radio("Entrega", ["Retiro", "Delivery"])
        dir = st.text_input("Dirección") if ent == "Delivery" else "Retiro"
        
        if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_tel, "nombre":st.session_state.user_name, "detalle":detalle, "total":total, "dir":dir}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n📍 {dir}\n{detalle}\n💰 *TOTAL: ${total:,.0f}*"
            enviar_telegram(msg, st.session_state.user_tel)
            st.success("¡Pedido enviado! Ahora podés consultarlo en la sección de seguimiento.")
            st.session_state.carrito = {} # Limpiamos carrito

# --- SECTOR: CONSULTAR ESTADO ---
elif opcion == "📦 Consultar Mi Pedido":
    st.title("Seguimiento")
    
    # Si ya pidió en esta sesión, autocompletamos el teléfono
    tel_consulta = st.text_input("Ingresá tu teléfono para consultar:", value=st.session_state.get('user_tel', ""))
    
    if tel_consulta:
        df_peds = obtener_pedidos_frescos()
        try:
            # Buscamos la última fila que coincida
            res = df_peds[df_peds['TELEFONO'].astype(str).str.contains(str(tel_consulta))].iloc[-1]
            estado = str(res['ESTADO']).upper()
            nombre_c = res['NOMBRE']
            
            st.markdown(f"""
                <div style="padding:20px; border-radius:15px; border:3px solid #E63946; text-align:center;">
                    <h3>Hola {nombre_c}</h3>
                    <p>Tu último pedido está:</p>
                    <h1 style="color:#E63946; font-size:45px;">{estado}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            # El refresco automático solo ocurre aquí si el pedido no está "ENTREGADO"
            if estado not in ["ENTREGADO", "FINALIZADO"]:
                st.caption("🔄 Esta pantalla se actualiza sola cada 20 segundos...")
                time.sleep(20)
                st.rerun()
        except:
            st.warning("No encontramos pedidos pendientes para ese número.")

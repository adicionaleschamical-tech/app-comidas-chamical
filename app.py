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

# !!! IMPORTANTE: Cambia el GID por el de tu pestaña PEDIDOS
GID_PEDIDOS = "TU_GID_AQUI" 

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

st.set_page_config(page_title="Pedidos Chamical", page_icon="🍟")

# --- 2. FUNCIONES CRÍTICAS ---

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

@st.cache_data(ttl=60) # El menú cambia poco, podemos cachearlo 1 minuto
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def obtener_pedidos_frescos():
    """Descarga los pedidos ignorando el caché de Google"""
    try:
        # El cache_buster hace que la URL sea única cada vez (ej: &t=171234567)
        url_fresca = f"{URL_PEDIDOS_BASE}&cache_buster={int(time.time())}"
        resp = requests.get(url_fresca)
        df = pd.read_csv(StringIO(resp.text))
        return df
    except:
        return pd.DataFrame()

def enviar_telegram_botones(mensaje, tel):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    link_aceptar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=COCINANDO"
    link_enviar = f"{URL_APPS_SCRIPT}?tel={tel}&estado=EN_CAMINO"
    
    texto_final = (
        f"{mensaje}\n\n"
        f"✅ [ACEPTAR Y COCINAR]({link_aceptar})\n"
        f"🛵 [PEDIDO EN CAMINO]({link_enviar})"
    )
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto_final, "parse_mode": "Markdown"})

# --- 3. LÓGICA DE NAVEGACIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- PANTALLA: LOGIN ---
if st.session_state.paso == 'login':
    st.title("🍔 Bienvenido")
    nombre = st.text_input("Tu Nombre")
    tel = st.text_input("Tu Teléfono (ej: 3826123456)")
    if st.button("Ingresar al Menú", use_container_width=True):
        if nombre and len(tel) > 7:
            st.session_state.user_name = nombre
            st.session_state.user_tel = tel
            st.session_state.paso = 'menu'
            st.rerun()
        else:
            st.error("Datos insuficientes.")
    st.stop()

# --- PANTALLA: SEGUIMIENTO (LA MODIFICADA) ---
if st.session_state.paso == 'seguimiento':
    st.title("📦 Seguimiento del Pedido")
    
    # Consultamos datos frescos
    df_peds = obtener_pedidos_frescos()
    estado = "PENDIENTE"
    
    if not df_peds.empty:
        try:
            # Buscamos la última fila que coincida con el teléfono del usuario
            res = df_peds[df_peds['TELEFONO'].astype(str).str.contains(str(st.session_state.user_tel))].iloc[-1]
            estado = str(res['ESTADO']).upper()
        except:
            estado = "PENDIENTE"

    st.markdown(f"""
        <div style="padding:25px; border-radius:15px; border:4px solid #E63946; text-align:center; background-color: #FFF;">
            <h3 style="color: #333;">{st.session_state.user_name}, tu pedido está:</h3>
            <h1 style="color:#E63946; font-size: 55px; margin: 10px 0;">{estado}</h1>
        </div>
    """, unsafe_allow_html=True)

    if estado == "COCINANDO":
        st.success("👨‍🍳 ¡El local ya está preparando tu comida!")
    elif estado == "EN_CAMINO":
        st.warning("🛵 ¡El pedido ya salió! Atento al timbre.")
    else:
        st.info("🕒 Esperando confirmación del local...")

    if st.button("🛒 Hacer otro pedido"):
        st.session_state.paso = 'menu'
        st.session_state.carrito = {}
        st.rerun()

    # REFRESCAR AUTOMÁTICAMENTE
    time.sleep(15) # Espera 15 segundos
    st.rerun() # Reinicia el script para buscar cambios
    st.stop()

# --- PANTALLA: MENÚ ---
st.title("🍴 Menú Digital")
df_p = cargar_productos()

if not df_p.empty:
    for idx, row in df_p.iterrows():
        if str(row['DISPONIBLE']).upper() == "SI":
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.subheader(row['PRODUCTO'])
                c2.write(f"**Precio: ${row['PRECIO']}**")
                if c2.button("➕ Agregar", key=f"btn_{idx}"):
                    st.session_state.carrito[row['PRODUCTO']] = st.session_state.carrito.get(row['PRODUCTO'], 0) + 1
                    st.toast(f"Agregado: {row['PRODUCTO']}")

# --- CARRITO ---
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Carrito")
    resumen_txt = ""
    total_acumulado = 0
    
    for prod, cant in st.session_state.carrito.items():
        fila = df_p[df_p['PRODUCTO'] == prod]
        if not fila.empty:
            p_unitario = limpiar_precio(fila['PRECIO'].iloc[0])
            subtotal = p_unitario * cant
            total_acumulado += subtotal
            st.write(f"**{cant}x** {prod} -- ${subtotal:,.0f}")
            resumen_txt += f"- {cant}x {prod}\n"

    entrega = st.radio("¿Entrega?", ["Retiro en Local", "Delivery"])
    direc = st.text_input("Dirección") if entrega == "Delivery" else "Retiro"
    
    st.markdown(f"## TOTAL: ${total_acumulado:,.0f}")

    if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
        if entrega == "Delivery" and not direc:
            st.error("Falta dirección")
        else:
            params = {
                "accion": "nuevo",
                "tel": st.session_state.user_tel,
                "nombre": st.session_state.user_name,
                "detalle": resumen_txt,
                "total": total_acumulado,
                "dir": direc
            }
            # Guardar en Sheet
            requests.get(URL_APPS_SCRIPT, params=params)
            # Avisar a Telegram
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📞 {st.session_state.user_tel}\n📍 {direc}\n\n{resumen_txt}\n💰 *TOTAL: ${total_acumulado:,.0f}*"
            enviar_telegram_botones(msg, st.session_state.user_tel)
            
            st.session_state.paso = 'seguimiento'
            st.rerun()

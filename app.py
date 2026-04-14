import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN ---
# Nota: En producción, usa st.secrets para los tokens
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs para descarga (ajusta el gid de la hoja PEDIDOS si es necesario)
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIONES AUXILIARES ---
def extraer_numero(precio_str):
    if pd.isna(precio_str): return 0
    solo_digitos = re.sub(r'[^\d]', '', str(precio_str))
    return int(solo_digitos) if solo_digitos else 0

def enviar_telegram(mensaje, id_pedido=None):
    """Envía notificación con botones de acción al comercio"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        # Si quieres botones automáticos, aquí se agregan (requiere bot backend)
        requests.post(url, json=payload, timeout=5)
    except:
        pass

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        resp_p = requests.get(URL_PRODUCTOS, timeout=10)
        df_prod = pd.read_csv(StringIO(resp_p.text))
        df_prod.columns = [c.strip().upper() for c in df_prod.columns]
        
        resp_c = requests.get(URL_CONFIG, timeout=10)
        df_conf = pd.read_csv(StringIO(resp_c.text))
        conf = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_conf.iterrows()}
        
        return df_prod, df_conf, conf
    except:
        return pd.DataFrame(), pd.DataFrame(), {}

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .precio-tag { color: #E63946 !important; font-size: 22px; font-weight: bold; }
    .status-box { padding: 20px; border-radius: 10px; background-color: #f0f2f6; border-left: 5px solid #E63946; }
    </style>
    """, unsafe_allow_html=True)

# --- MANEJO DE SESIÓN ---
if 'rol' not in st.session_state: st.session_state.rol = 'cliente'
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'user_auth' not in st.session_state: st.session_state.user_auth = False

df_prod, df_conf, conf = cargar_datos()
nombre_local = conf.get("Nombre Negocio", "Mi Local")

# --- PANTALLA DE IDENTIFICACIÓN (LOGIN) ---
if not st.session_state.user_auth and st.session_state.rol == 'cliente':
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_local}</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("¡Hola! Para pedir, identificate:")
        nombre = st.text_input("Tu Nombre")
        telefono = st.text_input("Tu Teléfono (ej: 3826123456)")
        
        if st.button("Ingresar al Menú", use_container_width=True):
            if nombre and len(telefono) > 7:
                st.session_state.user_name = nombre
                st.session_state.user_tel = telefono
                st.session_state.user_auth = True
                st.rerun()
            else:
                st.error("Por favor ingresá tu nombre y un teléfono válido")
    
    with st.expander("🛠️ Acceso Administración"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Login Admin"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"):
                st.session_state.rol = 'admin'
                st.rerun()
    st.stop()

# --- VISTA ADMINISTRADOR ---
if st.session_state.rol == 'admin':
    st.title("Panel Admin")
    if st.button("Cerrar Sesión"):
        st.session_state.rol = 'cliente'
        st.session_state.user_auth = False
        st.rerun()
    st.dataframe(df_prod)
    st.stop()

# --- VISTA CLIENTE (MENÚ) ---
st.markdown(f"<h3 style='text-align:right;'>👤 {st.session_state.user_name}</h3>", unsafe_allow_html=True)
st.title(f"Menú de {nombre_local}")

# Categorías y Productos
df_disponibles = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
categorias = df_disponibles['CATEGORIA'].unique()
tabs = st.tabs(list(categorias))

for i, cat in enumerate(categorias):
    with tabs[i]:
        prods = df_disponibles[df_disponibles['CATEGORIA'] == cat]
        for idx, p in prods.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(p['IMAGEN'] if pd.notna(p['IMAGEN']) else "https://via.placeholder.com/150", use_container_width=True)
                with col2:
                    st.subheader(p['PRODUCTO'])
                    precio = extraer_numero(p['PRECIO'])
                    st.markdown(f'<p class="precio-tag">$ {precio:,.0f}</p>', unsafe_allow_html=True)
                    if st.button(f"➕ Agregar", key=f"add_{idx}"):
                        item = p['PRODUCTO']
                        if item in st.session_state.carrito:
                            st.session_state.carrito[item]['cant'] += 1
                        else:
                            st.session_state.carrito[item] = {'precio': precio, 'cant': 1}
                        st.toast(f"{item} al carrito")

# --- CARRITO Y CIERRE DE PEDIDO ---
if st.session_state.carrito:
    st.divider()
    st.header("🛒 Tu Pedido")
    total_compra = 0
    for item, d in list(st.session_state.carrito.items()):
        c1, c2, c3 = st.columns([3, 1, 1])
        subt = d['precio'] * d['cant']
        total_compra += subt
        c1.write(f"**{item}**")
        cant = c2.number_input("Cant", 0, 20, d['cant'], key=f"q_{item}", label_visibility="collapsed")
        if cant != d['cant']:
            if cant == 0: del st.session_state.carrito[item]
            else: st.session_state.carrito[item]['cant'] = cant
            st.rerun()
        c3.write(f"${subt:,.0f}")

    tipo_entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
    dir_envio = ""
    costo_env = 0
    if tipo_entrega == "Delivery":
        dir_envio = st.text_input("📍 Dirección de entrega *")
        costo_env = extraer_numero(conf.get("Costo Delivery", "0"))
        st.caption(f"Costo de envío: ${costo_env:,.0f}")

    total_final = total_compra + costo_env
    st.markdown(f"## TOTAL: ${total_final:,.0f}")

    if st.button("📱 Confirmar Pedido", type="primary", use_container_width=True):
        if tipo_entrega == "Delivery" and not dir_envio:
            st.error("Ingresá una dirección")
        else:
            # Preparar mensaje
            detalles = "\n".join([f"• {v['cant']}x {k}" for k, v in st.session_state.carrito.items()])
            msg = f"🔔 *NUEVO PEDIDO*\n👤 *Cliente:* {st.session_state.user_name}\n📞 *Tel:* {st.session_state.user_tel}\n📍 *Tipo:* {tipo_entrega}\n"
            if dir_envio: msg += f"🏠 *Dirección:* {dir_envio}\n"
            msg += f"📝 *Detalle:*\n{detalles}\n💰 *TOTAL:* ${total_final:,.0f}"
            
            enviar_telegram(msg)
            
            # Limpiar carrito y avisar
            st.session_state.carrito = {}
            st.session_state.pedido_finalizado = True
            st.success("¡Pedido enviado con éxito!")
            
            # Botón opcional de WhatsApp para seguridad
            wa_url = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msg)}"
            st.link_button("Abrir WhatsApp para confirmar", wa_url, use_container_width=True)

if st.session_state.get('pedido_finalizado'):
    st.balloons()
    st.info("Gracias por tu compra. Tu pedido está siendo procesado.")
    if st.button("Hacer otro pedido"):
        st.session_state.pedido_finalizado = False
        st.rerun()

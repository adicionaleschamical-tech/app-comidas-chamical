import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN Y SECRETOS ---
# Nota: En producción, usa st.secrets["TELEGRAM_TOKEN"]
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs para descarga directa
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIONES DE UTILIDAD ---
def extraer_numero(precio_str):
    """Limpia el string y devuelve el número entero"""
    if pd.isna(precio_str): return 0
    solo_digitos = re.sub(r'[^\d]', '', str(precio_str))
    return int(solo_digitos) if solo_digitos else 0

def enviar_telegram(mensaje):
    """Envía notificación por Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        st.error(f"Error al avisar por Telegram: {e}")

@st.cache_data(ttl=30)
def cargar_datos():
    """Carga los CSV directamente desde Google Sheets"""
    try:
        resp_p = requests.get(URL_PRODUCTOS, timeout=10)
        df_prod = pd.read_csv(StringIO(resp_p.text))
        df_prod.columns = [c.strip().upper() for c in df_prod.columns]
        
        resp_c = requests.get(URL_CONFIG, timeout=10)
        df_conf = pd.read_csv(StringIO(resp_c.text))
        conf = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_conf.iterrows() if len(row) >= 2}
        
        return df_prod, df_conf, conf
    except Exception as e:
        st.error(f"Error crítico: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}

# --- ESTILOS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .precio-tag { color: #E63946 !important; font-size: 22px; font-weight: bold; }
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
for key in ['rol', 'carrito', 'sel_v']:
    if key not in st.session_state:
        st.session_state[key] = 'cliente' if key == 'rol' else {}

# --- CARGA DE DATOS ---
df_prod, df_conf, conf = cargar_datos()
if df_prod.empty: st.stop()

# Variables de configuración
nombre_local = conf.get("Nombre Negocio", "Mi Local")
alias = conf.get("Alias", "No definido")
telefono = conf.get("Telefono", "5493826000000")
costo_delivery = extraer_numero(conf.get("Costo Delivery", "0"))

# --- SIDEBAR (ADMIN) ---
with st.sidebar:
    st.header("🛠️ Acceso")
    if st.session_state['rol'] == 'cliente':
        with st.expander("👤 Admin"):
            u = st.text_input("DNI / Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Ingresar"):
                if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User") and p == conf.get("User_Pass"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Error de credenciales")
    else:
        st.info(f"Sesión: {st.session_state['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTA CLIENTE ---
if st.session_state['rol'] == 'cliente':
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_local}</h1>", unsafe_allow_html=True)
    
    df_disponibles = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
    categorias = df_disponibles['CATEGORIA'].unique()
    tabs = st.tabs(list(categorias))
    
    for i, cat in enumerate(categorias):
        with tabs[i]:
            productos_cat = df_disponibles[df_disponibles['CATEGORIA'] == cat]
            for idx, prod in productos_cat.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(prod['IMAGEN'] if pd.notna(prod['IMAGEN']) else "https://via.placeholder.com/150", use_container_width=True)
                    
                    with c2:
                        st.subheader(prod['PRODUCTO'])
                        
                        # Manejo de Variedades
                        variedad_sel = ""
                        precio_final = extraer_numero(prod['PRECIO'])
                        
                        if pd.notna(prod['VARIEDADES']):
                            opciones = [v.strip() for v in str(prod['VARIEDADES']).split(',')]
                            precios_lista = [extraer_numero(p) for p in str(prod['PRECIO']).split(';')]
                            
                            # Asegurar que cada variedad tenga un precio
                            while len(precios_lista) < len(opciones):
                                precios_lista.append(precios_lista[-1] if precios_lista else 0)
                            
                            idx_v = st.selectbox("Elegí opción:", range(len(opciones)), 
                                               format_func=lambda x: opciones[x], key=f"sel_{idx}")
                            variedad_sel = opciones[idx_v]
                            precio_final = precios_lista[idx_v]
                            
                            # Ingredientes por variedad
                            if pd.notna(prod['INGREDIENTES']):
                                ing_lista = str(prod['INGREDIENTES']).split(';')
                                if idx_v < len(ing_lista):
                                    st.caption(f"📋 {ing_lista[idx_v]}")
                        elif pd.notna(prod['INGREDIENTES']):
                            st.caption(f"📋 {prod['INGREDIENTES']}")

                        st.markdown(f'<p class="precio-tag">$ {precio_final:,.0f}</p>', unsafe_allow_html=True)
                        
                        if st.button("➕ Agregar", key=f"btn_{idx}_{variedad_sel}"):
                            item_key = f"{prod['PRODUCTO']} - {variedad_sel}" if variedad_sel else prod['PRODUCTO']
                            if item_key in st.session_state['carrito']:
                                st.session_state['carrito'][item_key]['cant'] += 1
                            else:
                                st.session_state['carrito'][item_key] = {'precio': precio_final, 'cant': 1}
                            st.toast(f"Agregado: {item_key}")

    # --- CARRITO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_productos = 0
        
        for item, datos in list(st.session_state['carrito'].items()):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1: st.write(item)
            with col2:
                nueva_cant = st.number_input("Cant", 0, 99, datos['cant'], key=f"q_{item}", label_visibility="collapsed")
                if nueva_cant != datos['cant']:
                    if nueva_cant == 0: del st.session_state['carrito'][item]
                    else: st.session_state['carrito'][item]['cant'] = nueva_cant
                    st.rerun()
            with col3: st.write(f"${datos['precio']*datos['cant']:,.0f}")
            total_productos += datos['precio'] * datos['cant']

        st.divider()
        nombre_c = st.text_input("👤 Tu Nombre *")
        entrega = st.radio("Entrega:", ["🏪 Retiro en local", "🛵 Delivery"])
        
        direccion = ""
        envio = 0
        if "Delivery" in entrega:
            direccion = st.text_input("📍 Dirección de entrega *")
            envio = costo_delivery
            st.warning(f"Costo de envío: ${envio:,.0f}")

        total_final = total_productos + envio
        st.markdown(f"### TOTAL: ${total_final:,.0f}")

        if st.button("📱 Confirmar y Enviar Pedido", type="primary", use_container_width=True):
            if not nombre_c or ("Delivery" in entrega and not direccion):
                st.error("⚠️ Completá tu nombre y dirección")
            else:
                # Construir Mensaje
                msg = f"🔔 *NUEVO PEDIDO*\n👤 *Cliente:* {nombre_c}\n📦 *Tipo:* {entrega}\n"
                if direccion: msg += f"📍 *Dirección:* {direccion}\n"
                msg += "--- \n"
                for i, d in st.session_state['carrito'].items():
                    msg += f"• {d['cant']}x {i} (${d['precio']*d['cant']:,.0f})\n"
                msg += f"---\n💰 *TOTAL:* ${total_final:,.0f}\n💳 *Alias:* {alias}"

                enviar_telegram(msg)
                wa_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(msg)}"
                st.success("¡Pedido enviado a la cocina!")
                st.link_button("Ir a WhatsApp para coordinar", wa_url, use_container_width=True)

# --- PANEL ADMIN ---
else:
    st.title("Panel de Control")
    st.info("Editá el Google Sheet para cambios permanentes.")
    t1, t2 = st.tabs(["Menú", "Config"])
    with t1: st.dataframe(df_prod)
    with t2: st.dataframe(df_conf)

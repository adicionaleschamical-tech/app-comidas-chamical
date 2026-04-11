import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# URLs CORRECTAS para descarga directa
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIONES ---
def extraer_numero(precio_str):
    numeros = re.findall(r'\d+', str(precio_str).replace(',', ''))
    return float("".join(numeros)) if numeros else 0

@st.cache_data(ttl=30)
def cargar_datos():
    """Carga los CSV directamente desde Google Sheets"""
    try:
        # Descargar productos
        resp_p = requests.get(URL_PRODUCTOS, timeout=10)
        resp_p.raise_for_status()
        df_prod = pd.read_csv(StringIO(resp_p.text))
        df_prod.columns = [c.strip().upper() for c in df_prod.columns]
        
        # Descargar configuración
        resp_c = requests.get(URL_CONFIG, timeout=10)
        resp_c.raise_for_status()
        df_conf = pd.read_csv(StringIO(resp_c.text))
        
        # Convertir a diccionario
        conf = {}
        for _, row in df_conf.iterrows():
            if len(row) >= 2:
                conf[str(row.iloc[0]).strip()] = str(row.iloc[1]).strip()
        
        return df_prod, df_conf, conf
    
    except Exception as e:
        st.error(f"Error al cargar: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}

# --- INICIALIZAR SESIÓN ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- CARGAR DATOS ---
df_prod, df_conf, conf = cargar_datos()

if df_prod.empty:
    st.stop()

# --- DATOS DEL LOCAL ---
nombre_local = conf.get("Nombre Negocio", "Mi Local")
alias = conf.get("Alias", "No definido")
telefono = conf.get("Telefono", "5493826000000")
costo_delivery = extraer_numero(conf.get("Costo Delivery", "0"))

# --- VISTA PRINCIPAL ---
st.title(f"🍟 {nombre_local}")

# Mostrar productos
df_disponibles = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]

if df_disponibles.empty:
    st.warning("No hay productos disponibles")
else:
    for _, producto in df_disponibles.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                img = producto['IMAGEN'] if pd.notna(producto['IMAGEN']) else "https://via.placeholder.com/150"
                st.image(img, use_container_width=True)
            
            with col2:
                st.subheader(producto['PRODUCTO'])
                
                # Precio (sin variedades por simplicidad)
                precio = extraer_numero(producto['PRECIO'])
                st.metric("Precio", f"${precio:,.0f}")
                
                # Botón agregar
                if st.button(f"➕ Agregar", key=f"add_{producto.name}"):
                    nombre = producto['PRODUCTO']
                    if nombre in st.session_state['carrito']:
                        st.session_state['carrito'][nombre]['cant'] += 1
                    else:
                        st.session_state['carrito'][nombre] = {'precio': precio, 'cant': 1}
                    st.toast(f"✅ {nombre} agregado", icon="🛒")

# --- CARRITO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Tu Pedido")
    
    total = 0
    for nombre, datos in st.session_state['carrito'].items():
        subtotal = datos['precio'] * datos['cant']
        total += subtotal
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{nombre}**")
        col2.write(f"${datos['precio']:,.0f}")
        nueva_cant = col3.number_input("Cant", min_value=0, value=datos['cant'], key=f"cant_{nombre}", label_visibility="collapsed")
        if nueva_cant != datos['cant']:
            if nueva_cant == 0:
                del st.session_state['carrito'][nombre]
            else:
                st.session_state['carrito'][nombre]['cant'] = nueva_cant
            st.rerun()
    
    st.divider()
    
    nombre_cliente = st.text_input("👤 Tu nombre")
    tipo_entrega = st.radio("Tipo de entrega", ["Retiro", "Delivery"], horizontal=True)
    
    costo_envio = costo_delivery if tipo_entrega == "Delivery" else 0
    total_final = total + costo_envio
    
    st.metric("TOTAL", f"${total_final:,.0f}")
    if costo_envio > 0:
        st.caption(f"Incluye delivery: ${costo_envio:,.0f}")
    
    st.info(f"💳 Alias para pagar: **{alias}**")
    
    if st.button("📱 Enviar pedido por WhatsApp", type="primary", use_container_width=True):
        if not nombre_cliente:
            st.error("Ingresá tu nombre")
        else:
            mensaje = f"🔔 *NUEVO PEDIDO*\n👤 {nombre_cliente}\n📦 {tipo_entrega}\n---\n"
            for nombre, datos in st.session_state['carrito'].items():
                mensaje += f"• {datos['cant']}x {nombre} — ${datos['precio'] * datos['cant']:,.0f}\n"
            mensaje += f"---\n💰 *TOTAL: ${total_final:,.0f}*"
            
            whatsapp_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(mensaje)}"
            st.link_button("💬 Abrir WhatsApp para enviar", whatsapp_url, use_container_width=True)

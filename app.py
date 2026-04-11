import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime
from io import StringIO

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# URLs para descarga directa
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIÓN CORREGIDA PARA EXTRAER PRECIO ---
def extraer_numero(precio_str):
    """
    Extrae el primer número válido de un string de precio
    Ejemplos:
    - "$7.000" -> 7000
    - "7000;8000;9000" -> 7000 (solo el primero)
    - "$ 7,500" -> 7500
    """
    if pd.isna(precio_str):
        return 0
    
    texto = str(precio_str).strip()
    
    # Si hay múltiples precios (para diferentes variedades), tomar el primero
    if ';' in texto:
        texto = texto.split(';')[0]
    
    # Eliminar todo excepto dígitos
    solo_digitos = re.sub(r'[^\d]', '', texto)
    
    # Convertir a entero
    return int(solo_digitos) if solo_digitos else 0

def enviar_telegram(mensaje):
    """Envía notificación por Telegram"""
    try:
        telegram_token = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
        telegram_chat_id = "7860013984"
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        requests.post(url, data={"chat_id": telegram_chat_id, "text": mensaje, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass  # No interrumpe la app si falla Telegram

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
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}

# --- DISEÑO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-card { 
        border: 1px solid #EEE; 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        background-color: #FDFDFD;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    .precio-tag { 
        color: #E63946 !important; 
        font-size: 24px !important; 
        font-weight: bold !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAR SESIÓN ---
if 'rol' not in st.session_state:
    st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state:
    st.session_state['sel_v'] = {}

# --- CARGAR DATOS ---
with st.spinner("Cargando menú..."):
    df_prod, df_conf, conf = cargar_datos()

if df_prod.empty:
    st.error("No se pudieron cargar los datos. Verificá que el Google Sheet sea público.")
    st.stop()

# --- DATOS DEL LOCAL ---
nombre_local = conf.get("Nombre Negocio", "Mi Local")
alias = conf.get("Alias", "No definido")
telefono = conf.get("Telefono", "5493826000000")
costo_delivery = extraer_numero(conf.get("Costo Delivery", "0"))

# --- SIDEBAR PARA LOGIN ---
with st.sidebar:
    st.header("🛠️ Acceso")
    if st.session_state['rol'] == 'cliente':
        with st.expander("👤 Ingresar como administrador"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Login"):
                admin_dni = conf.get("Admin_DNI", "30588807")
                admin_pass = conf.get("Admin_Pass", "124578")
                user = conf.get("User", "usuario")
                user_pass = conf.get("User_Pass", "usuario123")
                
                if u == admin_dni and p == admin_pass:
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == user and p == user_pass:
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    else:
        st.info(f"Sesión: {st.session_state['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.session_state['carrito'] = {}
            st.session_state['sel_v'] = {}
            st.rerun()

# --- VISTA DE ADMINISTRACIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("Panel de Control")
    st.warning("⚠️ Los cambios son temporales. Editá directamente en Google Sheets para guardar permanentemente.")
    
    tab1, tab2 = st.tabs(["🍔 Menú de Productos", "⚙️ Configuración"])
    
    with tab1:
        st.dataframe(df_prod, use_container_width=True, height=400)
        
        # Mostrar columnas esperadas
        st.caption("Columnas esperadas: PRODUCTO, CATEGORIA, PRECIO, VARIEDADES, INGREDIENTES, DISPONIBLE, IMAGEN")
    
    with tab2:
        st.dataframe(df_conf, use_container_width=True, height=300)
        st.caption("Configuración: Nombre Negocio, Alias, Telefono, Costo Delivery, Admin_DNI, Admin_Pass, User, User_Pass")

# --- VISTA DE CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_local}</h1>", unsafe_allow_html=True)
    
    # Filtrar productos disponibles
    df_disponibles = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
    
    if df_disponibles.empty:
        st.warning("No hay productos disponibles en este momento")
    else:
        # Mostrar por categorías
        categorias = df_disponibles['CATEGORIA'].unique()
        tabs = st.tabs(list(categorias))
        
        for i, cat in enumerate(categorias):
            with tabs[i]:
                productos_cat = df_disponibles[df_disponibles['CATEGORIA'] == cat]
                
                for idx, producto in productos_cat.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([1, 2])
                        
                        # Columna de imagen
                        with col1:
                            img_url = producto['IMAGEN'] if pd.notna(producto['IMAGEN']) else "https://via.placeholder.com/150x150?text=Sin+imagen"
                            try:
                                st.image(img_url, use_container_width=True)
                            except:
                                st.image("https://via.placeholder.com/150x150?text=Error", use_container_width=True)
                        
                        # Columna de información
                        with col2:
                            st.markdown(f"### {producto['PRODUCTO']}")
                            
                            # Verificar si tiene variedades
                            tiene_variedades = pd.notna(producto['VARIEDADES']) and str(producto['VARIEDADES']).strip() != ''
                            
                            variedad_seleccionada = None
                            precio_seleccionado = extraer_numero(producto['PRECIO'])
                            
                            if tiene_variedades:
                                opciones_variedad = [v.strip() for v in str(producto['VARIEDADES']).split(',')]
                                
                                # Obtener precios para cada variedad
                                precios_raw = str(producto['PRECIO']).split(';')
                                precios_variedad = []
                                for p in precios_raw:
                                    precios_variedad.append(extraer_numero(p))
                                
                                # Si hay más variedades que precios, repetir el último precio
                                while len(precios_variedad) < len(opciones_variedad):
                                    precios_variedad.append(precios_variedad[-1] if precios_variedad else 0)
                                
                                # Selector de variedad
                                if idx not in st.session_state['sel_v']:
                                    st.session_state['sel_v'][idx] = 0
                                
                                variedad_seleccionada = st.selectbox(
                                    "Variedad",
                                    opciones_variedad,
                                    index=st.session_state['sel_v'][idx],
                                    key=f"var_{idx}"
                                )
                                
                                nuevo_idx = opciones_variedad.index(variedad_seleccionada)
                                if st.session_state['sel_v'][idx] != nuevo_idx:
                                    st.session_state['sel_v'][idx] = nuevo_idx
                                    st.rerun()
                                
                                precio_seleccionado = precios_variedad[st.session_state['sel_v'][idx]]
                                
                                # Mostrar ingredientes específicos de la variedad
                                if pd.notna(producto['INGREDIENTES']):
                                    ingredientes_raw = str(producto['INGREDIENTES']).split(';')
                                    if st.session_state['sel_v'][idx] < len(ingredientes_raw):
                                        st.caption(f"📋 {ingredientes_raw[st.session_state['sel_v'][idx]]}")
                            else:
                                # Sin variedades, mostrar ingredientes generales
                                if pd.notna(producto['INGREDIENTES']):
                                    st.caption(f"📋 {producto['INGREDIENTES']}")
                            
                            # Mostrar precio y botón de agregar
                            col_precio, col_boton = st.columns(2)
                            with col_precio:
                                st.markdown(f'<p class="precio-tag">💰 ${precio_seleccionado:,.0f}</p>', unsafe_allow_html=True)
                            
                            with col_boton:
                                nombre_producto = f"{producto['PRODUCTO']} ({variedad_seleccionada})" if tiene_variedades else producto['PRODUCTO']
                                
                                if st.button(f"➕ Agregar al carrito", key=f"add_{idx}_{st.session_state['sel_v'].get(idx, 0)}", use_container_width=True):
                                    if nombre_producto in st.session_state['carrito']:
                                        st.session_state['carrito'][nombre_producto]['cant'] += 1
                                    else:
                                        st.session_state['carrito'][nombre_producto] = {
                                            'precio': precio_seleccionado,
                                            'cant': 1,
                                            'nombre_base': producto['PRODUCTO']
                                        }
                                    st.toast(f"✅ {nombre_producto} agregado", icon="🛒")
                                    st.balloons()
    
    # --- CARRITO DE COMPRAS ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        
        total = 0
        items_a_eliminar = []
        
        for nombre, datos in st.session_state['carrito'].items():
            subtotal = datos['precio'] * datos['cant']
            total += subtotal
            
            col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 0.8])
            with col1:
                st.write(f"**{nombre}**")
            with col2:
                st.write(f"${datos['precio']:,.0f} c/u")
            with col3:
                nueva_cant = st.number_input(
                    "Cantidad",
                    min_value=0,
                    max_value=99,
                    value=datos['cant'],
                    key=f"cant_{nombre}",
                    label_visibility="collapsed"
                )
                if nueva_cant != datos['cant']:
                    if nueva_cant == 0:
                        items_a_eliminar.append(nombre)
                    else:
                        st.session_state['carrito'][nombre]['cant'] = nueva_cant
                    st.rerun()
            with col4:
                st.write(f"**${subtotal:,.0f}**")
        
        # Eliminar items marcados
        for item in items_a_eliminar:
            del st.session_state['carrito'][item]
            st.rerun()
        
        st.divider()
        
        # Datos del cliente
        nombre_cliente = st.text_input("👤 Tu nombre *", placeholder="Obligatorio")
        
        col_envio, col_costo = st.columns(2)
        with col_envio:
            tipo_entrega = st.radio("Tipo de entrega", ["🏪 Retiro", "🛵 Delivery"], horizontal=False)
        with col_costo:
            costo_envio = costo_delivery if "Delivery" in tipo_entrega else 0
            st.metric("Costo de envío", f"${costo_envio:,.0f}")
        
        total_final = total + costo_envio
        
        st.markdown(f"## 💰 TOTAL: ${total_final:,.0f}")
        
        if costo_envio > 0:
            st.caption(f"Incluye delivery: ${costo_envio:,.0f}")
        
        st.info(f"💳 Alias para pagar: **{alias}**")
        
        # Botones de acción
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🗑️ Vaciar carrito", use_container_width=True):
                st.session_state['carrito'] = {}
                st.rerun()
        
        with col_btn2:
            if st.button("📱 Enviar pedido", type="primary", use_container_width=True):
                if not nombre_cliente:
                    st.error("❌ Por favor, ingresá tu nombre")
                elif not st.session_state['carrito']:
                    st.error("❌ El carrito está vacío")
                else:
                    # Generar mensaje para WhatsApp
                    mensaje = f"🔔 *NUEVO PEDIDO*\n"
                    mensaje += f"👤 *Cliente:* {nombre_cliente}\n"
                    mensaje += f"📦 *Entrega:* {tipo_entrega.replace('🏪 ', '').replace('🛵 ', '')}\n"
                    mensaje += f"⏰ *Hora:* {datetime.now().strftime('%H:%M - %d/%m')}\n"
                    mensaje += f"---\n"
                    
                    for nombre, datos in st.session_state['carrito'].items():
                        subtotal_item = datos['precio'] * datos['cant']
                        mensaje += f"• {datos['cant']}x {nombre} — ${subtotal_item:,.0f}\n"
                    
                    mensaje += f"---\n"
                    mensaje += f"💰 *Subtotal:* ${total:,.0f}\n"
                    if costo_envio > 0:
                        mensaje += f"🛵 *Delivery:* ${costo_envio:,.0f}\n"
                    mensaje += f"💵 *TOTAL:* ${total_final:,.0f}\n"
                    mensaje += f"---\n"
                    mensaje += f"💳 *Alias:* {alias}"
                    
                    # Enviar notificación por Telegram
                    enviar_telegram(mensaje)
                    
                    # Link de WhatsApp
                    whatsapp_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(mensaje)}"
                    
                    st.success("✅ Pedido preparado correctamente")
                    st.link_button("💬 Enviar por WhatsApp", whatsapp_url, use_container_width=True)
    
    else:
        st.info("🛍️ Tu carrito está vacío. Agregá productos para comenzar.")

# --- FOOTER ---
st.markdown("---")
st.caption(f"🍟 {nombre_local} - Sistema de pedidos | {datetime.now().strftime('%Y')}")

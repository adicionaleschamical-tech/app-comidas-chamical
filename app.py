import streamlit as st
import pandas as pd
import time
import requests
import urllib.parse
import re
from datetime import datetime

# --- CONFIGURACIÓN DE CONEXIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM (usando st.secrets para seguridad) ---
# Para usar esto, creá un archivo .streamlit/secrets.toml con:
# TELEGRAM_TOKEN = "tu_token"
# TELEGRAM_ID = "tu_id"
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_ID = st.secrets["TELEGRAM_ID"]
except:
    # Fallback solo para desarrollo (NO usar en producción)
    TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
    TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIONES AUXILIARES ---
def extraer_numero(precio_str):
    """Extrae el número de un string de precio (ej: '$12.500' -> 12500)"""
    numeros = re.findall(r'\d+', str(precio_str).replace(',', ''))
    return float("".join(numeros)) if numeros else 0

def enviar_telegram(mensaje):
    """Envía un mensaje por Telegram (opcional)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except:
        pass  # No falla si Telegram no funciona

@st.cache_data(ttl=30)  # Cache de 30 segundos
def cargar_datos():
    """Carga los datos desde Google Sheets con caché"""
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf_dict = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, df_c, conf_dict
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}

# --- DISEÑO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { 
        border: 1px solid #EEE; padding: 12px; border-radius: 15px; 
        margin-bottom: 15px; background-color: #FDFDFD !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    .stImage > img { border-radius: 12px; max-height: 180px; object-fit: cover; }
    .precio-tag { color: #E63946 !important; font-size: 26px !important; font-weight: 900 !important; margin: 0; }
    .ing-box { background: #FFF9C4; padding: 8px; border-radius: 8px; font-size: 14px; margin: 8px 0; border-left: 4px solid #FBC02D; }
    .carrito-item { padding: 8px 0; border-bottom: 1px solid #EEE; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAR SESIÓN ---
if 'rol' not in st.session_state:
    st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}
if 'ultima_verificacion' not in st.session_state:
    st.session_state['ultima_verificacion'] = 0

# --- CARGAR DATOS ---
df_prod, df_conf_raw, conf = cargar_datos()

# --- DATOS DINÁMICOS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "5493826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- VERIFICAR DISPONIBILIDAD DEL CARRITO ---
def verificar_disponibilidad_carrito():
    """Elimina del carrito productos que ya no están disponibles"""
    if not df_prod.empty and time.time() - st.session_state['ultima_verificacion'] > 60:
        productos_disponibles = set(df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]['PRODUCTO'].values)
        carrito_actual = list(st.session_state['carrito'].keys())
        for item in carrito_actual:
            # Extraer nombre base del producto (sin variedad)
            nombre_base = item.split(' (')[0] if ' (' in item else item
            if nombre_base not in productos_disponibles:
                del st.session_state['carrito'][item]
        st.session_state['ultima_verificacion'] = time.time()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛠️ Acceso")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingresar"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Login"):
                # Las credenciales deberían estar en secrets, esto es solo ejemplo
                if u == conf.get("Admin_DNI", "30588807") and p == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User", "usuario") and p == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    else:
        st.info(f"Sesión: {st.session_state['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.session_state['carrito'] = {}
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("Panel de Control")
    t1, t2 = st.tabs(["🍔 Menú", "⚙️ Configuración"])

    with t1:
        st.warning("⚠️ Los cambios aquí son temporales. Para guardar, editar directamente en Google Sheets.")
        if st.session_state['rol'] == 'admin':
            edited_df = st.data_editor(df_prod, use_container_width=True, key="menu_editor")
        else:
            cols = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            edited_df = st.data_editor(df_prod[cols], use_container_width=True, key="menu_editor_user")

    with t2:
        st.subheader("Personalización del Comprador")
        campos_visibles = ["Nombre Negocio", "Alias", "Telefono", "Costo Delivery"]
        
        if st.session_state['rol'] == 'usuario':
            df_usuario = df_conf_raw[df_conf_raw.iloc[:, 0].isin(campos_visibles)]
            st.write("Modificá el Alias y datos de contacto aquí:")
            st.data_editor(df_usuario, use_container_width=True, key="editor_comprador")
            st.info("ℹ️ Los cambios se reflejarán al recargar la página")
        else:
            st.data_editor(df_conf_raw, use_container_width=True, key="editor_admin")

# --- VISTA CLIENTE ---
else:
    # Verificar disponibilidad del carrito
    verificar_disponibilidad_carrito()
    
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        
        if df_ver.empty:
            st.warning("No hay productos disponibles en este momento")
        else:
            categorias = df_ver['CATEGORIA'].unique()
            tabs = st.tabs(list(categorias))

            for i, cat in enumerate(categorias):
                with tabs[i]:
                    items = df_ver[df_ver['CATEGORIA'] == cat]
                    for idx, row in items.iterrows():
                        st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                        c_img, c_txt = st.columns([1, 1.2])
                        
                        with c_img:
                            img = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200x150?text=Sin+imagen"
                            try:
                                st.image(img, use_container_width=True)
                            except:
                                st.image("https://via.placeholder.com/200x150?text=Error+imagen", use_container_width=True)

                        with c_txt:
                            st.markdown(f"### {row['PRODUCTO']}")
                            
                            # SELECCIÓN DE VARIEDAD (usando radio para evitar reruns innecesarios)
                            tiene_v = pd.notna(row['VARIEDADES']) and str(row['VARIEDADES']).strip() != ''
                            
                            if tiene_v:
                                ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                                if idx not in st.session_state['sel_v']:
                                    st.session_state['sel_v'][idx] = 0
                                
                                variedad_seleccionada = st.radio(
                                    "Variedad:", 
                                    ops, 
                                    index=st.session_state['sel_v'][idx],
                                    key=f"radio_{idx}",
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )
                                st.session_state['sel_v'][idx] = ops.index(variedad_seleccionada)
                                p_idx = st.session_state['sel_v'][idx]
                            else:
                                p_idx = 0

                            # INGREDIENTES
                            if pd.notna(row['INGREDIENTES']) and str(row['INGREDIENTES']).strip() != '':
                                ings = str(row['INGREDIENTES']).split(';')
                                if tiene_v and p_idx < len(ings):
                                    txt_ing = ings[p_idx]
                                elif not tiene_v and len(ings) > 0:
                                    txt_ing = ings[0]
                                else:
                                    txt_ing = str(row['INGREDIENTES'])
                                st.markdown(f'<div class="ing-box">📋 {txt_ing}</div>', unsafe_allow_html=True)

                            # PRECIO
                            precios = str(row['PRECIO']).split(';')
                            if tiene_v and p_idx < len(precios):
                                p_raw = precios[p_idx]
                            else:
                                p_raw = precios[0]
                            p_f = extraer_numero(p_raw)
                            
                            col_pre, col_add = st.columns([1, 1])
                            with col_pre:
                                st.markdown(f'<p class="precio-tag">💰 ${p_f:,.0f}</p>', unsafe_allow_html=True)
                            with col_add:
                                nombre_producto = f"{row['PRODUCTO']} ({variedad_seleccionada})" if tiene_v else row['PRODUCTO']
                                if st.button("➕ Añadir", key=f"add_{idx}", use_container_width=True):
                                    if nombre_producto in st.session_state['carrito']:
                                        st.session_state['carrito'][nombre_producto]['cant'] += 1
                                    else:
                                        st.session_state['carrito'][nombre_producto] = {'precio': p_f, 'cant': 1}
                                    st.toast(f"✅ Agregado: {nombre_producto}", icon="🛒")
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- CARRITO DE COMPRAS ---
    if st.session_state['carrito']:
        with st.container(border=True):
            st.markdown("### 🛒 Tu Pedido")
            
            total = 0
            resumen = ""
            
            # Mostrar items del carrito con opción de modificar cantidad
            for item, d in list(st.session_state['carrito'].items()):
                sub = d['precio'] * d['cant']
                total += sub
                resumen += f"• {d['cant']}x {item} — ${sub:,.0f}\n"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{item}**")
                with col2:
                    st.write(f"${d['precio']:,.0f} c/u")
                with col3:
                    nueva_cant = st.number_input(
                        "Cant", 
                        min_value=0, 
                        max_value=99, 
                        value=d['cant'], 
                        key=f"cant_{item}",
                        label_visibility="collapsed"
                    )
                    if nueva_cant != d['cant']:
                        if nueva_cant == 0:
                            del st.session_state['carrito'][item]
                            st.rerun()
                        else:
                            st.session_state['carrito'][item]['cant'] = nueva_cant
                            st.rerun()
            
            st.divider()
            
            # Datos del cliente
            nom_cli = st.text_input("👤 Tu nombre:", placeholder="Obligatorio")
            envio_tipo = st.radio("📦 Tipo de entrega:", ["🏠 Delivery", "🏪 Retiro"], horizontal=True)
            
            costo_env = int(extraer_numero(costo_d)) if envio_tipo == "🏠 Delivery" else 0
            
            st.markdown(f"## 💵 TOTAL: ${total + costo_env:,.0f}")
            if costo_env > 0:
                st.caption(f"*Delivery: ${costo_env:,.0f}*")
            
            st.info(f"💳 Alias de pago: **{alias_n}**")
            
            # Botones de acción
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🗑️ Vaciar carrito", use_container_width=True):
                    st.session_state['carrito'] = {}
                    st.rerun()
            
            with col_btn2:
                # Preparar mensaje de WhatsApp
                if st.button("📱 Enviar pedido", use_container_width=True, type="primary"):
                    if not nom_cli:
                        st.error("Por favor, ingresá tu nombre")
                    elif not st.session_state['carrito']:
                        st.error("El carrito está vacío")
                    else:
                        # Verificar disponibilidad nuevamente antes de enviar
                        verificar_disponibilidad_carrito()
                        if not st.session_state['carrito']:
                            st.error("Algunos productos ya no están disponibles. Revisá tu carrito.")
                        else:
                            # Recalcular total
                            total_final = sum(d['precio'] * d['cant'] for d in st.session_state['carrito'].values()) + costo_env
                            resumen_final = ""
                            for item, d in st.session_state['carrito'].items():
                                resumen_final += f"• {d['cant']}x {item} — ${d['precio'] * d['cant']:,.0f}\n"
                            
                            # Crear mensaje
                            mensaje = f"🔔 *NUEVO PEDIDO*\n"
                            mensaje += f"👤 {nom_cli}\n"
                            mensaje += f"🛵 {envio_tipo.replace('🏠 ', '').replace('🏪 ', '')}\n"
                            mensaje += f"⏰ {datetime.now().strftime('%H:%M - %d/%m')}\n"
                            mensaje += f"---\n{resumen_final}\n"
                            mensaje += f"💰 *TOTAL: ${total_final:,.0f}*\n"
                            mensaje += f"---\n💳 Alias: {alias_n}"
                            
                            # Enviar también por Telegram (opcional)
                            enviar_telegram(mensaje)
                            
                            # Link de WhatsApp
                            txt = urllib.parse.quote(mensaje)
                            wa_link = f"https://wa.me/{tel_n}?text={txt}"
                            
                            st.success("✅ Pedido preparado! Hacé clic en el botón para enviar")
                            st.link_button("💬 Enviar por WhatsApp", wa_link, use_container_width=True)
    
    else:
        st.info("🛍️ Tu carrito está vacío. Agregá productos para comenzar.")

# --- FOOTER ---
st.markdown("---")
st.caption(f"🍟 {nombre_n} - Sistema de pedidos")

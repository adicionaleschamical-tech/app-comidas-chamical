import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import logging
from datetime import datetime
import json

from config import (
    cargar_config, limpiar_precio, formatear_moneda,
    cargar_productos, URL_PEDIDOS_BASE
)

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FUNCIONES DE TELEGRAM ====================
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

class PedidoManager:
    def __init__(self):
        self.url_apps_script = URL_APPS_SCRIPT
        self.telegram_token = TELEGRAM_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
    
    def registrar_pedido(self, dni, nombre, detalle, total, direccion):
        try:
            params = {
                "accion": "nuevo",
                "tel": dni,
                "nombre": nombre,
                "detalle": detalle,
                "total": total,
                "dir": direccion
            }
            response = requests.get(self.url_apps_script, params=params, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error registrando pedido: {e}")
            return False
    
    def enviar_notificacion(self, nombre, dni, direccion, detalle, total, formatear_func):
        try:
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Aceptar (Preparando)", "callback_data": f"est_Preparando_{dni}"},
                        {"text": "🛵 Enviar (En Camino)", "callback_data": f"est_Enviado_{dni}"}
                    ],
                    [
                        {"text": "🏁 Completar (Listo)", "callback_data": f"est_Listo_{dni}"},
                        {"text": "❌ Cancelar", "callback_data": f"est_Cancelado_{dni}"}
                    ]
                ]
            }
            
            msg = (
                f"🔔 *NUEVO PEDIDO*\n\n"
                f"👤 *Cliente:* {nombre}\n"
                f"🆔 *DNI:* {dni}\n"
                f"📍 *Dirección:* {direccion}\n\n"
                f"*Detalle:*\n{detalle}\n\n"
                f"💰 *TOTAL: {formatear_func(total)}*\n"
                f"🕒 *Hora:* {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"📌 *Estado actual:* Pendiente"
            )
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                data={
                    "chat_id": self.telegram_chat_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(keyboard)
                },
                timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"Error en notificación: {e}")
            return False

# ==================== TEMAS ====================
def apply_custom_theme():
    config = cargar_config()
    primary = config.get('tema_primario', '#FF6B35')
    background = config.get('background_color', '#FFF8F0')
    
    custom_css = f"""
    <style>
        .stButton > button {{
            background-color: {primary} !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            border: none !important;
        }}
        h1, h2, h3 {{
            color: {primary} !important;
        }}
        .stApp {{
            background-color: {background} !important;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            margin-top: 40px;
        }}
        .stProgress > div > div {{
            background-color: {primary} !important;
        }}
        .diagnostico-box {{
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def mostrar_header():
    config = cargar_config()
    icono = config.get('icono', '🍔')
    if 'ð' in icono or 'Ÿ' in icono or 'Ã' in icono or len(icono) > 2:
        icono = '🍔'
    st.markdown(f"<h1 style='text-align: center;'>{icono} {config['nombre_local']}</h1>", unsafe_allow_html=True)
    if config.get('horario'):
        st.caption(f"🕒 {config['horario']}")
    if config.get('telefono'):
        st.caption(f"📱 {config['telefono']}")

def mostrar_productos():
    """Muestra productos con diagnóstico para ver errores"""
    
    # ========== DIAGNÓSTICO ==========
    with st.expander("🔍 DIAGNÓSTICO - Ver datos cargados", expanded=True):
        st.markdown('<div class="diagnostico-box">', unsafe_allow_html=True)
        
        df = cargar_productos()
        
        if df.empty:
            st.error("❌ No se pudieron cargar productos. Verifica la conexión con Google Sheets.")
            st.info("Revisa que el GID_PRODUCTOS en secrets.toml sea correcto")
            return
        
        st.write(f"**📊 Total de filas cargadas:** {len(df)}")
        st.write(f"**📋 Columnas encontradas:** {list(df.columns)}")
        
        # Verificar columnas necesarias
        columnas_necesarias = ['producto', 'precio']
        for col in columnas_necesarias:
            if col not in df.columns:
                st.error(f"❌ Falta la columna '{col}' en tu Google Sheets")
                st.stop()
        
        # Mostrar los primeros productos
        st.write("**📝 Primeros 3 productos (datos crudos):**")
        st.dataframe(df.head(3))
        
        # Verificar productos disponibles
        if 'disponible' in df.columns:
            disponibles = df[df['disponible'].str.upper() == 'SI']
            st.write(f"**✅ Productos con Disponible='SI':** {len(disponibles)} de {len(df)}")
            st.write(f"**Valores únicos en columna 'disponible':** {df['disponible'].unique()}")
        else:
            st.warning("⚠️ No se encontró la columna 'disponible'. Mostrando todos los productos.")
            disponibles = df
        
        if disponibles.empty:
            st.error("❌ No hay productos con Disponible='SI'")
            st.stop()
        
        # Mostrar resumen de variedades
        st.write("**📊 Resumen de variedades:**")
        for idx, row in disponibles.iterrows():
            producto = row.get('producto', 'Unknown')
            variedades_raw = row.get('variedades', 'Única')
            num_variedades = len(str(variedades_raw).split(';'))
            st.write(f"  - {producto}: {num_variedades} variedad(es) - '{variedades_raw}'")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    # ========== FIN DIAGNÓSTICO ==========
    
    # Mostrar productos
    for idx, row in disponibles.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                imagen_url = row.get('imagen', '')
                if pd.notna(imagen_url) and str(imagen_url).strip() != "":
                    try:
                        st.image(imagen_url, use_container_width=True)
                    except:
                        st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
                else:
                    st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
            
            with col2:
                nombre_producto = str(row.get('producto', 'Producto'))
                st.subheader(nombre_producto)
                
                # Obtener variedades, ingredientes y precios
                variedades_raw = row.get('variedades', 'Única')
                ingredientes_raw = row.get('ingredientes', '')
                precios_raw = row.get('precio', '0')
                
                # Separar por punto y coma y limpiar espacios
                variedades = [v.strip() for v in str(variedades_raw).split(';')]
                
                # Manejar ingredientes (pueden estar vacíos)
                if pd.notna(ingredientes_raw) and str(ingredientes_raw).strip():
                    ingredientes = [i.strip() for i in str(ingredientes_raw).split(';')]
                else:
                    ingredientes = [""] * len(variedades)
                
                # Manejar precios
                precios_raw_list = [p.strip() for p in str(precios_raw).split(';')]
                precios = []
                for p in precios_raw_list:
                    if p:
                        precios.append(limpiar_precio(p))
                    else:
                        precios.append(0)
                
                # Asegurar que todas las listas tengan la misma longitud
                while len(ingredientes) < len(variedades):
                    ingredientes.append("")
                while len(precios) < len(variedades):
                    precios.append(0)
                
                # Mostrar diagnóstico individual (solo en modo debug)
                with st.expander(f"🔧 Debug: {nombre_producto}"):
                    st.write(f"**Variedades:** {variedades}")
                    st.write(f"**Ingredientes:** {ingredientes}")
                    st.write(f"**Precios raw:** {precios_raw_list}")
                    st.write(f"**Precios limpios:** {precios}")
                
                # Si hay más de una variedad, mostrar como tabs
                if len(variedades) > 1:
                    tabs = st.tabs(variedades)
                    for i, tab in enumerate(tabs):
                        with tab:
                            if ingredientes[i] and ingredientes[i] != "":
                                st.info(f"✨ {ingredientes[i]}")
                            else:
                                st.caption("📌 Sin ingredientes detallados")
                            
                            if precios[i] > 0:
                                st.markdown(f"### {formatear_moneda(precios[i])}")
                            else:
                                st.markdown(f"### Precio no disponible")
                            
                            item_id = f"{nombre_producto}_{variedades[i]}_{idx}"
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            
                            col_a, col_b, col_c = st.columns([1, 1, 1])
                            with col_a:
                                if st.button("➖", key=f"minus_{item_id}"):
                                    if cant > 0:
                                        if cant == 1:
                                            del st.session_state.carrito[item_id]
                                        else:
                                            st.session_state.carrito[item_id]['cant'] -= 1
                                        st.rerun()
                            with col_b:
                                st.markdown(f"<h3 style='text-align: center;'>{cant}</h3>", unsafe_allow_html=True)
                            with col_c:
                                if st.button("➕", key=f"plus_{item_id}"):
                                    if item_id in st.session_state.carrito:
                                        st.session_state.carrito[item_id]['cant'] += 1
                                    else:
                                        st.session_state.carrito[item_id] = {
                                            'cant': 1, 
                                            'precio': precios[i],
                                            'nombre': f"{nombre_producto} ({variedades[i]})"
                                        }
                                    st.rerun()
                else:
                    # Una sola variedad
                    if ingredientes[0] and ingredientes[0] != "":
                        st.info(f"✨ {ingredientes[0]}")
                    
                    if precios[0] > 0:
                        st.markdown(f"### {formatear_moneda(precios[0])}")
                    else:
                        st.markdown(f"### Precio no disponible")
                    
                    item_id = f"{nombre_producto}_{idx}"
                    cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                    
                    col_a, col_b, col_c = st.columns([1, 1, 1])
                    with col_a:
                        if st.button("➖", key=f"minus_{item_id}"):
                            if cant > 0:
                                if cant == 1:
                                    del st.session_state.carrito[item_id]
                                else:
                                    st.session_state.carrito[item_id]['cant'] -= 1
                                st.rerun()
                    with col_b:
                        st.markdown(f"<h3 style='text-align: center;'>{cant}</h3>", unsafe_allow_html=True)
                    with col_c:
                        if st.button("➕", key=f"plus_{item_id}"):
                            if item_id in st.session_state.carrito:
                                st.session_state.carrito[item_id]['cant'] += 1
                            else:
                                st.session_state.carrito[item_id] = {
                                    'cant': 1, 
                                    'precio': precios[0],
                                    'nombre': nombre_producto
                                }
                            st.rerun()

# ==================== APP PRINCIPAL ====================
apply_custom_theme()
pedido_manager = PedidoManager()
conf = cargar_config()
costo_delivery = conf.get('costo_delivery', 500)

# Inicializar session state
if 'vista' not in st.session_state:
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'admin_logged' not in st.session_state:
    st.session_state.admin_logged = False
if 'admin_tipo' not in st.session_state:
    st.session_state.admin_tipo = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_dni' not in st.session_state:
    st.session_state.user_dni = None
if 'modo_diagnostico' not in st.session_state:
    st.session_state.modo_diagnostico = True  # Activado por defecto

def cerrar_sesion_admin():
    st.session_state.admin_logged = False
    st.session_state.admin_tipo = None
    st.session_state.vista = 'inicio'
    st.rerun()

def mostrar_carrito():
    if not st.session_state.carrito:
        return
    
    st.markdown("---")
    st.header("🛒 Resumen de tu Pedido")
    
    total_productos = 0
    detalle_para_envio = ""
    
    items_a_eliminar = []
    for item_id, datos in st.session_state.carrito.items():
        if datos.get('precio', 0) <= 0 or datos.get('cant', 0) <= 0:
            items_a_eliminar.append(item_id)
        else:
            subtotal = datos['cant'] * datos['precio']
            total_productos += subtotal
            nombre = datos.get('nombre', item_id)
            detalle_para_envio += f"• {datos['cant']}x {nombre}\n"
            st.write(f"**{datos['cant']}x** {nombre} → {formatear_moneda(subtotal)}")
    
    for item_id in items_a_eliminar:
        del st.session_state.carrito[item_id]
        if items_a_eliminar:
            st.rerun()
    
    metodo_entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
    direccion = "Retiro en Local"
    cargo_envio = 0
    
    if metodo_entrega == "Delivery":
        cargo_envio = costo_delivery
        direccion = st.text_input("🏠 Dirección de entrega:", placeholder="Calle y número")
        if direccion and direccion != "Retiro en Local":
            st.info(f"Costo de envío: {formatear_moneda(cargo_envio)}")
    
    total_final = total_productos + cargo_envio
    st.markdown(f"## TOTAL A PAGAR: {formatear_moneda(total_final)}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Vaciar carrito", use_container_width=True):
            st.session_state.carrito = {}
            st.rerun()
    with col2:
        if st.button("🚀 CONFIRMAR Y ENVIAR", use_container_width=True, type="primary"):
            if metodo_entrega == "Delivery" and (not direccion or direccion == "Retiro en Local"):
                st.error("Por favor, ingresá una dirección válida")
                return
            
            if st.session_state.user_dni and st.session_state.user_name:
                if pedido_manager.registrar_pedido(
                    st.session_state.user_dni,
                    st.session_state.user_name,
                    detalle_para_envio,
                    total_final,
                    direccion
                ):
                    pedido_manager.enviar_notificacion(
                        st.session_state.user_name,
                        st.session_state.user_dni,
                        direccion,
                        detalle_para_envio,
                        total_final,
                        formatear_moneda
                    )
                    st.success("¡Pedido enviado correctamente!")
                    st.balloons()
                    st.session_state.carrito = {}
                    time.sleep(2)
                    st.session_state.vista = 'inicio'
                    st.rerun()
            else:
                st.error("Error: No se encontraron los datos del usuario")

def login_admin():
    st.subheader("🔐 Panel de Administración")
    conf_actual = cargar_config()
    
    admin_dni = conf_actual.get('admin_dni', '30588807')
    admin_pass = conf_actual.get('admin_pass', '124578')
    user = conf_actual.get('user', 'usuario')
    user_pass = conf_actual.get('user_pass', 'usuario123')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    
    with col2:
        st.markdown("### Ingresa tus credenciales")
        usuario = st.text_input("DNI o Usuario")
        password = st.text_input("Contraseña", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Ingresar", type="primary", use_container_width=True):
                if usuario == admin_dni and password == admin_pass:
                    st.session_state.admin_logged = True
                    st.session_state.admin_tipo = "admin"
                    st.success("✅ Acceso ADMINISTRADOR concedido")
                    time.sleep(1)
                    st.rerun()
                elif usuario == user and password == user_pass:
                    st.session_state.admin_logged = True
                    st.session_state.admin_tipo = "user"
                    st.success("✅ Acceso USUARIO concedido")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        with col_b:
            if st.button("⬅ Volver al inicio", use_container_width=True):
                st.session_state.vista = 'inicio'
                st.rerun()

def panel_admin():
    if not st.session_state.get('admin_logged', False):
        login_admin()
        return
    
    conf_actual = cargar_config()
    tipo_usuario = st.session_state.get('admin_tipo', 'user')
    
    if tipo_usuario == "admin":
        st.title(f"👑 Panel de Administrador - {conf_actual['nombre_local']}")
        st.success("✅ Tienes acceso TOTAL al sistema")
    else:
        st.title(f"📱 Panel de Usuario - {conf_actual['nombre_local']}")
        st.info("ℹ️ Tienes acceso LIMITADO")
    
    st.markdown("---")
    
    if tipo_usuario == "admin":
        tabs = st.tabs(["📊 Dashboard", "📋 Pedidos", "⚙️ Configuración", "🤖 Ayuda"])
        
        with tabs[0]:
            st.subheader("Estadísticas del negocio")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pedidos hoy", "0")
            with col2:
                st.metric("Ingresos hoy", "$0")
            with col3:
                st.metric("Clientes", "0")
            st.info("📊 Las estadísticas se actualizarán automáticamente")
        
        with tabs[1]:
            st.subheader("Lista de pedidos")
            try:
                sheet_id = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
                gid_pedidos = "1395505058"
                url_pedidos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_pedidos}&cb={int(time.time())}"
                df_pedidos = pd.read_csv(url_pedidos)
                if not df_pedidos.empty:
                    st.dataframe(df_pedidos, use_container_width=True)
                else:
                    st.info("No hay pedidos registrados")
            except Exception as e:
                st.info("No se pudieron cargar los pedidos")
        
        with tabs[2]:
            st.subheader("Configuración actual")
            for key, value in conf_actual.items():
                if key not in ['admin_pass', 'user_pass']:
                    st.write(f"**{key}:** {value}")
            st.info("📝 Para modificar la configuración, edita tu Google Sheets")
        
        with tabs[3]:
            st.markdown("""
            ### 📋 Estados del pedido:
            - ⏳ **Pendiente**: Pedido recibido
            - 👨‍🍳 **Preparando**: En cocina
            - 🛵 **Enviado**: En camino
            - ✅ **Listo**: Completado
            - ❌ **Cancelado**: Anulado
            
            ### 🤖 Bot de Telegram:
            Los botones actualizan automáticamente el estado
            """)
    
    else:
        st.subheader("Panel de Usuario")
        st.info("Como usuario puedes ver tus pedidos desde la pantalla principal con 'RASTREAR MI PEDIDO'")
    
    st.markdown("---")
    
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        cerrar_sesion_admin()

def vista_inicio():
    mostrar_header()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'
            st.rerun()
    with col2:
        if st.button("🔍 RASTREAR MI PEDIDO", use_container_width=True):
            st.session_state.vista = 'rastreo'
            st.rerun()
    
    col3, col4, col5 = st.columns([1, 2, 1])
    with col4:
        if st.button("⚙️ ADMIN", use_container_width=True):
            st.session_state.vista = 'admin'
            st.rerun()
    
    with st.expander("ℹ️ Información del local"):
        if conf.get('direccion_local'):
            st.write(f"**📍 Dirección:** {conf['direccion_local']}")
        if conf.get('horario'):
            st.write(f"**📅 Horario:** {conf['horario']}")
        if conf.get('telefono'):
            st.write(f"**📱 Teléfono:** {conf['telefono']}")
        if conf.get('whatsapp'):
            st.write(f"**💬 WhatsApp:** {conf['whatsapp']}")
        st.write(f"**🚚 Costo de envío:** {formatear_moneda(costo_delivery)}")
    
    # Botón para desactivar diagnóstico
    if st.session_state.modo_diagnostico:
        if st.button("🔧 Desactivar modo diagnóstico", use_container_width=True):
            st.session_state.modo_diagnostico = False
            st.rerun()

def vista_rastreo():
    """Pantalla de rastreo de pedidos"""
    st.subheader("🔍 Estado de tu pedido")
    
    if st.button("⬅ Volver al inicio", use_container_width=True):
        st.session_state.vista = 'inicio'
        st.rerun()
    
    st.markdown("---")
    
    dni_input = st.text_input("Ingresá tu DNI (sin puntos)", placeholder="Ej: 30588807")
    
    if st.button("Buscar mi pedido", type="primary", use_container_width=True):
        if not dni_input:
            st.warning("⚠️ Por favor ingresá tu DNI")
            return
        
        dni_limpio = re.sub(r'[^\d]', '', str(dni_input))
        
        if len(dni_limpio) not in [7, 8]:
            st.error("❌ El DNI debe tener 7 u 8 dígitos")
            return
        
        try:
            with st.spinner("🔍 Buscando tu pedido..."):
                sheet_id = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
                gid_pedidos = "1395505058"
                url_pedidos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_pedidos}&cb={int(time.time())}"
                df_peds = pd.read_csv(url_pedidos)
                df_peds.columns = [c.strip().upper() for c in df_peds.columns]
                
                if 'DNI' not in df_peds.columns:
                    st.error("Error: La hoja de pedidos no tiene columna DNI")
                    return
                
                df_peds['DNI_LIMPIO'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
                pedidos_usuario = df_peds[df_peds['DNI_LIMPIO'] == dni_limpio].sort_values(by=['FECHA'], ascending=False)
                
                if pedidos_usuario.empty:
                    st.warning("❌ No encontramos pedidos con ese DNI")
                    st.info("💡 Si ya hiciste un pedido, asegurate de usar el mismo DNI que registraste")
                else:
                    pedido = pedidos_usuario.iloc[0]
                    
                    estado = pedido.get('ESTADO', 'Pendiente')
                    estado_emoji = {
                        'Pendiente': '⏳ Pendiente',
                        'Preparando': '👨‍🍳 En preparación',
                        'Enviado': '🛵 En camino',
                        'Listo': '✅ Listo para retirar',
                        'Cancelado': '❌ Cancelado'
                    }.get(estado, f'📦 {estado}')
                    
                    st.success(f"### 🎯 Hola {pedido['NOMBRE']}!")
                    st.markdown(f"### Estado de tu pedido: **{estado_emoji}**")
                    
                    estados_progreso = ['Pendiente', 'Preparando', 'Enviado', 'Listo']
                    if estado in estados_progreso:
                        progreso = estados_progreso.index(estado) + 1
                        st.progress(progreso / len(estados_progreso))
                    
                    with st.expander("📋 Ver detalles del pedido", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**📅 Fecha:**", pedido.get('FECHA', 'No registrada'))
                            st.write("**📍 Dirección:**", pedido.get('DIRECCION', 'Retiro en local'))
                        with col2:
                            total_limpio = limpiar_precio(pedido.get('TOTAL', '0'))
                            st.write("**💰 Total:**", formatear_moneda(total_limpio))
                            st.write("**🆔 DNI:**", pedido.get('DNI', ''))
                        
                        st.markdown("---")
                        st.write("**🍔 Detalle del pedido:**")
                        detalle = pedido.get('DETALLE', '')
                        if pd.notna(detalle) and str(detalle).strip():
                            lineas = str(detalle).split('\\n')
                            for linea in lineas:
                                if linea.strip():
                                    st.write(f"  {linea}")
                        else:
                            st.write("  No hay detalle disponible")
                            
        except Exception as e:
            st.error(f"❌ Error al consultar el estado: {e}")

def vista_pedir():
    if st.button("⬅ Volver al inicio"):
        st.session_state.vista = 'inicio'
        st.rerun()
    
    mostrar_header()
    
    if st.session_state.user_dni is None:
        with st.container(border=True):
            st.subheader("📝 Tus datos")
            nombre = st.text_input("Nombre completo*")
            dni = st.text_input("DNI (solo números)*")
            
            if st.button("Ingresar al Menú", type="primary", use_container_width=True):
                if nombre and dni:
                    dni_limpio = re.sub(r'[^\d]', '', str(dni))
                    if len(dni_limpio) in [7, 8]:
                        st.session_state.user_name = nombre
                        st.session_state.user_dni = dni_limpio
                        st.rerun()
                    else:
                        st.error("❌ El DNI debe tener 7 u 8 dígitos")
                else:
                    st.error("Por favor completá todos los datos")
        st.stop()
    
    mostrar_productos()
    mostrar_carrito()
    
    st.markdown("---")
    st.markdown(
        f"<div class='footer'>"
        f"{conf['icono']} {conf['nombre_local']} - Pedidos online<br>"
        f"© {datetime.now().year} - Todos los derechos reservados"
        f"</div>",
        unsafe_allow_html=True
    )

def main():
    conf_actual = cargar_config()
    
    if conf_actual.get('modo_mantenimiento', False):
        st.warning("🔧 El local está en mantenimiento. Volvemos pronto.")
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486899.png", width=200)
        st.info(f"📞 Contacto: {conf_actual.get('telefono', 'Consultar')}")
        return
    
    if st.session_state.vista == 'inicio':
        vista_inicio()
    elif st.session_state.vista == 'rastreo':
        vista_rastreo()
    elif st.session_state.vista == 'pedir':
        vista_pedir()
    elif st.session_state.vista == 'admin':
        panel_admin()

if __name__ == "__main__":
    main()

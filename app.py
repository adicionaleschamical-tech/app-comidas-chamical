import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import logging
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intentar cargar secrets
try:
    TELEGRAM_TOKEN = st.secrets["telegram"]["token"]
    TELEGRAM_CHAT_ID = st.secrets["telegram"]["chat_id"]
    ID_SHEET = st.secrets["sheets"]["id_sheet"]
    GID_CONFIG = st.secrets["sheets"]["gid_config"]
    GID_PRODUCTOS = st.secrets["sheets"]["gid_productos"]
    GID_PEDIDOS = st.secrets["sheets"]["gid_pedidos"]
except:
    TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
    TELEGRAM_CHAT_ID = "7860013984"
    ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
    GID_CONFIG = "612320365"
    GID_PRODUCTOS = "0"
    GID_PEDIDOS = "1395505058"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

# ==================== FUNCIONES DE APOYO ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    texto_limpio = str(texto).replace('.', '').replace(',', '')
    numeros = re.findall(r'\d+', texto_limpio)
    return int(''.join(numeros)) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

@st.cache_data(ttl=300)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), header=None)
        
        config = {}
        for _, row in df.iterrows():
            if pd.notna(row[0]):
                key = str(row[0]).strip()
                value = str(row[1]).strip() if pd.notna(row[1]) else ""
                config[key] = value
        
        return {
            'nombre_local': config.get('Nombre_Local', 'HAMBUR LOCOS'),
            'logo_url': config.get('Logo_URL', ''),
            'direccion_local': config.get('Direccion_Local', 'AVDA. SAN FRANCISCO KM 4 1/2'),
            'costo_delivery': limpiar_precio(config.get('Costo_Delivery', 500)),
            'telefono': config.get('Telefono', '3826430724'),
            'admin_dni': config.get('Admin_DNI', '30588807'),
            'admin_pass': config.get('Admin_Pass', '124578'),
            'user': config.get('User', 'usuario'),
            'user_pass': config.get('User_Pass', 'usuario123'),
            'modo_mantenimiento': config.get('MODO_MANTENIMIENTO', 'NO').upper() == 'SI',
            'tema_primario': config.get('Tema_Primario', '#FF6B35'),
            'tema_secundario': config.get('Tema_Secundario', '#FF6B35'),
            'horario': config.get('Horario', 'Lun-Dom 19:00 a 00:30'),
            'whatsapp': config.get('WhatsApp', '3826430724'),
            'icono': config.get('icono', '🍔'),
            'background_color': config.get('Background_Color', '#FFF8F0'),
        }
    except Exception as e:
        return {
            'nombre_local': 'HAMBUR LOCOS',
            'costo_delivery': 500,
            'admin_dni': '30588807',
            'admin_pass': '124578',
            'user': 'usuario',
            'user_pass': 'usuario123',
            'telefono': '3826430724',
            'direccion_local': 'AVDA. SAN FRANCISCO KM 4 1/2',
            'modo_mantenimiento': False,
            'tema_primario': '#FF6B35',
            'tema_secundario': '#FF6B35',
            'horario': 'Lun-Dom 19:00 a 00:30',
            'whatsapp': '3826430724',
            'icono': '🍔',
            'background_color': '#FFF8F0',
        }

@st.cache_data(ttl=60)
def cargar_productos():
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}", timeout=10)
        resp_p.raise_for_status()
        df_p = pd.read_csv(StringIO(resp_p.text))
        df_p.columns = [c.strip().lower() for c in df_p.columns]
        return df_p
    except:
        return pd.DataFrame()

# ==================== PEDIDO MANAGER ====================
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
        except:
            return False
    
    def enviar_notificacion(self, nombre, dni, direccion, detalle, total, formatear_func):
        try:
            msg = f"🔔 NUEVO PEDIDO\n\nCliente: {nombre}\nDNI: {dni}\nDirección: {direccion}\n\nDetalle:\n{detalle}\n\nTOTAL: {formatear_func(total)}"
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                data={"chat_id": self.telegram_chat_id, "text": msg}
            )
            return True
        except:
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
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def mostrar_header():
    config = cargar_config()
    st.markdown(f"<h1 style='text-align: center;'>{config['icono']} {config['nombre_local']}</h1>", unsafe_allow_html=True)
    if config.get('horario'):
        st.caption(f"🕒 {config['horario']}")
    if config.get('telefono'):
        st.caption(f"📱 {config['telefono']}")

def mostrar_productos():
    df = cargar_productos()
    if df.empty:
        st.warning("No hay productos disponibles")
        return
    
    for _, row in df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
            with col2:
                st.subheader(row.get('producto', 'Producto'))
                precio = limpiar_precio(row.get('precio', '0'))
                st.markdown(f"### {formatear_moneda(precio)}")
                
                item_id = str(row.get('producto', 'producto'))
                cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                
                if st.button("➕ Agregar", key=f"add_{item_id}"):
                    st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': precio}
                    st.rerun()
                if cant > 0:
                    st.caption(f"En carrito: {cant}")

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
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_dni' not in st.session_state:
    st.session_state.user_dni = None

def cerrar_sesion_admin():
    """Cierra la sesión de admin y vuelve al inicio"""
    st.session_state.admin_logged = False
    st.session_state.vista = 'inicio'
    st.rerun()

def mostrar_carrito():
    if not st.session_state.carrito:
        return
    
    st.markdown("---")
    st.header("🛒 Resumen de tu Pedido")
    
    total_productos = 0
    detalle_para_envio = ""
    
    for item, datos in st.session_state.carrito.items():
        subtotal = datos['cant'] * datos['precio']
        total_productos += subtotal
        detalle_para_envio += f"• {datos['cant']}x {item}\n"
        st.write(f"**{datos['cant']}x** {item} → {formatear_moneda(subtotal)}")
    
    metodo_entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
    direccion = "Retiro en Local"
    cargo_envio = 0
    
    if metodo_entrega == "Delivery":
        cargo_envio = costo_delivery
        direccion = st.text_input("🏠 Dirección de entrega:")
        if direccion:
            st.info(f"Costo de envío: {formatear_moneda(cargo_envio)}")
    
    total_final = total_productos + cargo_envio
    st.markdown(f"## TOTAL A PAGAR: {formatear_moneda(total_final)}")
    
    if st.button("🚀 CONFIRMAR Y ENVIAR", use_container_width=True, type="primary"):
        if metodo_entrega == "Delivery" and (not direccion or direccion == "Retiro en Local"):
            st.error("Por favor, ingresá una dirección válida")
            return
        
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

def login_admin():
    st.subheader("🔐 Panel de Administración")
    conf_actual = cargar_config()
    
    admin_dni = conf_actual.get('admin_dni', '30588807')
    admin_pass = conf_actual.get('admin_pass', '124578')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    
    with col2:
        usuario = st.text_input("DNI o Usuario")
        password = st.text_input("Contraseña", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Ingresar", type="primary", use_container_width=True):
                if usuario == admin_dni and password == admin_pass:
                    st.session_state.admin_logged = True
                    st.success("✅ Acceso concedido")
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
    st.title(f"👑 Panel de Administrador - {conf_actual['nombre_local']}")
    st.success("✅ Has iniciado sesión como ADMINISTRADOR")
    
    st.markdown("---")
    
    # Pestañas del panel de admin
    tabs = st.tabs(["📊 Dashboard", "📋 Pedidos", "⚙️ Configuración"])
    
    with tabs[0]:
        st.subheader("Estadísticas del negocio")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pedidos hoy", "0")
        with col2:
            st.metric("Ingresos hoy", "$0")
        with col3:
            st.metric("Clientes", "0")
    
    with tabs[1]:
        st.subheader("Lista de pedidos")
        try:
            df_pedidos = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
            if not df_pedidos.empty:
                st.dataframe(df_pedidos, use_container_width=True)
            else:
                st.info("No hay pedidos registrados")
        except:
            st.info("No se pudieron cargar los pedidos")
    
    with tabs[2]:
        st.subheader("Configuración actual")
        for key, value in conf_actual.items():
            if key not in ['admin_pass']:
                st.write(f"**{key}:** {value}")
        st.info("📝 Para modificar la configuración, edita tu Google Sheets")
    
    st.markdown("---")
    
    # Botón de cerrar sesión - VUELVE AL INICIO
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
        if st.button("⚙️ ADMIN", use_container_width=True):
            st.session_state.vista = 'admin'
            st.rerun()
    
    with st.expander("ℹ️ Información del local"):
        st.write(f"**📍 Dirección:** {conf.get('direccion_local', 'No especificada')}")
        st.write(f"**📅 Horario:** {conf.get('horario', 'No especificado')}")
        st.write(f"**📱 Teléfono:** {conf.get('telefono', 'No especificado')}")
        st.write(f"**🚚 Costo de envío:** {formatear_moneda(costo_delivery)}")

def vista_pedir():
    # Botón volver
    if st.button("⬅ Volver al inicio"):
        st.session_state.vista = 'inicio'
        st.rerun()
    
    mostrar_header()
    
    # Validar datos del usuario
    if st.session_state.user_dni is None:
        with st.container(border=True):
            st.subheader("📝 Tus datos")
            nombre = st.text_input("Nombre completo*")
            dni = st.text_input("DNI (solo números)*")
            
            if st.button("Ingresar al Menú", type="primary", use_container_width=True):
                if nombre and dni:
                    st.session_state.user_name = nombre
                    st.session_state.user_dni = dni
                    st.rerun()
                else:
                    st.error("Por favor completá todos los datos")
        st.stop()
    
    # Mostrar productos y carrito
    mostrar_productos()
    mostrar_carrito()
    
    # Footer
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
    
    # Verificar modo mantenimiento
    if conf_actual.get('modo_mantenimiento', False):
        st.warning("🔧 El local está en mantenimiento. Volvemos pronto.")
        st.info(f"📞 Contacto: {conf_actual.get('telefono', 'Consultar')}")
        return
    
    # Navegación
    if st.session_state.vista == 'inicio':
        vista_inicio()
    elif st.session_state.vista == 'pedir':
        vista_pedir()
    elif st.session_state.vista == 'admin':
        panel_admin()

if __name__ == "__main__":
    main()

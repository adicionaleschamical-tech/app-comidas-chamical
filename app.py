import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import logging
from datetime import datetime

from config import (
    cargar_config, limpiar_precio, formatear_moneda,
    cargar_productos, URL_PEDIDOS_BASE
)
from theme_manager import apply_custom_theme, mostrar_header, mostrar_productos
from pedido_manager import PedidoManager

# Configuración
logger = logging.getLogger(__name__)
apply_custom_theme()
pedido_manager = PedidoManager()
conf = cargar_config()
costo_delivery = conf.get('costo_delivery', 0)

# Inicializar session state
if 'vista' not in st.session_state:
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'admin_logged' not in st.session_state:
    st.session_state.admin_logged = False

def validar_dni(dni):
    """Valida formato de DNI"""
    dni_str = re.sub(r'[^\d]', '', str(dni))
    if len(dni_str) not in [7, 8]:
        return False, "El DNI debe tener 7 u 8 dígitos"
    return True, dni_str

def mostrar_carrito():
    """Muestra el resumen del carrito"""
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
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{datos['cant']}x** {item}")
        with col2:
            st.write(f"{formatear_moneda(subtotal)}")
    
    metodo_entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
    direccion = "Retiro en Local"
    cargo_envio = 0
    
    if metodo_entrega == "Delivery":
        cargo_envio = costo_delivery
        direccion = st.text_input("🏠 Dirección de entrega:", placeholder="Calle y número")
        if direccion:
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
    """Pantalla de login para administradores"""
    st.subheader("🔐 Panel de Administración")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    
    with col2:
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            if user == conf.get('user') and password == conf.get('user_pass'):
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

def panel_admin():
    """Panel de administración"""
    if not st.session_state.get('admin_logged', False):
        login_admin()
        return
    
    st.title(f"📊 Panel de {conf['nombre_local']}")
    
    tabs = st.tabs(["📈 Dashboard", "📋 Pedidos", "⚙️ Configuración", "ℹ️ Ayuda"])
    
    with tabs[0]:
        st.subheader("Estadísticas del día")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pedidos hoy", "0", "+0")
        with col2:
            st.metric("Ingresos hoy", "$0", "+0")
        with col3:
            st.metric("Clientes", "0", "+0")
        st.info("📊 Las estadísticas se actualizarán automáticamente cuando tengas pedidos")
    
    with tabs[1]:
        st.subheader("Pedidos")
        try:
            df_pedidos = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
            if not df_pedidos.empty:
                st.dataframe(df_pedidos, use_container_width=True)
            else:
                st.info("No hay pedidos registrados aún")
        except:
            st.info("No se pudieron cargar los pedidos")
    
    with tabs[2]:
        st.subheader("Configuración del negocio")
        st.info("📝 Edita estos valores directamente en tu Google Sheets")
        
        for key, value in conf.items():
            if key not in ['admin_pass_hash', 'user_pass']:
                st.text_input(key.replace('_', ' ').title(), value=value, disabled=True)
    
    with tabs[3]:
        st.subheader("Ayuda rápida")
        st.markdown("""
        ### 📋 Instrucciones:
        1. **Productos**: Edita la hoja "PRODUCTOS" en Google Sheets
        2. **Configuración**: Edita la hoja "CONFIGURACIÓN"
        3. **Pedidos**: Se ven automáticamente en la pestaña Pedidos
        
        ### 🎨 Personalización:
        - Cambia `Tema_Primario` y `Tema_Secundario` para cambiar colores
        - Agrega un `Logo_URL` para tu logo
        - Modifica `Horario` y `Telefono` para mostrar información de contacto
        """)
    
    if st.button("🚪 Cerrar sesión"):
        st.session_state.admin_logged = False
        st.rerun()

def vista_inicio():
    """Pantalla de inicio"""
    mostrar_header()
    
    # Botón de admin oculto (click en el icono)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("⚙️", help="Panel de administración"):
            st.session_state.vista = 'admin'
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'
            st.rerun()
    with col2:
        if st.button("🔍 RASTREAR MI PEDIDO", use_container_width=True):
            st.session_state.vista = 'rastreo'
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
        st.write(f"**🚚 Delivery:** {formatear_moneda(costo_delivery)}")

def vista_rastreo():
    """Pantalla de rastreo de pedidos"""
    st.subheader("🔍 Estado de tu pedido")
    
    if st.button("⬅ Volver", use_container_width=True):
        st.session_state.vista = 'inicio'
        st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI (sin puntos)", placeholder="Ej: 12345678")
    
    if st.button("Buscar mi pedido", type="primary"):
        if not dni_input:
            st.warning("Por favor ingresá tu DNI")
            return
        
        try:
            with st.spinner("Buscando tu pedido..."):
                df_peds = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
                df_peds.columns = [c.strip().upper() for c in df_peds.columns]
                dni_l = re.sub(r'[^\d]', '', str(dni_input))
                df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
                res = df_peds[df_peds['DNI_L'] == dni_l].tail(1)
                
                if not res.empty:
                    pedido = res.iloc[0]
                    estado = pedido.get('ESTADO', 'Pendiente')
                    
                    estado_emoji = {
                        'Pendiente': '⏳',
                        'Preparando': '👨‍🍳',
                        'Enviado': '🛵',
                        'Listo': '✅',
                        'Cancelado': '❌'
                    }.get(estado, '📦')
                    
                    st.success(f"Hola {pedido['NOMBRE']}, tu pedido está: **{estado_emoji} {estado}**")
                    
                    with st.expander("Ver detalles"):
                        st.write(f"**📍 Dirección:** {pedido.get('DIRECCION', 'Retiro en local')}")
                        st.write(f"**💰 Total:** {formatear_moneda(limpiar_precio(pedido.get('TOTAL', 0)))}")
                else:
                    st.warning("No encontramos pedidos con ese DNI")
        except Exception as e:
            st.error("Error al consultar el estado")

def vista_pedir():
    """Pantalla principal de pedidos"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅", help="Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
    with col2:
        mostrar_header()
    
    # Validar datos del usuario
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("📝 Tus datos")
            nombre = st.text_input("Nombre completo*")
            dni = st.text_input("DNI (solo números)*")
            
            if st.button("Ingresar al Menú", type="primary", use_container_width=True):
                if not nombre:
                    st.error("Por favor ingresá tu nombre")
                elif not dni:
                    st.error("Por favor ingresá tu DNI")
                else:
                    is_valid, msg = validar_dni(dni)
                    if is_valid:
                        st.session_state.user_name = nombre
                        st.session_state.user_dni = msg
                        st.rerun()
                    else:
                        st.error(msg)
        st.stop()
    
    # Mostrar productos
    mostrar_productos()
    
    # Mostrar carrito
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
    """Punto de entrada principal"""
    conf = cargar_config()
    
    # Verificar modo mantenimiento
    if conf.get('modo_mantenimiento', False):
        st.warning("🔧 El local está en mantenimiento. Volvemos pronto.")
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486899.png", width=200)
        st.info(f"📞 Contacto: {conf.get('telefono', 'Consultar')}")
        return
    
    # Navegación
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

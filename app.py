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
if 'admin_tipo' not in st.session_state:
    st.session_state.admin_tipo = None

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
            if metodo_entrega == "Delivery" and (not direccion or direccion == "Retiro en Local" or direccion.strip() == ""):
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
    """Pantalla de login - VERSIÓN CORREGIDA"""
    st.subheader("🔐 Panel de Administración")
    
    # Recargar configuración
    conf_actual = cargar_config()
    
    # Obtener credenciales
    admin_dni = conf_actual.get('admin_dni', '')
    admin_pass = conf_actual.get('admin_pass', '')
    user = conf_actual.get('user', '')
    user_pass = conf_actual.get('user_pass', '')
    
    # Diagnóstico (opcional - lo puedes quitar después)
    with st.expander("🔍 Diagnóstico - Ver configuración"):
        st.write("**Credenciales cargadas:**")
        st.write(f"Admin_DNI: '{admin_dni}'")
        st.write(f"Admin_Pass: '{'*' * len(admin_pass) if admin_pass else 'No encontrada'}'")
        st.write(f"User: '{user}'")
        st.write(f"User_Pass: '{'*' * len(user_pass) if user_pass else 'No encontrada'}'")
        
        if admin_dni and admin_pass:
            st.success("✅ Credenciales de ADMIN cargadas correctamente")
        else:
            st.error("❌ No se encontraron las credenciales de ADMIN")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    
    with col2:
        st.markdown("### Ingresa tus credenciales")
        
        usuario = st.text_input("DNI o Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary", use_container_width=True):
            usuario_limpio = usuario.strip() if usuario else ""
            password_limpia = password.strip() if password else ""
            
            # Mostrar comparación
            st.write("---")
            st.write("**Comparación:**")
            st.write(f"Usuario ingresado: '{usuario_limpio}'")
            st.write(f"Admin_DNI del sistema: '{admin_dni}'")
            st.write(f"¿Coinciden DNI? {usuario_limpio == admin_dni}")
            
            # Verificar ADMIN
            if usuario_limpio == admin_dni and password_limpia == admin_pass:
                st.success("✅ ACCESO ADMINISTRADOR CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "admin"
                time.sleep(1)
                st.rerun()
            
            # Verificar USUARIO
            elif usuario_limpio == user and password_limpia == user_pass:
                st.success("✅ ACCESO USUARIO CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "user"
                time.sleep(1)
                st.rerun()
            
            else:
                st.error("❌ DNI/Usuario o contraseña incorrectos")
                
                # Sugerencias específicas
                if usuario_limpio == admin_dni:
                    st.warning("⚠️ El DNI es correcto pero la contraseña no coincide")
                    if not admin_pass:
                        st.error("El sistema no encontró la contraseña en el Google Sheet")
                    else:
                        st.info(f"La contraseña configurada tiene {len(admin_pass)} caracteres")

def panel_admin():
    """Panel de administración"""
    
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
        st.info("ℹ️ Tienes acceso LIMITADO (solo para ver tus pedidos)")
    
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.admin_logged = False
        st.session_state.admin_tipo = None
        st.rerun()
    
    st.markdown("---")
    
    if tipo_usuario == "admin":
        tabs = st.tabs(["📈 Dashboard", "📋 Todos los Pedidos", "⚙️ Configuración", "ℹ️ Ayuda"])
        
        with tabs[0]:
            st.subheader("Estadísticas del negocio")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pedidos hoy", "0")
            with col2:
                st.metric("Ingresos hoy", "$0")
            with col3:
                st.metric("Clientes totales", "0")
            st.info("📊 Las estadísticas se actualizarán automáticamente cuando tengas pedidos")
        
        with tabs[1]:
            st.subheader("Todos los pedidos")
            try:
                df_pedidos = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
                if not df_pedidos.empty:
                    st.dataframe(df_pedidos, use_container_width=True)
                else:
                    st.info("No hay pedidos registrados aún")
            except Exception as e:
                st.info("No se pudieron cargar los pedidos")
        
        with tabs[2]:
            st.subheader("Configuración del negocio")
            st.info("📝 Edita estos valores directamente en tu Google Sheets")
            st.markdown("---")
            st.subheader("Credenciales configuradas:")
            st.write(f"**Admin DNI:** {conf_actual.get('admin_dni', 'No configurado')}")
            st.write(f"**Admin Pass:** {'✅ Configurada' if conf_actual.get('admin_pass') else '❌ No configurada'}")
            st.write(f"**User:** {conf_actual.get('user', 'No configurado')}")
            st.write(f"**User Pass:** {'✅ Configurada' if conf_actual.get('user_pass') else '❌ No configurada'}")
            st.markdown("---")
            st.subheader("Datos del negocio:")
            st.write(f"**Nombre:** {conf_actual.get('nombre_local')}")
            st.write(f"**Dirección:** {conf_actual.get('direccion_local')}")
            st.write(f"**Teléfono:** {conf_actual.get('telefono')}")
            st.write(f"**WhatsApp:** {conf_actual.get('whatsapp')}")
            st.write(f"**Horario:** {conf_actual.get('horario')}")
            st.write(f"**Delivery:** {formatear_moneda(conf_actual.get('costo_delivery', 0))}")
        
        with tabs[3]:
            st.markdown("""
            ### 📋 Privilegios de Administrador:
            - ✅ Ver TODOS los pedidos del negocio
            - ✅ Modificar configuración (via Google Sheets)
            - ✅ Ver estadísticas completas
            - ✅ Gestionar productos (via Google Sheets)
            
            ### 🔧 Para modificar la configuración:
            1. Abre tu Google Sheets
            2. Ve a la hoja "CONFIGURACION"
            3. Edita los valores que necesites
            4. Recarga esta página
            """)
    
    else:
        tabs = st.tabs(["📋 Mis Pedidos", "ℹ️ Información"])
        
        with tabs[0]:
            st.subheader("Mis pedidos")
            try:
                df_pedidos = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
                if not df_pedidos.empty:
                    df_pedidos.columns = [c.strip().upper() for c in df_pedidos.columns]
                    dni_usuario = conf_actual.get('user')
                    if 'DNI' in df_pedidos.columns and dni_usuario:
                        pedidos_usuario = df_pedidos[df_pedidos['DNI'].astype(str) == str(dni_usuario)]
                        if not pedidos_usuario.empty:
                            st.dataframe(pedidos_usuario, use_container_width=True)
                        else:
                            st.info("No tienes pedidos registrados")
                    else:
                        st.info("No se encontró la columna DNI en los pedidos")
                else:
                    st.info("No hay pedidos registrados aún")
            except Exception as e:
                st.info("No se pudieron cargar tus pedidos")
        
        with tabs[1]:
            st.markdown("""
            ### ℹ️ Información del usuario:
            
            Como usuario común puedes:
            - ✅ Ver tus propios pedidos
            - ✅ Hacer nuevos pedidos desde el menú principal
            
            ### 📞 Contacto del local:
            """)
            if conf_actual.get('telefono'):
                st.write(f"**Teléfono:** {conf_actual['telefono']}")
            if conf_actual.get('whatsapp'):
                st.write(f"**WhatsApp:** {conf_actual['whatsapp']}")
            if conf_actual.get('direccion_local'):
                st.write(f"**Dirección:** {conf_actual['direccion_local']}")

def vista_inicio():
    """Pantalla de inicio"""
    mostrar_header()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("⚙️ Admin", help="Panel de administración"):
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
        st.write(f"**🚚 Costo de envío:** {formatear_moneda(costo_delivery)}")

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
            st.error(f"Error al consultar el estado: {e}")

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
    conf_actual = cargar_config()
    
    # Verificar modo mantenimiento
    if conf_actual.get('modo_mantenimiento', False):
        st.warning("🔧 El local está en mantenimiento. Volvemos pronto.")
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486899.png", width=200)
        st.info(f"📞 Contacto: {conf_actual.get('telefono', 'Consultar')}")
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

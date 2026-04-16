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
    """Pantalla de login - VERSIÓN FLEXIBLE Y CORREGIDA"""
    st.subheader("🔐 Panel de Administración")
    
    # Recargar configuración
    conf_actual = cargar_config()
    
    # Obtener credenciales (ya vienen limpias desde config.py)
    admin_dni = conf_actual.get('admin_dni', '')
    admin_pass = conf_actual.get('admin_pass', '')
    user = conf_actual.get('user', '')
    user_pass = conf_actual.get('user_pass', '')
    
    # Diagnóstico
    with st.expander("🔍 DIAGNÓSTICO - Ver qué está leyendo el sistema"):
        st.write("**Valores leídos del Google Sheet:**")
        st.write(f"Admin_DNI: '{admin_dni}'")
        st.write(f"Admin_Pass: '{admin_pass}'")
        st.write(f"User: '{user}'")
        st.write(f"User_Pass: '{user_pass}'")
        
        if admin_dni and admin_pass:
            st.success("✅ Credenciales de ADMIN cargadas correctamente")
        else:
            st.error("❌ No se encontraron las credenciales de ADMIN")
            st.info("💡 Asegúrate que tu Google Sheet tenga las columnas: 'Admin_DNI' y 'Admin_Pass'")
    
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
            st.write("**🔍 Comparación:**")
            st.write(f"Usuario ingresado: '{usuario_limpio}'")
            st.write(f"Admin_DNI del sistema: '{admin_dni}'")
            st.write(f"¿Coinciden DNI? {usuario_limpio == admin_dni}")
            st.write(f"Password ingresada: '{password_limpia}'")
            st.write(f"Admin_Pass del sistema: '{admin_pass}'")
            st.write(f"¿Coinciden Pass? {password_limpia == admin_pass}")
            
            # Verificar ADMIN
            if usuario_limpio == admin_dni and password_limpia == admin_pass:
                st.success("✅ ACCESO ADMINISTRADOR CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "admin"
                time.sleep(2)
                st.rerun()
            
            # Verificar USUARIO
            elif usuario_limpio == user and password_limpia == user_pass:
                st.success("✅ ACCESO USUARIO CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "user"
                time.sleep(2)
                st.rerun()
            
            else:
                st.error("❌ DNI/Usuario o contraseña incorrectos")
                
                # Sugerencias específicas
                if usuario_limpio == admin_dni and password_limpia != admin_pass:
                    st.warning("⚠️ El DNI es correcto pero la contraseña no coincide")
                    if not admin_pass:
                        st.error("El sistema no encontró la contraseña. Verifica que la columna se llame 'Admin_Pass' en tu Google Sheet")
                elif usuario_limpio != admin_dni:
                    st.warning(f"⚠️ El DNI '{usuario_limpio}' no coincide con el configurado '{admin_dni}'")

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
        st.info("ℹ️ Tienes acceso LIMITADO")
    
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
        
        with tabs[1]:
            st.subheader("Todos los pedidos")
            try:
                df_pedidos = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
                if not df_pedidos.empty:
                    st.dataframe(df_pedidos, use_container_width=True)
                else:
                    st.info("No hay pedidos registrados aún")
            except:
                st.info("No se pudieron cargar los pedidos")
        
        with tabs[2]:
            st.subheader("Configuración")
            st.write(f"**Admin DNI:** {'✅ Configurado' if conf_actual.get('admin_dni') else '❌ No'}")
            st.write(f"**Admin Pass:** {'✅ Configurada' if conf_actual.get('admin_pass') else '❌ No'}")
            st.write(f"**User:** {'✅ Configurado' if conf_actual.get('user') else '❌ No'}")
            st.write(f"**User Pass:** {'✅ Configurada' if conf_actual.get('user_pass') else '❌ No'}")
        
        with tabs[3]:
            st.markdown("""
            ### 📋 Privilegios:
            - ✅ Ver todos los pedidos
            - ✅ Modificar configuración
            - ✅ Gestionar productos
            """)
    
    else:
        tabs = st.tabs(["📋 Mis Pedidos", "ℹ️ Información"])
        
        with tabs[0]:
            st.subheader("Mis pedidos")
            st.info("Aquí verás tus pedidos cuando tengas alguno")
        
        with tabs[1]:
            st.markdown("""
            ### ℹ️ Información:
            - ✅ Ver tus pedidos
            - ✅ Hacer nuevos pedidos
            """)

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
        st.write(f"**🚚 Delivery:** {formatear_moneda(costo_delivery)}")

def vista_rastreo():
    """Pantalla de rastreo"""
    st.subheader("🔍 Estado de tu pedido")
    
    if st.button("⬅ Volver", use_container_width=True):
        st.session_state.vista = 'inicio'
        st.rerun()
    
    dni_input = st.text_input("Ingresá tu DNI", placeholder="Ej: 12345678")
    
    if st.button("Buscar", type="primary"):
        if not dni_input:
            st.warning("Ingresá tu DNI")
            return
        
        try:
            df_peds = pd.read_csv(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
            df_peds.columns = [c.strip().upper() for c in df_peds.columns]
            dni_l = re.sub(r'[^\d]', '', str(dni_input))
            df_peds['DNI_L'] = df_peds['DNI'].astype(str).str.replace(r'[^\d]', '', regex=True)
            res = df_peds[df_peds['DNI_L'] == dni_l].tail(1)
            
            if not res.empty:
                pedido = res.iloc[0]
                estado = pedido.get('ESTADO', 'Pendiente')
                st.success(f"Tu pedido está: **{estado}**")
            else:
                st.warning("No se encontró el DNI")
        except:
            st.error("Error al consultar")

def vista_pedir():
    """Pantalla de pedidos"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅"):
            st.session_state.vista = 'inicio'
            st.rerun()
    with col2:
        mostrar_header()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            st.subheader("📝 Tus datos")
            nombre = st.text_input("Nombre completo*")
            dni = st.text_input("DNI*")
            
            if st.button("Ingresar", type="primary"):
                if nombre and dni:
                    is_valid, msg = validar_dni(dni)
                    if is_valid:
                        st.session_state.user_name = nombre
                        st.session_state.user_dni = msg
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Completá todos los datos")
        st.stop()
    
    mostrar_productos()
    mostrar_carrito()
    
    st.markdown("---")
    st.markdown(
        f"<div class='footer'>{conf['icono']} {conf['nombre_local']} - Pedidos online</div>",
        unsafe_allow_html=True
    )

def main():
    conf_actual = cargar_config()
    
    if conf_actual.get('modo_mantenimiento', False):
        st.warning("🔧 Local en mantenimiento")
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

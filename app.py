import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import logging
from datetime import datetime

# Importar módulos
from config import (
    cargar_config, limpiar_precio, formatear_moneda,
    URL_PRODUCTOS, URL_PEDIDOS_BASE
)
from theme_manager import apply_custom_theme, mostrar_header
from pedido_manager import PedidoManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INICIALIZACIÓN ---
apply_custom_theme()
pedido_manager = PedidoManager()
conf = cargar_config()
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

# Inicializar session state
if 'vista' not in st.session_state:
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'carrito_backup' not in st.session_state:
    st.session_state.carrito_backup = {}

# --- FUNCIONES AUXILIARES ---
@st.cache_data(ttl=60)
def cargar_productos():
    """Carga productos con caché y manejo de errores"""
    try:
        with st.spinner("Cargando menú..."):
            resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}", timeout=10)
            resp_p.raise_for_status()
            df_p = pd.read_csv(StringIO(resp_p.text))
            df_p.columns = [c.strip().upper() for c in df_p.columns]
            return df_p
    except Exception as e:
        logger.error(f"Error cargando productos: {e}")
        st.error("Error al cargar el menú. Por favor recargá la página.")
        return pd.DataFrame()

def validar_dni(dni):
    """Valida formato de DNI"""
    dni_str = re.sub(r'[^\d]', '', str(dni))
    if len(dni_str) not in [7, 8]:
        return False, "El DNI debe tener 7 u 8 dígitos"
    return True, dni_str

def guardar_carrito_backup():
    """Guarda backup del carrito"""
    st.session_state.carrito_backup = st.session_state.carrito.copy()

def mostrar_productos():
    """Muestra el grid de productos"""
    df_p = cargar_productos()
    if df_p.empty:
        return
    
    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                # Imagen
                img_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) else None
                if img_url and img_url.startswith('http'):
                    st.image(img_url, use_container_width=True)
                
                # Nombre del producto
                st.subheader(row['PRODUCTO'])
                
                # Variedades
                v_noms = str(row['VARIEDADES']).split(';')
                v_ings = str(row['INGREDIENTES']).split(';') if pd.notna(row['INGREDIENTES']) else []
                v_pres = str(row['PRECIO']).split(';')
                
                if len(v_noms) > 1:
                    tabs = st.tabs([v.strip() for v in v_noms])
                    for i, tab in enumerate(tabs):
                        with tab:
                            _mostrar_variedad(row, i, v_noms, v_ings, v_pres)
                else:
                    _mostrar_variedad(row, 0, v_noms, v_ings, v_pres)

def _mostrar_variedad(row, idx, v_noms, v_ings, v_pres):
    """Muestra una variedad del producto"""
    nom_v = v_noms[idx].strip() if idx < len(v_noms) else "Única"
    pre_v = limpiar_precio(v_pres[idx]) if idx < len(v_pres) else 0
    
    if idx < len(v_ings) and v_ings[idx].strip():
        st.info(f"✨ {v_ings[idx].strip()}")
    
    st.markdown(f"### {formatear_moneda(pre_v)}")
    
    item_id = f"{row['PRODUCTO']} ({nom_v})"
    cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    if col1.button("➖", key=f"m_{item_id}"):
        if cant > 0:
            st.session_state.carrito[item_id]['cant'] -= 1
            if st.session_state.carrito[item_id]['cant'] == 0:
                del st.session_state.carrito[item_id]
            st.rerun()
    
    col2.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
    
    if col3.button("➕", key=f"p_{item_id}"):
        st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': pre_v}
        guardar_carrito_backup()
        st.rerun()

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
            st.error("Por favor, ingresá una dirección válida.")
            return
        
        # Registrar pedido
        if pedido_manager.registrar_pedido(
            st.session_state.user_dni,
            st.session_state.user_name,
            detalle_para_envio,
            total_final,
            direccion
        ):
            # Enviar notificación
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

# --- VISTAS PRINCIPALES ---
def vista_inicio():
    """Pantalla de inicio"""
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
    
    # Mostrar información del local
    with st.expander("ℹ️ Información del local"):
        st.write(f"**📅 Horario:** {conf.get('horario', 'Consultar')}")
        if conf.get('whatsapp'):
            st.write(f"**📱 WhatsApp:** {conf['whatsapp']}")
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
                    estado = pedido['ESTADO']
                    
                    # Emojis según estado
                    estado_emoji = {
                        'Pendiente': '⏳',
                        'Preparando': '👨‍🍳',
                        'Enviado': '🛵',
                        'Listo': '✅',
                        'Cancelado': '❌'
                    }.get(estado, '📦')
                    
                    st.success(f"Hola {pedido['NOMBRE']}, tu pedido está: **{estado_emoji} {estado}**")
                    
                    # Mostrar más detalles
                    with st.expander("Ver detalles del pedido"):
                        st.write(f"**📍 Dirección:** {pedido.get('DIRECCION', 'Retiro en local')}")
                        st.write(f"**💰 Total:** {formatear_moneda(limpiar_precio(pedido.get('TOTAL', 0)))}")
                else:
                    st.warning("No encontramos pedidos con ese DNI")
        except Exception as e:
            logger.error(f"Error en rastreo: {e}")
            st.error("Error al consultar el estado del pedido")

def vista_pedir():
    """Pantalla principal de pedidos"""
    # Header con botón volver
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅", help="Volver al inicio"):
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
    
    # Footer personalizado
    st.markdown("---")
    st.markdown(
        f"<div class='footer'>"
        f"🍔 {conf['Nombre_Local']} - Pedidos online<br>"
        f"© {datetime.now().year} - Todos los derechos reservados"
        f"</div>",
        unsafe_allow_html=True
    )

# --- MAIN ---
def main():
    """Punto de entrada principal"""
    try:
        if st.session_state.vista == 'inicio':
            vista_inicio()
        elif st.session_state.vista == 'rastreo':
            vista_rastreo()
        elif st.session_state.vista == 'pedir':
            vista_pedir()
    except Exception as e:
        logger.error(f"Error en main: {e}")
        st.error("Ocurrió un error inesperado. Por favor recargá la página.")
        if st.button("Recargar"):
            st.rerun()

if __name__ == "__main__":
    main()

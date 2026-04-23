import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
from datetime import datetime
import json

# ==================== CONFIGURACIÓN CRÍTICA ====================
# 1. PEGA AQUÍ TU URL DE GOOGLE APPS SCRIPT (LA QUE TERMINA EN /exec)
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbymW0gaCBRJPTdG7kckbMmTYWJE6dbT_HvZMDrfzgZHaWbM8PFbd3oiizRegD2-7J-Pgw/exec"

# 2. DATOS DE TU PLANILLA
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365"
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

# 3. TELEGRAM
TELEGRAM_TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es"
TELEGRAM_CHAT_ID = "7860013984"

# 4. CONTRASEÑA PARA ADMIN (CÁMBIALA POR LA QUE QUIERAS)
ADMIN_PASSWORD = "admin123"

# URLs de descarga
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# ==================== FUNCIONES LÓGICAS ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "": return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

@st.cache_data(ttl=60)
def cargar_datos(url):
    try:
        resp = requests.get(f"{url}&cb={int(time.time())}", timeout=10)
        return pd.read_csv(StringIO(resp.text))
    except:
        return pd.DataFrame()

def obtener_configuracion():
    """Obtiene toda la configuración desde el sheet"""
    try:
        df_config = cargar_datos(URL_CONFIG)
        config = {}
        if not df_config.empty:
            for _, row in df_config.iterrows():
                config[row['parametro']] = row['valor']
        return config
    except:
        return {}

def obtener_nombre_local():
    """Lee el nombre del local desde la hoja CONFIG"""
    config = obtener_configuracion()
    return config.get('nombre_local', 'HAMBUR LOCOS')

def guardar_configuracion(parametro, valor):
    """Guarda/actualiza un valor en la hoja CONFIG via Apps Script"""
    params = {
        "accion": "guardar_config",
        "parametro": parametro,
        "valor": valor
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15, allow_redirects=True)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def guardar_producto(producto, precio):
    """Guarda/actualiza un producto en la hoja PRODUCTOS via Apps Script"""
    params = {
        "accion": "guardar_producto",
        "producto": producto,
        "precio": precio
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15, allow_redirects=True)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error al guardar producto: {e}")
        return False

def eliminar_producto(producto):
    """Elimina un producto de la hoja PRODUCTOS via Apps Script"""
    params = {
        "accion": "eliminar_producto",
        "producto": producto
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15, allow_redirects=True)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error al eliminar producto: {e}")
        return False

# ==================== CLASE MANAGER ====================
class PedidoManager:
    def registrar(self, dni, nombre, detalle, total, direccion):
        params = {
            "accion": "nuevo",
            "tel": dni,
            "nombre": nombre,
            "detalle": detalle,
            "total": total,
            "dir": direccion
        }
        try:
            r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15, allow_redirects=True)
            return "OK" in r.text
        except Exception as e:
            st.error(f"Error de red: {e}")
            return False

    def notificar_telegram(self, nombre, dni, direccion, detalle, total):
        keyboard = {
            "inline_keyboard": [
                [{"text": "👨‍🍳 Preparando", "callback_data": f"est_Preparando_{dni}"},
                 {"text": "🛵 Enviado", "callback_data": f"est_Enviado_{dni}"}],
                [{"text": "✅ Finalizado", "callback_data": f"est_Listo_{dni}"}]
            ]
        }
        msg = f"🔔 *NUEVO PEDIDO*\n\n👤 {nombre}\n🆔 DNI: {dni}\n📍 {direccion}\n\n*Detalle:*\n{detalle}\n💰 *TOTAL: {formatear_moneda(total)}*"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)})

# ==================== INTERFAZ ====================
if 'vista' not in st.session_state: 
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: 
    st.session_state.carrito = {}
if 'admin_autenticado' not in st.session_state:
    st.session_state.admin_autenticado = False

def main():
    # Leer nombre del local desde la configuración
    nombre_local = obtener_nombre_local()
    
    st.set_page_config(page_title=nombre_local, page_icon="🍔")

    # VISTA DE INICIO
    if st.session_state.vista == 'inicio':
        st.title(f"🍔 {nombre_local}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 HACER PEDIDO", use_container_width=True):
                st.session_state.vista = 'pedir'
                st.session_state.admin_autenticado = False
                st.rerun()
        with col2:
            if st.button("⚙️ ADMIN", use_container_width=True):
                st.session_state.vista = 'admin_login'
                st.rerun()

    # LOGIN DE ADMIN
    elif st.session_state.vista == 'admin_login':
        st.subheader("🔐 Acceso Administrador")
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        with st.form("login_admin"):
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_autenticado = True
                    st.session_state.vista = 'admin'
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")

    # PANEL DE ADMINISTRACIÓN
    elif st.session_state.vista == 'admin':
        st.subheader("⚙️ Panel de Administración")
        
        if st.button("⬅ Volver al Inicio"):
            st.session_state.vista = 'inicio'
            st.session_state.admin_autenticado = False
            st.rerun()
        
        # Pestañas para diferentes secciones
        tab1, tab2, tab3, tab4 = st.tabs(["🏪 Configuración Local", "🍔 Productos", "📊 Pedidos", "🔧 Diagnóstico"])
        
        # TAB 1: CONFIGURACIÓN DEL LOCAL
        with tab1:
            st.subheader("Configuración del Local")
            
            # Cargar configuración actual
            config_actual = obtener_configuracion()
            
            # Formulario para editar configuración
            with st.form("editar_config"):
                nombre = st.text_input("Nombre del Local", config_actual.get('nombre_local', ''))
                direccion = st.text_area("Dirección", config_actual.get('direccion', ''))
                telefono = st.text_input("Teléfono", config_actual.get('telefono', ''))
                horario = st.text_input("Horario de Atención", config_actual.get('horario', ''))
                
                if st.form_submit_button("💾 Guardar Configuración"):
                    if guardar_configuracion('nombre_local', nombre):
                        st.success("✅ Nombre del local actualizado")
                    if guardar_configuracion('direccion', direccion):
                        st.success("✅ Dirección actualizada")
                    if guardar_configuracion('telefono', telefono):
                        st.success("✅ Teléfono actualizado")
                    if guardar_configuracion('horario', horario):
                        st.success("✅ Horario actualizado")
                    
                    # Limpiar cache para recargar
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
        
        # TAB 2: GESTIÓN DE PRODUCTOS
        with tab2:
            st.subheader("Gestión de Productos")
            
            # Formulario para agregar/editar producto
            with st.expander("➕ Agregar/Editar Producto"):
                with st.form("form_producto"):
                    nombre_producto = st.text_input("Nombre del Producto")
                    precio_producto = st.number_input("Precio", min_value=0, step=100)
                    
                    if st.form_submit_button("💾 Guardar Producto"):
                        if nombre_producto and precio_producto > 0:
                            if guardar_producto(nombre_producto, precio_producto):
                                st.success(f"✅ Producto {nombre_producto} guardado")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("❌ Complete todos los campos")
            
            # Lista de productos actuales con opción de eliminar
            st.subheader("Productos Actuales")
            df_productos = cargar_datos(URL_PRODUCTOS)
            
            if not df_productos.empty:
                for idx, row in df_productos.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{row['producto']}**")
                    with col2:
                        st.write(formatear_moneda(limpiar_precio(row['precio'])))
                    with col3:
                        if st.button("🗑️", key=f"del_{idx}"):
                            if eliminar_producto(row['producto']):
                                st.success(f"✅ {row['producto']} eliminado")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
            else:
                st.info("No hay productos cargados")
        
        # TAB 3: PEDIDOS
        with tab3:
            st.subheader("Historial de Pedidos")
            
            # Botón para refrescar
            if st.button("🔄 Refrescar Pedidos"):
                st.cache_data.clear()
                st.rerun()
            
            df_pedidos = cargar_datos(URL_PEDIDOS_BASE)
            if not df_pedidos.empty:
                # Mostrar pedidos recientes (últimos 20)
                df_pedidos = df_pedidos.tail(20).iloc[::-1]  # Invertir orden
                for idx, row in df_pedidos.iterrows():
                    with st.container(border=True):
                        st.write(f"**Pedido #{idx+1}** - {row.get('fecha', 'Sin fecha')}")
                        st.write(f"👤 {row.get('nombre', 'N/A')} - DNI: {row.get('tel', 'N/A')}")
                        st.write(f"📍 {row.get('dir', 'N/A')}")
                        st.write(f"📝 {row.get('detalle', 'N/A')}")
                        st.write(f"💰 {formatear_moneda(limpiar_precio(row.get('total', 0)))}")
                        st.divider()
            else:
                st.info("No hay pedidos registrados")
        
        # TAB 4: DIAGNÓSTICO
        with tab4:
            st.subheader("🔧 Diagnóstico del Sistema")
            
            if st.button("Ejecutar Test de Conexión"):
                res = requests.get(f"{URL_APPS_SCRIPT}?accion=test&cb={int(time.time())}", allow_redirects=True)
                st.code(f"Respuesta de Google Apps Script: {res.text}")
                
                if "OK" in res.text:
                    st.success("✅ Conexión exitosa con Google Sheets")
                else:
                    st.error("❌ Problemas de conexión. Verifica los permisos.")
            
            # Mostrar configuración actual
            with st.expander("Ver Configuración Actual"):
                config = obtener_configuracion()
                st.json(config)

    # VISTA DE PEDIDO (CLIENTE)
    elif st.session_state.vista == 'pedir':
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.session_state.carrito = {}
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("login"):
                nombre_local = obtener_nombre_local()
                st.write(f"Bienvenido a **{nombre_local}**")
                n = st.text_input("Tu Nombre")
                d = st.text_input("Tu DNI (sin puntos)")
                if st.form_submit_button("Entrar a la Carta"):
                    if n and d:
                        st.session_state.user_name = n
                        st.session_state.user_dni = d
                        st.rerun()
            return

        # Cargar Productos
        df = cargar_datos(URL_PRODUCTOS)
        if not df.empty:
            st.subheader("📋 Nuestra Carta")
            for i, r in df.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{r['producto']}**")
                    with col2:
                        p = limpiar_precio(r['precio'])
                        st.write(formatear_moneda(p))
                    with col3:
                        if st.button(f"Añadir", key=f"btn_{i}"):
                            st.session_state.carrito[r['producto']] = st.session_state.carrito.get(r['producto'], 0) + 1
                            st.toast(f"✓ Añadido: {r['producto']}", icon="🍔")
        
        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 Tu Carrito")
            resumen = ""
            total = 0
            for k, v in st.session_state.carrito.items():
                st.write(f"{v}x {k}")
                resumen += f"• {v}x {k}\n"
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Vaciar Carrito"):
                    st.session_state.carrito = {}
                    st.rerun()
            with col2:
                if st.button("🚀 ENVIAR PEDIDO", type="primary"):
                    mgr = PedidoManager()
                    if mgr.registrar(st.session_state.user_dni, st.session_state.user_name, resumen, 0, "Local"):
                        mgr.notificar_telegram(st.session_state.user_name, st.session_state.user_dni, "Local", resumen, 0)
                        st.success("✅ ¡Pedido enviado con éxito!")
                        st.session_state.carrito = {}
                        st.session_state.pop('user_name', None)
                        st.session_state.pop('user_dni', None)
                        time.sleep(2)
                        st.session_state.vista = 'inicio'
                        st.rerun()
                    else:
                        st.error("❌ Error al enviar el pedido")

if __name__ == "__main__":
    main()

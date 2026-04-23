import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
from datetime import datetime
import json
import base64

# ==================== CONFIGURACIÓN ====================
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwn1XLeQTH0VI3ROo3iu9-vDy4Cs211ClMCYgTC5RsOOnvIQoafVb7sze22qZVhApQfCQ/exec"

ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365"
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

TELEGRAM_TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es"
TELEGRAM_CHAT_ID = "7860013984"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# ==================== FUNCIONES UNIVERSALES ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

@st.cache_data(ttl=60)
def cargar_datos(url):
    try:
        resp = requests.get(f"{url}&cb={int(time.time())}", timeout=10)
        resp.raise_for_status()
        return pd.read_csv(StringIO(resp.text))
    except Exception as e:
        return pd.DataFrame()

def obtener_toda_configuracion():
    """Lee toda la configuración del sheet sin importar los nombres de columnas"""
    try:
        df = cargar_datos(URL_CONFIG)
        config = {}
        
        if df.empty:
            return config
        
        # La primera columna es la clave, la segunda es el valor
        # (funciona con cualquier nombre de columna)
        if len(df.columns) >= 2:
            col_clave = df.columns[0]
            col_valor = df.columns[1]
            
            for _, row in df.iterrows():
                clave = str(row[col_clave]).strip() if pd.notna(row[col_clave]) else ""
                valor = str(row[col_valor]).strip() if pd.notna(row[col_valor]) else ""
                if clave:
                    config[clave] = valor
        
        return config
    except Exception as e:
        st.error(f"Error en configuración: {e}")
        return {}

def obtener_valor_config(clave, valor_defecto=""):
    """Obtiene un valor de configuración sin importar mayúsculas/minúsculas"""
    config = obtener_toda_configuracion()
    
    # Buscar exacto
    if clave in config:
        return config[clave]
    
    # Buscar sin importar mayúsculas/minúsculas
    for k, v in config.items():
        if k.lower() == clave.lower():
            return v
    
    return valor_defecto

def verificar_credenciales(tipo, valor_ingresado):
    """Verifica credenciales de admin o usuario desde el sheet"""
    if tipo == "admin":
        pass_correcta = obtener_valor_config("Admin_Pass", "")
        dni_correcto = obtener_valor_config("Admin_DNI", "")
        
        # Puede ingresar con DNI o con contraseña
        if valor_ingresado == pass_correcta or valor_ingresado == dni_correcto:
            return True
    
    elif tipo == "usuario":
        user_correcto = obtener_valor_config("User", "")
        pass_correcta = obtener_valor_config("User_Pass", "")
        
        if valor_ingresado == user_correcto or valor_ingresado == pass_correcta:
            return True
    
    return False

def esta_en_mantenimiento():
    """Verifica si el sistema está en modo mantenimiento"""
    modo = obtener_valor_config("MODO_MANTENIMIENTO", "NO")
    return modo.upper() == "SI"

def aplicar_tema():
    """Aplica los colores y fuentes desde la configuración"""
    tema_primario = obtener_valor_config("Tema_Primario", "#FF6B35")
    tema_secundario = obtener_valor_config("Tema_Secundario", "#FF6B35")
    bg_color = obtener_valor_config("Background_Color", "#FFF8F0")
    font_family = obtener_valor_config("Font_Family", "'Poppins', sans-serif")
    
    st.markdown(f"""
        <style>
        :root {{
            --primary: {tema_primario};
            --secondary: {tema_secundario};
            --background: {bg_color};
        }}
        .stApp {{
            background-color: {bg_color};
        }}
        .stButton > button {{
            background-color: {tema_primario};
            color: white;
            font-family: {font_family};
        }}
        .stButton > button:hover {{
            background-color: {tema_secundario};
        }}
        h1, h2, h3, h4, h5, h6, p, div {{
            font-family: {font_family};
        }}
        </style>
    """, unsafe_allow_html=True)

def mostrar_logo():
    """Muestra el logo si está configurado"""
    logo_url = obtener_valor_config("Logo_URL", "")
    if logo_url and logo_url != "":
        try:
            st.image(logo_url, width=150)
        except:
            pass

def guardar_configuracion(parametro, valor):
    """Guarda/actualiza configuración en Google Sheets"""
    params = {
        "accion": "guardar_config",
        "parametro": parametro,
        "valor": valor
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def guardar_producto(producto, precio):
    params = {
        "accion": "guardar_producto",
        "producto": producto,
        "precio": precio
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def eliminar_producto(producto):
    params = {
        "accion": "eliminar_producto",
        "producto": producto
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        return "OK" in r.text
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# ==================== CLASE PEDIDO ====================
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
            r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
            return "OK" in r.text
        except Exception as e:
            st.error(f"Error: {e}")
            return False

    def notificar_telegram(self, nombre, dni, direccion, detalle, total):
        costo_delivery = obtener_valor_config("Costo_Delivery", "0")
        keyboard = {
            "inline_keyboard": [
                [{"text": "👨‍🍳 Preparando", "callback_data": f"est_Preparando_{dni}"},
                 {"text": "🛵 Enviado", "callback_data": f"est_Enviado_{dni}"}],
                [{"text": "✅ Finalizado", "callback_data": f"est_Listo_{dni}"}]
            ]
        }
        msg = f"🔔 *NUEVO PEDIDO*\n\n👤 {nombre}\n🆔 DNI: {dni}\n📍 {direccion}\n\n*Detalle:*\n{detalle}\n💰 *TOTAL: {formatear_moneda(total)}*\n🚚 *Delivery: {formatear_moneda(int(costo_delivery))}*"
        
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                         data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)})
        except:
            pass

# ==================== INTERFAZ PRINCIPAL ====================
if 'vista' not in st.session_state:
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'admin_autenticado' not in st.session_state:
    st.session_state.admin_autenticado = False
if 'usuario_autenticado' not in st.session_state:
    st.session_state.usuario_autenticado = False

def main():
    # Verificar modo mantenimiento
    if esta_en_mantenimiento() and st.session_state.vista != 'admin' and not st.session_state.admin_autenticado:
        st.title("🔧 MANTENIMIENTO")
        st.warning("El sistema está en mantenimiento. Los pedidos no están disponibles temporalmente.")
        
        if st.button("🔐 Acceso Administrador"):
            st.session_state.vista = 'admin_login'
            st.rerun()
        return
    
    # Aplicar tema visual
    aplicar_tema()
    
    # Obtener nombre del local
    nombre_local = obtener_valor_config("Nombre_Local", "MI NEGOCIO")
    
    # Configurar página
    st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="centered")
    
    # VISTA DE INICIO
    if st.session_state.vista == 'inicio':
        # Mostrar logo si existe
        mostrar_logo()
        
        st.title(f"🍔 {nombre_local}")
        
        # Mostrar horario
        horario = obtener_valor_config("Horario", "")
        if horario:
            st.caption(f"🕒 {horario}")
        
        # Mostrar teléfono/WhatsApp
        telefono = obtener_valor_config("WhatsApp", obtener_valor_config("Telefono", ""))
        if telefono:
            st.caption(f"📞 {telefono}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 HACER PEDIDO", use_container_width=True):
                st.session_state.vista = 'pedir'
                st.rerun()
        with col2:
            if st.button("⚙️ ADMIN", use_container_width=True):
                st.session_state.vista = 'admin_login'
                st.rerun()
    
    # LOGIN ADMIN
    elif st.session_state.vista == 'admin_login':
        st.subheader("🔐 Acceso Administrador")
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        with st.form("login_admin"):
            credencial = st.text_input("DNI o Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                if verificar_credenciales("admin", credencial):
                    st.session_state.admin_autenticado = True
                    st.session_state.vista = 'admin'
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
    
    # PANEL ADMIN
    elif st.session_state.vista == 'admin':
        st.subheader(f"⚙️ Panel de Administración - {nombre_local}")
        
        if st.button("⬅ Volver al Inicio"):
            st.session_state.vista = 'inicio'
            st.session_state.admin_autenticado = False
            st.rerun()
        
        # Recargar configuración actual
        config_actual = obtener_toda_configuracion()
        
        tab1, tab2, tab3, tab4 = st.tabs(["🏪 Configuración", "🍔 Productos", "📊 Pedidos", "🎨 Personalización"])
        
        # TAB 1: CONFIGURACIÓN GENERAL
        with tab1:
            st.subheader("Configuración del Negocio")
            
            with st.form("editar_config"):
                nombre = st.text_input("Nombre del Local", config_actual.get("Nombre_Local", ""))
                direccion = st.text_area("Dirección", config_actual.get("Direccion_Local", ""))
                telefono = st.text_input("Teléfono", config_actual.get("Telefono", ""))
                whatsapp = st.text_input("WhatsApp", config_actual.get("WhatsApp", ""))
                horario = st.text_input("Horario", config_actual.get("Horario", ""))
                alias = st.text_input("Alias (Mercado Pago)", config_actual.get("Alias", ""))
                costo_delivery = st.number_input("Costo de Delivery ($)", min_value=0, step=100, value=int(config_actual.get("Costo_Delivery", "0")))
                modo_mant = st.selectbox("Modo Mantenimiento", ["NO", "SI"], index=0 if config_actual.get("MODO_MANTENIMIENTO", "NO") == "NO" else 1)
                
                # Credenciales
                st.divider()
                st.subheader("Credenciales de Acceso")
                admin_dni = st.text_input("DNI Administrador", config_actual.get("Admin_DNI", ""))
                admin_pass = st.text_input("Contraseña Administrador", config_actual.get("Admin_Pass", ""), type="password")
                user = st.text_input("Usuario", config_actual.get("User", ""))
                user_pass = st.text_input("Contraseña Usuario", config_actual.get("User_Pass", ""), type="password")
                
                if st.form_submit_button("💾 Guardar Todo"):
                    guardar_configuracion("Nombre_Local", nombre)
                    guardar_configuracion("Direccion_Local", direccion)
                    guardar_configuracion("Telefono", telefono)
                    guardar_configuracion("WhatsApp", whatsapp)
                    guardar_configuracion("Horario", horario)
                    guardar_configuracion("Alias", alias)
                    guardar_configuracion("Costo_Delivery", str(costo_delivery))
                    guardar_configuracion("MODO_MANTENIMIENTO", modo_mant)
                    guardar_configuracion("Admin_DNI", admin_dni)
                    guardar_configuracion("Admin_Pass", admin_pass)
                    guardar_configuracion("User", user)
                    guardar_configuracion("User_Pass", user_pass)
                    
                    st.success("✅ Configuración guardada")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
        
        # TAB 2: PRODUCTOS
        with tab2:
            st.subheader("Gestión de Productos")
            
            with st.expander("➕ Agregar/Editar Producto"):
                with st.form("form_producto"):
                    nombre_producto = st.text_input("Nombre del Producto")
                    precio_producto = st.number_input("Precio", min_value=0, step=100)
                    
                    if st.form_submit_button("💾 Guardar Producto"):
                        if nombre_producto and precio_producto > 0:
                            if guardar_producto(nombre_producto, precio_producto):
                                st.success(f"✅ {nombre_producto} guardado")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
            
            df_productos = cargar_datos(URL_PRODUCTOS)
            if not df_productos.empty:
                for idx, row in df_productos.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{row.iloc[0]}**")
                    with col2:
                        st.write(formatear_moneda(limpiar_precio(row.iloc[1])))
                    with col3:
                        if st.button("🗑️", key=f"del_{idx}"):
                            if eliminar_producto(row.iloc[0]):
                                st.success(f"✅ Eliminado")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
        
        # TAB 3: PEDIDOS
        with tab3:
            st.subheader("Historial de Pedidos")
            if st.button("🔄 Refrescar"):
                st.cache_data.clear()
                st.rerun()
            
            df_pedidos = cargar_datos(URL_PEDIDOS)
            if not df_pedidos.empty:
                df_pedidos = df_pedidos.tail(20).iloc[::-1]
                for idx, row in df_pedidos.iterrows():
                    with st.container(border=True):
                        st.write(f"**Pedido** - {row.iloc[0] if len(row) > 0 else 'Sin fecha'}")
                        st.write(f"👤 {row.iloc[2] if len(row) > 2 else 'N/A'} - DNI: {row.iloc[1] if len(row) > 1 else 'N/A'}")
                        st.write(f"📍 {row.iloc[3] if len(row) > 3 else 'N/A'}")
                        st.write(f"📝 {row.iloc[4] if len(row) > 4 else 'N/A'}")
                        st.write(f"💰 {formatear_moneda(limpiar_precio(row.iloc[5] if len(row) > 5 else 0))}")
                        estado = row.iloc[6] if len(row) > 6 else "Pendiente"
                        st.write(f"📊 Estado: **{estado}**")
        
        # TAB 4: PERSONALIZACIÓN
        with tab4:
            st.subheader("Personalización Visual")
            
            with st.form("personalizacion"):
                tema_primario = st.color_picker("Color Principal", config_actual.get("Tema_Primario", "#FF6B35"))
                tema_secundario = st.color_picker("Color Secundario", config_actual.get("Tema_Secundario", "#FF6B35"))
                bg_color = st.color_picker("Color de Fondo", config_actual.get("Background_Color", "#FFF8F0"))
                font_family = st.selectbox("Fuente", ["'Poppins', sans-serif", "'Arial', sans-serif", "'Roboto', sans-serif", "'Montserrat', sans-serif"], 
                                          index=0)
                logo_url = st.text_input("URL del Logo", config_actual.get("Logo_URL", ""))
                icono = st.text_input("Icono (emoji)", config_actual.get("icono", "🍔"))
                
                if st.form_submit_button("💾 Guardar Personalización"):
                    guardar_configuracion("Tema_Primario", tema_primario)
                    guardar_configuracion("Tema_Secundario", tema_secundario)
                    guardar_configuracion("Background_Color", bg_color)
                    guardar_configuracion("Font_Family", font_family)
                    guardar_configuracion("Logo_URL", logo_url)
                    guardar_configuracion("icono", icono)
                    st.success("✅ Personalización guardada")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
    
    # VISTA DE PEDIDO
    elif st.session_state.vista == 'pedir':
        # Verificar mantenimiento
        if esta_en_mantenimiento():
            st.warning("🔧 Sistema en mantenimiento. No se pueden tomar pedidos.")
            if st.button("⬅ Volver"):
                st.session_state.vista = 'inicio'
                st.rerun()
            return
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.session_state.carrito = {}
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("login"):
                nombre_local = obtener_valor_config("Nombre_Local", "MI NEGOCIO")
                st.write(f"Bienvenido a **{nombre_local}**")
                n = st.text_input("Tu Nombre")
                d = st.text_input("Tu DNI (sin puntos)")
                
                # Opción de delivery
                delivery = st.checkbox("📦 Envío a domicilio")
                direccion = ""
                if delivery:
                    direccion = st.text_area("Dirección de entrega")
                
                if st.form_submit_button("Entrar a la Carta"):
                    if n and d:
                        if delivery and not direccion:
                            st.error("Ingresa tu dirección")
                        else:
                            st.session_state.user_name = n
                            st.session_state.user_dni = d
                            st.session_state.user_direccion = direccion if delivery else "Retira en local"
                            st.rerun()
            return
        
        # Mostrar productos
        mostrar_logo()
        st.subheader("📋 Nuestra Carta")
        
        df = cargar_datos(URL_PRODUCTOS)
        if not df.empty:
            for i, row in df.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{row.iloc[0]}**")
                    with col2:
                        p = limpiar_precio(row.iloc[1])
                        st.write(formatear_moneda(p))
                    with col3:
                        if st.button(f"Añadir", key=f"btn_{i}"):
                            st.session_state.carrito[row.iloc[0]] = st.session_state.carrito.get(row.iloc[0], 0) + 1
                            st.toast(f"✓ Añadido: {row.iloc[0]}", icon="🍔")
        
        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 Tu Carrito")
            resumen = ""
            total = 0
            for k, v in st.session_state.carrito.items():
                st.write(f"{v}x {k}")
                resumen += f"• {v}x {k}\n"
            
            # Calcular total con delivery
            costo_delivery = int(obtener_valor_config("Costo_Delivery", "0"))
            if st.session_state.get('user_direccion', '') != "Retira en local":
                st.info(f"🚚 Costo de delivery: {formatear_moneda(costo_delivery)}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Vaciar"):
                    st.session_state.carrito = {}
                    st.rerun()
            with col2:
                if st.button("🚀 ENVIAR PEDIDO", type="primary"):
                    mgr = PedidoManager()
                    direccion_final = st.session_state.get('user_direccion', 'Retira en local')
                    if mgr.registrar(st.session_state.user_dni, st.session_state.user_name, resumen, total, direccion_final):
                        mgr.notificar_telegram(st.session_state.user_name, st.session_state.user_dni, direccion_final, resumen, total)
                        st.success("✅ ¡Pedido enviado!")
                        st.balloons()
                        st.session_state.carrito = {}
                        st.session_state.pop('user_name', None)
                        st.session_state.pop('user_dni', None)
                        st.session_state.pop('user_direccion', None)
                        time.sleep(2)
                        st.session_state.vista = 'inicio'
                        st.rerun()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
from datetime import datetime
import json

# ==================== CONFIGURACIÓN ====================
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwqueCR9XaCqwi31_eg94r4GGxNT8fxAavkad5JreWGekDHJ0pOi7vfs_L-L1cPTye6KQ/exec"

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
    """Lee toda la configuración del sheet"""
    try:
        df = cargar_datos(URL_CONFIG)
        config = {}
        
        if df.empty:
            return config
        
        # Siempre usar primera columna como clave, segunda como valor
        if len(df.columns) >= 2:
            for _, row in df.iterrows():
                clave = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                valor = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                if clave and clave != "nan":
                    config[clave] = valor
        
        return config
    except Exception as e:
        return {}

def obtener_valor_config(clave, valor_defecto=""):
    """Obtiene un valor de configuración"""
    config = obtener_toda_configuracion()
    
    # Buscar exactamente igual
    if clave in config:
        return config[clave]
    
    # Buscar sin importar mayúsculas/minúsculas
    for k, v in config.items():
        if k.lower() == clave.lower():
            return v
    
    return valor_defecto

def obtener_nombre_local():
    """Obtiene el nombre del local"""
    nombre = obtener_valor_config("Nombre_Local", "")
    if nombre:
        return nombre
    return "MI NEGOCIO"

def verificar_credenciales(tipo, valor_ingresado):
    """Verifica credenciales desde el sheet"""
    if tipo == "admin":
        pass_correcta = obtener_valor_config("Admin_Pass", "")
        dni_correcto = obtener_valor_config("Admin_DNI", "")
        
        if valor_ingresado == pass_correcta or valor_ingresado == dni_correcto:
            return "admin"
    
    elif tipo == "usuario":
        user_correcto = obtener_valor_config("User", "")
        pass_correcta = obtener_valor_config("User_Pass", "")
        
        if valor_ingresado == user_correcto or valor_ingresado == pass_correcta:
            return "usuario"
    
    return None

def esta_en_mantenimiento():
    modo = obtener_valor_config("MODO_MANTENIMIENTO", "NO")
    return modo.upper() == "SI"

def aplicar_tema():
    tema_primario = obtener_valor_config("Tema_Primario", "#FF6B35")
    tema_secundario = obtener_valor_config("Tema_Secundario", "#FF6B35")
    bg_color = obtener_valor_config("Background_Color", "#FFF8F0")
    font_family = obtener_valor_config("Font_Family", "'Poppins', sans-serif")
    
    st.markdown(f"""
        <style>
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
        h1, h2, h3, h4, h5, h6, p, div, .stMarkdown {{
            font-family: {font_family};
        }}
        </style>
    """, unsafe_allow_html=True)

def mostrar_logo():
    logo_url = obtener_valor_config("Logo_URL", "")
    if logo_url and logo_url != "" and logo_url != "nan":
        try:
            st.image(logo_url, width=150)
        except:
            pass

def guardar_configuracion(parametro, valor):
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
        msg = f"🔔 *NUEVO PEDIDO*\n\n👤 {nombre}\n🆔 DNI: {dni}\n📍 {direccion}\n\n*Detalle:*\n{detalle}\n💰 *TOTAL: {formatear_moneda(total)}*"
        
        if int(costo_delivery) > 0 and direccion != "Retira en local":
            msg += f"\n🚚 *Delivery: {formatear_moneda(int(costo_delivery))}*"
        
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
if 'tipo_usuario' not in st.session_state:
    st.session_state.tipo_usuario = None
if 'usuario_autenticado' not in st.session_state:
    st.session_state.usuario_autenticado = False

def main():
    # Verificar modo mantenimiento
    if esta_en_mantenimiento() and st.session_state.vista != 'admin' and st.session_state.tipo_usuario != 'admin':
        st.title("🔧 MANTENIMIENTO")
        st.warning("El sistema está en mantenimiento. Los pedidos no están disponibles temporalmente.")
        
        if st.button("🔐 Acceso Administrador"):
            st.session_state.vista = 'login'
            st.rerun()
        return
    
    # Aplicar tema visual
    aplicar_tema()
    
    # Obtener nombre del local (FORZAR LECTURA DIRECTA)
    config = obtener_toda_configuracion()
    st.write("Debug - Configuración leída:", config)  # DEBUG: Ver qué se está leyendo
    
    nombre_local = config.get("Nombre_Local", "")
    if not nombre_local:
        nombre_local = config.get("nombre_local", "")
    if not nombre_local:
        nombre_local = "MI NEGOCIO"
    
    st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="centered")
    
    # VISTA DE INICIO
    if st.session_state.vista == 'inicio':
        mostrar_logo()
        st.title(f"🍔 {nombre_local}")
        
        horario = obtener_valor_config("Horario", "")
        if horario:
            st.caption(f"🕒 {horario}")
        
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
                st.session_state.vista = 'login'
                st.rerun()
    
    # LOGIN
    elif st.session_state.vista == 'login':
        st.subheader("🔐 Acceso al Sistema")
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        with st.form("login_form"):
            credencial = st.text_input("DNI, Usuario o Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                # Verificar si es admin
                tipo = verificar_credenciales("admin", credencial)
                if tipo:
                    st.session_state.tipo_usuario = "admin"
                    st.session_state.usuario_autenticado = True
                    st.session_state.vista = 'admin'
                    st.rerun()
                
                # Verificar si es usuario
                tipo = verificar_credenciales("usuario", credencial)
                if tipo:
                    st.session_state.tipo_usuario = "usuario"
                    st.session_state.usuario_autenticado = True
                    st.session_state.vista = 'admin'
                    st.rerun()
                
                if not tipo:
                    st.error("❌ Credenciales incorrectas")
    
    # PANEL ADMIN (con permisos diferenciados)
    elif st.session_state.vista == 'admin':
        es_admin = (st.session_state.tipo_usuario == "admin")
        tipo_texto = "ADMINISTRADOR" if es_admin else "USUARIO"
        st.subheader(f"⚙️ Panel de {tipo_texto} - {nombre_local}")
        
        if not es_admin:
            st.info("👤 Modo Usuario: Puedes editar configuración no sensible")
        
        if st.button("⬅ Volver al Inicio"):
            st.session_state.vista = 'inicio'
            st.session_state.tipo_usuario = None
            st.session_state.usuario_autenticado = False
            st.rerun()
        
        config_actual = obtener_toda_configuracion()
        
        # Pestañas según permisos
        if es_admin:
            tabs = st.tabs(["🏪 Configuración General", "🍔 Productos", "📊 Pedidos", "🎨 Personalización", "🔐 Seguridad"])
        else:
            tabs = st.tabs(["🏪 Configuración General", "🍔 Productos", "📊 Pedidos", "🎨 Personalización"])
        
        # TAB 1: CONFIGURACIÓN GENERAL (visible para ambos)
        with tabs[0]:
            st.subheader("Configuración del Negocio")
            
            with st.form("editar_config_general"):
                nombre = st.text_input("Nombre del Local", config_actual.get("Nombre_Local", ""))
                direccion = st.text_area("Dirección", config_actual.get("Direccion_Local", ""))
                telefono = st.text_input("Teléfono", config_actual.get("Telefono", ""))
                whatsapp = st.text_input("WhatsApp", config_actual.get("WhatsApp", ""))
                horario = st.text_input("Horario", config_actual.get("Horario", ""))
                alias = st.text_input("Alias (Mercado Pago)", config_actual.get("Alias", ""))
                costo_delivery = st.number_input("Costo de Delivery ($)", min_value=0, step=100, value=int(config_actual.get("Costo_Delivery", "0")))
                
                # Modo mantenimiento solo para admin
                if es_admin:
                    modo_mant = st.selectbox("Modo Mantenimiento", ["NO", "SI"], index=0 if config_actual.get("MODO_MANTENIMIENTO", "NO") == "NO" else 1)
                else:
                    modo_mant = config_actual.get("MODO_MANTENIMIENTO", "NO")
                    st.info(f"Modo Mantenimiento actual: {modo_mant} (solo administrador puede cambiar)")
                
                if st.form_submit_button("💾 Guardar"):
                    guardar_configuracion("Nombre_Local", nombre)
                    guardar_configuracion("Direccion_Local", direccion)
                    guardar_configuracion("Telefono", telefono)
                    guardar_configuracion("WhatsApp", whatsapp)
                    guardar_configuracion("Horario", horario)
                    guardar_configuracion("Alias", alias)
                    guardar_configuracion("Costo_Delivery", str(costo_delivery))
                    if es_admin:
                        guardar_configuracion("MODO_MANTENIMIENTO", modo_mant)
                    
                    st.success("✅ Configuración guardada")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
        
        # TAB 2: PRODUCTOS (visible para ambos)
        with tabs[1]:
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
        
        # TAB 3: PEDIDOS (visible para ambos)
        with tabs[2]:
            st.subheader("Historial de Pedidos")
            if st.button("🔄 Refrescar"):
                st.cache_data.clear()
                st.rerun()
            
            df_pedidos = cargar_datos(URL_PEDIDOS)
            if not df_pedidos.empty:
                df_pedidos = df_pedidos.tail(20).iloc[::-1]
                for idx, row in df_pedidos.iterrows():
                    with st.container(border=True):
                        fecha = row.iloc[0] if len(row) > 0 else 'Sin fecha'
                        nombre = row.iloc[2] if len(row) > 2 else 'N/A'
                        dni = row.iloc[1] if len(row) > 1 else 'N/A'
                        direccion = row.iloc[3] if len(row) > 3 else 'N/A'
                        detalle = row.iloc[4] if len(row) > 4 else 'N/A'
                        total = formatear_moneda(limpiar_precio(row.iloc[5] if len(row) > 5 else 0))
                        estado = row.iloc[6] if len(row) > 6 else "Pendiente"
                        
                        st.write(f"**{fecha}**")
                        st.write(f"👤 {nombre} - DNI: {dni}")
                        st.write(f"📍 {direccion}")
                        st.write(f"📝 {detalle}")
                        st.write(f"💰 {total}")
                        st.write(f"📊 Estado: **{estado}**")
        
        # TAB 4: PERSONALIZACIÓN (visible para ambos)
        with tabs[3]:
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
        
        # TAB 5: SEGURIDAD (SOLO ADMIN)
        if es_admin and len(tabs) > 4:
            with tabs[4]:
                st.subheader("🔐 Configuración de Seguridad")
                st.warning("⚠️ Estas configuraciones solo visibles para el Administrador")
                
                with st.form("seguridad"):
                    admin_dni = st.text_input("DNI Administrador", config_actual.get("Admin_DNI", ""))
                    admin_pass = st.text_input("Contraseña Administrador", config_actual.get("Admin_Pass", ""), type="password")
                    user = st.text_input("Usuario", config_actual.get("User", ""))
                    user_pass = st.text_input("Contraseña Usuario", config_actual.get("User_Pass", ""), type="password")
                    
                    if st.form_submit_button("💾 Guardar Credenciales"):
                        guardar_configuracion("Admin_DNI", admin_dni)
                        guardar_configuracion("Admin_Pass", admin_pass)
                        guardar_configuracion("User", user)
                        guardar_configuracion("User_Pass", user_pass)
                        st.success("✅ Credenciales guardadas")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
    
    # VISTA DE PEDIDO
    elif st.session_state.vista == 'pedir':
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
            with st.form("login_cliente"):
                mostrar_logo()
                st.write(f"Bienvenido a **{nombre_local}**")
                n = st.text_input("Tu Nombre")
                d = st.text_input("Tu DNI (sin puntos)")
                
                delivery = st.checkbox("📦 Envío a domicilio")
                direccion = ""
                if delivery:
                    direccion = st.text_area("Dirección de entrega")
                
                if st.form_submit_button("Ver Carta"):
                    if n and d:
                        if delivery and not direccion:
                            st.error("Ingresa tu dirección")
                        else:
                            st.session_state.user_name = n
                            st.session_state.user_dni = d
                            st.session_state.user_direccion = direccion if delivery else "Retira en local"
                            st.rerun()
            return
        
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
            
            costo_delivery = int(obtener_valor_config("Costo_Delivery", "0"))
            if st.session_state.get('user_direccion', '') != "Retira en local" and costo_delivery > 0:
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

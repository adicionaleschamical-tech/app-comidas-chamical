import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import json

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

# ==================== FUNCIONES ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

def cargar_datos_sin_cache(url):
    """Carga datos SIN CACHÉ - siempre actualizado"""
    try:
        timestamp = int(time.time() * 1000)
        resp = requests.get(f"{url}&_={timestamp}", timeout=10)
        resp.raise_for_status()
        contenido = resp.content.decode('utf-8-sig')
        return pd.read_csv(StringIO(contenido))
    except Exception as e:
        return pd.DataFrame()

def obtener_toda_configuracion():
    """Lee TODA la configuración del sheet con los nombres exactos"""
    try:
        df = cargar_datos_sin_cache(URL_CONFIG)
        config = {}
        
        if df.empty:
            return config
        
        # Las columnas son: primera columna = clave, segunda columna = valor
        for idx, row in df.iterrows():
            if len(row) >= 2:
                clave = str(row.iloc[0]).strip()
                valor = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                
                # Limpiar caracteres raros
                valor = valor.replace("Â°", "°").replace("NÂ°", "N°")
                
                # Guardar solo claves válidas
                if clave and clave != "nan" and clave != "None":
                    config[clave] = valor
        
        return config
    except Exception as e:
        return {}

def obtener_valor_config(clave_exacta):
    """Obtiene un valor usando la clave EXACTA del sheet"""
    config = obtener_toda_configuracion()
    
    # Buscar con la clave exacta
    if clave_exacta in config:
        valor = config[clave_exacta]
        return valor if valor and valor != "nan" else ""
    
    return ""

def obtener_nombre_local():
    """Obtiene el nombre del local usando la clave exacta 'Nombre_Local'"""
    nombre = obtener_valor_config("Nombre_Local")
    if nombre:
        return nombre
    return "MI NEGOCIO"

def verificar_credenciales(tipo, valor_ingresado):
    """Verifica credenciales usando las claves exactas"""
    if tipo == "admin":
        pass_correcta = obtener_valor_config("Admin_Pass")
        dni_correcto = obtener_valor_config("Admin_DNI")
        
        if valor_ingresado == pass_correcta or valor_ingresado == dni_correcto:
            return "admin"
    
    elif tipo == "usuario":
        user_correcto = obtener_valor_config("User")
        pass_correcta = obtener_valor_config("User_Pass")
        
        if valor_ingresado == user_correcto or valor_ingresado == pass_correcta:
            return "usuario"
    
    return None

def esta_en_mantenimiento():
    modo = obtener_valor_config("MODO_MANTENIMIENTO")
    return modo.upper() == "SI"

def aplicar_tema():
    """Aplica los colores desde el sheet"""
    tema_primario = obtener_valor_config("Tema_Primario")
    if not tema_primario:
        tema_primario = "#FF6B35"
    
    tema_secundario = obtener_valor_config("Tema_Secundario")
    if not tema_secundario:
        tema_secundario = "#FF6B35"
    
    bg_color = obtener_valor_config("Background_Color")
    if not bg_color:
        bg_color = "#FFF8F0"
    
    font_family = obtener_valor_config("Font_Family")
    if not font_family:
        font_family = "'Poppins', sans-serif"
    
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {bg_color};
        }}
        .stButton > button {{
            background-color: {tema_primario};
            color: white;
            font-weight: bold;
        }}
        .stButton > button:hover {{
            background-color: {tema_secundario};
        }}
        </style>
    """, unsafe_allow_html=True)

def mostrar_logo():
    logo_url = obtener_valor_config("Logo_URL")
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
    except:
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
    except:
        return False

def eliminar_producto(producto):
    params = {
        "accion": "eliminar_producto",
        "producto": producto
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        return "OK" in r.text
    except:
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
        except:
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

def main():
    # Verificar mantenimiento
    if esta_en_mantenimiento() and st.session_state.vista != 'admin' and st.session_state.tipo_usuario != 'admin':
        st.title("🔧 MANTENIMIENTO")
        st.warning("Sistema en mantenimiento")
        if st.button("🔐 Admin"):
            st.session_state.vista = 'login'
            st.rerun()
        return
    
    aplicar_tema()
    nombre_local = obtener_nombre_local()
    st.set_page_config(page_title=nombre_local, page_icon="🍔")
    
    # Sidebar con recarga
    with st.sidebar:
        st.info(f"📍 {nombre_local}")
        if st.button("🔄 RECARGAR DATOS", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # VISTA INICIO
    if st.session_state.vista == 'inicio':
        mostrar_logo()
        st.title(f"🍔 {nombre_local}")
        
        horario = obtener_valor_config("Horario")
        if horario:
            st.caption(f"🕒 {horario}")
        
        telefono = obtener_valor_config("WhatsApp")
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
        st.subheader("🔐 Acceso")
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        with st.form("login"):
            credencial = st.text_input("DNI, Usuario o Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                tipo = verificar_credenciales("admin", credencial)
                if not tipo:
                    tipo = verificar_credenciales("usuario", credencial)
                
                if tipo:
                    st.session_state.tipo_usuario = tipo
                    st.session_state.vista = 'admin'
                    st.rerun()
                else:
                    st.error("❌ Credencial incorrecta")
    
    # PANEL ADMIN
    elif st.session_state.vista == 'admin':
        es_admin = (st.session_state.tipo_usuario == "admin")
        st.subheader(f"⚙️ Panel de {'ADMIN' if es_admin else 'USUARIO'}")
        
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.session_state.tipo_usuario = None
            st.rerun()
        
        config = obtener_toda_configuracion()
        
        # Mostrar valores actuales (debug)
        with st.expander("📋 Configuración actual del sheet"):
            st.json(config)
        
        if es_admin:
            tabs = st.tabs(["🏪 General", "🍔 Productos", "📊 Pedidos", "🎨 Personalización", "🔐 Seguridad"])
        else:
            tabs = st.tabs(["🏪 General", "🍔 Productos", "📊 Pedidos", "🎨 Personalización"])
        
        # TAB GENERAL
        with tabs[0]:
            with st.form("general"):
                nombre = st.text_input("Nombre del Local", config.get("Nombre_Local", nombre_local))
                direccion = st.text_area("Dirección", config.get("Direccion_Local", ""))
                telefono = st.text_input("Teléfono", config.get("Telefono", ""))
                whatsapp = st.text_input("WhatsApp", config.get("WhatsApp", ""))
                horario = st.text_input("Horario", config.get("Horario", ""))
                alias = st.text_input("Alias (Mercado Pago)", config.get("Alias", ""))
                costo = st.number_input("Costo Delivery", min_value=0, value=int(config.get("Costo_Delivery", "0") or 0))
                
                if es_admin:
                    mantenimiento = st.selectbox("Modo Mantenimiento", ["NO", "SI"], 
                                                index=0 if config.get("MODO_MANTENIMIENTO", "NO") == "NO" else 1)
                
                if st.form_submit_button("Guardar"):
                    guardar_configuracion("Nombre_Local", nombre)
                    guardar_configuracion("Direccion_Local", direccion)
                    guardar_configuracion("Telefono", telefono)
                    guardar_configuracion("WhatsApp", whatsapp)
                    guardar_configuracion("Horario", horario)
                    guardar_configuracion("Alias", alias)
                    guardar_configuracion("Costo_Delivery", str(costo))
                    if es_admin:
                        guardar_configuracion("MODO_MANTENIMIENTO", mantenimiento)
                    st.success("✅ Guardado")
                    time.sleep(1)
                    st.rerun()
        
        # TAB PRODUCTOS
        with tabs[1]:
            with st.expander("➕ Nuevo Producto"):
                with st.form("producto"):
                    nombre_prod = st.text_input("Nombre")
                    precio_prod = st.number_input("Precio", min_value=0)
                    if st.form_submit_button("Guardar"):
                        if guardar_producto(nombre_prod, precio_prod):
                            st.success("✅ Producto guardado")
                            time.sleep(1)
                            st.rerun()
            
            df = cargar_datos_sin_cache(URL_PRODUCTOS)
            if not df.empty:
                for i, row in df.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(row.iloc[0])
                    with c2:
                        st.write(formatear_moneda(limpiar_precio(row.iloc[1])))
                    with c3:
                        if st.button("🗑️", key=f"del_{i}"):
                            eliminar_producto(row.iloc[0])
                            st.rerun()
        
        # TAB PEDIDOS
        with tabs[2]:
            if st.button("🔄 Refrescar Pedidos"):
                st.rerun()
            
            df_ped = cargar_datos_sin_cache(URL_PEDIDOS)
            if not df_ped.empty:
                for _, row in df_ped.tail(10).iterrows():
                    with st.container(border=True):
                        fecha = row.iloc[0] if len(row) > 0 else "Sin fecha"
                        nombre = row.iloc[2] if len(row) > 2 else "N/A"
                        direccion = row.iloc[3] if len(row) > 3 else "N/A"
                        detalle = row.iloc[4] if len(row) > 4 else "N/A"
                        total = formatear_moneda(limpiar_precio(row.iloc[5] if len(row) > 5 else 0))
                        estado = row.iloc[6] if len(row) > 6 else "Pendiente"
                        
                        st.write(f"**{fecha}** - {nombre}")
                        st.write(f"📍 {direccion}")
                        st.write(f"📝 {detalle}")
                        st.write(f"💰 {total}")
                        st.write(f"📊 Estado: **{estado}**")
        
        # TAB PERSONALIZACIÓN
        with tabs[3]:
            with st.form("personalizacion"):
                color1 = st.color_picker("Color Primario", config.get("Tema_Primario", "#FF6B35"))
                color2 = st.color_picker("Color Secundario", config.get("Tema_Secundario", "#FF6B35"))
                bg = st.color_picker("Fondo", config.get("Background_Color", "#FFF8F0"))
                logo = st.text_input("URL Logo", config.get("Logo_URL", ""))
                icono = st.text_input("Icono", config.get("icono", "🍔"))
                font = st.selectbox("Fuente", ["'Poppins', sans-serif", "'Arial', sans-serif", "'Roboto', sans-serif"], 
                                   index=0 if config.get("Font_Family", "").find("Poppins") >= 0 else 0)
                
                if st.form_submit_button("Guardar"):
                    guardar_configuracion("Tema_Primario", color1)
                    guardar_configuracion("Tema_Secundario", color2)
                    guardar_configuracion("Background_Color", bg)
                    guardar_configuracion("Logo_URL", logo)
                    guardar_configuracion("icono", icono)
                    guardar_configuracion("Font_Family", font)
                    st.success("✅ Guardado")
                    time.sleep(1)
                    st.rerun()
        
        # TAB SEGURIDAD (solo admin)
        if es_admin and len(tabs) > 4:
            with tabs[4]:
                with st.form("seguridad"):
                    admin_dni = st.text_input("DNI Admin", config.get("Admin_DNI", ""))
                    admin_pass = st.text_input("Pass Admin", config.get("Admin_Pass", ""), type="password")
                    user = st.text_input("Usuario", config.get("User", ""))
                    user_pass = st.text_input("Pass Usuario", config.get("User_Pass", ""), type="password")
                    
                    if st.form_submit_button("Guardar"):
                        guardar_configuracion("Admin_DNI", admin_dni)
                        guardar_configuracion("Admin_Pass", admin_pass)
                        guardar_configuracion("User", user)
                        guardar_configuracion("User_Pass", user_pass)
                        st.success("✅ Credenciales guardadas")
                        st.rerun()
    
    # VISTA PEDIDO
    elif st.session_state.vista == 'pedir':
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("cliente"):
                st.write(f"Bienvenido a **{nombre_local}**")
                nombre = st.text_input("Tu Nombre")
                dni = st.text_input("Tu DNI (sin puntos)")
                
                delivery = st.checkbox("📦 Envío a domicilio")
                direccion = ""
                if delivery:
                    direccion = st.text_area("Dirección de entrega")
                
                if st.form_submit_button("Ver Carta"):
                    if nombre and dni:
                        if delivery and not direccion:
                            st.error("Ingresa tu dirección")
                        else:
                            st.session_state.user_name = nombre
                            st.session_state.user_dni = dni
                            st.session_state.user_direccion = direccion if delivery else "Retira en local"
                            st.rerun()
            return
        
        st.subheader("📋 NUESTRA CARTA")
        
        df = cargar_datos_sin_cache(URL_PRODUCTOS)
        if not df.empty:
            for i, row in df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(f"**{row.iloc[0]}**")
                    with c2:
                        p = limpiar_precio(row.iloc[1])
                        st.write(formatear_moneda(p))
                    with c3:
                        if st.button("➕ Añadir", key=f"add_{i}"):
                            st.session_state.carrito[row.iloc[0]] = st.session_state.carrito.get(row.iloc[0], 0) + 1
                            st.toast(f"✓ Añadido: {row.iloc[0]}", icon="🍔")
                            st.rerun()
        
        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 TU CARRITO")
            resumen = ""
            total = 0
            for k, v in st.session_state.carrito.items():
                st.write(f"{v}x {k}")
                resumen += f"• {v}x {k}\n"
            
            costo_delivery = int(obtener_valor_config("Costo_Delivery") or 0)
            if st.session_state.get('user_direccion', '') != "Retira en local" and costo_delivery > 0:
                st.info(f"🚚 Costo de delivery: {formatear_moneda(costo_delivery)}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Vaciar Carrito"):
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
                    else:
                        st.error("❌ Error al enviar el pedido")

if __name__ == "__main__":
    main()

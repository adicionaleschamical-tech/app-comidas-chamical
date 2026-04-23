import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import json
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
URL_APPS_SCRIPT = "URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwtcGVzIGbgJNo6Gmf92TkFEdDd8Okw_iO1yDhu_kzT2c9knUck34ecvgze48hXqWR4JQ/exec"

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
    try:
        timestamp = int(time.time() * 1000)
        resp = requests.get(f"{url}&_={timestamp}", timeout=10)
        resp.raise_for_status()
        contenido = resp.content.decode('utf-8-sig')
        return pd.read_csv(StringIO(contenido))
    except Exception as e:
        return pd.DataFrame()

def obtener_toda_configuracion():
    try:
        df = cargar_datos_sin_cache(URL_CONFIG)
        config = {}
        
        if df.empty:
            return config
        
        for i in range(len(df)):
            clave = str(df.iloc[i, 0]).strip()
            valor = str(df.iloc[i, 1]).strip() if len(df.columns) > 1 else ""
            
            if valor == "nan" or valor == "None":
                valor = ""
            
            valor = valor.replace("Â°", "°").replace("NÂ°", "N°")
            
            if clave and clave != "nan":
                config[clave] = valor
        
        return config
    except Exception as e:
        return {}

def obtener_valor_config(clave_exacta):
    config = obtener_toda_configuracion()
    
    if clave_exacta in config:
        valor = config[clave_exacta]
        return valor if valor and valor != "nan" else ""
    
    return ""

def obtener_nombre_local():
    nombre = obtener_valor_config("Nombre_Local")
    if nombre:
        return nombre
    return "MI NEGOCIO"

def verificar_credenciales(tipo, valor_ingresado):
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
        .product-card {{
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: white;
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

def enviar_mensaje_telegram(mensaje, parse_mode="Markdown"):
    """Envía un mensaje de prueba a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": parse_mode
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
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
                [{"text": "✅ Finalizado", "callback_data": f"est_Finalizado_{dni}"}]
            ]
        }
        msg = f"🔔 *NUEVO PEDIDO*\n\n👤 {nombre}\n🆔 DNI: {dni}\n📍 {direccion}\n\n*Detalle:*\n{detalle}\n💰 *TOTAL: {formatear_moneda(total)}*"
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(url, data=payload, timeout=10)
        except:
            pass

# ==================== INTERFAZ PRINCIPAL ====================
if 'vista' not in st.session_state:
    st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'tipo_usuario' not in st.session_state:
    st.session_state.tipo_usuario = None

def mostrar_productos_cliente():
    """Muestra productos con imágenes, variedades y precios"""
    df = cargar_datos_sin_cache(URL_PRODUCTOS)
    
    if df.empty:
        st.warning("No hay productos disponibles")
        return
    
    # Agrupar por categoría
    if 'Categoria' in df.columns:
        categorias = df['Categoria'].unique()
    else:
        categorias = ['Productos']
    
    for categoria in categorias:
        st.subheader(f"📌 {categoria}")
        
        if 'Categoria' in df.columns:
            productos_cat = df[df['Categoria'] == categoria]
        else:
            productos_cat = df
        
        for idx, row in productos_cat.iterrows():
            with st.container(border=True):
                # Imagen
                imagen_url = row.get('Imagen', '')
                if imagen_url and imagen_url != '' and imagen_url != 'nan':
                    try:
                        st.image(imagen_url, width=200)
                    except:
                        pass
                
                # Nombre del producto
                producto = row.get('Producto', 'Sin nombre')
                st.markdown(f"### 🍔 {producto}")
                
                # Ingredientes
                ingredientes = row.get('Ingredientes', '')
                if ingredientes and ingredientes != 'nan':
                    with st.expander("📋 Ver ingredientes"):
                        st.write(ingredientes)
                
                # Variedades y precios
                variedades = row.get('Variedades', '')
                precios = row.get('Precio', '')
                
                if variedades and variedades != 'nan':
                    variedades_lista = [v.strip() for v in str(variedades).split(';')]
                    precios_lista = [p.strip() for p in str(precios).split(';')] if precios != 'nan' else []
                    
                    for j, var in enumerate(variedades_lista):
                        precio_var = precios_lista[j] if j < len(precios_lista) else '0'
                        precio_num = limpiar_precio(precio_var)
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{var}**")
                        with col2:
                            st.write(formatear_moneda(precio_num))
                        with col3:
                            if st.button(f"Añadir", key=f"add_{producto}_{j}"):
                                item_key = f"{producto} - {var}"
                                if item_key in st.session_state.carrito:
                                    st.session_state.carrito[item_key]['cantidad'] += 1
                                else:
                                    st.session_state.carrito[item_key] = {
                                        'nombre': item_key,
                                        'precio': precio_num,
                                        'cantidad': 1
                                    }
                                st.toast(f"✓ Añadido: {var}", icon="🍔")
                                st.rerun()
                else:
                    # Producto simple
                    precio_num = limpiar_precio(precios)
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{producto}**")
                    with col2:
                        st.write(formatear_moneda(precio_num))
                    with col3:
                        if st.button(f"Añadir", key=f"add_simple_{idx}"):
                            if producto in st.session_state.carrito:
                                st.session_state.carrito[producto]['cantidad'] += 1
                            else:
                                st.session_state.carrito[producto] = {
                                    'nombre': producto,
                                    'precio': precio_num,
                                    'cantidad': 1
                                }
                            st.toast(f"✓ Añadido: {producto}", icon="🍔")
                            st.rerun()
                
                # Disponibilidad
                disponible = row.get('Disponible', 'SI')
                if disponible == 'NO':
                    st.warning("⚠️ Producto no disponible")

def main():
    # Verificar mantenimiento
    if esta_en_mantenimiento() and st.session_state.vista != 'admin' and st.session_state.tipo_usuario != 'admin':
        st.title("🔧 MANTENIMIENTO")
        st.warning("Sistema en mantenimiento. Pronto volvemos.")
        if st.button("🔐 Acceso Administrador"):
            st.session_state.vista = 'login'
            st.rerun()
        return
    
    aplicar_tema()
    nombre_local = obtener_nombre_local()
    st.set_page_config(page_title=nombre_local, page_icon="🍔", layout="wide")
    
    # Sidebar - Solo visible para admin/usuario
    if st.session_state.tipo_usuario in ['admin', 'usuario']:
        with st.sidebar:
            st.info(f"📍 {nombre_local}")
            st.markdown("---")
            st.markdown(f"👤 **Usuario:** {st.session_state.tipo_usuario.upper()}")
            
            # Estado del sistema
            st.markdown("### 📡 Estado del Sistema")
            
            # Verificar Google Sheets
            config_check = obtener_toda_configuracion()
            if config_check:
                st.success("✅ Google Sheets: Conectado")
            else:
                st.error("❌ Google Sheets: Error")
            
            # Verificar Telegram
            st.markdown("---")
            st.markdown("### 🤖 Telegram")
            col_tg1, col_tg2 = st.columns(2)
            with col_tg1:
                if st.button("📨 Probar Bot", use_container_width=True):
                    with st.spinner("Enviando..."):
                        if enviar_mensaje_telegram("✅ *MENSAJE DE PRUEBA*\n\nTu bot de Telegram funciona correctamente.\n\nHora: " + datetime.now().strftime("%H:%M:%S")):
                            st.success("✅ Mensaje enviado")
                        else:
                            st.error("❌ Error al enviar")
            with col_tg2:
                st.caption("Chat ID: " + TELEGRAM_CHAT_ID[-4:])
            
            st.markdown("---")
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.tipo_usuario = None
                st.session_state.vista = 'inicio'
                st.session_state.carrito = {}
                st.rerun()
            
            if st.button("🔄 Recargar Datos", use_container_width=True):
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
        st.subheader("🔐 Acceso Administrativo")
        
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
        st.subheader(f"⚙️ Panel de {'ADMINISTRADOR' if es_admin else 'USUARIO'}")
        
        if st.button("⬅ Volver al Inicio"):
            st.session_state.vista = 'inicio'
            st.session_state.tipo_usuario = None
            st.rerun()
        
        config = obtener_toda_configuracion()
        
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
        
        # TAB PRODUCTOS - Vista previa
        with tabs[1]:
            st.subheader("Gestión de Productos")
            st.info("📝 Para editar productos, abre Google Sheets directamente:")
            st.markdown(f"[📊 Abrir Google Sheets - Productos](https://docs.google.com/spreadsheets/d/{ID_SHEET}/edit#gid={GID_PRODUCTOS})")
            
            # Vista previa de productos
            df = cargar_datos_sin_cache(URL_PRODUCTOS)
            if not df.empty:
                st.write("### Vista previa de productos")
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{row.get('Producto', 'Sin nombre')}**")
                            st.caption(f"📂 {row.get('Categoria', 'N/A')}")
                            st.caption(f"🥗 Variedades: {row.get('Variedades', 'N/A')}")
                        with col2:
                            st.write(f"💰 {row.get('Precio', 'N/A')}")
                            disponible = row.get('Disponible', 'SI')
                            if disponible == 'SI':
                                st.success("✅ Disponible")
                            else:
                                st.error("❌ No disponible")
        
        # TAB PEDIDOS
        with tabs[2]:
            if st.button("🔄 Refrescar Pedidos"):
                st.cache_data.clear()
                st.rerun()
            
            df_ped = cargar_datos_sin_cache(URL_PEDIDOS)
            if not df_ped.empty:
                st.write(f"📋 Últimos {min(20, len(df_ped))} pedidos")
                for _, row in df_ped.tail(20).iloc[::-1].iterrows():
                    with st.container(border=True):
                        fecha = row.iloc[0] if len(row) > 0 else "Sin fecha"
                        dni = row.iloc[1] if len(row) > 1 else "N/A"
                        nombre = row.iloc[2] if len(row) > 2 else "N/A"
                        direccion = row.iloc[3] if len(row) > 3 else "N/A"
                        detalle = row.iloc[4] if len(row) > 4 else "N/A"
                        total = formatear_moneda(limpiar_precio(row.iloc[5] if len(row) > 5 else 0))
                        estado = row.iloc[6] if len(row) > 6 else "Pendiente"
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{fecha}** - #{dni}")
                            st.write(f"👤 {nombre}")
                            st.write(f"📍 {direccion}")
                            st.write(f"📝 {detalle}")
                        with col2:
                            st.write(f"💰 {total}")
                            if estado == "Pendiente":
                                st.warning(f"📊 {estado}")
                            elif estado == "Preparando":
                                st.info(f"👨‍🍳 {estado}")
                            elif estado == "Enviado":
                                st.success(f"🛵 {estado}")
                            else:
                                st.success(f"✅ {estado}")
            else:
                st.info("No hay pedidos registrados")
        
        # TAB PERSONALIZACIÓN
        with tabs[3]:
            with st.form("personalizacion"):
                color1 = st.color_picker("Color Primario", config.get("Tema_Primario", "#FF6B35"))
                color2 = st.color_picker("Color Secundario", config.get("Tema_Secundario", "#FF6B35"))
                bg = st.color_picker("Color de Fondo", config.get("Background_Color", "#FFF8F0"))
                logo = st.text_input("URL del Logo", config.get("Logo_URL", ""))
                font = st.selectbox("Fuente", ["'Poppins', sans-serif", "'Arial', sans-serif", "'Roboto', sans-serif"], 
                                   index=0 if "Poppins" in config.get("Font_Family", "") else 0)
                
                if st.form_submit_button("Guardar Personalización"):
                    guardar_configuracion("Tema_Primario", color1)
                    guardar_configuracion("Tema_Secundario", color2)
                    guardar_configuracion("Background_Color", bg)
                    guardar_configuracion("Logo_URL", logo)
                    guardar_configuracion("Font_Family", font)
                    st.success("✅ Personalización guardada")
                    time.sleep(1)
                    st.rerun()
        
        # TAB SEGURIDAD (solo admin)
        if es_admin and len(tabs) > 4:
            with tabs[4]:
                st.warning("⚠️ Configuración sensible - Solo Administrador")
                with st.form("seguridad"):
                    admin_dni = st.text_input("DNI Administrador", config.get("Admin_DNI", ""))
                    admin_pass = st.text_input("Contraseña Administrador", config.get("Admin_Pass", ""), type="password")
                    user = st.text_input("Usuario", config.get("User", ""))
                    user_pass = st.text_input("Contraseña Usuario", config.get("User_Pass", ""), type="password")
                    
                    if st.form_submit_button("Guardar Credenciales"):
                        guardar_configuracion("Admin_DNI", admin_dni)
                        guardar_configuracion("Admin_Pass", admin_pass)
                        guardar_configuracion("User", user)
                        guardar_configuracion("User_Pass", user_pass)
                        st.success("✅ Credenciales guardadas")
                        st.rerun()
    
    # VISTA PEDIDO (CLIENTE)
    elif st.session_state.vista == 'pedir':
        if st.button("⬅ Volver al Inicio"):
            st.session_state.vista = 'inicio'
            st.session_state.carrito = {}
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("cliente"):
                mostrar_logo()
                st.write(f"Bienvenido a **{nombre_local}**")
                nombre = st.text_input("Tu Nombre")
                dni = st.text_input("Tu DNI (sin puntos)")
                direccion = st.text_area("Dirección de entrega (opcional - solo si necesitas delivery)")
                st.caption("Si no ingresas dirección, el pedido será para retirar en el local")
                
                if st.form_submit_button("Ver Carta"):
                    if nombre and dni:
                        st.session_state.user_name = nombre
                        st.session_state.user_dni = dni
                        st.session_state.user_direccion = direccion if direccion else "Retira en local"
                        st.rerun()
                    else:
                        st.error("❌ Completa tu nombre y DNI")
            return
        
        # Mostrar productos
        mostrar_productos_cliente()
        
        # Carrito
        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 TU CARRITO")
            resumen = ""
            total = 0
            
            for key, item in st.session_state.carrito.items():
                cantidad = item['cantidad']
                precio = item['precio']
                subtotal = cantidad * precio
                total += subtotal
                st.write(f"{cantidad}x {key} - {formatear_moneda(subtotal)}")
                resumen += f"• {cantidad}x {key}\n"
            
            # Delivery
            costo_delivery = int(obtener_valor_config("Costo_Delivery") or 0)
            direccion_final = st.session_state.get('user_direccion', 'Retira en local')
            
            if direccion_final != "Retira en local" and costo_delivery > 0:
                st.info(f"🚚 Costo de delivery: {formatear_moneda(costo_delivery)}")
                total += costo_delivery
                resumen += f"• Delivery: {formatear_moneda(costo_delivery)}\n"
            
            st.markdown(f"### TOTAL: {formatear_moneda(total)}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Vaciar Carrito"):
                    st.session_state.carrito = {}
                    st.rerun()
            with col2:
                if st.button("🚀 CONFIRMAR PEDIDO", type="primary"):
                    mgr = PedidoManager()
                    if mgr.registrar(st.session_state.user_dni, st.session_state.user_name, resumen, total, direccion_final):
                        mgr.notificar_telegram(st.session_state.user_name, st.session_state.user_dni, direccion_final, resumen, total)
                        st.success("✅ ¡Pedido enviado con éxito!")
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
        else:
            st.info("🛒 Tu carrito está vacío. Agrega productos para hacer un pedido.")

if __name__ == "__main__":
    main()

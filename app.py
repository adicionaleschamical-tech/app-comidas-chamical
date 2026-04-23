import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import json

# ==================== CONFIGURACIÓN ====================
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbxtSvR607JdhJUHnR36hpohG48vzk0P9gFEVo6541pljj6BcZ59z3x6nzEW45vUwCM6/exec"

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

@st.cache_data(ttl=30)
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
        
        # Buscar la fila con el nombre del local específicamente
        for idx, row in df.iterrows():
            if len(row) >= 2:
                clave = str(row.iloc[0]).strip()
                valor = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                
                # Limpiar caracteres raros
                valor = valor.replace("Â°", "°").replace("NÂ°", "N°")
                
                if clave and clave != "nan" and clave.lower() not in ["clave", "parametro", "config"]:
                    config[clave] = valor
        
        return config
    except Exception as e:
        return {}

def obtener_valor_config(clave, valor_defecto=""):
    """Obtiene un valor de configuración"""
    config = obtener_toda_configuracion()
    
    # Buscar exactamente
    if clave in config:
        return config[clave]
    
    # Buscar sin importar mayúsculas
    for k, v in config.items():
        if k.lower() == clave.lower():
            return v
    
    return valor_defecto

def obtener_nombre_local():
    """Obtiene el nombre del local correctamente"""
    nombre = obtener_valor_config("Nombre_Local", "")
    if nombre and nombre != "":
        return nombre
    return "HAMBURGUESAS REGIONAL QUINTA"

def verificar_credenciales(tipo, valor_ingresado):
    """Verifica credenciales"""
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
            font-weight: bold;
        }}
        .stButton > button:hover {{
            background-color: {tema_secundario};
            transform: scale(1.02);
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
    
    # VISTA INICIO
    if st.session_state.vista == 'inicio':
        mostrar_logo()
        st.title(f"🍔 {nombre_local}")
        
        horario = obtener_valor_config("Horario", "")
        if horario:
            st.caption(f"🕒 {horario}")
        
        telefono = obtener_valor_config("WhatsApp", "")
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
        
        # Pestañas
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
                costo = st.number_input("Costo Delivery", min_value=0, value=int(config.get("Costo_Delivery", "500")))
                
                if es_admin:
                    mantenimiento = st.selectbox("Modo Mantenimiento", ["NO", "SI"], 
                                                index=0 if config.get("MODO_MANTENIMIENTO", "NO") == "NO" else 1)
                
                if st.form_submit_button("Guardar"):
                    guardar_configuracion("Nombre_Local", nombre)
                    guardar_configuracion("Direccion_Local", direccion)
                    guardar_configuracion("Telefono", telefono)
                    guardar_configuracion("WhatsApp", whatsapp)
                    guardar_configuracion("Horario", horario)
                    guardar_configuracion("Costo_Delivery", str(costo))
                    if es_admin:
                        guardar_configuracion("MODO_MANTENIMIENTO", mantenimiento)
                    st.success("✅ Guardado")
                    st.cache_data.clear()
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
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
            
            df = cargar_datos(URL_PRODUCTOS)
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
            if st.button("🔄 Refrescar"):
                st.cache_data.clear()
                st.rerun()
            
            df_ped = cargar_datos(URL_PEDIDOS)
            if not df_ped.empty:
                for _, row in df_ped.tail(10).iterrows():
                    with st.container(border=True):
                        st.write(f"**{row.iloc[0]}** - {row.iloc[2]}")
                        st.write(f"📍 {row.iloc[3]}")
                        st.write(f"📝 {row.iloc[4]}")
                        st.write(f"💰 {formatear_moneda(limpiar_precio(row.iloc[5]))}")
                        st.write(f"📊 Estado: **{row.iloc[6] if len(row) > 6 else 'Pendiente'}**")
        
        # TAB PERSONALIZACIÓN
        with tabs[3]:
            with st.form("personalizacion"):
                color1 = st.color_picker("Color Primario", config.get("Tema_Primario", "#FF6B35"))
                color2 = st.color_picker("Color Secundario", config.get("Tema_Secundario", "#FF6B35"))
                bg = st.color_picker("Fondo", config.get("Background_Color", "#FFF8F0"))
                logo = st.text_input("URL Logo", config.get("Logo_URL", ""))
                
                if st.form_submit_button("Guardar"):
                    guardar_configuracion("Tema_Primario", color1)
                    guardar_configuracion("Tema_Secundario", color2)
                    guardar_configuracion("Background_Color", bg)
                    guardar_configuracion("Logo_URL", logo)
                    st.success("✅ Guardado")
                    st.cache_data.clear()
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
    
    # VISTA PEDIDO
    elif st.session_state.vista == 'pedir':
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("cliente"):
                nombre = st.text_input("Tu Nombre")
                dni = st.text_input("Tu DNI")
                if st.form_submit_button("Continuar"):
                    if nombre and dni:
                        st.session_state.user_name = nombre
                        st.session_state.user_dni = dni
                        st.rerun()
            return
        
        st.subheader("📋 CARTA")
        df = cargar_datos(URL_PRODUCTOS)
        if not df.empty:
            for i, row in df.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"**{row.iloc[0]}**")
                with c2:
                    st.write(formatear_moneda(limpiar_precio(row.iloc[1])))
                with c3:
                    if st.button("➕", key=f"add_{i}"):
                        st.session_state.carrito[row.iloc[0]] = st.session_state.carrito.get(row.iloc[0], 0) + 1
                        st.rerun()
        
        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 CARRITO")
            resumen = ""
            for k, v in st.session_state.carrito.items():
                st.write(f"{v}x {k}")
                resumen += f"{v}x {k}\n"
            
            if st.button("🚀 ENVIAR PEDIDO"):
                mgr = PedidoManager()
                if mgr.registrar(st.session_state.user_dni, st.session_state.user_name, resumen, 0, "Local"):
                    mgr.notificar_telegram(st.session_state.user_name, st.session_state.user_dni, "Local", resumen, 0)
                    st.success("✅ Pedido enviado")
                    st.session_state.carrito = {}
                    del st.session_state.user_name
                    del st.session_state.user_dni
                    time.sleep(2)
                    st.session_state.vista = 'inicio'
                    st.rerun()

if __name__ == "__main__":
    main()

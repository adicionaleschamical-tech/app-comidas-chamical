import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwlHFcGkkbIuPPcgLeIl2UleCp3qA4dOJrXgHZAEMDILnnK1hFbzHsUO91oQ0Zqg32_SA/exec"
TELEGRAM_TOKEN = "8597598506:AAGgsvhwhG9pCJkr6epmxmH8qGU0DvNBCyA"
TELEGRAM_CHAT_ID = "7860013984"

# --- FUNCIONES DE DATOS ---
def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion})
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return {}

# 1. Cargar Configuración Inicial
config_raw = leer_datos("leer_config")
# Convertimos las claves a minúsculas para evitar errores de tipeo en el Sheet
config = {str(k).lower(): v for k, v in config_raw.items()}

# --- CONFIGURACIÓN DE PÁGINA DINÁMICA ---
nombre_local = config.get("nombre_local", "Mi Comercio")
st.set_page_config(page_title=nombre_local, layout="wide")

# APLICAR TEMA VISUAL DESDE EL SHEET
color_primario = config.get("tema_primario", "#FF6B35")
bg_color = config.get("background_color", "#FFF8F0")
font_family = config.get("font_family", "sans-serif")

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        font-family: {font_family};
    }}
    .main-title {{
        color: {color_primario};
        text-align: center;
        font-weight: bold;
        margin-bottom: 0;
    }}
    .stButton>button {{
        background-color: {color_primario};
        color: white;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- SIDEBAR: LOGIN Y PANEL ---
st.sidebar.title("🛂 Acceso")
if not st.session_state.autenticado:
    with st.sidebar.expander("Ingreso Personal"):
        u_input = st.text_input("Usuario / DNI")
        p_input = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if u_input == str(config.get("admin_dni")) and p_input == str(config.get("admin_pass")):
                st.session_state.autenticado = True
                st.session_state.rol = "admin"
                st.rerun()
            elif u_input == config.get("user_name") and p_input == config.get("user_pass"):
                st.session_state.autenticado = True
                st.session_state.rol = "user"
                st.rerun()
            else:
                st.error("Credenciales Inválidas")
else:
    st.sidebar.success(f"Sesión: {st.session_state.rol.upper()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.rol = None
        st.rerun()

# --- VISTA DE ADMINISTRACIÓN ---
if st.session_state.autenticado:
    st.title(f"⚙️ Panel de Control - {nombre_local}")
    
    if config.get("modo_mantenimiento") == "SI":
        st.warning("⚠️ El modo mantenimiento está ACTIVO actualmente.")

    tab1, tab2 = st.tabs(["📊 Productos", "🔧 Configuración Global"])
    
    with tab1:
        st.subheader("Edición de Catálogo")
        prods = leer_datos("leer_productos")
        if prods:
            df = pd.DataFrame(prods)
            st.data_editor(df, num_rows="dynamic", key="editor_prods")
            if st.button("Guardar Cambios"):
                st.info("Función de guardado en desarrollo conectando al Sheet...")

    with tab2:
        st.write(f"**Costo de Delivery actual:** ${config.get('costo_delivery')}")
        st.write(f"**Horario:** {config.get('horario')}")
        if st.session_state.rol == "admin":
            st.toggle("Activar Mantenimiento Global", value=(config.get("modo_mantenimiento") == "SI"))

# --- VISTA PÚBLICA (CLIENTE) ---
else:
    # Encabezado con Logo
    col_logo, col_tit = st.columns([1, 4])
    with col_logo:
        if config.get("logo_url"):
            st.image(config.get("logo_url"), width=120)
    with col_tit:
        st.markdown(f"<h1 class='main-title'>{nombre_local}</h1>", unsafe_allow_html=True)
        st.caption(f"📍 {config.get('direccion_local')} | ⏰ {config.get('horario')}")

    if config.get("modo_mantenimiento") == "SI":
        st.error(" estamos realizando mejoras. Volvemos pronto.")
        st.stop()

    # Catálogo
    st.divider()
    prods = leer_datos("leer_productos")
    if not prods:
        st.info("Cargando menú...")
    else:
        c_prods = st.columns(3)
        for idx, p in enumerate(prods):
            with c_prods[idx % 3]:
                st.image(p['imagen'], use_container_width=True)
                st.subheader(p['nombre'])
                st.markdown(f"**${p['precio']}**")
                if st.button("Añadir 🛒", key=f"add_{idx}"):
                    st.session_state.carrito.append(p)
                    st.toast(f"{p['nombre']} al carrito")

    # Carrito Flotante / Final de página
    if st.session_state.carrito:
        with st.expander(f"🛒 Tu Pedido ({len(st.session_state.carrito)} items)"):
            total = sum(item['precio'] for item in st.session_state.carrito)
            for item in st.session_state.carrito:
                st.write(f"- {item['nombre']} (${item['precio']})")
            
            deliv = float(config.get("costo_delivery", 0))
            st.write(f"**Envío:** ${deliv}")
            st.subheader(f"Total: ${total + deliv}")
            
            with st.form("form_pedido"):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Tu Nombre")
                dni_cli = c2.text_input("DNI (para el bot)")
                dire = st.text_input("Dirección exacta")
                
                if st.form_submit_button("CONFIRMAR PEDIDO"):
                    detalles = ", ".join([x['nombre'] for x in st.session_state.carrito])
                    params = {
                        "accion": "nuevo",
                        "tel": dni_cli,
                        "nombre": nombre,
                        "dir": dire,
                        "detalle": detalles,
                        "total": total + deliv
                    }
                    res = requests.get(URL_GOOGLE_SCRIPT, params=params)
                    if res.text == "OK":
                        st.success("¡Pedido enviado con éxito!")
                        st.session_state.carrito = []
                        # El script de Google se encarga de enviar el Telegram con botones
                    else:
                        st.error("Error al registrar en el sistema.")

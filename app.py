import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE ACCESO (GOOGLE SHEETS) ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food - Gestión", page_icon="🍟", layout="wide")

# --- CSS PARA IOS Y DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { 
        border: 2px solid #EEE; padding: 15px; border-radius: 15px; 
        margin-bottom: 20px; background-color: #F9F9F9 !important;
    }
    .btn-active > button { background-color: #E63946 !important; color: white !important; }
    .ingredientes-vivos { background-color: #FFF9C4 !important; color: #000; padding: 15px; border-radius: 12px; border-left: 10px solid #FBC02D !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, conf
    except: return pd.DataFrame(), {}

# --- LÓGICA DE LOGIN ---
if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if 'rol' not in st.session_state: st.session_state['rol'] = None

if not st.session_state['logueado']:
    st.title("🔐 Acceso al Sistema")
    user = st.text_input("Usuario:")
    clave = st.text_input("Contraseña:", type="password")
    
    if st.button("Ingresar"):
        if user == "admin" and clave == "admin123":
            st.session_state['logueado'] = True
            st.session_state['rol'] = "admin"
            st.rerun()
        elif user == "staff" and clave == "staff123":
            st.session_state['logueado'] = True
            st.session_state['rol'] = "usuario"
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- CARGAR INFO ---
df_prod, conf = cargar_datos()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title(f"👤 {st.session_state['rol'].upper()}")
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# --- 🛠️ VISTA ADMINISTRADOR (TODO TIPO DE CAMBIOS) ---
if st.session_state['rol'] == "admin":
    st.title("⚙️ Panel del Administrador")
    tab1, tab2, tab3 = st.tabs(["Base de Datos", "Configuración Técnica", "Mantenimiento"])
    
    with tab1:
        st.subheader("Control Total de Productos")
        st.write("Como Administrador, podés editar toda la estructura.")
        edited_df = st.data_editor(df_prod, num_rows="dynamic", use_container_width=True)
        if st.button("Guardar Estructura"):
            st.success("Cambios estructurales guardados (Simulado)")

    with tab2:
        st.subheader("Tokens y Conexiones")
        new_token = st.text_input("Telegram Token:", value=TELEGRAM_TOKEN)
        new_sheet = st.text_input("ID Google Sheet:", value=ID_SHEET)
        if st.button("Actualizar Conexiones"):
            st.info("Configuración técnica actualizada.")

    with tab3:
        if st.toggle("Activar Modo Mantenimiento"):
            st.warning("⚠️ Aplicación bloqueada para clientes.")

# --- 📝 VISTA USUARIO (CAMBIOS EN CONTENIDO) ---
else:
    st.title(f"📝 Gestión de {conf.get('Nombre Negocio', 'Caniche Food')}")
    
    st.info("Tu perfil permite editar: Nombres, Ingredientes, Precios y Datos del Local.")
    
    menu_user = st.selectbox("¿Qué desea editar?", ["Menú de Comida", "Información del Local"])
    
    if menu_user == "Menú de Comida":
        # Filtramos solo las columnas que el USUARIO puede tocar
        columnas_permitidas = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
        df_usuario = df_prod[columnas_permitidas]
        
        st.write("Edite los precios o ingredientes aquí abajo:")
        cambios_user = st.data_editor(df_usuario, use_container_width=True)
        
        if st.button("Actualizar Menú"):
            st.success("¡Menú actualizado correctamente!")

    elif menu_user == "Información del Local":
        st.subheader("Datos del Negocio")
        nombre_biz = st.text_input("Nombre del Negocio:", value=conf.get("Nombre Negocio", "Caniche Food"))
        dir_biz = st.text_input("Dirección del Local:", value=conf.get("Direccion", "Chamical, La Rioja"))
        costo_env = st.number_input("Costo de Delivery:", value=int(conf.get("Costo Delivery", 0)))
        
        if st.button("Guardar Datos del Local"):
            st.balloons()
            st.success("Datos del negocio actualizados.")

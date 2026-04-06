import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM (Estos datos también podrían ir al Sheet si quisieras) ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- CARGA DE DATOS ---
def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        # Convertimos a diccionario para uso rápido en la App
        conf_dict = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, df_c, conf_dict
    except: return pd.DataFrame(), pd.DataFrame(), {}

# --- INICIALIZACIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
df_prod, df_conf_raw, conf = cargar_datos()

# --- DATOS DINÁMICOS DEL NEGOCIO ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "000000")
costo_d = conf.get("Costo Delivery", "0")

# --- LOGIN SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Acceso Staff")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingresar"):
            u_in = st.text_input("Usuario / DNI:", key="u_log")
            p_in = st.text_input("Clave:", type="password", key="p_log")
            if st.button("Entrar"):
                if u_in == conf.get("Admin_DNI", "30588807") and p_in == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u_in == conf.get("User", "usuario") and p_in == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Datos incorrectos")
    else:
        st.write(f"Conectado como: **{st.session_state['rol'].upper()}**")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title(f"🛠️ Panel de Control: {nombre_n}")
    
    t_menu, t_config = st.tabs(["🍔 Editar Menú", "⚙️ Configuración del Local"])

    with t_menu:
        st.subheader("Gestión de Productos")
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True, key="ed_admin_p")
        else:
            # Columnas que el comprador puede tocar
            cols_edit = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            st.data_editor(df_prod[cols_edit], use_container_width=True, key="ed_user_p")

    with t_config:
        st.subheader("Datos de Facturación y Marca")
        
        # --- FILTRO DE SEGURIDAD PARA EL COMPRADOR ---
        if st.session_state['rol'] == 'usuario':
            # Definimos qué palabras NO puede ver el usuario (tus claves privadas)
            prohibido = ["Admin_DNI", "Admin_Pass", "User_Pass"]
            # El "Alias" NO está en la lista de prohibidos, por lo tanto será visible y editable
            mask = ~df_conf_raw.iloc[:, 0].str.contains('|'.join(prohibido), case=False, na=False)
            df_visible = df_conf_raw[mask]
            
            st.info("Aquí podés cambiar el nombre de tu local, tu teléfono y el ALIAS para cobrar.")
            st.data_editor(df_visible, use_container_width=True, key="ed_conf_user")
        else:
            # El Administrador (tú) ve y edita todo, incluyendo las claves de acceso
            st.warning("⚠️ Vista de Desarrollador: Cuidado al editar claves de acceso.")
            st.data_editor(df_conf_raw, use_container_width=True, key="ed_conf_admin")

# --- VISTA CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    # Al final del pedido, podemos mostrar el Alias dinámicamente
    if st.session_state.get('carrito'):
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #E63946;">
            <p style="margin:0; font-weight:bold; color:#333;">💳 Datos de Pago:</p>
            <p style="margin:0; color:#555;">Alias: <b>{alias_n}</b></p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    st.write("Seleccioná tus categorías arriba para empezar.")
    # (Aquí sigue el código del menú que ya tenemos)

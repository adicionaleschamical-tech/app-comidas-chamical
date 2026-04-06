import streamlit as st
import pandas as pd
import urllib.parse
import time

# ==========================================
# 🔗 CONFIGURACIÓN DE TU GOOGLE SHEET
# ==========================================
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- ESTILOS CSS PARA CELULAR (Botones Horizontales) ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; height: 45px; font-size: 18px; font-weight: bold; border-radius: 8px; }
    .stSelectbox label { font-size: 14px; font-weight: bold; color: #555; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    h2 { margin-bottom: 0px !important; padding-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'user_role' not in st.session_state: st.session_state['user_role'] = None

# --- CARGA DE DATOS ---
@st.cache_data(ttl=5)
def cargar_todo():
    try:
        t = int(time.time())
        # Carga Configuración
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf_dict = dict(zip(df_c.iloc[:, 0].astype(str).str.strip(), df_c.iloc[:, 1].astype(str).str.strip()))
        
        # Carga Productos
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [str(c).strip().capitalize() for c in df_p.columns]
        return df_p, conf_dict
    except:
        return pd.DataFrame(), {}

df_prod, conf = cargar_todo()

# --- LOGIN OCULTO (SIDEBAR) ---
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=CANICHE+FOOD", use_container_width=True) # Podés poner tu logo aquí
    with st.expander("🔐 Acceso Personal"):
        dni_in = st.text_input("DNI / Usuario")
        pass_in = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            if dni_in == conf.get("Admin_DNI") and pass_in == conf.get("Admin_Pass"):
                st.session_state['user_role'] = "admin"
                st.success("Modo Administrador")
                st.rerun()
            elif dni_in == conf.get("User") and pass_in == conf.get("User_Pass"):
                st.session_state['user_role'] = "usuario"
                st.success("Modo Usuario")
                st.rerun()
            else:
                st.error("Datos incorrectos")
    
    if st.session_state['user_role']:
        st.info(f"Sesión: {st.session_state['user_role'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['user_role'] = None
            st.rerun()

# --- INTERFAZ DE VENTAS ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical, La Rioja')}")

if not df_prod.empty:
    # Si es Admin ve todo, si no, solo los "SI" disponibles
    df_ver = df_prod if st.session_state['user_role'] == "admin" else df_prod[df_prod['Disponible'].astype(str).str.upper() == "SI"]
    
    categorias = df_ver['Categoria'].unique()
    tabs = st.tabs(categorias)

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df_ver[df_ver['Categoria'] == cat]
            for _, row in items.iterrows():
                with st.container(border=True):
                    # Imagen y Título
                    img = row.get('Imagen')
                    st.image(img if pd.notna(img) else "https://via.placeholder.com/400x200?text=Caniche+Food", use_container_width=True)
                    st.subheader(row['Producto'])
                    
                    # --- SUB-MENÚ DE VARIEDADES (Desde columna Variedades del Sheet) ---
                    var_sel = ""
                    if 'Variedades' in row and pd.notna(row['Variedades']):
                        ops = [o.strip() for o in str(row['Variedades']).split(',')]
                        var_sel = st.selectbox("Elegí variedad:", ops, key=f"sel_{row['Producto']}")
                    
                    st.write(f"### ${row['Precio']}")

                    # --- BOTONES HORIZONTALES (+ Y -) ---
                    c1, c2, c3 = st.columns([1, 1, 1])
                    p_id = f"{row['Producto']} ({var_sel})" if var_sel else row['Producto']
                    
                    with c1:
                        if st.button("➖", key=f"btn_r_{p_id}"):
                            if p_id in st.session_state['carrito']:
                                st.session_state['carrito'][p_id]['cant'] -= 1
                                if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                st.rerun()
                    with c2:
                        n = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                        st.markdown(f"<h2 style='text-align:center;'>{n}</h2>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕", key=f"btn_a_{p_id}"):
                            if p_id in st.session_state['carrito']:
                                st.session_state['carrito'][p_id]['cant'] += 1
                            else:
                                st.session_state['carrito'][p_id] = {'precio': row['Precio'], 'cant': 1}
                            st.rerun()

    # --- PANELES DE CONTROL (OCULTOS) ---
    if st.session_state['user_role'] == "admin":
        st.divider()
        st.header("🛠️ Panel Administrador")
        st.write("Vista completa del corazón de la base de datos:")
        st.dataframe(df_prod)

    elif st.session_state['user_role'] == "usuario":
        st.divider()
        st.header("📋 Lista de Precios y Stock")
        st.table(df_prod[['Producto', 'Precio', 'Disponible']])

    # --- CARRITO DE COMPRAS ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_m = 0
        resumen_txt = ""
        for prod, data in st.session_state['carrito'].items():
            sub = data['precio'] * data['cant']
            total_m += sub
            st.write(f"✅ {data['cant']}x {prod} — **${sub:,.0f}**")
            resumen_txt += f"- {data['cant']}x {prod} (${sub:,.0f})\n"

        st.write(f"## SUBTOTAL: ${total_m:,.0f}")
        
        nombre = st.text_input("Tu Nombre")
        entrega = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        
        costo_envio = int(conf.get("Costo Delivery", 500)) if entrega == "Delivery" else 0
        if costo_envio > 0: st.info(f"🛵 Envío a domicilio: ${costo_envio}")
        
        total_final = total_m + costo_envio
        st.success(f"### TOTAL A PAGAR: ${total_final:,.0f}")
        
        if st.button("🚀 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
            if not nombre:
                st.error("Falta tu nombre")
            else:
                pago_msg = f"\n💰 *TOTAL CON ENVÍO: ${total_final:,.0f}*\n🏦 *Alias:* {conf.get('Alias')}"
                msj_wa = f"🍔 *NUEVO PEDIDO - CANICHE FOOD*\n👤 *Cliente:* {nombre}\n📍 *Entrega:* {entrega}\n--------------------------\n{resumen_txt}--------------------------{pago_msg}"
                url_wa = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msj_wa)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()

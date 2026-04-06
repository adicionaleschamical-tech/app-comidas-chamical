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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    /* Botones más compactos */
    .stButton > button { width: 100%; height: 40px; font-size: 16px; font-weight: bold; border-radius: 8px; }
    /* Centrar elementos en columnas */
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; flex-direction: column; }
    /* Ajuste de márgenes para que todo entre en menos espacio */
    .stContainer { padding: 10px !important; }
    h2 { margin: 0px !important; font-size: 24px !important; }
    h3 { margin-top: 5px !important; font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'user_role' not in st.session_state: st.session_state['user_role'] = None

# --- CARGA DE DATOS ---
@st.cache_data(ttl=5)
def cargar_todo():
    try:
        t = int(time.time())
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf_dict = dict(zip(df_c.iloc[:, 0].astype(str).str.strip(), df_c.iloc[:, 1].astype(str).str.strip()))
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [str(c).strip().capitalize() for c in df_p.columns]
        return df_p, conf_dict
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_todo()

# --- LOGIN OCULTO ---
with st.sidebar:
    with st.expander("🔐 Acceso Personal"):
        dni_in = st.text_input("DNI / Usuario")
        pass_in = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            if dni_in == conf.get("Admin_DNI") and pass_in == conf.get("Admin_Pass"):
                st.session_state['user_role'] = "admin"
                st.rerun()
            elif dni_in == conf.get("User") and pass_in == conf.get("User_Pass"):
                st.session_state['user_role'] = "usuario"
                st.rerun()
            else: st.error("Datos incorrectos")
    if st.session_state['user_role']:
        if st.button("Cerrar Sesión"):
            st.session_state['user_role'] = None
            st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical')}")

if not df_prod.empty:
    df_ver = df_prod if st.session_state['user_role'] == "admin" else df_prod[df_prod['Disponible'].astype(str).str.upper() == "SI"]
    
    if not df_ver.empty:
        categorias = [c for c in df_ver['Categoria'].unique() if pd.notna(c)]
        tabs = st.tabs(categorias)
        
        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # --- DISEÑO REDUCIDO: Imagen a la izquierda, Info a la derecha ---
                        col_img, col_info = st.columns([1, 1.5])
                        
                        with col_img:
                            img = row.get('Imagen')
                            # FIXED: Imagen con ancho controlado (150px) para que no sea gigante
                            st.image(img if pd.notna(img) else "https://via.placeholder.com/150", width=150)
                        
                        with col_info:
                            st.subheader(row['Producto'])
                            
                            # Variedades (Sub-menú)
                            var_sel = ""
                            if 'Variedades' in row and pd.notna(row['Variedades']):
                                ops = [o.strip() for o in str(row['Variedades']).split(',')]
                                var_sel = st.selectbox("Variedad:", ops, key=f"v_{idx}")
                            
                            st.write(f"### ${row['Precio']}")

                        # --- BOTONES + Y - (Abajo de la info, bien horizontales) ---
                        st.write("---")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        p_id = f"{row['Producto']} ({var_sel})" if var_sel else row['Producto']
                        
                        with c1:
                            if st.button("➖", key=f"r_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2:
                            n = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                            st.markdown(f"## {n}")
                        with c3:
                            if st.button("➕", key=f"a_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] += 1
                                else:
                                    st.session_state['carrito'][p_id] = {'precio': row['Precio'], 'cant': 1}
                                st.rerun()

    # --- PANELES SEGÚN ROL ---
    if st.session_state['user_role'] == "admin":
        st.divider()
        st.subheader("🛠️ Panel Admin")
        st.dataframe(df_prod)
    elif st.session_state['user_role'] == "usuario":
        st.divider()
        st.subheader("📋 Stock")
        st.table(df_prod[['Producto', 'Precio', 'Disponible']])

    # --- CARRITO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_m = 0
        txt = ""
        for p, d in st.session_state['carrito'].items():
            sub = d['precio'] * d['cant']
            total_m += sub
            st.write(f"✅ {d['cant']}x {p} — ${sub:,.0f}")
            txt += f"- {d['cant']}x {p} (${sub:,.0f})\n"
        
        nombre = st.text_input("Tu Nombre")
        entrega = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        envio = int(conf.get("Costo Delivery", 500)) if entrega == "Delivery" else 0
        total_f = total_m + envio
        
        st.success(f"### TOTAL: ${total_f:,.0f}")
        
        if st.button("🚀 PEDIR POR WHATSAPP", use_container_width=True):
            if nombre:
                msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nombre}\n📍 *Entrega:* {entrega}\n{txt}\n💰 *TOTAL: ${total_f:,.0f}*"
                url = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            else: st.error("Falta tu nombre")

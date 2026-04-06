import streamlit as st
import pandas as pd
import urllib.parse
import time

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .btn-variedad > button { height: 35px; font-size: 12px; background-color: #f0f2f6; border: 1px solid #dcdfe3; }
    .btn-variedad-active > button { background-color: #FF4B4B; color: white; border: 1px solid #FF4B4B; }
    .ingredientes-box { background-color: #fdf2f2; padding: 10px; border-radius: 8px; border-left: 5px solid #FF4B4B; font-size: 14px; margin-bottom: 10px; min-height: 50px; color: #333; }
    .precio-tag { color: #FF4B4B; font-size: 26px; font-weight: bold; margin: 5px 0; }
    .stImage > img { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        t = int(time.time())
        # Carga Config (Login, Datos Local)
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = dict(zip(df_c.iloc[:,0].astype(str).str.strip(), df_c.iloc[:,1].astype(str).str.strip()))
        # Carga Productos
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [str(c).strip().capitalize() for c in df_p.columns]
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- LOGIN (SIDEBAR) ---
with st.sidebar:
    st.markdown("### 🔐 Gestión")
    with st.expander("Acceso Personal"):
        u = st.text_input("Usuario / DNI")
        p = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"): 
                st.session_state['user_role'] = "admin"
                st.rerun()
            elif u == conf.get("User") and p == conf.get("User_Pass"): 
                st.session_state['user_role'] = "usuario"
                st.rerun()
            else: st.error("Datos incorrectos")
    
    if st.session_state['user_role']:
        st.info(f"Modo: {st.session_state['user_role'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['user_role'] = None
            st.rerun()

# --- INTERFAZ DE VENTAS ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical, La Rioja')}")

if not df_prod.empty:
    # FILTRO DE DISPONIBILIDAD (El Admin ve todo para controlar)
    if st.session_state['user_role'] == "admin":
        df_ver = df_prod
    else:
        # Solo lo que tiene "SI" en la columna Disponible
        col_disp = 'Disponible' if 'Disponible' in df_prod.columns else None
        if col_disp:
            df_ver = df_prod[df_prod[col_disp].astype(str).str.upper().str.strip() == "SI"]
        else:
            df_ver = df_prod

    if not df_ver.empty:
        cats = [c for c in df_ver['Categoria'].unique() if pd.notna(c)]
        tabs = st.tabs(cats)
        
        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # Lógica de Variedades
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                        pos = st.session_state['sel_v'][idx]

                        # Listas dinámicas por posición (;)
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Datos de la opción seleccionada
                        c_nom = ops[pos] if has_v and pos < len(ops) else ""
                        c_ing = ings[pos] if pos < len(ings) else "Consultar ingredientes"
                        c_img = imgs[pos] if pos < len(imgs) and str(imgs[pos]).startswith('http') else "https://via.placeholder.com/300x200?text=Caniche+Food"
                        
                        try:
                            val_p = pres[pos] if pos < len(pres) else pres[0]
                            c_pre = float("".join(filter(str.isdigit, val_p)))
                        except: c_pre = 0.0

                        # --- DISEÑO DEL PRODUCTO ---
                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: 
                            st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("Elegí:")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        act = "btn-variedad-active" if st.session_state['sel_v'][idx] == vi else "btn-variedad"
                                        st.markdown(f'<div class="{act}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="ingredientes-box">📖 {c_ing}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="precio-tag">${c_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- CARRITO ---
                        st.write("---")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        
                        with c1:
                            if st.button("➖", key=f"r_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2:
                            st.markdown(f"<h2 style='text-align:center;'>{st.session_state['carrito'].get(p_id, {}).get('cant', 0)}</h2>", unsafe_allow_html=True)
                        with c3:
                            if st.button("➕", key=f"a_{idx}"):
                                if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                else: st.session_state['carrito'][p_id] = {'precio': c_pre, 'cant': 1}
                                st.rerun()

    # --- PANELES DE CONTROL ---
    if st.session_state['user_role'] == "admin":
        st.divider()
        st.subheader("🛠️ Panel Admin (Vista Sheet)")
        st.dataframe(df_prod)

    # --- CARRITO FINAL ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_p = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
        for k, v in st.session_state['carrito'].items():
            st.write(f"✅ {v['cant']}x {k} — **${v['precio']*v['cant']:,.0f}**")
        
        nombre = st.text_input("Tu Nombre")
        entrega = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        costo_env = int(conf.get("Costo Delivery", 500)) if entrega == "Delivery" else 0
        
        st.success(f"### TOTAL: ${total_p + costo_env:,.0f}")
        
        if st.button("🚀 ENVIAR POR WHATSAPP", use_container_width=True):
            if nombre:
                resumen = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
                msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nombre}\n📍 *Entrega:* {entrega}\n------------------\n{resumen}\n------------------\n💰 *TOTAL: ${total_p + costo_env:,.0f}*"
                url = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            else: st.error("Por favor, ingresá tu nombre")

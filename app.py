import streamlit as st
import pandas as pd
import urllib.parse
import time
import unicodedata

# --- CONFIGURACIÓN DE FUENTES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- FUNCIÓN DE LIMPIEZA DE COLUMNAS (A prueba de errores de escritura) ---
def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .btn-variedad > button { height: 35px; font-size: 11px; background-color: #f0f2f6; border: 1px solid #dcdfe3; padding: 2px; }
    .btn-variedad-active > button { background-color: #FF4B4B !important; color: white !important; border: 1px solid #FF4B4B; }
    .ingredientes-box { background-color: #fdf2f2; padding: 12px; border-radius: 8px; border-left: 5px solid #FF4B4B; font-size: 14px; margin-top: 10px; color: #333; min-height: 50px; }
    .precio-tag { color: #FF4B4B; font-size: 28px; font-weight: bold; margin: 10px 0; }
    .stImage > img { border-radius: 12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; flex-direction: column; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        t = int(time.time())
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = dict(zip(df_c.iloc[:,0].astype(str).str.strip(), df_c.iloc[:,1].astype(str).str.strip()))
        
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [limpiar_col(c) for c in df_p.columns]
        
        # Asegurar columna Categoria
        if 'Categoria' not in df_p.columns: df_p['Categoria'] = 'General'
        df_p['Categoria'] = df_p['Categoria'].fillna('General').replace('', 'General')
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=Caniche+Food", width=100)
    with st.expander("🔐 Acceso Personal"):
        u = st.text_input("DNI / Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"): 
                st.session_state['user_role'] = "admin"; st.rerun()
            elif u == conf.get("User") and p == conf.get("User_Pass"): 
                st.session_state['user_role'] = "usuario"; st.rerun()
    
    if st.session_state['user_role']:
        st.success(f"Modo: {st.session_state['user_role'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['user_role'] = None; st.rerun()

# --- CUERPO DE LA APP ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical, La Rioja')}")

if not df_prod.empty:
    # Filtro de Disponibilidad
    if st.session_state['user_role'] == "admin":
        df_ver = df_prod
    elif 'Disponible' in df_prod.columns:
        df_ver = df_prod[df_prod['Disponible'].astype(str).str.upper().str.strip() == "SI"]
    else:
        df_ver = df_prod

    cats = [str(c) for c in df_ver['Categoria'].unique() if pd.notna(c)]
    
    if len(cats) > 0:
        tabs = st.tabs(cats)
        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # --- LÓGICA DE SELECCIÓN ---
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        
                        pos = st.session_state['sel_v'][idx]
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Si ya se eligió una variedad o el producto NO tiene variedades
                        if pos is not None or not has_v:
                            p_idx = pos if pos is not None else 0
                            c_nom = ops[p_idx] if has_v else ""
                            c_ing = ings[p_idx] if p_idx < len(ings) else "Ver detalle en el local"
                            c_img = imgs[p_idx] if p_idx < len(imgs) and str(imgs[p_idx]).startswith('http') else (imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/300x200?text=Caniche+Food")
                            try:
                                val_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                c_pre = float("".join(filter(str.isdigit, str(val_p))))
                            except: c_pre = 0.0
                        else:
                            # Estado inicial para productos con variedades
                            c_nom = ""
                            c_ing = "Elegí una opción arriba para ver los ingredientes 🔍"
                            c_img = imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/300x200?text=Caniche+Food"
                            try:
                                c_pre = float("".join(filter(str.isdigit, str(pres[0]))))
                            except: c_pre = 0.0

                        # --- DISEÑO VISUAL ---
                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("Variedad:")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        estilo = "btn-variedad-active" if st.session_state['sel_v'][idx] == vi else "btn-variedad"
                                        st.markdown(f'<div class="{estilo}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi; st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="ingredientes-box">📖 {c_ing}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="precio-tag">${c_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- CONTROLES DE CARRITO ---
                        st.write("---")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        with c1:
                            if st.button("➖", key=f"r_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2: st.markdown(f"<h2 style='text-align:center;'>{st.session_state['carrito'].get(p_id, {}).get('cant', 0)}</h2>", unsafe_allow_html=True)
                        with c3:
                            if st.button("➕", key=f"a_{idx}"):
                                if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                else: st.session_state['carrito'][p_id] = {'precio': c_pre, 'cant': 1}
                                st.rerun()

# --- RESUMEN Y ENVÍO ---
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
    if st.button("🚀 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
        if nombre:
            resumen = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nombre}\n📍 *Entrega:* {entrega}\n------------------\n{resumen}\n------------------\n💰 *TOTAL: ${total_p + costo_env:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)
        else: st.error("Ingresá tu nombre para enviar el pedido")

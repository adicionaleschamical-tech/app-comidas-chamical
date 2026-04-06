import streamlit as st
import pandas as pd
import urllib.parse
import time
import unicodedata

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- ESTILOS CSS "FOOD APP" ---
st.markdown("""
    <style>
    /* Botones de Variedad */
    .stButton > button { width: 100%; border-radius: 20px; font-weight: 600; transition: 0.3s; }
    .btn-variedad > button { height: 32px; font-size: 11px; background-color: #f8f9fa; border: 1px solid #dee2e6; color: #495057; }
    .btn-variedad-active > button { background-color: #FF4B4B !important; color: white !important; border: none; box-shadow: 0 4px 8px rgba(255,75,75,0.3); }
    
    /* Caja de Ingredientes */
    .ingredientes-box { background-color: #ffffff; padding: 12px; border-radius: 12px; border: 1px dashed #FF4B4B; font-size: 14px; margin: 10px 0; color: #555; line-height: 1.4; }
    
    /* Precio */
    .precio-tag { color: #212529; font-size: 24px; font-weight: 800; margin-top: 5px; }
    
    /* --- DISEÑO DE SELECTOR DE CANTIDAD --- */
    .qty-container { background-color: #f8f9fa; border-radius: 30px; padding: 5px 15px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #e9ecef; width: 140px; margin: 0 auto; }
    .qty-btn > button { width: 35px !important; height: 35px !important; border-radius: 50% !important; padding: 0 !important; font-size: 18px !important; line-height: 1 !important; background-color: white !important; border: 1px solid #dee2e6 !important; color: #FF4B4B !important; }
    .qty-btn > button:hover { background-color: #FF4B4B !important; color: white !important; }
    .qty-val { font-size: 20px; font-weight: 700; color: #212529; width: 30px; text-align: center; }
    
    /* Imágenes */
    .stImage > img { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

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
        if 'Categoria' not in df_p.columns: df_p['Categoria'] = 'General'
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- LOGIN ---
with st.sidebar:
    with st.expander("🔐 Acceso"):
        u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"): st.session_state['user_role'] = "admin"; st.rerun()
            elif u == conf.get("User") and p == conf.get("User_Pass"): st.session_state['user_role'] = "usuario"; st.rerun()

st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical')}")

if not df_prod.empty:
    if st.session_state['user_role'] == "admin":
        df_ver = df_prod
    else:
        df_ver = df_prod[df_prod['Disponible'].astype(str).str.upper().str.strip() == "SI"] if 'Disponible' in df_prod.columns else df_prod

    cats = [str(c) for c in df_ver['Categoria'].unique() if pd.notna(c)]
    
    if cats:
        tabs = st.tabs(cats)
        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # --- LÓGICA ---
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        c_img = imgs[pos] if pos is not None and pos < len(imgs) and str(imgs[pos]).startswith('http') else (imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/300x200?text=Caniche+Food")

                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("👇 Seleccioná:")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if st.session_state['sel_v'][idx] == vi else "btn-variedad"
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi; st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            
                            if pos is not None or not has_v:
                                p_idx = pos if pos is not None else 0
                                c_ing = ings[p_idx] if p_idx < len(ings) else ""
                                try:
                                    val_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    c_pre = float("".join(filter(str.isdigit, str(val_p))))
                                except: c_pre = 0.0
                                
                                if c_ing: st.markdown(f'<div class="ingredientes-box">📝 {c_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${c_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- SELECTOR DE CANTIDAD ESTILO APP ---
                        st.write("")
                        c_nom = ops[pos] if pos is not None and has_v else ""
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        bloqueado = has_v and pos is None
                        
                        # Contenedor del selector
                        col_espacio, col_selector, col_espacio2 = st.columns([1, 2, 1])
                        with col_selector:
                            if not bloqueado:
                                # HTML para el estilo visual
                                st.markdown('<div class="qty-container">', unsafe_allow_html=True)
                                c_btn_m, c_val, c_btn_p = st.columns([1, 1, 1])
                                with c_btn_m:
                                    st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                                    if st.button("−", key=f"r_{idx}"):
                                        if p_id in st.session_state['carrito']:
                                            st.session_state['carrito'][p_id]['cant'] -= 1
                                            if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                            st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with c_val:
                                    cant_actual = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                    st.markdown(f'<div class="qty-val">{cant_actual}</div>', unsafe_allow_html=True)
                                
                                with c_btn_p:
                                    st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                                    if st.button("+", key=f"a_{idx}"):
                                        if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                        else: st.session_state['carrito'][p_id] = {'precio': c_pre, 'cant': 1}
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            else:
                                st.caption("👆 Elegí una opción para sumar")

# --- RESUMEN DE COMPRA ---
if st.session_state['carrito']:
    st.markdown("---")
    st.header("🛒 Tu Pedido")
    total_p = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
    for k, v in st.session_state['carrito'].items():
        st.write(f"**{v['cant']}x** {k} — ${v['precio']*v['cant']:,.0f}")
    
    nom = st.text_input("Tu Nombre")
    ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
    costo_env = int(conf.get("Costo Delivery", 500)) if ent == "Delivery" else 0
    st.success(f"### TOTAL: ${total_p + costo_env:,.0f}")
    if st.button("🚀 ENVIAR A WHATSAPP", use_container_width=True):
        if nom:
            res = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n{res}\n💰 *TOTAL: ${total_p + costo_env:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)

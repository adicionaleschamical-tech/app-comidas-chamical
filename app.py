import streamlit as st
import pandas as pd
import urllib.parse
import time

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .btn-variedad > button { height: 35px; font-size: 12px; background-color: #f0f2f6; border: 1px solid #dcdfe3; padding: 0px; }
    .btn-variedad-active > button { background-color: #FF4B4B; color: white; border: 1px solid #FF4B4B; }
    .ingredientes-box { background-color: #fdf2f2; padding: 10px; border-radius: 8px; border-left: 5px solid #FF4B4B; font-size: 14px; margin-bottom: 10px; color: #333; min-height: 60px; }
    .precio-tag { color: #FF4B4B; font-size: 26px; font-weight: bold; margin: 5px 0; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; flex-direction: column; }
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
        df_p.columns = [str(c).strip().capitalize() for c in df_p.columns]
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- LOGIN (SIDEBAR) ---
with st.sidebar:
    with st.expander("🔐 Acceso"):
        u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"): 
                st.session_state['user_role'] = "admin"
                st.rerun()
            elif u == conf.get("User") and p == conf.get("User_Pass"): 
                st.session_state['user_role'] = "usuario"
                st.rerun()

# --- APP PRINCIPAL ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical')}")

if not df_prod.empty:
    df_ver = df_prod if st.session_state['user_role'] == "admin" else df_prod[df_prod['Disponible'].astype(str).str.upper() == "SI"]
    
    if not df_ver.empty:
        tabs = st.tabs(list(df_ver['Categoria'].unique()))
        for i, cat in enumerate(df_ver['Categoria'].unique()):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # --- PROCESAMIENTO DE VARIEDADES ---
                        has_var = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                        pos = st.session_state['sel_v'][idx]

                        # Listas de datos
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_var else []
                        ing_list = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pre_list = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        img_list = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Selección actual
                        current_nom = ops[pos] if has_var and pos < len(ops) else ""
                        current_ing = ing_list[pos] if pos < len(ing_list) else "Sin descripción"
                        current_img = img_list[pos] if pos < len(img_list) and img_list[pos].startswith('http') else "https://via.placeholder.com/300x200?text=Sin+Foto"
                        
                        try:
                            val_pre = pre_list[pos] if pos < len(pre_list) else "0"
                            current_pre = float("".join(filter(str.isdigit, val_pre)))
                        except: current_pre = 0.0

                        # --- DISEÑO ---
                        col_img, col_info = st.columns([1.2, 2])
                        
                        with col_img:
                            # LA IMAGEN CAMBIA SEGÚN LA VARIEDAD
                            st.image(current_img, use_container_width=True)
                        
                        with col_info:
                            st.subheader(row['Producto'])
                            
                            if has_var:
                                st.write("Seleccioná variedad:")
                                cols_v = st.columns(len(ops))
                                for v_i, v_n in enumerate(ops):
                                    with cols_v[v_i]:
                                        active = "btn-variedad-active" if st.session_state['sel_v'][idx] == v_i else "btn-variedad"
                                        st.markdown(f'<div class="{active}">', unsafe_allow_html=True)
                                        if st.button(v_n, key=f"v_{idx}_{v_i}"):
                                            st.session_state['sel_v'][idx] = v_i
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown(f'<div class="ingredientes-box">📖 {current_ing}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="precio-tag">${current_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- CONTROLES CARRITO ---
                        st.write("---")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        p_id = f"{row['Producto']} ({current_nom})" if current_nom else row['Producto']
                        
                        with c1:
                            if st.button("➖", key=f"r_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2:
                            st.markdown(f"## {st.session_state['carrito'].get(p_id, {}).get('cant', 0)}")
                        with c3:
                            if st.button("➕", key=f"a_{idx}"):
                                if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                else: st.session_state['carrito'][p_id] = {'precio': current_pre, 'cant': 1}
                                st.rerun()

    # --- CIERRE DE PEDIDO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total = sum(d['precio'] * d['cant'] for d in st.session_state['carrito'].values())
        for p, d in st.session_state['carrito'].items():
            st.write(f"✅ {d['cant']}x {p} — **${d['precio']*d['cant']:,.0f}**")
        
        nom = st.text_input("Tu Nombre")
        ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        env = int(conf.get("Costo Delivery", 500)) if ent == "Delivery" else 0
        st.success(f"### TOTAL: ${total + env:,.0f}")
        
        if st.button("🚀 PEDIR POR WHATSAPP", use_container_width=True):
            if nom:
                msg = f"🍔 *PEDIDO*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n" + "\n".join([f"- {v['cant']}x {k}" for k,v in st.session_state['carrito'].items()]) + f"\n💰 *TOTAL: ${total+env:,.0f}*"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)

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
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .btn-variedad > button { height: 35px; font-size: 14px; background-color: #f0f2f6; color: #31333F; border: 1px solid #dcdfe3; }
    .btn-variedad-active > button { background-color: #FF4B4B; color: white; border: 1px solid #FF4B4B; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    .ingredientes-box { background-color: #fff4f4; padding: 8px; border-radius: 5px; border-left: 4px solid #FF4B4B; font-size: 13px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'seleccion_variedad' not in st.session_state: st.session_state['seleccion_variedad'] = {}

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

# --- SIDEBAR LOGIN ---
with st.sidebar:
    with st.expander("🔐 Acceso"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"): st.session_state['user_role'] = "admin"; st.rerun()
            elif u == conf.get("User") and p == conf.get("User_Pass"): st.session_state['user_role'] = "usuario"; st.rerun()
    if st.session_state['user_role']:
        if st.button("Salir"): st.session_state['user_role'] = None; st.rerun()

# --- CUERPO DE LA APP ---
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
                        col_img, col_info = st.columns([1, 2])
                        
                        with col_img:
                            st.image(row.get('Imagen') if pd.notna(row.get('Imagen')) else "https://via.placeholder.com/150", width=120)
                        
                        with col_info:
                            st.subheader(row['Producto'])
                            
                            # --- LÓGICA DE BOTONES DE VARIEDAD ---
                            if 'Variedades' in row and pd.notna(row['Variedades']):
                                ops = [o.strip() for o in str(row['Variedades']).split(',')]
                                ing_list = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                                
                                # Si no hay selección previa, elegimos la primera
                                if idx not in st.session_state['seleccion_variedad']:
                                    st.session_state['seleccion_variedad'][idx] = ops[0]
                                
                                # Fila de botones para variedades
                                st.write("Seleccioná:")
                                cols_var = st.columns(len(ops))
                                for v_idx, v_nom in enumerate(ops):
                                    with cols_var[v_idx]:
                                        estilo = "btn-variedad-active" if st.session_state['seleccion_variedad'][idx] == v_nom else "btn-variedad"
                                        st.markdown(f'<div class="{estilo}">', unsafe_allow_html=True)
                                        if st.button(v_nom, key=f"btn_{idx}_{v_idx}"):
                                            st.session_state['seleccion_variedad'][idx] = v_nom
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Mostrar Ingredientes según la variedad seleccionada
                                try:
                                    current_v_idx = ops.index(st.session_state['seleccion_variedad'][idx])
                                    if current_v_idx < len(ing_list):
                                        st.markdown(f'<div class="ingredientes-box">📖 {ing_list[current_v_idx]}</div>', unsafe_allow_html=True)
                                except: pass
                            
                            st.write(f"### ${row['Precio']}")

                        # --- CONTROLES DE CANTIDAD ---
                        st.write("---")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        v_actual = st.session_state['seleccion_variedad'].get(idx, "")
                        p_id = f"{row['Producto']} ({v_actual})" if v_actual else row['Producto']
                        
                        with c1:
                            if st.button("➖", key=f"res_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2:
                            n = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                            st.markdown(f"## {n}")
                        with c3:
                            if st.button("➕", key=f"add_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] += 1
                                else:
                                    st.session_state['carrito'][p_id] = {'precio': row['Precio'], 'cant': 1}
                                st.rerun()

    # --- CARRITO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_m = 0
        txt = ""
        for p, d in st.session_state['carrito'].items():
            sub = d['precio'] * d['cant']
            total_m += sub
            st.write(f"✅ {d['cant']}x {p} — **${sub:,.0f}**")
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

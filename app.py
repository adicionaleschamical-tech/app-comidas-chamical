import streamlit as st
import pandas as pd
import time
import requests

# --- DATOS DE ACCESO ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food", page_icon="🍟", layout="centered")

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok")
    except: return False

def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, conf
    except: return pd.DataFrame(), {}

# --- DISEÑO ANTI-MODO OSCURO (ESPECIAL PARA IOS) ---
st.markdown("""
    <style>
    /* Forzar fondo blanco total en toda la app */
    .stApp, div[data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
    }

    /* Forzar color de texto negro en CUALQUIER elemento */
    h1, h2, h3, p, span, div, label, .stMarkdown {
        color: #111111 !important;
    }

    /* Caja de producto con bordes claros y fondo sólido */
    .producto-caja { 
        border: 2px solid #F0F0F0 !important; 
        padding: 12px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        background-color: #F9F9F9 !important;
    }
    
    /* Imagen con tamaño controlado */
    [data-testid="stImage"] img {
        max-height: 140px !important;
        width: auto !important;
        border-radius: 8px;
    }

    /* Precio en rojo Caniche */
    .precio { 
        color: #E63946 !important; 
        font-size: 24px !important; 
        font-weight: 800 !important; 
    }

    /* Botones con fondo gris claro para que se vean siempre */
    .stButton > button {
        background-color: #EEEEEE !important;
        color: #111111 !important;
        border: 1px solid #CCCCCC !important;
        height: 45px !important;
    }

    /* Estilo del resumen final */
    .resumen-item {
        background-color: #FFFFFF !important;
        border-left: 5px solid #E63946 !important;
        padding: 8px;
        margin-bottom: 5px;
        color: #111111 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, conf = cargar_datos()

st.markdown("<h1 style='text-align: center;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)

if not df_prod.empty:
    df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"] if 'DISPONIBLE' in df_prod.columns else df_prod
    categorias = df_ver['CATEGORIA'].unique()
    tabs = st.tabs(list(categorias))

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df_ver[df_ver['CATEGORIA'] == cat]
            for idx, row in items.iterrows():
                st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                
                col_img, col_txt = st.columns([1, 1.5])
                
                with col_img:
                    img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150"
                    st.image(img)
                
                with col_txt:
                    st.markdown(f"**{row['PRODUCTO']}**")
                    
                    tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                    if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                    
                    if tiene_v:
                        ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                        sel = st.selectbox("Variedad:", ["Elegir..."] + ops, key=f"sel_{idx}")
                        if sel != "Elegir...":
                            st.session_state['sel_v'][idx] = ops.index(sel)
                    
                    pos = st.session_state['sel_v'][idx]
                    if not tiene_v or pos is not None:
                        p_idx = pos if pos is not None else 0
                        precios = str(row['PRECIO']).split(';')
                        try:
                            p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                            precio_f = float("".join(filter(str.isdigit, p_raw)))
                        except: precio_f = 0
                        
                        st.markdown(f'<p class="precio">${precio_f:,.0f}</p>', unsafe_allow_html=True)

                        # Botones cantidad
                        p_nom = f"{row['PRODUCTO']} ({ops[pos]})" if tiene_v else row['PRODUCTO']
                        c1, c2, c3 = st.columns([1,1,1])
                        with c1:
                            if st.button("➖", key=f"m_{idx}"):
                                if p_nom in st.session_state['carrito']:
                                    st.session_state['carrito'][p_nom]['cant'] -= 1
                                    if st.session_state['carrito'][p_nom]['cant'] <= 0: del st.session_state['carrito'][p_nom]
                                    st.rerun()
                        with c2:
                            cant = st.session_state['carrito'].get(p_nom, {}).get('cant', 0)
                            st.markdown(f"<p style='text-align:center;'><b>{cant}</b></p>", unsafe_allow_html=True)
                        with c3:
                            if st.button("➕", key=f"p_{idx}"):
                                if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                                else: st.session_state['carrito'][p_nom] = {'precio': precio_f, 'cant': 1}
                                st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL DE CIERRE ---
if st.session_state['carrito']:
    st.divider()
    st.markdown("### 🛒 Tu Pedido")
    total_f = 0
    resumen = ""
    for item, d in st.session_state['carrito'].items():
        sub = d['precio'] * d['cant']
        total_f += sub
        st.markdown(f"<div class='resumen-item'><b>{d['cant']}x</b> {item} (${sub:,.0f})</div>", unsafe_allow_html=True)
        resumen += f"• {d['cant']}x {item} (${sub:,.0f})\n"

    nom = st.text_input("Nombre:")
    ent = st.radio("Entrega:", ["Retiro", "Delivery"], horizontal=True)
    
    c_env = 0
    if ent == "Delivery":
        dir_c = st.text_area("Dirección:")
        try: c_env = int(conf.get("Costo Delivery", 0))
        except: c_env = 0
    
    total_total = total_f + c_env
    st.markdown(f"<h2 style='color:#E63946 !important;'>Total: ${total_total:,.0f}</h2>", unsafe_allow_html=True)

    if st.button("🚀 ENVIAR PEDIDO", use_container_width=True):
        if nom:
            msg = f"🔔 *PEDIDO*\n👤 {nom}\n📍 {ent}\n------------------\n{resumen}------------------\n💰 *TOTAL: ${total_total:,.0f}*"
            if enviar_telegram(msg):
                st.success("¡Enviado! Revisá tu Telegram X.")
                st.session_state['carrito'] = {}
                st.balloons()

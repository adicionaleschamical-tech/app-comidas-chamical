import streamlit as st
import pandas as pd
import time
import unicodedata
import requests

# --- DATOS DE ACCESO ---
ID_SHEET = "1WcVWos3p9NJKKEpY2V1-gmKhEkZJH1FL8Hy5bNqHyRA"
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

def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- DISEÑO ULTRA-COMPATIBLE CON IOS ---
st.markdown("""
    <style>
    /* Reset de fuentes y colores para Safari */
    * { color: #111111 !important; font-family: -apple-system, sans-serif !important; }
    
    .stApp { background-color: #FFFFFF !important; }

    /* Contenedores Flexibles (No fijos para que el texto respire) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FDFDFD !important; 
        border: 2px solid #EEEEEE !important; 
        border-radius: 15px; 
        padding: 15px; 
        margin-bottom: 10px;
    }

    /* Títulos y Subtítulos con contraste alto */
    h1, h2, h3, p, span, label { color: #000000 !important; font-weight: 600; }

    /* Caja de Ingredientes (Fondo más fuerte para que resalte el texto) */
    .ingredientes-box { 
        background-color: #FFF3CD !important; 
        padding: 10px; 
        border-radius: 10px; 
        border-left: 8px solid #FFB703; 
        margin: 10px 0; 
        font-size: 16px !important;
        display: block !important;
    }

    /* Precio resaltado */
    .precio-tag { color: #E63946 !important; font-size: 28px !important; font-weight: 900 !important; }

    /* Botones de Variedad (Más altos para el dedo) */
    .stButton > button { 
        height: 50px !important; 
        border-radius: 10px !important;
        border: 1px solid #DDD !important;
    }
    
    /* Cantidades */
    .qty-text { font-size: 24px !important; font-weight: bold !important; text-align: center; }

    /* Item del Carrito */
    .item-resumen { 
        background: #F1F1F1 !important; 
        padding: 12px; 
        border-radius: 12px; 
        margin-bottom: 5px; 
        border-left: 6px solid #E63946; 
    }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        t = int(time.time())
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [limpiar_col(c) for c in df_p.columns]
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

st.markdown("<h1 style='text-align: center; color: #E63946 !important;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)

if not df_prod.empty:
    df_ver = df_prod[df_prod['Disponible'].astype(str).str.upper().str.strip() == "SI"] if 'Disponible' in df_prod.columns else df_prod
    cats = [str(c) for c in df_ver['Categoria'].unique() if pd.notna(c)]
    
    if cats:
        tabs = st.tabs(cats)
        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        c_img = imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/400x300?text=Comida"

                        # Layout simplificado para mejor lectura en pantallas pequeñas
                        st.image(c_img, use_container_width=True)
                        st.markdown(f"### {row['Producto']}")
                        
                        if has_v:
                            st.write("🥤 **Elegí una opción:**")
                            for vi, vn in enumerate(ops):
                                if st.button(f"{vn}", key=f"v_{idx}_{vi}", use_container_width=True):
                                    st.session_state['sel_v'][idx] = vi
                                    st.rerun()

                        if not has_v or pos is not None:
                            p_idx = pos if pos is not None else 0
                            d_ing = ings[p_idx] if p_idx < len(ings) else ""
                            try:
                                raw_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                d_pre = float("".join(filter(str.isdigit, str(raw_p))))
                            except: d_pre = 0.0

                            if d_ing:
                                st.markdown(f'<div class="ingredientes-box"><b>Detalle:</b> {d_ing}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                            # Selector de cantidad
                            p_id = f"{row['Producto']} ({ops[pos]})" if has_v and pos is not None else row['Producto']
                            c1, c2, c3 = st.columns([1,1,1])
                            with c1:
                                if st.button("➖", key=f"r_{idx}"):
                                    if p_id in st.session_state['carrito']:
                                        st.session_state['carrito'][p_id]['cant'] -= 1
                                        if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                        st.rerun()
                            with c2:
                                q = st.session_state["carrito"].get(p_id, {}).get("cant", 0)
                                st.markdown(f"<p class='qty-text'>{q}</p>", unsafe_allow_html=True)
                            with c3:
                                if st.button("➕", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': d_pre, 'cant': 1}
                                    st.rerun()

# --- SECCIÓN CARRITO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Resumen")
    tot_p = 0
    res_t = ""
    for k, v in st.session_state['carrito'].items():
        sub = v['precio'] * v['cant']
        tot_p += sub
        st.markdown(f"<div class='item-resumen'><b>{v['cant']}x</b> {k}<br>Subtotal: ${sub:,.0f}</div>", unsafe_allow_html=True)
        res_t += f"• {v['cant']}x {k} (${sub:,.0f})\n"

    with st.container(border=True):
        nom = st.text_input("👤 Nombre:")
        pago = st.selectbox("💰 Pago:", ["Efectivo", "Transferencia", "Mercado Pago"])
        ent = st.radio("🛵 Entrega:", ["Retiro", "Delivery"], horizontal=True)
        
        c_env = 0
        dir_c = ""
        if ent == "Delivery":
            dir_c = st.text_area("🏠 Dirección:")
            try: c_env = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "0")))))
            except: c_env = 0
        
        total_f = tot_p + c_env
        st.markdown(f"<h2 style='text-align:center; background:#E63946 !important; color:white !important; padding:15px; border-radius:15px;'>TOTAL: ${total_f:,.0f}</h2>", unsafe_allow_html=True)

        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True):
            if nom and (ent == "Retiro" or dir_c):
                msg = (f"🔔 *NUEVO PEDIDO*\n\n👤 *Cliente:* {nom}\n📍 *Modo:* {ent}\n"
                       f"💳 *Pago:* {pago}\n------------------\n{res_t}"
                       f"------------------\n💰 *TOTAL: ${total_f:,.0f}*")
                if enviar_telegram(msg):
                    st.success("¡Pedido enviado!")
                    st.session_state['carrito'] = {}
                    st.balloons()

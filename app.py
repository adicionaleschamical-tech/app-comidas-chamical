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

# --- DISEÑO REFORZADO PARA VISIBILIDAD TOTAL EN IOS ---
st.markdown("""
    <style>
    /* Forzar fondo blanco y texto negro en todo */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: #111111 !important; }

    /* Caja de producto */
    .producto-caja { 
        border: 2px solid #E0E0E0 !important; 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        background-color: #FDFDFD !important;
    }
    
    /* CAJA DE INGREDIENTES: Post-it Amarillo para que se vea SI O SI */
    .ingredientes-vivos {
        background-color: #FFF9C4 !important; /* Amarillo claro */
        color: #000000 !important;
        padding: 12px;
        border-radius: 10px;
        border-left: 8px solid #FBC02D !important;
        margin: 10px 0px;
        font-size: 15px !important;
        font-weight: 600 !important;
        line-height: 1.4;
    }

    /* Precio resaltado */
    .precio-vete { 
        color: #E63946 !important; 
        font-size: 26px !important; 
        font-weight: 800 !important; 
        margin: 10px 0;
    }

    /* Botones de cantidad con mejor contraste */
    .stButton > button {
        background-color: #F1F1F1 !important;
        color: #111111 !important;
        border: 1px solid #BBBBBB !important;
        font-weight: bold !important;
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
                
                # Imagen y Nombre
                img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150"
                st.image(img, width=180)
                st.markdown(f"## {row['PRODUCTO']}")
                
                # Manejo de Variedades
                tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                
                if tiene_v:
                    ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                    sel = st.selectbox("👇 Elegí tu Variedad:", ["- Seleccionar -"] + ops, key=f"sel_{idx}")
                    if sel != "- Seleccionar -":
                        st.session_state['sel_v'][idx] = ops.index(sel)
                    else:
                        st.session_state['sel_v'][idx] = None
                
                # Mostrar Detalles solo si hay selección o no hay variedad
                pos = st.session_state['sel_v'][idx]
                if not tiene_v or pos is not None:
                    p_idx = pos if pos is not None else 0
                    
                    # --- MOSTRAR INGREDIENTES ---
                    if 'INGREDIENTES' in row and pd.notna(row['INGREDIENTES']):
                        ings_list = str(row['INGREDIENTES']).split(';')
                        det_ing = ings_list[p_idx] if p_idx < len(ings_list) else ings_list[0]
                        st.markdown(f'<div class="ingredientes-vivos"><b>Trae:</b><br>{det_ing}</div>', unsafe_allow_html=True)

                    # --- MOSTRAR PRECIO ---
                    precios_list = str(row['PRECIO']).split(';')
                    try:
                        p_raw = precios_list[p_idx] if p_idx < len(precios_list) else precios_list[0]
                        precio_f = float("".join(filter(str.isdigit, p_raw)))
                    except: precio_f = 0
                    
                    st.markdown(f'<p class="precio-vete">${precio_f:,.0f}</p>', unsafe_allow_html=True)

                    # --- CONTROLES DE CARRITO ---
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
                        st.markdown(f"<h3 style='text-align:center; margin-top:10px;'>{cant}</h3>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕", key=f"p_{idx}"):
                            if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                            else: st.session_state['carrito'][p_nom] = {'precio': precio_f, 'cant': 1}
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL DE CIERRE ---
if st.session_state['carrito']:
    st.divider()
    st.markdown("## 🛒 Tu Carrito")
    total_f = 0
    resumen = ""
    for item, d in st.session_state['carrito'].items():
        sub = d['precio'] * d['cant']
        total_f += sub
        st.markdown(f"**{d['cant']}x** {item} (${sub:,.0f})")
        resumen += f"• {d['cant']}x {item} (${sub:,.0f})\n"

    nom = st.text_input("👤 Nombre del Cliente:")
    ent = st.radio("🛵 ¿Cómo lo recibís?", ["Retiro en Local", "Delivery"], horizontal=True)
    
    c_env = 0
    if ent == "Delivery":
        dir_c = st.text_area("🏠 Dirección y Referencias:")
        try: c_env = int(conf.get("Costo Delivery", 0))
        except: c_env = 0
    
    total_total = total_f + c_env
    st.markdown(f"<h2 style='color:#E63946 !important; text-align:center;'>Total: ${total_total:,.0f}</h2>", unsafe_allow_html=True)

    if st.button("🚀 CONFIRMAR Y ENVIAR PEDIDO", use_container_width=True):
        if nom:
            msg = f"🔔 *PEDIDO NUEVO*\n👤 {nom}\n📍 {ent}\n------------------\n{resumen}------------------\n💰 *TOTAL: ${total_total:,.0f}*"
            if enviar_telegram(msg):
                st.success("¡Pedido enviado con éxito!")
                st.session_state['carrito'] = {}
                st.balloons()
            else:
                st.error("Error al enviar. ¿Diste START al bot?")

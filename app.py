import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE ACCESO ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- CONFIGURACIÓN DE TELEGRAM ---
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

# --- DISEÑO DE BOTONES Y VISIBILIDAD ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }

    .producto-caja { 
        border: 2px solid #EEEEEE !important; 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        background-color: #F9F9F9 !important;
    }

    .btn-active > button {
        background-color: #E63946 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }

    .stButton > button {
        height: 45px !important;
        border-radius: 8px !important;
    }

    .ingredientes-vivos {
        background-color: #FFF9C4 !important; 
        color: #000000 !important;
        padding: 15px;
        border-radius: 12px;
        border-left: 10px solid #FBC02D !important;
        margin: 12px 0px;
        font-size: 16px !important;
    }

    .precio-vete { 
        color: #E63946 !important; 
        font-size: 32px !important; 
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, conf = cargar_datos()

st.markdown("<h1 style='text-align: center; color: #E63946 !important;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)

if not df_prod.empty:
    df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"] if 'DISPONIBLE' in df_prod.columns else df_prod
    categorias = df_ver['CATEGORIA'].unique()
    tabs = st.tabs(list(categorias))

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df_ver[df_ver['CATEGORIA'] == cat]
            for idx, row in items.iterrows():
                st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                
                img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200"
                st.image(img, width=250)
                st.markdown(f"## {row['PRODUCTO']}")
                
                tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                
                if tiene_v:
                    ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                    st.write("✨ **Elegí tu opción:**")
                    cols_btn = st.columns(len(ops))
                    for vi, vn in enumerate(ops):
                        with cols_btn[vi]:
                            is_active = st.session_state['sel_v'][idx] == vi
                            if is_active: st.markdown('<div class="btn-active">', unsafe_allow_html=True)
                            if st.button(vn, key=f"btn_{idx}_{vi}", use_container_width=True):
                                st.session_state['sel_v'][idx] = vi
                                st.rerun()
                            if is_active: st.markdown('</div>', unsafe_allow_html=True)

                pos = st.session_state['sel_v'][idx]
                if not tiene_v or pos is not None:
                    p_idx = pos if pos is not None else 0
                    if 'INGREDIENTES' in row and pd.notna(row['INGREDIENTES']):
                        ings_list = str(row['INGREDIENTES']).split(';')
                        det_ing = ings_list[p_idx] if p_idx < len(ings_list) else ings_list[0]
                        st.markdown(f'<div class="ingredientes-vivos"><b>Esta variedad trae:</b><br>{det_ing}</div>', unsafe_allow_html=True)

                    precios_list = str(row['PRECIO']).split(';')
                    try:
                        p_raw = precios_list[p_idx] if p_idx < len(precios_list) else precios_list[0]
                        precio_f = float("".join(filter(str.isdigit, p_raw)))
                    except: precio_f = 0
                    
                    st.markdown(f'<p class="precio-vete">${precio_f:,.0f}</p>', unsafe_allow_html=True)

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
                        st.markdown(f"<h2 style='text-align:center;'>{cant}</h2>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕", key=f"p_{idx}"):
                            if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                            else: st.session_state['carrito'][p_nom] = {'precio': precio_f, 'cant': 1}
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL FINAL ---
if st.session_state['carrito']:
    st.divider()
    st.markdown("## 🛒 Tu Pedido")
    total_acumulado = 0
    resumen_txt = ""
    for item, d in st.session_state['carrito'].items():
        sub = d['precio'] * d['cant']
        total_acumulado += sub
        st.write(f"✅ **{d['cant']}x** {item} (${sub:,.0f})")
        resumen_txt += f"• {d['cant']}x {item} (${sub:,.0f})\n"

    with st.container(border=True):
        nombre = st.text_input("👤 Tu Nombre:")
        metodo = st.selectbox("💰 Pago:", ["Efectivo", "Transferencia", "Mercado Pago"])
        entrega = st.radio("🛵 Entrega:", ["Retiro en Local", "Delivery"], horizontal=True)
        
        envio_costo = 0
        dir_c = ""
        if entrega == "Delivery":
            dir_c = st.text_area("🏠 Dirección y Referencias (Ej: Calle Falsa 123, portón verde):")
            try: envio_costo = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "0")))))
            except: envio_costo = 0
        
        total_final = total_acumulado + envio_costo
        st.markdown(f"<h1 style='text-align:center; background:#E63946; color:white; border-radius:15px;'>TOTAL: ${total_final:,.0f}</h1>", unsafe_allow_html=True)

        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True):
            if not nombre:
                st.error("Por favor, ingresá tu nombre.")
            elif entrega == "Delivery" and not dir_c:
                st.error("Por favor, ingresá la dirección para el Delivery.")
            else:
                # --- CORRECCIÓN AQUÍ: Agregamos la dirección al mensaje ---
                detalles_entrega = f"🏠 *Dirección:* {dir_c}" if entrega == "Delivery" else "🏢 *Retira en local*"
                
                msg = (f"🔔 *NUEVO PEDIDO*\n\n"
                       f"👤 *Cliente:* {nombre}\n"
                       f"🛵 *Modo:* {entrega}\n"
                       f"{detalles_entrega}\n"
                       f"💳 *Pago:* {metodo}\n"
                       f"------------------\n"
                       f"{resumen_txt}"
                       f"------------------\n"
                       f"💰 *TOTAL: ${total_final:,.0f}*")
                
                if enviar_telegram(msg):
                    st.success("¡Pedido enviado! Revisá tu Telegram X.")
                    st.session_state['carrito'] = {}
                    st.balloons()
                else:
                    st.error("Error al enviar. ¿Diste START al bot?")

import streamlit as st
import pandas as pd
import urllib.parse
import time
import unicodedata
import requests

# --- CONFIGURACIÓN DE ACCESO ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TUS DATOS DE TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        st.error("Error de conexión con el servidor de notificaciones.")

def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- ESTILO VISUAL FAST FOOD ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FFFFFF; border: none !important; border-radius: 20px; 
        padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .btn-variedad-active > button { background-color: #E63946 !important; color: white !important; border: none; }
    .ingredientes-box { background-color: #FFF9E6; padding: 15px; border-radius: 15px; border-left: 6px solid #FFB703; margin: 10px 0; }
    .precio-tag { color: #E63946; font-size: 30px; font-weight: 900; }
    .qty-container { background-color: #F1F1F1; border-radius: 50px; padding: 5px; display: flex; align-items: center; justify-content: center; gap: 15px; width: 150px; margin: 10px auto; }
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

st.markdown("<h1 style='text-align: center; color: #E63946;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)

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

                        col_img, col_info = st.columns([1, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("🥤 **Variedad:**")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if pos == vi else ""
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)

                            if not has_v or pos is not None:
                                p_idx = pos if pos is not None else 0
                                d_ing = ings[p_idx] if p_idx < len(ings) else ""
                                try:
                                    raw_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    d_pre = float("".join(filter(str.isdigit, str(raw_p))))
                                except: d_pre = 0.0

                                if d_ing:
                                    st.markdown(f'<div class="ingredientes-box"><b>Esta variedad trae:</b><br>{d_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                        p_id = f"{row['Producto']} ({ops[pos]})" if has_v and pos is not None else row['Producto']
                        if not (has_v and pos is None):
                            st.markdown('<div class="qty-container">', unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([1,1,1])
                            with c1:
                                if st.button("−", key=f"r_{idx}"):
                                    if p_id in st.session_state['carrito']:
                                        st.session_state['carrito'][p_id]['cant'] -= 1
                                        if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                        st.rerun()
                            with c2:
                                st.markdown(f'<b>{st.session_state["carrito"].get(p_id, {}).get("cant", 0)}</b>', unsafe_allow_html=True)
                            with c3:
                                if st.button("+", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': d_pre, 'cant': 1}
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

# --- SECCIÓN DE PAGO Y ENVÍO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Finalizar Compra")
    
    nom = st.text_input("👤 Tu Nombre:")
    pago = st.selectbox("💰 Medio de Pago:", ["Efectivo", "Transferencia", "Mercado Pago"])
    ent = st.radio("🛵 Entrega:", ["Retiro en Local", "Delivery"], horizontal=True)
    
    costo_envio = 0
    dir_cliente = ""
    if ent == "Delivery":
        dir_cliente = st.text_area("🏠 Dirección y referencias:")
        try: costo_envio = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "500")))))
        except: costo_envio = 0
        st.warning(f"Costo de envío: ${costo_envio:,.0f}")
    else:
        st.info(f"📍 Retirás en: {conf.get('Direccion Local', 'Chamical')}")

    total_prod = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
    total_total = total_prod + costo_envio
    
    st.markdown(f"<h2 style='text-align:center; background:#E63946; color:white; padding:15px; border-radius:15px;'>TOTAL: ${total_total:,.0f}</h2>", unsafe_allow_html=True)

    if st.button("🚀 CONFIRMAR PEDIDO", use_container_width=True):
        if nom and (ent == "Retiro en Local" or dir_cliente):
            items = "\n".join([f"• {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            ticket = (
                f"🔔 *¡NUEVO PEDIDO RECIBIDO!*\n\n"
                f"👤 *Cliente:* {nom}\n"
                f"📍 *Modo:* {ent}\n"
                f"{'🏠 *Dirección:* ' + dir_cliente if ent == 'Delivery' else '🏢 *Retira en local*'}\n"
                f"💳 *Pago:* {pago}\n"
                f"--------------------------\n"
                f"{items}\n"
                f"--------------------------\n"
                f"💰 *TOTAL A COBRAR: ${total_total:,.0f}*"
            )
            enviar_telegram(ticket)
            st.success("¡Pedido enviado! Te avisaremos por WhatsApp para coordinar la entrega.")
            st.balloons()
            # Opcional: limpiar carrito tras pedir
            # st.session_state['carrito'] = {}
        else:
            st.error("⚠️ Por favor completa tu nombre y dirección.")

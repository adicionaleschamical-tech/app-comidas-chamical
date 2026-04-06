import streamlit as st
import pandas as pd
import urllib.parse
import time
import unicodedata
import requests

# --- CONFIGURACIÓN DE ACCESO (TU GOOGLE SHEETS) ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TUS DATOS DE TELEGRAM (VERIFICADOS) ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- FUNCIÓN DE ENVÍO CON DIAGNÓSTICO ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_ID, 
        "text": mensaje, 
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        resultado = response.json()
        if resultado.get("ok"):
            st.success("✅ ¡Pedido enviado a Telegram!")
            return True
        else:
            # Esto te dirá exactamente qué falla (ej: "Forbidden: bot was blocked by the user")
            st.error(f"❌ Error de Telegram: {resultado.get('description')}")
            st.info("Asegurate de haberle dado 'START' a tu propio Bot en Telegram X.")
            return False
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return False

def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FFFFFF; border: none !important; border-radius: 20px; 
        padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .btn-variedad-active > button { background-color: #E63946 !important; color: white !important; border: none; }
    .ingredientes-box { background-color: #FFF9E6; padding: 12px; border-radius: 12px; border-left: 5px solid #FFB703; margin: 10px 0; font-size: 13px; color: #555; }
    .precio-tag { color: #E63946; font-size: 28px; font-weight: 900; margin-top: 10px; }
    .qty-container { background-color: #F1F1F1; border-radius: 50px; padding: 5px; display: flex; align-items: center; justify-content: center; gap: 15px; width: 140px; margin: 10px auto; }
    .item-resumen { background: #fdfdfd; padding: 10px; border-radius: 10px; margin-bottom: 8px; border-left: 4px solid #E63946; box-shadow: 2px 2px 5px rgba(0,0,0,0.02); }
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

st.markdown("<h1 style='text-align: center; color: #E63946; margin-bottom: 0;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>¡Elegí, confirmá y recibí!</p>", unsafe_allow_html=True)

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

                        c_img = imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/400x300?text=Caniche+Food"

                        col_img, col_info = st.columns([1, 1.5])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("👇 **Elegí tu variedad:**")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if pos == vi else ""
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}", use_container_width=True):
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
                                    st.markdown(f'<div class="ingredientes-box">📋 {d_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- LÓGICA DE CANTIDADES ---
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
                                cant_actual = st.session_state["carrito"].get(p_id, {}).get("cant", 0)
                                st.markdown(f'<div style="font-size:22px; font-weight:bold; text-align:center;">{cant_actual}</div>', unsafe_allow_html=True)
                            with c3:
                                if st.button("+", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': d_pre, 'cant': 1}
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL DE FINALIZACIÓN ---
if st.session_state['carrito']:
    st.divider()
    st.header("📋 Resumen de tu Pedido")
    
    total_acumulado = 0
    texto_telegram = ""
    
    # Mostrar el detalle en la web para que el cliente esté seguro
    for item, datos in st.session_state['carrito'].items():
        sub = datos['precio'] * datos['cant']
        total_acumulado += sub
        st.markdown(f"""
            <div class="item-resumen">
                <b>{datos['cant']}x {item}</b><br>
                <small style="color:#E63946;">Subtotal: ${sub:,.0f}</small>
            </div>
        """, unsafe_allow_html=True)
        texto_telegram += f"• {datos['cant']}x {item} (${sub:,.0f})\n"

    st.write("")
    with st.container(border=True):
        st.subheader("📍 Datos de entrega")
        nom = st.text_input("¿A nombre de quién?")
        pago = st.selectbox("¿Cómo vas a pagar?", ["Efectivo", "Transferencia / Alias", "Mercado Pago"])
        ent = st.radio("¿Retiro o Envío?", ["Retiro en Local", "Delivery"], horizontal=True)
        
        costo_envio = 0
        dir_cliente = ""
        if ent == "Delivery":
            dir_cliente = st.text_area("Dirección exacta:")
            try: costo_envio = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "0")))))
            except: costo_envio = 0
            if costo_envio > 0: st.info(f"Costo de envío: ${costo_envio:,.0f}")
        
        total_final = total_acumulado + costo_envio
        st.markdown(f"<h2 style='text-align:center; background:#E63946; color:white; padding:15px; border-radius:15px;'>TOTAL: ${total_final:,.0f}</h2>", unsafe_allow_html=True)

        if st.button("🚀 CONFIRMAR PEDIDO Y ENVIAR", use_container_width=True):
            if not nom:
                st.error("⚠️ Por favor, ingresá tu nombre.")
            elif ent == "Delivery" and not dir_cliente:
                st.error("⚠️ Necesitamos tu dirección para el envío.")
            else:
                # Construcción del remito para vos
                remito = (
                    f"🔔 *¡NUEVO PEDIDO RECIBIDO!*\n\n"
                    f"👤 *Cliente:* {nom}\n"
                    f"🛵 *Tipo:* {ent}\n"
                    f"{'🏠 *Dirección:* ' + dir_cliente if ent == 'Delivery' else '🏢 *Retira en local*'}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"--------------------------\n"
                    f"{texto_telegram}"
                    f"--------------------------\n"
                    f"💰 *TOTAL A COBRAR: ${total_final:,.0f}*"
                )
                
                # Ejecutar envío
                if enviar_telegram(remito):
                    st.balloons()
                    st.session_state['carrito'] = {} # Opcional: limpiar carrito
                    st.info("¡Gracias! Tu pedido ya entró al sistema. Si tenés dudas, escribinos por WhatsApp.")

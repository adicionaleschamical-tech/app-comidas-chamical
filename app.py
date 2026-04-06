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

# --- ESTILO VISUAL: FAST FOOD (Blanco, Rojo y Amarillo) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    
    /* Tarjetas */
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FFFFFF; border: none !important; border-radius: 20px; 
        padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 15px;
    }

    /* Botones Variedad */
    .stButton > button { border-radius: 12px; font-weight: 700; }
    .btn-variedad > button { background-color: #F1F1F1; border: 1px solid #DDD; color: #555; }
    .btn-variedad-active > button { 
        background-color: #E63946 !important; color: white !important; border: none;
        box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
    }

    /* Caja de Ingredientes Dinámica */
    .ingredientes-box { 
        background-color: #FFF9E6; padding: 15px; border-radius: 15px; 
        border-left: 6px solid #FFB703; font-size: 15px; margin: 15px 0; color: #333; 
    }
    .intro-texto { font-weight: 800; color: #E63946; margin-bottom: 5px; display: block; }

    /* Precio */
    .precio-tag { color: #E63946; font-size: 32px; font-weight: 900; }

    /* Selector de Cantidad */
    .qty-container { 
        background-color: #F1F1F1; border-radius: 50px; padding: 5px; 
        display: flex; align-items: center; justify-content: center; gap: 15px;
        width: 150px; margin: 10px auto;
    }
    .qty-btn > button { 
        width: 35px !important; height: 35px !important; border-radius: 50% !important; 
        background-color: #FFFFFF !important; color: #E63946 !important; border: 1px solid #DDD !important;
    }
    .qty-val { font-size: 20px; font-weight: 800; }
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
                        # Lógica de Datos
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        c_img = imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/400x300?text=Caniche+Food"

                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("🥤 **Seleccioná una variedad:**")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if pos == vi else "btn-variedad"
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)

                            # --- MOSTRAR DESCRIPCIÓN CON FRASE INTRODUCTORIA ---
                            if not has_v or pos is not None:
                                p_idx = pos if pos is not None else 0
                                d_ing = ings[p_idx] if p_idx < len(ings) else ""
                                try:
                                    raw_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    d_pre = float("".join(filter(str.isdigit, str(raw_p))))
                                except: d_pre = 0.0

                                if d_ing:
                                    st.markdown(f"""
                                        <div class="ingredientes-box">
                                            <span class="intro-texto">Esta variedad trae:</span>
                                            {d_ing}
                                        </div>
                                    """, unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- SELECTOR CANTIDAD ---
                        c_nom = ops[pos] if pos is not None and has_v else ""
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        
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
                                cant = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                st.markdown(f'<div class="qty-val">{cant}</div>', unsafe_allow_html=True)
                            with c3:
                                if st.button("+", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': d_pre, 'cant': 1}
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

# --- CARRITO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Tu Pedido")
    total = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
    for k, v in st.session_state['carrito'].items():
        st.write(f"✅ **{v['cant']}x** {k} — ${v['precio']*v['cant']:,.0f}")
    
    nom = st.text_input("Tu nombre:")
    ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
    try: envio = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "0"))))) if ent == "Delivery" else 0
    except: envio = 0
    
    st.success(f"### TOTAL: ${total + envio:,.0f}")
    if st.button("🚀 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
        if nom:
            resumen = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n{resumen}\n💰 *TOTAL: ${total + envio:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)

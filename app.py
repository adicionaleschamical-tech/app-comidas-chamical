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

# --- ESTILO VISUAL: FAST FOOD VIBRANTE (Rojo, Blanco y Amarillo) ---
st.markdown("""
    <style>
    /* Fondo y Base */
    .stApp { background-color: #F8F9FA; color: #333; }
    
    /* Tarjeta de Producto */
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FFFFFF; 
        border: None !important; 
        border-radius: 25px; 
        padding: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        margin-bottom: 15px;
    }

    /* Botones de Variedad (Estilo Fast Food) */
    .stButton > button { border-radius: 15px; font-weight: 700; transition: 0.2s; text-transform: uppercase; }
    
    .btn-variedad > button { 
        height: 40px; font-size: 12px; 
        background-color: #FFFFFF; 
        border: 2px solid #E0E0E0; 
        color: #555; 
    }
    
    .btn-variedad-active > button { 
        background-color: #E63946 !important; /* Rojo Fast Food */
        color: #FFFFFF !important; 
        border: 2px solid #E63946;
        box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
    }

    /* Caja de Ingredientes (Solo si hay selección) */
    .ingredientes-box { 
        background-color: #FFF9E6; /* Amarillo muy suave */
        padding: 15px; 
        border-radius: 15px; 
        border-left: 6px solid #FFB703; /* Amarillo Mostaza */
        font-size: 14px; 
        margin: 15px 0; 
        color: #444; 
        line-height: 1.5;
    }

    /* Precio */
    .precio-tag { color: #E63946; font-size: 32px; font-weight: 900; margin: 5px 0; font-family: 'Arial Black', sans-serif; }

    /* Selector de Cantidad */
    .qty-container { 
        background-color: #F1F1F1; 
        border-radius: 50px; 
        padding: 6px 12px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 20px;
        width: 150px; 
        margin: 10px auto;
    }
    .qty-btn > button { 
        width: 40px !important; height: 40px !important; 
        border-radius: 50% !important; background-color: #FFFFFF !important; 
        border: 1px solid #DDD !important; color: #E63946 !important; 
        font-size: 22px !important;
    }
    .qty-val { font-size: 22px; font-weight: 800; color: #333; }

    /* Imágenes */
    .stImage > img { border-radius: 20px; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #EEE; border-radius: 10px 10px 0 0; padding: 10px 20px; color: #777; 
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #E63946; }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        t = int(time.time())
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = dict(zip(df_c.iloc[:,0].astype(str).str.strip(), df_c.iloc[:,1].astype(str).str.strip()))
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [limpiar_col(c) for c in df_p.columns]
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- HEADER ---
st.markdown(f"<h1 style='text-align: center; color: #E63946;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #666;'>📍 {conf.get('Direccion Local', 'Chamical')} | 📞 {conf.get('Telefono')}</p>", unsafe_allow_html=True)

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
                        # --- PROCESO ---
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Imagen (siempre visible la principal)
                        c_img = imgs[pos] if pos is not None and pos < len(imgs) and str(imgs[pos]).startswith('http') else (imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/400x300?text=Caniche+Food")

                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            
                            if has_v:
                                st.write("🥤 **Elegí tu combo:**")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if pos == vi else "btn-variedad"
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi; st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)

                            # --- OCULTAMIENTO TOTAL (SOLUCIÓN) ---
                            # Solo entra aquí si el producto no tiene variedades O si ya se seleccionó una.
                            if not has_v or pos is not None:
                                p_idx = pos if pos is not None else 0
                                d_ing = ings[p_idx] if p_idx < len(ings) else ""
                                try:
                                    raw_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    d_pre = float("".join(filter(str.isdigit, str(raw_p))))
                                except: d_pre = 0.0

                                if d_ing:
                                    st.markdown(f'<div class="ingredientes-box">📖 {d_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- SELECTOR DE CANTIDAD ---
                        c_nom = ops[pos] if pos is not None and has_v else ""
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        bloqueado = has_v and pos is None
                        
                        if not bloqueado:
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
                                cant = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                st.markdown(f'<div class="qty-val">{cant}</div>', unsafe_allow_html=True)
                            with c_btn_p:
                                st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                                if st.button("+", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': d_pre, 'cant': 1}
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

# --- CARRITO ---
if st.session_state['carrito']:
    st.divider()
    st.markdown("<h2 style='color: #E63946;'>🛒 Tu Pedido</h2>", unsafe_allow_html=True)
    total = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
    for k, v in st.session_state['carrito'].items():
        st.write(f"✅ **{v['cant']}x** {k} — ${v['precio']*v['cant']:,.0f}")
    
    nom = st.text_input("Tu nombre para el pedido:")
    ent = st.radio("Forma de entrega:", ["Retiro en Local", "Delivery"])
    envio = int(conf.get("Costo Delivery", 500)) if ent == "Delivery" else 0
    
    st.markdown(f"<h3 style='color: #E63946;'>TOTAL: ${total + envio:,.0f}</h3>", unsafe_allow_html=True)
    if st.button("🔥 CONFIRMAR PEDIDO POR WHATSAPP", use_container_width=True):
        if nom:
            resumen = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n{resumen}\n💰 *TOTAL: ${total + envio:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)

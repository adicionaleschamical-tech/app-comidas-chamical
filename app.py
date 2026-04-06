import streamlit as st
import pandas as pd
import urllib.parse
import time
import unicodedata

# --- CONFIGURACIÓN DE FUENTES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

def limpiar_col(txt):
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return txt.capitalize()

# --- NUEVO ESTILO CSS "DARK GOURMET" ---
st.markdown("""
    <style>
    /* Fondo y Texto General */
    .stApp { background-color: #121212; color: #E0E0E0; }
    h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-family: 'Playfair Display', serif; }
    .stCaption { color: #AAAAAA !important; }

    /* Contenedor de Producto */
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #1E1E1E; 
        border: 1px solid #333333 !important; 
        border-radius: 15px; 
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }

    /* Botones de Variedad (Pills Dorados) */
    .stButton > button { border-radius: 25px; transition: 0.3s; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    
    .btn-variedad > button { 
        height: 35px; font-size: 11px; 
        background-color: transparent; 
        border: 2px solid #C4A77D; 
        color: #C4A77D; 
    }
    .btn-variedad > button:hover { background-color: rgba(196, 167, 125, 0.1); border-color: #C4A77D; color: #C4A77D; }
    
    .btn-variedad-active > button { 
        background-color: #C4A77D !important; 
        color: #121212 !important; 
        border: 2px solid #C4A77D;
        box-shadow: 0 0 15px rgba(196, 167, 125, 0.5);
    }

    /* Caja de Ingredientes Dinámica */
    .ingredientes-box { 
        background-color: #252525; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 4px solid #C4A77D; 
        font-size: 14px; 
        margin: 15px 0; 
        color: #CCCCCC; 
        line-height: 1.5;
        font-style: italic;
    }

    /* Precio */
    .precio-tag { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 10px 0; font-family: 'Oswald', sans-serif; }

    /* Selector de Cantidad (Minimalista) */
    .qty-container { 
        background-color: #252525; 
        border-radius: 30px; 
        padding: 5px; 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        border: 1px solid #333333; 
        width: 130px; 
        margin: 15px auto 0 auto; 
    }
    .qty-btn > button { 
        width: 35px !important; height: 35px !important; 
        border-radius: 50% !important; padding: 0 !important; 
        font-size: 20px !important; background-color: #1E1E1E !important; 
        border: 1px solid #333333 !important; color: #C4A77D !important; 
    }
    .qty-btn > button:hover { background-color: #C4A77D !important; color: #121212 !important; border-color: #C4A77D !important; }
    .qty-val { font-size: 18px; font-weight: 700; color: #FFFFFF; width: 30px; text-align: center; }

    /* Imágenes */
    .stImage > img { border-radius: 12px; filter: brightness(0.9); }

    /* Tabs (Categorías) */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 1px solid #333333; }
    .stTabs [data-baseweb="tab"] { color: #AAAAAA; font-weight: 600; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #C4A77D; }
    .stTabs [data-baseweb="tab"]:hover { color: #FFFFFF; }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Playfair+Display:ital,wght@0,600;1,400&display=swap" rel="stylesheet">
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
        df_p.columns = [limpiar_col(c) for c in df_p.columns]
        if 'Categoria' not in df_p.columns: df_p['Categoria'] = 'General'
        return df_p, conf
    except: return pd.DataFrame(), {}

df_prod, conf = cargar_datos()

# --- LOGO Y TÍTULO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo: st.image("https://via.placeholder.com/150/121212/C4A77D?text=CF", width=80)
with col_titulo:
    st.title("Caniche Food")
    st.caption(f"📍 Chamical, La Rioja | 📞 {conf.get('Telefono')}")

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
                        # --- DATOS ---
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Imagen inicial o seleccionada
                        c_img = imgs[pos] if pos is not None and pos < len(imgs) and str(imgs[pos]).startswith('http') else (imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/300x200?text=Caniche+Food")

                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            if has_v:
                                st.write("👇 *Seleccioná una opción para ver detalle y precio:*")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        est = "btn-variedad-active" if st.session_state['sel_v'][idx] == vi else "btn-variedad"
                                        st.markdown(f'<div class="{est}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi; st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            
                            # --- LÓGICA DE OCULTAMIENTO TOTAL ---
                            # Solo mostramos ingredientes y precio si hay selección o si el producto no tiene variedades
                            if pos is not None or not has_v:
                                p_idx = pos if pos is not None else 0
                                
                                # Obtenemos ingredientes de la posición seleccionada
                                c_ing = ings[p_idx] if p_idx < len(ings) else ""
                                
                                # Obtenemos precio de la posición seleccionada
                                try:
                                    val_p = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    c_pre = float("".join(filter(str.isdigit, str(val_p))))
                                except: c_pre = 0.0
                                
                                # Renderizado dinámico: Si no hay selección, este bloque NO se ejecuta
                                if c_ing: st.markdown(f'<div class="ingredientes-box">📝 {c_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${c_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- SELECTOR DE CANTIDAD (Minimalista) ---
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
                                cant_actual = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                st.markdown(f'<div class="qty-val">{cant_actual}</div>', unsafe_allow_html=True)
                            
                            with c_btn_p:
                                st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                                if st.button("+", key=f"a_{idx}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': c_pre, 'cant': 1}
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

# --- RESUMEN DE COMPRA (Estilo Elegante) ---
if st.session_state['carrito']:
    st.markdown("---")
    st.header("🛒 Tu Pedido")
    total_p = sum(v['precio'] * v['cant'] for v in st.session_state['carrito'].values())
    for k, v in st.session_state['carrito'].items():
        st.write(f"**{v['cant']}x** {k} — <span style='color:#C4A77D;'>${v['precio']*v['cant']:,.0f}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    nom = st.text_input("Contanos tu nombre:")
    ent = st.radio("¿Cómo lo recibís?", ["Delivery", "Retiro en Local"])
    costo_env = int(conf.get("Costo Delivery", 500)) if ent == "Delivery" else 0
    
    st.success(f"### TOTAL A PAGAR: ${total_p + costo_env:,.0f}")
    
    if st.button("📲 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
        if nom:
            res = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n------------------\n{res}\n------------------\n💰 *TOTAL: ${total_p + costo_env:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)
        else: st.error("Por favor, ingresá tu nombre para procesar el pedido.")

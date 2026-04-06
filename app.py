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

# --- ESTILO VISUAL: MINIMALISTA LIGHT (Limpio y Profesional) ---
st.markdown("""
    <style>
    /* Fondo Claro y Tipografía */
    .stApp { background-color: #FFFFFF; color: #2D3436; }
    h1, h2, h3 { color: #2D3436 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Tarjeta de Producto */
    div[data-testid="stVerticalBlock"] > div[style*="border"] { 
        background-color: #FDFDFD; 
        border: 1px solid #EAEAEA !important; 
        border-radius: 20px; 
        padding: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Botones de Variedad (Estilo Pill) */
    .stButton > button { border-radius: 12px; transition: 0.2s; font-weight: 500; }
    
    .btn-variedad > button { 
        height: 38px; font-size: 13px; 
        background-color: #F1F2F6; 
        border: 1px solid #EAEAEA; 
        color: #2D3436; 
    }
    
    .btn-variedad-active > button { 
        background-color: #FF4757 !important; 
        color: #FFFFFF !important; 
        border: none;
        box-shadow: 0 4px 10px rgba(255, 71, 87, 0.3);
    }

    /* Caja de Ingredientes (Solo visible al seleccionar) */
    .ingredientes-box { 
        background-color: #F9FAFB; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #EDEDED; 
        font-size: 14px; 
        margin: 15px 0; 
        color: #636E72; 
        line-height: 1.6;
    }

    /* Precio Destacado */
    .precio-tag { color: #2D3436; font-size: 30px; font-weight: 700; margin: 10px 0; }

    /* Selector de Cantidad Compacto */
    .qty-container { 
        background-color: #F1F2F6; 
        border-radius: 15px; 
        padding: 8px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 15px;
        width: 140px; 
        margin: 10px auto;
    }
    .qty-btn > button { 
        width: 35px !important; height: 35px !important; 
        border-radius: 10px !important; background-color: #FFFFFF !important; 
        border: 1px solid #EAEAEA !important; color: #FF4757 !important; 
        font-size: 20px !important; font-weight: bold !important;
    }
    .qty-val { font-size: 20px; font-weight: 700; color: #2D3436; min-width: 25px; text-align: center; }

    /* Imágenes con bordes suaves */
    .stImage > img { border-radius: 15px; object-fit: cover; }
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
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical')} | 📱 {conf.get('Telefono')}")

if not df_prod.empty:
    # Filtrar solo disponibles
    df_ver = df_prod[df_prod['Disponible'].astype(str).str.upper().str.strip() == "SI"] if 'Disponible' in df_prod.columns else df_prod
    
    cats = [str(c) for c in df_ver['Categoria'].unique() if pd.notna(c)]
    
    if cats:
        tabs = st.tabs(cats)
        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_ver[df_ver['Categoria'] == cat]
                for idx, row in items.iterrows():
                    with st.container(border=True):
                        # --- PROCESAMIENTO DE DATOS ---
                        has_v = 'Variedades' in row and pd.notna(row['Variedades'])
                        
                        # IMPORTANTE: Aseguramos que empiece en None
                        if idx not in st.session_state['sel_v']: 
                            st.session_state['sel_v'][idx] = None
                        
                        pos = st.session_state['sel_v'][idx]
                        
                        ops = [o.strip() for o in str(row['Variedades']).split(',')] if has_v else []
                        ings = [ig.strip() for ig in str(row.get('Ingredientes', '')).split(';')]
                        pres = [p.strip() for p in str(row.get('Precio', '0')).split(';')]
                        imgs = [im.strip() for im in str(row.get('Imagen', '')).split(';')]

                        # Imagen: Siempre mostramos la primera por defecto
                        c_img = imgs[pos] if pos is not None and pos < len(imgs) and str(imgs[pos]).startswith('http') else (imgs[0] if imgs and str(imgs[0]).startswith('http') else "https://via.placeholder.com/400x300?text=Caniche+Food")

                        col_img, col_info = st.columns([1.2, 2])
                        with col_img: st.image(c_img, use_container_width=True)
                        with col_info:
                            st.subheader(row['Producto'])
                            
                            if has_v:
                                st.write("👇 **Elegí una opción:**")
                                cvs = st.columns(len(ops))
                                for vi, vn in enumerate(ops):
                                    with cvs[vi]:
                                        estilo = "btn-variedad-active" if pos == vi else "btn-variedad"
                                        st.markdown(f'<div class="{estilo}">', unsafe_allow_html=True)
                                        if st.button(vn, key=f"v_{idx}_{vi}"):
                                            st.session_state['sel_v'][idx] = vi
                                            st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)

                            # --- LÓGICA DE OCULTAMIENTO ESTRICTO ---
                            # Si tiene variedades y NO se eligió ninguna (pos es None), no se muestra NADA abajo.
                            if not has_v or pos is not None:
                                p_idx = pos if pos is not None else 0
                                
                                # Extraer ingrediente y precio específico
                                d_ing = ings[p_idx] if p_idx < len(ings) else ""
                                try:
                                    d_pre_raw = pres[p_idx] if p_idx < len(pres) else pres[0]
                                    d_pre = float("".join(filter(str.isdigit, str(d_pre_raw))))
                                except: d_pre = 0.0

                                # Renderizado
                                if d_ing:
                                    st.markdown(f'<div class="ingredientes-box">📝 {d_ing}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="precio-tag">${d_pre:,.0f}</div>', unsafe_allow_html=True)

                        # --- SELECTOR DE CANTIDAD ---
                        c_nom = ops[pos] if pos is not None and has_v else ""
                        p_id = f"{row['Producto']} ({c_nom})" if c_nom else row['Producto']
                        
                        # Bloquear si no hay selección
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

# --- CARRITO Y ENVÍO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Tu Pedido")
    total = 0
    for k, v in st.session_state['carrito'].items():
        subtotal = v['precio'] * v['cant']
        total += subtotal
        st.write(f"**{v['cant']}x** {k} — ${subtotal:,.0f}")
    
    nom = st.text_input("Tu nombre:")
    ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
    costo_env = int(conf.get("Costo Delivery", 500)) if ent == "Delivery" else 0
    
    st.success(f"### TOTAL: ${total + costo_env:,.0f}")
    if st.button("🚀 ENVIAR POR WHATSAPP", use_container_width=True):
        if nom:
            resumen = "\n".join([f"- {v['cant']}x {k} (${v['precio']*v['cant']:,.0f})" for k,v in st.session_state['carrito'].items()])
            msg = f"🍔 *PEDIDO CANICHE FOOD*\n👤 *Cliente:* {nom}\n📍 *Entrega:* {ent}\n{resumen}\n💰 *TOTAL: ${total + costo_env:,.0f}*"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/{conf.get("Telefono")}?text={urllib.parse.quote(msg)}">', unsafe_allow_html=True)

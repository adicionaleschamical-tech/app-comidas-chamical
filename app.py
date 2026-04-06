import streamlit as st
import pandas as pd
import time
import requests
import urllib.parse

# --- CONFIGURACIÓN DE CONEXIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- DISEÑO (Imágenes compactas + Botones de Variedad) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { 
        border: 1px solid #EEE; padding: 12px; border-radius: 15px; 
        margin-bottom: 15px; background-color: #FDFDFD !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    .stImage > img { border-radius: 12px; max-height: 180px; object-fit: cover; }
    .btn-active > button { background-color: #E63946 !important; color: white !important; border: none !important; }
    .btn-inactive > button { background-color: #F0F2F6 !important; color: #333 !important; border: 1px solid #DDD !important; }
    .precio-tag { color: #E63946 !important; font-size: 26px !important; font-weight: 900 !important; margin: 0; }
    .ing-box { background: #FFF9C4; padding: 8px; border-radius: 8px; font-size: 14px; margin: 8px 0; border-left: 4px solid #FBC02D; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf_dict = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, df_c, conf_dict
    except: return pd.DataFrame(), pd.DataFrame(), {}

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {} # Guarda el índice seleccionado

df_prod, df_conf_raw, conf = cargar_datos()

# --- DATOS DINÁMICOS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "5493826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛠️ Acceso")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingresar"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Login"):
                if u == conf.get("Admin_DNI", "30588807") and p == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User", "usuario") and p == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
    else:
        st.info(f"Sesión: {st.session_state['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("Panel de Control")
    t1, t2 = st.tabs(["🍔 Menú", "⚙️ Configuración"])

    with t1:
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True)
        else:
            cols = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            st.data_editor(df_prod[cols], use_container_width=True)

    with t2:
        st.subheader("Personalización del Comprador")
        # LISTA BLANCA EXPLÍCITA
        campos_visibles = ["Nombre Negocio", "Alias", "Telefono", "Costo Delivery"]
        
        if st.session_state['rol'] == 'usuario':
            # Solo permitimos que el usuario vea y edite estos 4 campos
            df_usuario = df_conf_raw[df_conf_raw.iloc[:, 0].isin(campos_visibles)]
            st.write("Modificá el Alias y datos de contacto aquí:")
            st.data_editor(df_usuario, use_container_width=True, key="editor_comprador")
        else:
            st.data_editor(df_conf_raw, use_container_width=True)

# --- VISTA CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        categorias = df_ver['CATEGORIA'].unique()
        tabs = st.tabs(list(categorias))

        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_ver[df_ver['CATEGORIA'] == cat]
                for idx, row in items.iterrows():
                    st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                    c_img, c_txt = st.columns([1, 1.2])
                    
                    with c_img:
                        img = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200"
                        st.image(img)

                    with c_txt:
                        st.markdown(f"### {row['PRODUCTO']}")
                        
                        # BOTONES DE VARIEDAD (VUELVEN)
                        tiene_v = pd.notna(row['VARIEDADES'])
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                        
                        if tiene_v:
                            ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                            c_btns = st.columns(len(ops))
                            for vi, vn in enumerate(ops):
                                with c_btns[vi]:
                                    activo = st.session_state['sel_v'][idx] == vi
                                    estilo = "btn-active" if activo else "btn-inactive"
                                    st.markdown(f'<div class="{estilo}">', unsafe_allow_html=True)
                                    if st.button(vn, key=f"v_{idx}_{vi}", use_container_width=True):
                                        st.session_state['sel_v'][idx] = vi
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)

                        # Info según selección
                        p_idx = st.session_state['sel_v'][idx]
                        if pd.notna(row['INGREDIENTES']):
                            ings = str(row['INGREDIENTES']).split(';')
                            txt_ing = ings[p_idx] if p_idx < len(ings) else ings[0]
                            st.markdown(f'<div class="ing-box">{txt_ing}</div>', unsafe_allow_html=True)

                        precios = str(row['PRECIO']).split(';')
                        p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                        p_f = float("".join(filter(str.isdigit, p_raw)))
                        
                        col_pre, col_add = st.columns([1, 1])
                        with col_pre:
                            st.markdown(f'<p class="precio-tag">${p_f:,.0f}</p>', unsafe_allow_html=True)
                        with col_add:
                            if st.button("Añadir ➕", key=f"add_{idx}"):
                                p_nom = f"{row['PRODUCTO']} ({ops[p_idx]})" if tiene_v else row['PRODUCTO']
                                if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                                else: st.session_state['carrito'][p_nom] = {'precio': p_f, 'cant': 1}
                                st.toast(f"Agregado: {p_nom}")
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- CARRITO ---
    if st.session_state['carrito']:
        with st.container(border=True):
            st.markdown("### 🛒 Tu Pedido")
            total = 0
            resumen = ""
            for item, d in list(st.session_state['carrito'].items()):
                sub = d['precio'] * d['cant']
                total += sub
                st.write(f"**{d['cant']}x** {item} — ${sub:,.0f}")
                resumen += f"• {d['cant']}x {item}\n"
            
            st.divider()
            nom_cli = st.text_input("Nombre:")
            envio_tipo = st.radio("Entrega:", ["Retiro", "Delivery"], horizontal=True)
            costo_env = int(costo_d) if envio_tipo == "Delivery" else 0
            
            st.markdown(f"## TOTAL: ${total + costo_env:,.0f}")
            st.info(f"💳 Alias de pago: **{alias_n}**")

            if st.button("🚀 ENVIAR POR WHATSAPP", use_container_width=True):
                if nom_cli:
                    txt = urllib.parse.quote(f"🔔 *NUEVO PEDIDO*\n👤 {nom_cli}\n🛵 {envio_tipo}\n---\n{resumen}\n💰 *TOTAL: ${total + costo_env:,.0f}*")
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/{tel_n}?text={txt}\'">', unsafe_allow_html=True)

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

# --- DISEÑO MEJORADO (Imágenes controladas y botones compactos) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { 
        border: 1px solid #DDD; padding: 10px; border-radius: 12px; 
        margin-bottom: 15px; background-color: #FDFFDF !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    /* Control de tamaño de imagen */
    .stImage > img { 
        border-radius: 10px; 
        max-height: 200px; 
        object-fit: cover; 
    }
    .btn-active > button { background-color: #E63946 !important; color: white !important; font-weight: bold !important; }
    .ingredientes-vivos { 
        background-color: #FFF9C4 !important; color: #000; padding: 8px; 
        border-radius: 8px; border-left: 5px solid #FBC02D !important; font-size: 14px;
    }
    .precio-vete { color: #E63946 !important; font-size: 24px !important; font-weight: 800 !important; }
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

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=8)
    except: pass

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, df_conf_raw, conf = cargar_datos()

# --- DATOS DINÁMICOS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "5493826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.header("⚙️ Staff")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingreso"):
            u = st.text_input("Usuario/DNI")
            p = st.text_input("Clave", type="password")
            if st.button("Entrar"):
                if u == conf.get("Admin_DNI", "30588807") and p == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User", "usuario") and p == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
    else:
        st.write(f"Rol: **{st.session_state['rol'].upper()}**")
        if st.button("Salir"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- PANEL DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("🛠️ Personalización")
    t1, t2 = st.tabs(["🍔 Menú", "⚙️ Mi Negocio"])

    with t1:
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True)
        else:
            cols = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            st.data_editor(df_prod[cols], use_container_width=True)

    with t2:
        st.subheader("Datos de tu Local")
        if st.session_state['rol'] == 'usuario':
            # LISTA BLANCA: Solo lo que el comprador PUEDE ver y editar
            permitidos = ["Nombre Negocio", "Alias", "Telefono", "Costo Delivery"]
            df_compra = df_conf_raw[df_conf_raw.iloc[:, 0].isin(permitidos)]
            st.info("Editá estos campos para personalizar la App a tu medida:")
            st.data_editor(df_compra, use_container_width=True, key="ed_comprador")
        else:
            # Vos ves todo
            st.warning("VISTA DESARROLLADOR")
            st.data_editor(df_conf_raw, use_container_width=True)

# --- VISTA CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        tabs = st.tabs(list(df_ver['CATEGORIA'].unique()))

        for i, cat in enumerate(df_ver['CATEGORIA'].unique()):
            with tabs[i]:
                items = df_ver[df_ver['CATEGORIA'] == cat]
                for idx, row in items.iterrows():
                    with st.container():
                        st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                        col_img, col_txt = st.columns([1, 1.5])
                        
                        with col_img:
                            img = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200"
                            st.image(img)
                        
                        with col_txt:
                            st.markdown(f"### {row['PRODUCTO']}")
                            tiene_v = pd.notna(row['VARIEDADES'])
                            if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                            
                            if tiene_v:
                                ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                                sel = st.selectbox("Variedad:", ops, key=f"sel_{idx}")
                                p_idx = ops.index(sel)
                                st.session_state['sel_v'][idx] = p_idx
                            else:
                                p_idx = 0

                        # Info inferior
                        p_idx = st.session_state['sel_v'][idx]
                        if pd.notna(row['INGREDIENTES']):
                            ings = str(row['INGREDIENTES']).split(';')[p_idx]
                            st.markdown(f'<div class="ingredientes-vivos">{ings}</div>', unsafe_allow_html=True)

                        precios = str(row['PRECIO']).split(';')
                        p_f = float("".join(filter(str.isdigit, precios[p_idx] if p_idx < len(precios) else precios[0])))
                        
                        c_p, c_b = st.columns([1, 1])
                        with c_p:
                            st.markdown(f'<p class="precio-vete">${p_f:,.0f}</p>', unsafe_allow_html=True)
                        with c_b:
                            if st.button("Añadir ➕", key=f"add_{idx}"):
                                p_nom = f"{row['PRODUCTO']} ({ops[p_idx]})" if tiene_v else row['PRODUCTO']
                                if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                                else: st.session_state['carrito'][p_nom] = {'precio': p_f, 'cant': 1}
                                st.toast(f"Añadido: {p_nom}")
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- CARRITO ---
    if st.session_state['carrito']:
        with st.expander("🛒 Ver mi Pedido", expanded=True):
            total = 0
            resumen = ""
            for item, d in list(st.session_state['carrito'].items()):
                sub = d['precio'] * d['cant']
                total += sub
                st.write(f"**{d['cant']}x** {item} (${sub:,.0f})")
                resumen += f"• {d['cant']}x {item}\n"
                if st.button("Quitar", key=f"del_{item}"):
                    del st.session_state['carrito'][item]
                    st.rerun()
            
            st.divider()
            nombre_c = st.text_input("Tu Nombre:")
            entrega = st.radio("Envío:", ["Retiro", "Delivery"], horizontal=True)
            envio_p = int(costo_d) if entrega == "Delivery" else 0
            
            st.markdown(f"### Total: ${total + envio_p:,.0f}")
            st.caption(f"💳 Alias: {alias_n}")

            if st.button("✅ PEDIR POR WHATSAPP", use_container_width=True):
                if nombre_c:
                    txt = urllib.parse.quote(f"🔔 *PEDIDO - {nombre_n}*\n👤 {nombre_c}\n🛵 {entrega}\n---\n{resumen}\n💰 *TOTAL: ${total + envio_p:,.0f}*")
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/{tel_n}?text={txt}\'">', unsafe_allow_html=True)

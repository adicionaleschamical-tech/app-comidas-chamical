import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Gestión Caniche Food", page_icon="🍟", layout="centered")

# --- DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { border: 2px solid #EEE; padding: 15px; border-radius: 15px; margin-bottom: 20px; background-color: #F9F9F9 !important; }
    .btn-active > button { background-color: #E63946 !important; color: white !important; }
    .precio-vete { color: #E63946 !important; font-size: 32px !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, conf
    except: return pd.DataFrame(), {}

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok")
    except: return False

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, conf = cargar_datos()
# Estos valores ahora son dinámicos según lo que diga el Sheet
nombre_negocio = conf.get("Nombre Negocio", "Caniche Food")
tel_negocio = conf.get("Telefono", "No definido")
costo_envio = conf.get("Costo Delivery", "0")

# --- BARRA LATERAL (LOGIN) ---
with st.sidebar:
    st.header("⚙️ Acceso Staff")
    rol_actual = st.session_state.get('rol', 'cliente')
    
    if rol_actual == 'cliente':
        with st.expander("Ingresar"):
            u_in = st.text_input("Usuario / DNI:", key="u_log")
            p_in = st.text_input("Clave:", type="password", key="p_log")
            if st.button("Entrar"):
                if u_in == "30588807" and p_in == "124578":
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u_in == "usuario" and p_in == "usuario123":
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Datos incorrectos")
    else:
        st.info(f"Sesión: {str(rol_actual).upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title(f"🛠️ Panel de Gestión")
    
    # Pestañas para organizar la edición
    tab_productos, tab_negocio = st.tabs(["🍔 Productos", "⚙️ Datos del Negocio"])

    with tab_productos:
        st.subheader("Modificar Menú")
        # Columnas que el comprador/usuario podrá tocar libremente
        cols_edit = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
        
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True, key="ed_full")
        else:
            st.data_editor(df_prod[cols_edit], use_container_width=True, key="ed_user")

    with tab_negocio:
        st.subheader("Personalización de la Marca")
        st.write("Cualquier cambio aquí se reflejará automáticamente en la vista del cliente.")
        
        # Creamos un editor para los parámetros de configuración
        df_conf = pd.DataFrame(list(conf.items()), columns=["Parámetro", "Valor"])
        # Ambos roles pueden editar esto para que el comprador ajuste su local
        st.data_editor(df_conf, use_container_width=True, key="ed_conf")
        
        st.info(f"📱 Teléfono actual: {tel_negocio} | 🛵 Delivery: ${costo_envio}")

# --- VISTA CLIENTE ---
else:
    st.markdown(f"<h1 style='text-align: center; color: #E63946 !important;'>🍟 {nombre_negocio}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        categorias = df_ver['CATEGORIA'].unique()
        tabs = st.tabs(list(categorias))

        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_ver[df_ver['CATEGORIA'] == cat]
                for idx, row in items.iterrows():
                    st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                    img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200"
                    st.image(img, width=220)
                    st.markdown(f"## {row['PRODUCTO']}")
                    
                    tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                    if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                    
                    if tiene_v:
                        ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
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
                            ings = str(row['INGREDIENTES']).split(';')
                            det = ings[p_idx] if p_idx < len(ings) else ings[0]
                            st.markdown(f'<div class="ingredientes-vivos"><b>Trae:</b><br>{det}</div>', unsafe_allow_html=True)

                        nota = st.text_input("📝 ¿Algún cambio?", key=f"n_{idx}")
                        precios = str(row['PRECIO']).split(';')
                        try:
                            p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                            precio_f = float("".join(filter(str.isdigit, p_raw)))
                        except: precio_f = 0
                        
                        st.markdown(f'<p class="precio-vete">${precio_f:,.0f}</p>', unsafe_allow_html=True)

                        p_nom = f"{row['PRODUCTO']} ({ops[pos]})" if tiene_v else row['PRODUCTO']
                        p_id = f"{p_nom} [{nota}]" if nota else p_nom
                        
                        c1, c2, c3 = st.columns([1,1,1])
                        with c1:
                            if st.button("➖", key=f"m_{idx}"):
                                if p_id in st.session_state['carrito']:
                                    st.session_state['carrito'][p_id]['cant'] -= 1
                                    if st.session_state['carrito'][p_id]['cant'] <= 0: del st.session_state['carrito'][p_id]
                                    st.rerun()
                        with c2:
                            cant = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                            st.markdown(f"<h2 style='text-align:center;'>{cant}</h2>", unsafe_allow_html=True)
                        with c3:
                            if st.button("➕", key=f"p_{idx}"):
                                if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                else: st.session_state['carrito'][p_id] = {'precio': precio_f, 'cant': 1}
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- FINALIZAR COMPRA ---
    if st.session_state['carrito']:
        st.divider()
        st.markdown("## 🛒 Tu Pedido")
        total_acum = 0
        resumen = ""
        for item, d in st.session_state['carrito'].items():
            sub = d['precio'] * d['cant']
            total_acum += sub
            st.write(f"✅ **{d['cant']}x** {item} (${sub:,.0f})")
            resumen += f"• {d['cant']}x {item} (${sub:,.0f})\n"

        with st.container(border=True):
            nombre = st.text_input("👤 Tu Nombre:")
            entrega = st.radio("🛵 Entrega:", ["Retiro en Local", "Delivery"], horizontal=True)
            envio = 0
            if entrega == "Delivery":
                st.text_area("🏠 Dirección:")
                try: envio = int("".join(filter(str.isdigit, str(costo_envio))))
                except: envio = 0
            
            total_f = total_acum + envio
            st.markdown(f"<h1 style='text-align:center; background:#E63946; color:white; border-radius:15px;'>TOTAL: ${total_f:,.0f}</h1>", unsafe_allow_html=True)

            if st.button("🚀 ENVIAR PEDIDO", use_container_width=True):
                if nombre:
                    msg = f"🔔 *NUEVO PEDIDO - {nombre_negocio}*\n👤 {nombre}\n🛵 {entrega}\n------------------\n{resumen}------------------\n💰 *TOTAL: ${total_f:,.0f}*"
                    if enviar_telegram(msg):
                        st.success("¡Pedido enviado!")
                        st.session_state['carrito'] = {}
                        st.balloons()

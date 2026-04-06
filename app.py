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

st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- DISEÑO CUSTOM (Botones rojos, fondos claros) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label { color: #111111 !important; }
    .producto-caja { 
        border: 2px solid #EEE; padding: 15px; border-radius: 15px; 
        margin-bottom: 20px; background-color: #F9F9F9 !important;
    }
    .btn-active > button { background-color: #E63946 !important; color: white !important; font-weight: bold !important; }
    .ingredientes-vivos { 
        background-color: #FFF9C4 !important; color: #000; padding: 15px; 
        border-radius: 12px; border-left: 10px solid #FBC02D !important; margin-bottom: 10px;
    }
    .precio-vete { color: #E63946 !important; font-size: 32px !important; font-weight: 900 !important; margin: 0px; }
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
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok")
    except: return False

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, df_conf_raw, conf = cargar_datos()

# --- DATOS DINÁMICOS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "3826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- SIDEBAR (GESTIÓN INTERNA) ---
with st.sidebar:
    st.header("⚙️ Acceso Personal")
    rol_actual = st.session_state.get('rol', 'cliente')
    
    if rol_actual == 'cliente':
        with st.expander("Loguearse"):
            u_in = st.text_input("Usuario / DNI:", key="u_log")
            p_in = st.text_input("Clave:", type="password", key="p_log")
            if st.button("Entrar"):
                if u_in == conf.get("Admin_DNI", "30588807") and p_in == conf.get("Admin_Pass", "124578"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u_in == conf.get("User", "usuario") and p_in == conf.get("User_Pass", "usuario123"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Error de credenciales")
    else:
        st.write(f"Sesión: **{rol_actual.upper()}**")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- LÓGICA DE VISTAS ---

# 1. VISTA GESTIÓN (ADMIN Y USUARIO)
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title(f"🛠️ Panel de Gestión - {nombre_n}")
    t1, t2 = st.tabs(["🍔 Menú", "⚙️ Configuración Local"])

    with t1:
        if st.session_state['rol'] == 'admin':
            st.data_editor(df_prod, use_container_width=True, key="ed_admin_p")
        else:
            cols_u = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            st.data_editor(df_prod[cols_u], use_container_width=True, key="ed_user_p")

    with t2:
        if st.session_state['rol'] == 'usuario':
            prohibido = ["Admin_DNI", "Admin_Pass", "User_Pass"]
            mask = ~df_conf_raw.iloc[:, 0].str.contains('|'.join(prohibido), case=False, na=False)
            st.write("Editá Nombre, Alias, Teléfono y Delivery:")
            st.data_editor(df_conf_raw[mask], use_container_width=True, key="ed_conf_user")
        else:
            st.warning("VISTA MAESTRA (Cuidado con las claves)")
            st.data_editor(df_conf_raw, use_container_width=True, key="ed_conf_admin")

# 2. VISTA CLIENTE (MENÚ COMPLETO)
else:
    st.markdown(f"<h1 style='text-align: center; color: #E63946 !important;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        categorias = df_ver['CATEGORIA'].unique()
        tabs = st.tabs(list(categorias))

        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_ver[df_ver['CATEGORIA'] == cat]
                for idx, row in items.iterrows():
                    st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                    
                    # Imagen
                    img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/400x300?text=Sin+Imagen"
                    st.image(img, use_container_width=True)
                    
                    st.markdown(f"## {row['PRODUCTO']}")
                    
                    # Variedades
                    tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                    if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                    
                    if tiene_v:
                        ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                        st.write("✨ **Seleccioná una opción:**")
                        cols_btn = st.columns(len(ops))
                        for vi, vn in enumerate(ops):
                            with cols_btn[vi]:
                                is_active = st.session_state['sel_v'][idx] == vi
                                if is_active: st.markdown('<div class="btn-active">', unsafe_allow_html=True)
                                if st.button(vn, key=f"btn_{idx}_{vi}", use_container_width=True):
                                    st.session_state['sel_v'][idx] = vi
                                    st.rerun()
                                if is_active: st.markdown('</div>', unsafe_allow_html=True)

                    # Mostrar info si ya eligió variedad o si no tiene variedades
                    pos = st.session_state['sel_v'][idx]
                    if not tiene_v or pos is not None:
                        p_idx = pos if pos is not None else 0
                        
                        # Ingredientes
                        if 'INGREDIENTES' in row and pd.notna(row['INGREDIENTES']):
                            ings = str(row['INGREDIENTES']).split(';')
                            det = ings[p_idx] if p_idx < len(ings) else ings[0]
                            st.markdown(f'<div class="ingredientes-vivos"><b>Trae:</b><br>{det}</div>', unsafe_allow_html=True)

                        nota = st.text_input("📝 ¿Algún cambio?", key=f"n_{idx}", placeholder="Ej: Sin cebolla")
                        
                        # Precio
                        precios = str(row['PRECIO']).split(';')
                        try:
                            p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                            precio_f = float("".join(filter(str.isdigit, p_raw)))
                        except: precio_f = 0
                        
                        st.markdown(f'<p class="precio-vete">${precio_f:,.0f}</p>', unsafe_allow_html=True)

                        p_nom = f"{row['PRODUCTO']} ({ops[pos]})" if tiene_v else row['PRODUCTO']
                        p_id = f"{p_nom} [{nota}]" if nota else p_nom
                        
                        # Controles de cantidad
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

    # --- CARRITO DE COMPRAS ---
    if st.session_state['carrito']:
        st.divider()
        st.markdown("## 🛒 Tu Pedido")
        total_acum = 0
        resumen = ""
        for item, d in st.session_state['carrito'].items():
            sub = d['precio'] * d['cant']
            total_acum += sub
            st.write(f"✅ **{d['cant']}x** {item} — ${sub:,.0f}")
            resumen += f"• {d['cant']}x {item} (${sub:,.0f})\n"

        with st.container(border=True):
            nombre_c = st.text_input("👤 Tu Nombre:")
            entrega = st.radio("🛵 Entrega:", ["Retiro en Local", "Delivery"], horizontal=True)
            envio = 0
            dir_c = ""
            if entrega == "Delivery":
                dir_c = st.text_area("🏠 Dirección y Referencia:")
                try: envio = int("".join(filter(str.isdigit, str(costo_d))))
                except: envio = 0
            
            total_final = total_acum + envio
            st.markdown(f"<h1 style='text-align:center; background:#E63946; color:white; border-radius:15px; padding:10px;'>TOTAL: ${total_final:,.0f}</h1>", unsafe_allow_html=True)
            
            # Datos de pago dinámicos
            st.success(f"💳 Paga por transferencia al Alias: **{alias_n}**")

            if st.button("🚀 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
                if nombre_c:
                    msg = f"🔔 *PEDIDO - {nombre_n}*\n👤 Cliente: {nombre_c}\n🛵 Modo: {entrega}\n📍 Dirección: {dir_c}\n------------------\n{resumen}------------------\n💰 *TOTAL: ${total_final:,.0f}*"
                    # Opción 1: Telegram (automático)
                    enviar_telegram(msg)
                    # Opción 2: Abrir WhatsApp del local
                    import urllib.parse
                    ws_msg = urllib.parse.quote(msg)
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/{tel_n}?text={ws_msg}\'">', unsafe_allow_html=True)
                    st.success("Redirigiendo a WhatsApp...")
                else:
                    st.warning("Por favor, ingresá tu nombre.")

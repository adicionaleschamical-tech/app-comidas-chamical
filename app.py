import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import time

# --- CONFIGURACIÓN DE CONEXIÓN (Google Cloud) ---
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Extraemos la info de los secrets
        info_claves = dict(st.secrets["gcp_service_account"])
        # Corrección técnica para la llave privada (evita errores de conexión)
        info_claves["private_key"] = info_claves["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(info_claves, scopes=scope)
        cliente = gspread.authorize(creds)
        # ID de tu planilla de Google Sheets
        return cliente.open_by_key("1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA")
    except Exception as e:
        st.error(f"⚠️ Error de Credenciales: {e}")
        st.stop()

# --- INICIALIZACIÓN DE RECURSOS ---
try:
    doc = conectar_google()
    hoja_prod = doc.get_worksheet(0) # Pestaña de Productos
    hoja_conf = doc.get_worksheet(1) # Pestaña de Configuración
except Exception as e:
    st.error(f"Error al abrir las pestañas: {e}")
    st.stop()

# --- CARGA DE DATOS ---
def cargar_datos_vivos():
    # Productos
    data_p = hoja_prod.get_all_records()
    df_p = pd.DataFrame(data_p)
    df_p.columns = [c.strip().upper() for c in df_p.columns]
    
    # Configuración
    data_c = hoja_conf.get_all_records()
    df_c = pd.DataFrame(data_c)
    # Diccionario para acceso rápido: { 'Nombre Negocio': 'Caniche Food', ... }
    conf_dict = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
    
    return df_p, df_c, conf_dict

df_prod, df_conf_raw, conf = cargar_datos_vivos()

# --- DATOS DINÁMICOS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "5493826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=nombre_n, page_icon="🍟", layout="centered")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
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

# --- SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.session_state['rol'] == 'cliente':
        with st.expander("Ingresar"):
            u = st.text_input("Usuario/DNI")
            p = st.text_input("Clave", type="password")
            if st.button("Login"):
                if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User") and p == conf.get("User_Pass"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Credenciales incorrectas")
    else:
        st.write(f"Conectado como: **{st.session_state['rol'].upper()}**")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- VISTAS DE GESTIÓN ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("🛠️ Panel de Control")
    t1, t2 = st.tabs(["🍔 Productos", "⚙️ Configuración"])

    with t1:
        st.subheader("Menú de Ventas")
        if st.session_state['rol'] == 'admin':
            edit_p = st.data_editor(df_prod, use_container_width=True, key="ed_admin_p")
        else:
            cols_u = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            edit_p = st.data_editor(df_prod[cols_u], use_container_width=True, key="ed_user_p")
        
        if st.button("💾 Guardar Cambios en Menú"):
            hoja_prod.update([df_prod.columns.values.tolist()] + edit_p.values.tolist())
            st.success("¡Menú actualizado!")

    with t2:
        st.subheader("Datos del Local")
        campos_visibles = ["Nombre Negocio", "Alias", "Telefono", "Costo Delivery"]
        
        if st.session_state['rol'] == 'usuario':
            df_usuario = df_conf_raw[df_conf_raw.iloc[:, 0].isin(campos_visibles)]
            st.write("Modificá el **Alias**, Teléfono y Nombre de tu negocio:")
            edit_c = st.data_editor(df_usuario, use_container_width=True, key="ed_user_c", hide_index=True)
            
            if st.button("💾 GUARDAR MI CONFIGURACIÓN"):
                with st.spinner("Actualizando datos..."):
                    for _, fila in edit_c.iterrows():
                        param = fila.iloc[0]
                        valor = str(fila.iloc[1])
                        celda = hoja_conf.find(param)
                        hoja_conf.update_cell(celda.row, 2, valor)
                    st.success("✅ ¡Configuración guardada! Refrescá la página para ver los cambios.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
        else:
            st.warning("VISTA MAESTRA (Admin)")
            st.data_editor(df_conf_raw, use_container_width=True, key="ed_admin_c")

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
                        img_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) and row['IMAGEN'] != "" else "https://via.placeholder.com/200"
                        st.image(img_url)

                    with c_txt:
                        st.markdown(f"### {row['PRODUCTO']}")
                        
                        tiene_v = pd.notna(row['VARIEDADES']) and row['VARIEDADES'] != ""
                        if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                        
                        ops = []
                        if tiene_v:
                            ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                            c_btns = st.columns(len(ops))
                            for vi, vn in enumerate(ops):
                                with c_btns[vi]:
                                    clase = "btn-active" if st.session_state['sel_v'][idx] == vi else "btn-inactive"
                                    st.markdown(f'<div class="{clase}">', unsafe_allow_html=True)
                                    if st.button(vn, key=f"v_{idx}_{vi}", use_container_width=True):
                                        st.session_state['sel_v'][idx] = vi
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)

                        p_idx = st.session_state['sel_v'][idx]
                        if pd.notna(row['INGREDIENTES']) and row['INGREDIENTES'] != "":
                            ings = str(row['INGREDIENTES']).split(';')
                            txt_ing = ings[p_idx] if p_idx < len(ings) else ings[0]
                            st.markdown(f'<div class="ing-box">{txt_ing}</div>', unsafe_allow_html=True)

                        precios = str(row['PRECIO']).split(';')
                        p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                        p_f = float("".join(filter(str.isdigit, str(p_raw))))
                        
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

    if st.session_state['carrito']:
        with st.container(border=True):
            st.markdown("### 🛒 Tu Pedido")
            total_pedido = 0
            resumen_msg = ""
            for item, d in list(st.session_state['carrito'].items()):
                subtotal = d['precio'] * d['cant']
                total_pedido += subtotal
                st.write(f"**{d['cant']}x** {item} — ${subtotal:,.0f}")
                resumen_msg += f"• {d['cant']}x {item}\n"
            
            st.divider()
            nom_cli = st.text_input("Tu Nombre:")
            envio_tipo = st.radio("Forma de entrega:", ["Retiro en Local", "Delivery"], horizontal=True)
            costo_envio = int(costo_d) if envio_tipo == "Delivery" else 0
            
            total_final = total_pedido + costo_envio
            st.markdown(f"## TOTAL: ${total_final:,.0f}")
            st.info(f"💳 Pagá por transferencia al Alias: **{alias_n}**")

            if st.button("🚀 ENVIAR PEDIDO POR WHATSAPP", use_container_width=True):
                if nom_cli:
                    mensaje_ws = urllib.parse.quote(f"🔔 *NUEVO PEDIDO*\n👤 Cliente: {nom_cli}\n🛵 Entrega: {envio_tipo}\n---\n{resumen_msg}\n💰 *TOTAL: ${total_final:,.0f}*")
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/{tel_n}?text={mensaje_ws}\'">', unsafe_allow_html=True)
                else: st.warning("Por favor, ingresá tu nombre.")

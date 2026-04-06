import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import time

# --- CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="Gestión de Pedidos", page_icon="🍟", layout="centered")

# --- FUNCIÓN DE CONEXIÓN ROBUSTA ---
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    if "gcp_service_account" not in st.secrets:
        st.error("❌ ERROR: No se encontró la sección [gcp_service_account] en los Secrets de Streamlit.")
        st.stop()

    try:
        # Extraer y limpiar la llave privada
        info_claves = dict(st.secrets["gcp_service_account"])
        # Corregimos los saltos de línea que suelen romperse al pegar
        info_claves["private_key"] = info_claves["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(info_claves, scopes=scope)
        cliente = gspread.authorize(creds)
        
        # ID de tu Google Sheet
        return cliente.open_by_key("1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA")
    
    except Exception as e:
        st.error(f"⚠️ Error crítico al conectar con Google: {e}")
        st.info("Revisá que el correo de la cuenta de servicio tenga permisos de EDITOR en el Excel.")
        st.stop()

# --- INICIALIZACIÓN DE DATOS ---
try:
    doc = conectar_google()
    hoja_prod = doc.get_worksheet(0)
    hoja_conf = doc.get_worksheet(1)
except Exception as e:
    st.error(f"No se pudieron cargar las pestañas del Excel: {e}")
    st.stop()

def cargar_datos_vivos():
    # Productos
    data_p = hoja_prod.get_all_records()
    df_p = pd.DataFrame(data_p)
    df_p.columns = [c.strip().upper() for c in df_p.columns]
    
    # Configuración
    data_c = hoja_conf.get_all_records()
    df_c = pd.DataFrame(data_c)
    conf_dict = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
    
    return df_p, df_c, conf_dict

df_prod, df_conf_raw, conf = cargar_datos_vivos()

# --- VARIABLES DINÁMICAS ---
nombre_n = conf.get("Nombre Negocio", "Mi Local")
alias_n = conf.get("Alias", "No definido")
tel_n = conf.get("Telefono", "5493826000000")
costo_d = conf.get("Costo Delivery", "0")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    .producto-caja { 
        border: 1px solid #EEE; padding: 15px; border-radius: 15px; 
        margin-bottom: 15px; background-color: #FDFDFD;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
    }
    .precio-tag { color: #E63946; font-size: 24px; font-weight: bold; }
    .ing-box { background: #FFF9C4; padding: 10px; border-radius: 8px; font-size: 14px; border-left: 5px solid #FBC02D; }
    </style>
    """, unsafe_allow_html=True)

# --- MANEJO DE SESIÓN ---
if 'rol' not in st.session_state: st.session_state['rol'] = 'cliente'
if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.header("⚙️ Panel de Gestión")
    if st.session_state['rol'] == 'cliente':
        with st.expander("🔐 Ingresar"):
            u = st.text_input("Usuario/DNI")
            p = st.text_input("Clave", type="password")
            if st.button("Acceder"):
                if u == conf.get("Admin_DNI") and p == conf.get("Admin_Pass"):
                    st.session_state['rol'] = 'admin'
                    st.rerun()
                elif u == conf.get("User") and p == conf.get("User_Pass"):
                    st.session_state['rol'] = 'usuario'
                    st.rerun()
                else: st.error("Datos incorrectos")
    else:
        st.success(f"Sesión: {st.session_state['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['rol'] = 'cliente'
            st.rerun()

# --- LÓGICA DE VISTAS ---
if st.session_state['rol'] in ['admin', 'usuario']:
    st.title("🛠️ Administración")
    t1, t2 = st.tabs(["🍔 Menú de Productos", "🏠 Datos del Local"])

    with t1:
        st.subheader("Edición de Menú")
        if st.session_state['rol'] == 'admin':
            edit_p = st.data_editor(df_prod, use_container_width=True, key="admin_p")
        else:
            cols = ["PRODUCTO", "VARIEDADES", "INGREDIENTES", "PRECIO", "DISPONIBLE"]
            edit_p = st.data_editor(df_prod[cols], use_container_width=True, key="user_p")
        
        if st.button("💾 Guardar Menú"):
            hoja_prod.update([df_prod.columns.values.tolist()] + edit_p.values.tolist())
            st.success("¡Menú actualizado en la nube!")

    with t2:
        st.subheader("Configuración")
        campos = ["Nombre Negocio", "Alias", "Telefono", "Costo Delivery"]
        df_sub = df_conf_raw[df_conf_raw.iloc[:, 0].isin(campos)]
        edit_c = st.data_editor(df_sub, use_container_width=True, key="conf_edit", hide_index=True)
        
        if st.button("💾 Guardar Alias y Datos"):
            for _, fila in edit_c.iterrows():
                celda = hoja_conf.find(str(fila.iloc[0]))
                hoja_conf.update_cell(celda.row, 2, str(fila.iloc[1]))
            st.success("✅ ¡Datos actualizados! Reiniciando...")
            time.sleep(1)
            st.rerun()

# --- VISTA CLIENTE (PÚBLICA) ---
else:
    st.markdown(f"<h1 style='text-align:center; color:#E63946;'>🍟 {nombre_n}</h1>", unsafe_allow_html=True)
    
    if not df_prod.empty:
        df_v = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"]
        cats = df_v['CATEGORIA'].unique()
        tabs = st.tabs(list(cats))

        for i, cat in enumerate(cats):
            with tabs[i]:
                items = df_v[df_v['CATEGORIA'] == cat]
                for idx, row in items.iterrows():
                    with st.container():
                        st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                        col1, col2 = st.columns([1, 1.5])
                        
                        with col1:
                            img = row['IMAGEN'] if row['IMAGEN'] != "" else "https://via.placeholder.com/200"
                            st.image(img, use_container_width=True)

                        with col2:
                            st.subheader(row['PRODUCTO'])
                            # Manejo de Variedades
                            variedades = str(row['VARIEDADES']).split(',') if row['VARIEDADES'] != "" else []
                            if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = 0
                            
                            if variedades:
                                sel = st.selectbox("Elegí tamaño/tipo:", variedades, key=f"sel_{idx}", 
                                                   index=st.session_state['sel_v'][idx])
                                st.session_state['sel_v'][idx] = variedades.index(sel)

                            # Ingredientes y Precio
                            p_idx = st.session_state['sel_v'][idx]
                            if row['INGREDIENTES'] != "":
                                ings = str(row['INGREDIENTES']).split(';')
                                st.markdown(f'<div class="ing-box">{ings[p_idx] if p_idx < len(ings) else ings[0]}</div>', unsafe_allow_html=True)

                            precios = str(row['PRECIO']).split(';')
                            p_final = float("".join(filter(str.isdigit, precios[p_idx] if p_idx < len(precios) else precios[0])))
                            
                            st.markdown(f'<p class="precio-tag">${p_final:,.0f}</p>', unsafe_allow_html=True)
                            if st.button("Agregar 🛒", key=f"btn_{idx}"):
                                nom_full = f"{row['PRODUCTO']} ({variedades[p_idx]})" if variedades else row['PRODUCTO']
                                if nom_full in st.session_state['carrito']: st.session_state['carrito'][nom_full]['cant'] += 1
                                else: st.session_state['carrito'][nom_full] = {'precio': p_final, 'cant': 1}
                                st.toast("¡Agregado!")
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- CARRITO ---
    if st.session_state['carrito']:
        with st.sidebar:
            st.markdown("### 🛒 Tu Pedido")
            total = 0
            resumen = ""
            for it, d in list(st.session_state['carrito'].items()):
                sub = d['precio'] * d['cant']
                total += sub
                st.write(f"**{d['cant']}x** {it}")
                resumen += f"- {d['cant']}x {it}\n"
            
            st.divider()
            nom = st.text_input("¿Tu nombre?")
            envio = st.radio("Entrega:", ["Retiro", "Delivery"])
            c_envio = int(costo_d) if envio == "Delivery" else 0
            
            st.markdown(f"#### Total: ${total + c_envio:,.0f}")
            st.caption(f"Alias MP: {alias_n}")
            
            if st.button("🚀 Enviar a WhatsApp"):
                if nom:
                    msg = urllib.parse.quote(f"Hola! Soy {nom}. Pedido:\n{resumen}\nTotal: ${total+c_envio}")
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/{tel_n}?text={msg}\'">', unsafe_allow_html=True)
                else: st.warning("Falta tu nombre")

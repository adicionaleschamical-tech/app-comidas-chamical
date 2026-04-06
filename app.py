import streamlit as st
import pandas as pd
import time
import requests

# --- DATOS DE ACCESO (VERIFICADOS) ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food", page_icon="🍟")

# --- FUNCIÓN DE ENVÍO ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok")
    except: return False

# --- CARGA DE DATOS SIN CACHÉ CRÍTICA ---
def cargar_datos():
    try:
        t = int(time.time())
        df_p = pd.read_csv(f"{URL_PRODUCTOS}&t={t}")
        # Normalizar nombres de columnas a mayúsculas para evitar errores
        df_p.columns = [c.strip().upper() for c in df_p.columns]
        
        df_c = pd.read_csv(f"{URL_CONFIG}&t={t}")
        conf = {str(r.iloc[0]).strip(): str(r.iloc[1]).strip() for _, r in df_c.iterrows()}
        return df_p, conf
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), {}

# --- ESTILO FORZADO PARA IOS ---
st.markdown("""
    <style>
    * { color: #000000 !important; }
    .stApp { background-color: #FFFFFF !important; }
    .producto-caja { 
        border: 2px solid #EEE; 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        background: #F9F9F9;
    }
    .precio { color: #E63946 !important; font-size: 24px; font-weight: bold; }
    button { height: 45px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, conf = cargar_datos()

st.title("🍟 Caniche Food")

if df_prod.empty:
    st.warning("No se encontraron productos. Verificá que el Google Sheets sea público.")
else:
    # Filtrar solo disponibles
    df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"] if 'DISPONIBLE' in df_prod.columns else df_prod
    
    categorias = df_ver['CATEGORIA'].unique()
    tabs = st.tabs(list(categorias))

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df_ver[df_ver['CATEGORIA'] == cat]
            for idx, row in items.iterrows():
                with st.container():
                    st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                    
                    # Imagen
                    img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/400x200"
                    st.image(img, use_container_width=True)
                    
                    st.subheader(row['PRODUCTO'])
                    
                    # Lógica de Variedades
                    tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                    if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                    
                    if tiene_v:
                        ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                        st.write("Seleccioná opción:")
                        for vi, vn in enumerate(ops):
                            if st.button(vn, key=f"btn_{idx}_{vi}", use_container_width=True):
                                st.session_state['sel_v'][idx] = vi
                                st.rerun()
                    
                    # Mostrar Precio e Ingredientes si corresponde
                    pos = st.session_state['sel_v'][idx]
                    if not tiene_v or pos is not None:
                        p_idx = pos if pos is not None else 0
                        
                        # Extraer Precio
                        precios = str(row['PRECIO']).split(';')
                        try:
                            p_raw = precios[p_idx] if p_idx < len(precios) else precios[0]
                            precio_final = float("".join(filter(str.isdigit, p_raw)))
                        except: precio_final = 0
                        
                        # Extraer Ingredientes
                        if 'INGREDIENTES' in row and pd.notna(row['INGREDIENTES']):
                            ings = str(row['INGREDIENTES']).split(';')
                            det = ings[p_idx] if p_idx < len(ings) else ings[0]
                            st.info(f"Incluye: {det}")

                        st.markdown(f'<p class="precio">${precio_final:,.0f}</p>', unsafe_allow_html=True)

                        # Carrito
                        p_nombre = f"{row['PRODUCTO']} ({ops[pos]})" if tiene_v else row['PRODUCTO']
                        
                        col1, col2, col3 = st.columns([1,1,1])
                        with col1:
                            if st.button("➖", key=f"menos_{idx}"):
                                if p_nombre in st.session_state['carrito']:
                                    st.session_state['carrito'][p_nombre]['cant'] -= 1
                                    if st.session_state['carrito'][p_nombre]['cant'] <= 0: del st.session_state['carrito'][p_nombre]
                                    st.rerun()
                        with col2:
                            cant = st.session_state['carrito'].get(p_nombre, {}).get('cant', 0)
                            st.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                        with col3:
                            if st.button("➕", key=f"mas_{idx}"):
                                if p_nombre in st.session_state['carrito']: st.session_state['carrito'][p_nombre]['cant'] += 1
                                else: st.session_state['carrito'][p_nombre] = {'precio': precio_final, 'cant': 1}
                                st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# --- FINALIZAR PEDIDO ---
if st.session_state['carrito']:
    st.divider()
    st.header("🛒 Tu Pedido")
    total_final = 0
    resumen = ""
    
    for item, d in st.session_state['carrito'].items():
        sub = d['precio'] * d['cant']
        total_final += sub
        st.write(f"✅ {d['cant']}x {item} — ${sub:,.0f}")
        resumen += f"• {d['cant']}x {item} (${sub:,.0f})\n"

    nom = st.text_input("Tu Nombre:")
    ent = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
    
    costo_envio = 0
    if ent == "Delivery":
        dir_c = st.text_area("Dirección:")
        try: costo_envio = int(conf.get("Costo Delivery", 0))
        except: costo_envio = 0
    
    total_con_envio = total_final + costo_envio
    st.subheader(f"Total: ${total_con_envio:,.0f}")

    if st.button("🚀 ENVIAR PEDIDO A TELEGRAM", use_container_width=True):
        if nom:
            msg = (f"🔔 *PEDIDO NUEVO*\n👤 *Cliente:* {nom}\n📍 *Modo:* {ent}\n"
                   f"------------------\n{resumen}"
                   f"------------------\n💰 *TOTAL: ${total_con_envio:,.0f}*")
            if enviar_telegram(msg):
                st.success("¡Pedido enviado! Revisá tu Telegram X.")
                st.session_state['carrito'] = {}
                st.balloons()
            else:
                st.error("Error al enviar. Asegurate de haberle dado 'START' a tu bot.")

import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURACIÓN DE ACCESO (TU GOOGLE SHEETS) ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

# --- CONFIGURACIÓN DE TELEGRAM ---
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_ID = "7860013984"

st.set_page_config(page_title="Caniche Food", page_icon="🍟", layout="centered")

# --- FUNCIÓN DE ENVÍO A TELEGRAM ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok")
    except: return False

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

# --- DISEÑO ULTRA-VISIBILIDAD (ESPECIAL PARA IPHONE/IOS) ---
st.markdown("""
    <style>
    /* Forzar colores base para evitar problemas con Modo Oscuro de iOS */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, div, label, .stMarkdown { color: #111111 !important; }

    /* Caja contenedora del producto */
    .producto-caja { 
        border: 2px solid #EAEAEA !important; 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        background-color: #FDFDFD !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* CAJA DE INGREDIENTES (Diseño tipo Post-it para visibilidad total) */
    .ingredientes-vivos {
        background-color: #FFF9C4 !important; 
        color: #000000 !important;
        padding: 15px;
        border-radius: 12px;
        border-left: 10px solid #FBC02D !important;
        margin: 12px 0px;
        font-size: 16px !important;
        font-weight: 500 !important;
        line-height: 1.5;
    }

    /* Precio resaltado en Rojo Caniche */
    .precio-vete { 
        color: #E63946 !important; 
        font-size: 30px !important; 
        font-weight: 900 !important; 
        margin: 10px 0;
    }

    /* Botones de cantidad con contraste para Safari */
    .stButton > button {
        background-color: #F5F5F5 !important;
        color: #111111 !important;
        border: 1px solid #CCCCCC !important;
        font-weight: bold !important;
        height: 50px !important;
    }

    /* Estilo del resumen del carrito */
    .resumen-card {
        background-color: #F8F9FA !important;
        border-left: 6px solid #E63946 !important;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'carrito' not in st.session_state: st.session_state['carrito'] = {}
if 'sel_v' not in st.session_state: st.session_state['sel_v'] = {}

df_prod, conf = cargar_datos()

st.markdown("<h1 style='text-align: center; color: #E63946 !important;'>🍟 Caniche Food</h1>", unsafe_allow_html=True)

if not df_prod.empty:
    # Filtrar solo productos con DISPONIBLE = "SI"
    df_ver = df_prod[df_prod['DISPONIBLE'].astype(str).str.upper() == "SI"] if 'DISPONIBLE' in df_prod.columns else df_prod
    
    categorias = df_ver['CATEGORIA'].unique()
    tabs = st.tabs(list(categorias))

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df_ver[df_ver['CATEGORIA'] == cat]
            for idx, row in items.iterrows():
                st.markdown('<div class="producto-caja">', unsafe_allow_html=True)
                
                # Imagen del producto
                img = row['IMAGEN'] if 'IMAGEN' in row and pd.notna(row['IMAGEN']) else "https://via.placeholder.com/200"
                st.image(img, width=220)
                
                st.markdown(f"## {row['PRODUCTO']}")
                
                # Gestión de Variedades (Simple, Completa, etc.)
                tiene_v = 'VARIEDADES' in row and pd.notna(row['VARIEDADES'])
                if idx not in st.session_state['sel_v']: st.session_state['sel_v'][idx] = None
                
                if tiene_v:
                    ops = [o.strip() for o in str(row['VARIEDADES']).split(',')]
                    sel = st.selectbox("👇 Elegí tu opción:", ["- Seleccionar Variedad -"] + ops, key=f"sel_{idx}")
                    if sel != "- Seleccionar Variedad -":
                        st.session_state['sel_v'][idx] = ops.index(sel)
                    else:
                        st.session_state['sel_v'][idx] = None
                
                # Mostrar Detalles solo si no hay variedad o ya se eligió una
                pos = st.session_state['sel_v'][idx]
                if not tiene_v or pos is not None:
                    p_idx = pos if pos is not None else 0
                    
                    # --- MOSTRAR INGREDIENTES (El cuadro amarillo) ---
                    if 'INGREDIENTES' in row and pd.notna(row['INGREDIENTES']):
                        ings_list = str(row['INGREDIENTES']).split(';')
                        det_ing = ings_list[p_idx] if p_idx < len(ings_list) else ings_list[0]
                        st.markdown(f'<div class="ingredientes-vivos"><b style="color:#000;">Esta variedad trae:</b><br>{det_ing}</div>', unsafe_allow_html=True)

                    # --- MOSTRAR PRECIO ---
                    precios_list = str(row['PRECIO']).split(';')
                    try:
                        p_raw = precios_list[p_idx] if p_idx < len(precios_list) else precios_list[0]
                        precio_f = float("".join(filter(str.isdigit, p_raw)))
                    except: precio_f = 0
                    
                    st.markdown(f'<p class="precio-vete">${precio_f:,.0f}</p>', unsafe_allow_html=True)

                    # --- CONTROLES DE CARRITO ---
                    p_nom = f"{row['PRODUCTO']} ({ops[pos]})" if tiene_v else row['PRODUCTO']
                    c1, c2, c3 = st.columns([1,1,1])
                    with c1:
                        if st.button("➖", key=f"m_{idx}"):
                            if p_nom in st.session_state['carrito']:
                                st.session_state['carrito'][p_nom]['cant'] -= 1
                                if st.session_state['carrito'][p_nom]['cant'] <= 0: del st.session_state['carrito'][p_nom]
                                st.rerun()
                    with c2:
                        cant = st.session_state['carrito'].get(p_nom, {}).get('cant', 0)
                        st.markdown(f"<h3 style='text-align:center; margin-top:10px;'>{cant}</h3>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕", key=f"p_{idx}"):
                            if p_nom in st.session_state['carrito']: st.session_state['carrito'][p_nom]['cant'] += 1
                            else: st.session_state['carrito'][p_nom] = {'precio': precio_f, 'cant': 1}
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# --- RESUMEN Y FINALIZACIÓN DEL PEDIDO ---
if st.session_state['carrito']:
    st.divider()
    st.markdown("## 🛒 Tu Carrito")
    total_acumulado = 0
    texto_para_telegram = ""
    
    for item, d in st.session_state['carrito'].items():
        subtotal = d['precio'] * d['cant']
        total_acumulado += subtotal
        st.markdown(f"""
            <div class="resumen-card">
                <b>{d['cant']}x</b> {item}<br>
                <span style="color:#E63946;">Subtotal: ${subtotal:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)
        texto_para_telegram += f"• {d['cant']}x {item} (${subtotal:,.0f})\n"

    with st.container(border=True):
        st.subheader("📍 Datos de Entrega")
        nombre_cliente = st.text_input("¿A nombre de quién?")
        metodo_pago = st.selectbox("¿Cómo vas a pagar?", ["Efectivo", "Transferencia / Alias", "Mercado Pago"])
        tipo_entrega = st.radio("¿Retiro o Envío?", ["Retiro en Local", "Delivery"], horizontal=True)
        
        costo_envio = 0
        direccion_cliente = ""
        if tipo_entrega == "Delivery":
            direccion_cliente = st.text_area("Dirección exacta y alguna referencia:")
            try:
                # Busca el costo de envío en la pestaña Configuración del Excel
                costo_envio = int("".join(filter(str.isdigit, str(conf.get("Costo Delivery", "0")))))
            except: costo_envio = 0
            if costo_envio > 0:
                st.info(f"Costo de envío: ${costo_envio:,.0f}")
        
        total_final_con_envio = total_acumulado + costo_envio
        st.markdown(f"<h2 style='text-align:center; background:#E63946; color:white; padding:15px; border-radius:15px;'>TOTAL: ${total_final_con_envio:,.0f}</h2>", unsafe_allow_html=True)

        if st.button("🚀 ENVIAR PEDIDO A CANICHE FOOD", use_container_width=True):
            if not nombre_cliente:
                st.error("⚠️ Por favor, ingresá tu nombre para el pedido.")
            elif tipo_entrega == "Delivery" and not direccion_cliente:
                st.error("⚠️ Por favor, ingresá tu dirección para el envío.")
            else:
                # Armado del mensaje que te llega a Telegram
                mensaje_final = (
                    f"🔔 *¡NUEVO PEDIDO!*\n\n"
                    f"👤 *Cliente:* {nombre_cliente}\n"
                    f"🛵 *Tipo:* {tipo_entrega}\n"
                    f"{'🏠 *Dirección:* ' + direccion_cliente if tipo_entrega == 'Delivery' else '🏢 *Retira en local*'}\n"
                    f"💳 *Pago:* {metodo_pago}\n"
                    f"--------------------------\n"
                    f"{texto_para_telegram}"
                    f"--------------------------\n"
                    f"💰 *TOTAL A COBRAR: ${total_final_con_envio:,.0f}*"
                )
                
                if enviar_telegram(mensaje_final):
                    st.success("¡Pedido enviado con éxito! Te avisaremos cuando esté listo.")
                    st.balloons()
                    # Limpiar carrito después de enviar
                    st.session_state['carrito'] = {}
                else:
                    st.error("❌ No se pudo enviar el pedido. Asegurate de que el Bot esté activado.")

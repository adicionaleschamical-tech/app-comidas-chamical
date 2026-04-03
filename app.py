import streamlit as st
import pandas as pd
import urllib.parse
import re
import time

# --- ENLACES VINCULADOS A TU SHEET ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
# Pestaña Productos (gid=0)
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
# Pestaña Config (gid=612320365)
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE CARGA INTELIGENTE ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

@st.cache_data(ttl=10) # Se actualiza cada 10 segundos
def cargar_config():
    try:
        # Forzamos la descarga fresca para ver cambios del Sheet al instante
        df_conf = pd.read_csv(f"{URL_CONFIG}&cache={int(time.time())}")
        # Creamos diccionario Clave -> Valor
        return dict(zip(df_conf.iloc[:, 0].astype(str).str.strip(), df_conf.iloc[:, 1]))
    except:
        return {"Alias": "caniche.food.mp", "Costo Delivery": "800", "Direccion Local": "Chamical", "Telefono": "5493804000000"}

@st.cache_data(ttl=10)
def cargar_productos():
    try:
        df = pd.read_csv(f"{URL_PRODUCTOS}&cache={int(time.time())}")
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except: return pd.DataFrame()

# --- CARGA DE DATOS ---
conf = cargar_config()
df = cargar_productos()

st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical, La Rioja')}")

# --- LISTADO DE PRODUCTOS ---
if not df.empty:
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    categorias = list(df['Categoria'].unique())
    tabs = st.tabs(categorias)

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df[df['Categoria'] == cat]
            for _, row in items.iterrows():
                with st.container(border=True):
                    c_img, c_info, c_btns = st.columns([1, 1.5, 1])
                    with c_img:
                        if pd.notna(row.get('Imagen')):
                            st.image(row['Imagen'], use_container_width=True)
                    with c_info:
                        st.subheader(row['Producto'])
                        st.write(f"**${row['Precio_Num']:,.0f}**")
                    with c_btns:
                        r, n, s = st.columns([1,1,1])
                        prod_n = row['Producto']
                        with s: 
                            if st.button("➕", key=f"add_{prod_n}"):
                                if prod_n in st.session_state['carrito']:
                                    st.session_state['carrito'][prod_n]['cant'] += 1
                                else:
                                    st.session_state['carrito'][prod_n] = {'precio': row['Precio_Num'], 'cant': 1}
                                st.rerun()
                        with n:
                            cant = st.session_state['carrito'].get(prod_n, {}).get('cant', 0)
                            st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                        with r:
                            if st.button("➖", key=f"res_{prod_n}"):
                                if prod_n in st.session_state['carrito']:
                                    st.session_state['carrito'][prod_n]['cant'] -= 1
                                    if st.session_state['carrito'][prod_n]['cant'] <= 0:
                                        del st.session_state['carrito'][prod_n]
                                st.rerun()

    # --- CIERRE DEL PEDIDO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        
        total_prods = 0
        resumen_txt = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_prods += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            resumen_txt += f"- {info['cant']}x {p} (${sub:,.0f})\n"

        st.divider()
        nombre = st.text_input("Tu Nombre", placeholder="Escribí tu nombre")
        entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        
        envio = 0
        dire = ""
        if entrega == "Delivery":
            dire = st.text_input("Dirección de entrega")
            envio = limpiar_precio(conf.get("Costo Delivery"))
            st.warning(f"🛵 Envío: ${envio:,.0f}")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / MP"])
        total_final = total_prods + envio

        with st.expander("Detalle de Pago", expanded=True):
            st.write(f"Productos: ${total_prods:,.0f}")
            if envio > 0: st.write(f"Envío: ${envio:,.0f}")
            st.success(f"### TOTAL: ${total_final:,.0f}")
            if "Transferencia" in pago:
                st.info(f"🏦 **Alias:** `{conf.get('Alias')}`")

        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre or (entrega == "Delivery" and not dire):
                st.error("⚠️ Completá tu nombre y dirección.")
            else:
                msj = (
                    f"🍔 *PEDIDO - CANICHE FOOD*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"--------------------------\n{resumen_txt}"
                    f"--------------------------\n"
                    f"🛵 *Entrega:* {entrega}\n"
                    f"{'📍 *Dirección:* ' + dire if dire else ''}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"💰 *TOTAL: ${total_final:,.0f}*"
                )
                url_wa = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msj)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()
else:
    st.info("👋 ¡Hola! Elegí algo rico arriba.")

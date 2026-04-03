import streamlit as st
import pandas as pd
import urllib.parse
import time

# ==========================================
# 🔗 CONFIGURACIÓN DE TU GOOGLE SHEET
# ==========================================
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# Enlaces con GID específicos
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

# --- CARGA DE CONFIGURACIÓN DINÁMICA ---
@st.cache_data(ttl=5)
def cargar_config():
    # Estos son solo valores de "emergencia" si el Sheet falla
    conf_base = {
        "Alias": "tomas.130611", 
        "Costo Delivery": "800",
        "Direccion Local": "Chamical, La Rioja",
        "Telefono": "5493804000000"
    }
    try:
        # Intentamos leer el Sheet
        url_fresca = f"{URL_CONFIG}&t={int(time.time())}"
        df_conf = pd.read_csv(url_fresca)
        
        if not df_conf.empty:
            # Si el Sheet responde, sobreescribimos TODO con lo que diga el Excel
            claves = df_conf.iloc[:, 0].astype(str).str.strip()
            valores = df_conf.iloc[:, 1].astype(str).str.strip()
            nuevos_datos = dict(zip(claves, valores))
            
            # Buscamos 'Alias' en el Sheet (ignorando mayúsculas)
            for k, v in nuevos_datos.items():
                if k.lower() == "alias":
                    conf_base["Alias"] = v
                if k.lower() == "costo delivery":
                    conf_base["Costo Delivery"] = v
                if k.lower() == "direccion local":
                    conf_base["Direccion Local"] = v
                if k.lower() == "telefono":
                    conf_base["Telefono"] = v
                    
        return conf_base
    except Exception as e:
        # Si ves este error, es porque el Sheet sigue privado
        if "401" in str(e):
            st.sidebar.error("⚠️ El Sheet es PRIVADO. El Alias no se actualizará hasta que lo pongas en: 'Cualquier persona con el enlace -> Lector'")
        return conf_base

@st.cache_data(ttl=5)
def cargar_productos():
    try:
        url_fresca = f"{URL_PRODUCTOS}&t={int(time.time())}"
        df = pd.read_csv(url_fresca)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except:
        return pd.DataFrame()

# --- PROCESO ---
conf = cargar_config()
df = cargar_productos()

st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local')}")

# --- MOSTRAR PRODUCTOS ---
if not df.empty:
    if 'Disponible' in df.columns:
        df_ok = df[df['Disponible'].astype(str).str.upper().str.strip() == "SI"]
    else:
        df_ok = df

    if df_ok.empty:
        st.warning("👋 No hay productos disponibles.")
    else:
        categorias = list(df_ok['Categoria'].unique())
        tabs = st.tabs(categorias)
        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_ok[df_ok['Categoria'] == cat]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c_img, c_info, c_btns = st.columns([1, 1.5, 1])
                        with c_img:
                            img = row.get('Imagen')
                            st.image(img if pd.notna(img) and str(img).startswith('http') else "https://via.placeholder.com/150", use_container_width=True)
                        with c_info:
                            st.subheader(row['Producto'])
                            st.write(f"### ${row['Precio_Num']:,.0f}")
                        with c_btns:
                            r, n, s = st.columns([1,1,1])
                            p_id = row['Producto']
                            with s:
                                if st.button("➕", key=f"add_{p_id}"):
                                    if p_id in st.session_state['carrito']: st.session_state['carrito'][p_id]['cant'] += 1
                                    else: st.session_state['carrito'][p_id] = {'precio': row['Precio_Num'], 'cant': 1}
                                    st.rerun()
                            with n:
                                cant = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                            with r:
                                if st.button("➖", key=f"res_{p_id}"):
                                    if p_id in st.session_state['carrito'] and st.session_state['carrito'][p_id]['cant'] > 0:
                                        st.session_state['carrito'][p_id]['cant'] -= 1
                                        if st.session_state['carrito'][p_id]['cant'] == 0: del st.session_state['carrito'][p_id]
                                    st.rerun()

    # --- CARRITO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        total_p = 0
        txt_wa = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_p += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            txt_wa += f"- {info['cant']}x {p} (${sub:,.0f})\n"

        st.divider()
        nombre = st.text_input("Tu Nombre")
        entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        envio = 0
        dire = ""
        if entrega == "Delivery":
            dire = st.text_input("Dirección")
            envio = limpiar_precio(conf.get("Costo Delivery", 800))
            st.info(f"🛵 Envío: **${envio:,.0f}**")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        total_final = total_p + envio

        with st.expander("Resumen de Pago", expanded=True):
            st.write(f"Subtotal: ${total_p:,.0f}")
            if envio > 0: st.write(f"Envío: ${envio:,.0f}")
            st.success(f"### TOTAL: ${total_final:,.0f}")
            if "Transferencia" in pago:
                # AQUÍ SE MUESTRA EL ALIAS DINÁMICO DEL SHEET
                st.warning(f"🏦 **Alias:** `{conf.get('Alias')}`")

        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre or (entrega == "Delivery" and not dire):
                st.error("⚠️ Completá tus datos.")
            else:
                msj = f"🍔 *PEDIDO*\n👤 *Cliente:* {nombre}\n--------------------------\n{txt_wa}--------------------------\n🛵 *Entrega:* {entrega}\n{'📍 *Dirección:* ' + dire if dire else ''}\n💳 *Pago:* {pago}\n💰 *TOTAL: ${total_final:,.0f}*"
                url_wa = f"https://wa.me/{conf.get('Telefono')}?text={urllib.parse.quote(msj)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()
else:
    st.info("👋 El menú se cargará cuando el Sheet sea público.")

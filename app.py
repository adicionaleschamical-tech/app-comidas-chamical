import streamlit as st
import pandas as pd
import urllib.parse
import time
import re

# --- ENLACE DE TU GOOGLE SHEET (PUBLICADO COMO CSV) ---
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
# Enlace específico para la pestaña Config (usando tu GID detectado anteriormente)
URL_CONFIG = URL_BASE + "&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- INICIALIZACIÓN DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE CARGA Y LIMPIEZA ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    # Extrae solo números (ignora $, puntos y comas)
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

@st.cache_data(ttl=10)
def cargar_config():
    try:
        # Forzamos actualización con un timestamp
        df_conf = pd.read_csv(f"{URL_CONFIG}&t={int(time.time())}")
        return dict(zip(df_conf.iloc[:, 0].astype(str).str.strip(), df_conf.iloc[:, 1]))
    except:
        return {
            "Alias": "caniche.food.mp",
            "Costo Delivery": "800",
            "Direccion Local": "Chamical, La Rioja",
            "Telefono": "5493804000000"
        }

@st.cache_data(ttl=10)
def cargar_productos():
    try:
        df = pd.read_csv(f"{URL_BASE}&t={int(time.time())}")
        # Normalizar nombres de columnas
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except Exception as e:
        st.error(f"Error al conectar con el menú: {e}")
        return pd.DataFrame()

# --- CARGA DE DATOS ---
conf = cargar_config()
df = cargar_productos()

# --- INTERFAZ ---
st.title("🍔 Caniche Food")
st.caption(f"📍 Ubicación: {conf.get('Direccion Local', 'Chamical')}")

if not df.empty:
    # Filtrar solo productos disponibles
    if 'Disponible' in df.columns:
        df_visibles = df[df['Disponible'].astype(str).str.upper().str.contains("SI")]
    else:
        df_visibles = df

    if df_visibles.empty:
        st.warning("⚠️ No hay productos marcados como 'SI' en la columna Disponible.")
    else:
        # Categorías en pestañas
        categorias = list(df_visibles['Categoria'].unique())
        tabs = st.tabs(categorias)

        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_visibles[df_visibles['Categoria'] == cat]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c_img, c_info, c_btns = st.columns([1, 1.5, 1])
                        
                        with c_img:
                            img = row.get('Imagen')
                            if pd.notna(img) and str(img).startswith('http'):
                                st.image(img, use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                        
                        with c_info:
                            st.subheader(row['Producto'])
                            st.write(f"**${row['Precio_Num']:,.0f}**")
                        
                        with c_btns:
                            r, n, s = st.columns([1,1,1])
                            p_name = row['Producto']
                            with s: 
                                if st.button("➕", key=f"add_{p_name}"):
                                    if p_name in st.session_state['carrito']:
                                        st.session_state['carrito'][p_name]['cant'] += 1
                                    else:
                                        st.session_state['carrito'][p_name] = {'precio': row['Precio_Num'], 'cant': 1}
                                    st.rerun()
                            with n:
                                cant = st.session_state['carrito'].get(p_name, {}).get('cant', 0)
                                st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                            with r:
                                if st.button("➖", key=f"res_{p_name}"):
                                    if p_name in st.session_state['carrito']:
                                        st.session_state['carrito'][p_name]['cant'] -= 1
                                        if st.session_state['carrito'][p_name]['cant'] <= 0:
                                            del st.session_state['carrito'][p_name]
                                    st.rerun()

    # --- SECCIÓN DEL PEDIDO (CARRITO) ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        
        total_comida = 0
        resumen_wa = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_comida += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            resumen_wa += f"- {info['cant']}x {p} (${sub:,.0f})\n"

        st.divider()
        nombre = st.text_input("Tu Nombre", placeholder="Escribí tu nombre")
        entrega = st.radio("¿Cómo recibís el pedido?", ["Retiro en Local", "Delivery"])
        
        envio_costo = 0
        ubicacion = ""
        if entrega == "Delivery":
            ubicacion = st.text_input("Dirección de entrega")
            envio_costo = limpiar_precio(conf.get("Costo Delivery", 800))
            st.info(f"🛵 Envío: **${envio_costo:,.0f}**")
        else:
            st.success(f"🏠 Podés retirar en: {conf.get('Direccion Local', 'El local')}")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        total_final = total_comida + envio_costo

        with st.expander("Ver Detalle de Pago", expanded=True):
            st.write(f"Productos: ${total_comida:,.0f}")
            if envio_costo > 0: st.write(f"Delivery: ${envio_costo:,.0f}")
            st.success(f"### TOTAL A PAGAR: ${total_final:,.0f}")
            if "Transferencia" in pago:
                st.warning(f"🏦 **Alias:** `{conf.get('Alias', 'caniche.food.mp')}`")

        # --- BOTÓN FINAL ---
        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre:
                st.error("⚠️ Por favor, ingresá tu nombre.")
            elif entrega == "Delivery" and not ubicacion:
                st.error("⚠️ Falta la dirección para el envío.")
            else:
                msj = (
                    f"🍔 *CANICHE FOOD - NUEVO PEDIDO*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"--------------------------\n{resumen_wa}"
                    f"--------------------------\n"
                    f"🛵 *Entrega:* {entrega}\n"
                    f"{'📍 *Dirección:* ' + ubicacion if ubicacion else ''}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"💰 *TOTAL: ${total_final:,.0f}*"
                )
                tel = conf.get('Telefono', '5493804000000')
                url_wa = f"https://wa.me/{tel}?text={urllib.parse.quote(msj)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()
else:
    st.error("No se pudo cargar el archivo de productos. Revisá que esté publicado como CSV.")

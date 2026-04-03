import streamlit as st
import pandas as pd
import urllib.parse
import re

# --- ENLACES DE GOOGLE SHEETS ---
# Este es el link principal que me pasaste
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"

# Intentamos cargar la pestaña de Configuración (normalmente gid=987654321 o similar, 
# pero usaremos el base por defecto y validaremos)
URL_PRODUCTOS = URL_BASE 
URL_CONFIG = URL_BASE + "&gid=1334032152" # Gid típico de la segunda pestaña, verificar en tu navegador

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- INICIALIZACIÓN DE CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

@st.cache_data(ttl=30)
def cargar_config():
    try:
        # Intentamos leer la configuración del Sheet
        df_conf = pd.read_csv(URL_CONFIG)
        # Creamos un diccionario: la columna A es la clave, la B el valor
        return dict(zip(df_conf.iloc[:, 0], df_conf.iloc[:, 1]))
    except:
        # Valores de respaldo si la pestaña Config no está lista
        return {
            "Alias": "caniche.food.mp",
            "Costo Delivery": "800",
            "Direccion Local": "Chamical, La Rioja",
            "Telefono": "5493804000000"
        }

@st.cache_data(ttl=30)
def cargar_productos():
    try:
        df = pd.read_csv(URL_PRODUCTOS)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except: return pd.DataFrame()

# --- CARGA DE DATOS ---
conf = cargar_config()
df = cargar_productos()

# --- INTERFAZ PRINCIPAL ---
st.title("🍔 Caniche Food")
st.caption(f"📍 Local: {conf.get('Direccion Local')}")

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
                        with s: 
                            if st.button("➕", key=f"add_{row['Producto']}"):
                                prod = row['Producto']
                                if prod in st.session_state['carrito']:
                                    st.session_state['carrito'][prod]['cant'] += 1
                                else:
                                    st.session_state['carrito'][prod] = {'precio': row['Precio_Num'], 'cant': 1}
                                st.rerun()
                        with n:
                            cant = st.session_state['carrito'].get(row['Producto'], {}).get('cant', 0)
                            st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                        with r:
                            if st.button("➖", key=f"res_{row['Producto']}"):
                                prod = row['Producto']
                                if prod in st.session_state['carrito']:
                                    st.session_state['carrito'][prod]['cant'] -= 1
                                    if st.session_state['carrito'][prod]['cant'] <= 0:
                                        del st.session_state['carrito'][prod]
                                st.rerun()

    # --- SECCIÓN DEL PEDIDO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        
        total_productos = 0
        resumen_txt = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_productos += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            resumen_txt += f"- {info['cant']}x {p} (${sub:,.0f})\n"

        st.divider()
        nombre = st.text_input("Tu Nombre", placeholder="¿A nombre de quién el pedido?")
        entrega = st.radio("¿Cómo recibís tu pedido?", ["Retiro en Local", "Delivery"])
        
        envio_final = 0
        dire = ""
        if entrega == "Delivery":
            dire = st.text_input("Dirección de entrega")
            envio_final = limpiar_precio(conf.get("Costo Delivery"))
            st.info(f"🛵 Costo de envío: **${envio_final:,.0f}**")
        else:
            st.success(f"🏠 Podés retirar en: {conf.get('Direccion Local')}")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        total_final = total_productos + envio_final

        with st.expander("Resumen de Pago", expanded=True):
            st.write(f"Comida: ${total_productos:,.0f}")
            if envio_final > 0: st.write(f"Envío: ${envio_final:,.0f}")
            st.write(f"### TOTAL: ${total_final:,.0f}")
            if "Transferencia" in pago:
                st.warning(f"🏦 **Alias:** `{conf.get('Alias')}`")

        # --- BOTÓN FINAL ---
        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre:
                st.error("⚠️ Falta tu nombre.")
            elif entrega == "Delivery" and not dire:
                st.error("⚠️ Falta la dirección para el envío.")
            else:
                # Mensaje de WhatsApp
                msj = (
                    f"🍔 *CANICHE FOOD - NUEVO PEDIDO*\n"
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
    st.info("👋 ¡Hola! Elegí tus productos arriba para empezar.")

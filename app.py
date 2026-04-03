import streamlit as st
import pandas as pd
import urllib.parse
import time
import re

# ==========================================
# 🔗 ENLACES DE TU GOOGLE SHEET
# ==========================================
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# Enlaces directos de exportación (Más estables que el de publicación web común)
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- INICIALIZACIÓN DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE CARGA Y LIMPIEZA ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    # Extrae solo números (elimina $, puntos, comas y espacios)
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

@st.cache_data(ttl=5) # Actualiza cada 5 segundos
def cargar_config():
    try:
        # El cache_buster obliga a Google a dar el dato más reciente
        url_fresca = f"{URL_CONFIG}&cache_buster={int(time.time())}"
        df_conf = pd.read_csv(url_fresca)
        
        # Limpiamos las celdas de espacios invisibles
        df_conf.iloc[:, 0] = df_conf.iloc[:, 0].astype(str).str.strip()
        df_conf.iloc[:, 1] = df_conf.iloc[:, 1].astype(str).str.strip()
        
        # Convertimos a diccionario: Columna A -> Columna B
        return dict(zip(df_conf.iloc[:, 0], df_conf.iloc[:, 1]))
    except:
        # Valores de respaldo si falla la conexión
        return {
            "Alias": "caniche.food.mp",
            "Costo Delivery": "800",
            "Direccion Local": "Chamical, La Rioja",
            "Telefono": "5493804000000"
        }

@st.cache_data(ttl=5)
def cargar_productos():
    try:
        url_fresca = f"{URL_PRODUCTOS}&cache_buster={int(time.time())}"
        df = pd.read_csv(url_fresca)
        # Normalizar nombres de columnas (Primera letra mayúscula)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except:
        return pd.DataFrame()

# --- PROCESO DE DATOS ---
conf = cargar_config()
df = cargar_productos()

# --- INTERFAZ ---
st.title("🍔 Caniche Food")
st.caption(f"📍 Ubicación: {conf.get('Direccion Local', 'Chamical')}")

if not df.empty:
    # Filtrar solo productos con "SI" en Disponible
    if 'Disponible' in df.columns:
        df_visibles = df[df['Disponible'].astype(str).str.upper().str.strip() == "SI"]
    else:
        df_visibles = df

    if df_visibles.empty:
        st.warning("⚠️ No hay productos marcados como 'SI' en la columna Disponible.")
    else:
        # Crear pestañas por categoría
        categorias = list(df_visibles['Categoria'].unique())
        tabs = st.tabs(categorias)

        for i, cat in enumerate(categorias):
            with tabs[i]:
                items = df_visibles[df_visibles['Categoria'] == cat]
                for _, row in items.iterrows():
                    with st.container(border=True):
                        c_img, c_info, c_btns = st.columns([1, 1.5, 1])
                        
                        with c_img:
                            img_url = row.get('Imagen')
                            if pd.notna(img_url) and str(img_url).startswith('http'):
                                st.image(img_url, use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/150?text=Comida", use_container_width=True)
                        
                        with c_info:
                            st.subheader(row['Producto'])
                            st.write(f"### ${row['Precio_Num']:,.0f}")
                        
                        with c_btns:
                            # Botones de cantidad
                            r, n, s = st.columns([1,1,1])
                            p_id = row['Producto']
                            with s: 
                                if st.button("➕", key=f"add_{p_id}"):
                                    if p_id in st.session_state['carrito']:
                                        st.session_state['carrito'][p_id]['cant'] += 1
                                    else:
                                        st.session_state['carrito'][p_id] = {'precio': row['Precio_Num'], 'cant': 1}
                                    st.rerun()
                            with n:
                                cant = st.session_state['carrito'].get(p_id, {}).get('cant', 0)
                                st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                            with r:
                                if st.button("➖", key=f"res_{p_id}"):
                                    if p_id in st.session_state['carrito']:
                                        st.session_state['carrito'][p_id]['cant'] -= 1
                                        if st.session_state['carrito'][p_id]['cant'] <= 0:
                                            del st.session_state['carrito'][p_id]
                                    st.rerun()

    # --- SECCIÓN DEL CARRITO (Caja de pago) ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Pedido")
        
        total_items = 0
        txt_pedido = ""
        for p, info in st.session_state['carrito'].items():
            subt = info['precio'] * info['cant']
            total_items += subt
            st.write(f"✅ {info['cant']}x **{p}** — ${subt:,.0f}")
            txt_pedido += f"- {info['cant']}x {p} (${subt:,.0f})\n"

        st.divider()
        st.subheader("📍 Datos de Entrega")
        
        nombre = st.text_input("Tu Nombre")
        entrega = st.radio("¿Cómo recibís?", ["Retiro en Local", "Delivery"])
        
        costo_envio = 0
        dire = ""
        if entrega == "Delivery":
            dire = st.text_input("Dirección de entrega / Barrio")
            costo_envio = limpiar_precio(conf.get("Costo Delivery", 800))
            st.warning(f"🛵 Costo de envío: **${costo_envio:,.0f}**")
        else:
            st.success(f"🏪 Podés retirar en: {conf.get('Direccion Local', 'el local')}")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        total_final = total_items + costo_envio

        with st.expander("Ver Resumen Total", expanded=True):
            st.write(f"Subtotal: ${total_items:,.0f}")
            if costo_envio > 0: st.write(f"Envío: ${costo_envio:,.0f}")
            st.success(f"### TOTAL A PAGAR: ${total_final:,.0f}")
            if "Transferencia" in pago:
                st.info(f"🏦 **Pagar al Alias:** `{conf.get('Alias', 'caniche.food.mp')}`")

        # --- BOTÓN DE CIERRE ---
        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre:
                st.error("⚠️ Por favor, ingresá tu nombre.")
            elif entrega == "Delivery" and not dire:
                st.error("⚠️ Necesitamos tu dirección para el envío.")
            else:
                # Armado del mensaje para WhatsApp
                mensaje_final = (
                    f"🍔 *CANICHE FOOD - NUEVO PEDIDO*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"--------------------------\n{txt_pedido}"
                    f"--------------------------\n"
                    f"🛵 *Entrega:* {entrega}\n"
                    f"{'📍 *Dirección:* ' + dire if dire else ''}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"💰 *TOTAL: ${total_final:,.0f}*"
                )
                # Teléfono desde el Sheet
                num_wa = conf.get('Telefono', '5493804000000')
                url_wa = f"https://wa.me/{num_wa}?text={urllib.parse.quote(mensaje_final)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()
else:
    st.error("No se pudo cargar el menú. Revisá la conexión con Google Sheets.")

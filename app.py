import streamlit as st
import pandas as pd
import urllib.parse
import time
import re

# ==========================================
# 🔗 CONFIGURACIÓN DE ENLACES
# ==========================================
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"

# Enlaces con GID específicos para cada pestaña
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=612320365"

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- INICIALIZACIÓN DEL CARRITO ---
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    solo_num = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_num)
    except: return 0.0

# --- CARGA DE CONFIGURACIÓN (Pestaña Config) ---
@st.cache_data(ttl=5)
def cargar_config():
    try:
        url_fresca = f"{URL_CONFIG}&cache_buster={int(time.time())}"
        df_conf = pd.read_csv(url_fresca)
        if df_conf.empty:
            return {}
        # Crea diccionario: Columna A (Clave) -> Columna B (Valor)
        return dict(zip(df_conf.iloc[:, 0].astype(str).str.strip(), df_conf.iloc[:, 1].astype(str).str.strip()))
    except Exception as e:
        st.error(f"⚠️ Error al leer Config: {e}")
        return {
            "Alias": "caniche.food.mp",
            "Costo Delivery": "800",
            "Direccion Local": "Chamical, La Rioja",
            "Telefono": "5493804000000"
        }

# --- CARGA DE PRODUCTOS (Pestaña Productos) ---
@st.cache_data(ttl=5)
def cargar_productos():
    try:
        url_fresca = f"{URL_PRODUCTOS}&cache_buster={int(time.time())}"
        df = pd.read_csv(url_fresca)
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        else:
            st.error("❌ No se encontró la columna 'Precio' en el Sheet.")
            
        return df
    except Exception as e:
        st.error(f"❌ Error de conexión con Productos: {e}")
        return pd.DataFrame()

# --- PROCESO DE DATOS ---
conf = cargar_config()
df = cargar_productos()

# --- INTERFAZ PRINCIPAL ---
st.title("🍔 Caniche Food")
st.caption(f"📍 {conf.get('Direccion Local', 'Chamical, La Rioja')}")

if not df.empty:
    # Filtrar solo productos marcados con SI (en mayúsculas y sin espacios)
    if 'Disponible' in df.columns:
        df_visibles = df[df['Disponible'].astype(str).str.upper().str.strip() == "SI"]
    else:
        df_visibles = df

    if df_visibles.empty:
        st.warning("👋 ¡Hola! Por el momento no hay productos disponibles.")
    else:
        # Pestañas por Categoría
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
                                st.image("https://via.placeholder.com/150?text=Caniche+Food", use_container_width=True)
                        
                        with c_info:
                            st.subheader(row['Producto'])
                            st.write(f"### ${row['Precio_Num']:,.0f}")
                        
                        with c_btns:
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

    # --- SECCIÓN DEL CARRITO ---
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
            dire = st.text_input("Dirección de entrega")
            costo_envio = limpiar_precio(conf.get("Costo Delivery", 800))
            st.warning(f"🛵 Envío: **${costo_envio:,.0f}**")
        else:
            st.success(f"🏠 Podés retirar en: {conf.get('Direccion Local', 'el local')}")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        total_final = total_items + costo_envio

        with st.expander("Ver Resumen de Pago", expanded=True):
            st.write(f"Comida: ${total_items:,.0f}")
            if costo_envio > 0: st.write(f"Envío: ${costo_envio:,.0f}")
            st.success(f"### TOTAL: ${total_final:,.0f}")
            if "Transferencia" in pago:
                st.info(f"🏦 **Alias:** `{conf.get('Alias', 'caniche.food.mp')}`")

        # --- BOTÓN HACER PEDIDO ---
        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre:
                st.error("⚠️ Por favor, ingresá tu nombre.")
            elif entrega == "Delivery" and not dire:
                st.error("⚠️ Falta la dirección para el envío.")
            else:
                msj = (
                    f"🍔 *PEDIDO - CANICHE FOOD*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"--------------------------\n{txt_pedido}"
                    f"--------------------------\n"
                    f"🛵 *Entrega:* {entrega}\n"
                    f"{'📍 *Dirección:* ' + dire if dire else ''}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"💰 *TOTAL: ${total_final:,.0f}*"
                )
                wa_tel = conf.get('Telefono', '5493804000000')
                url_wa = f"https://wa.me/{wa_tel}?text={urllib.parse.quote(msj)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()
else:
    st.error("⚠️ No se pudieron cargar los datos. Verificá que el Sheet sea público (Cualquiera con el link -> Lector).")

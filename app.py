import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000" # <-- TU NÚMERO REAL
ALIAS_MP = "caniche.food.mp"

st.set_page_config(page_title="Caniche Food", page_icon="🍕")

# Inicializar carrito como un diccionario para manejar cantidades fácilmente
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        # Limpieza de precios: quitar $, puntos y espacios para asegurar que sean números
        if 'Precio' in df.columns:
            df['Precio'] = df['Precio'].astype(str).str.replace('$', '').str.replace('.', '').str.strip()
            df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# --- 2. LOGICA DE CONTROL DE CANTIDADES ---
def modificar_cantidad(producto, precio, operacion):
    if operacion == "sumar":
        if producto in st.session_state['carrito']:
            st.session_state['carrito'][producto]['cant'] += 1
        else:
            st.session_state['carrito'][producto] = {'precio': precio, 'cant': 1}
    elif operacion == "restar":
        if producto in st.session_state['carrito']:
            st.session_state['carrito'][producto]['cant'] -= 1
            if st.session_state['carrito'][producto]['cant'] <= 0:
                del st.session_state['carrito'][producto]

# --- 3. INTERFAZ DE PRODUCTOS ---
st.title("🍕 Caniche Food")
df = cargar_datos()

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
                        st.write(f"**${row['Precio']:,.0f}**")
                    
                    with c_btns:
                        # Botones de + y -
                        col_r, col_c, col_s = st.columns([1,1,1])
                        with col_s:
                            if st.button("➕", key=f"add_{row['Producto']}"):
                                modificar_cantidad(row['Producto'], row['Precio'], "sumar")
                                st.rerun()
                        with col_c:
                            cant_actual = st.session_state['carrito'].get(row['Producto'], {}).get('cant', 0)
                            st.markdown(f"<h3 style='text-align: center;'>{cant_actual}</h3>", unsafe_allow_html=True)
                        with col_r:
                            if st.button("➖", key=f"res_{row['Producto']}"):
                                modificar_cantidad(row['Producto'], row['Precio'], "restar")
                                st.rerun()

    # --- 4. RESUMEN DEL CARRITO ---
    st.divider()
    st.header("🛒 Tu Pedido")

    if st.session_state['carrito']:
        total_general = 0
        detalle_texto = ""
        
        for prod, info in st.session_state['carrito'].items():
            subtotal = info['precio'] * info['cant']
            total_general += subtotal
            st.write(f"✅ {info['cant']}x **{prod}** — ${subtotal:,.0f}")
            detalle_texto += f"✅ {info['cant']}x {prod} (${subtotal:,.0f})\n"

        st.markdown(f"## Total: ${total_general:,.0f}")
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()

        st.info(f"🏦 Alias: `{ALIAS_MP}`")

        # --- 5. WHATSAPP ---
        mensaje_wa = (
            f"¡Hola Caniche Food! 🐩\n\n"
            f"Este es mi pedido:\n"
            f"{detalle_texto}\n"
            f"💰 *Total: ${total_general:,.0f}*\n\n"
            f"¿Me confirman el pedido?"
        )
        link_final = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(mensaje_wa)}"
        st.link_button("🚀 ENVIAR PEDIDO POR WHATSAPP", link_final, use_container_width=True)
    else:
        st.write("Elegí tus productos arriba con el botón ➕")
else:
    st.error("Error al cargar el menú.")

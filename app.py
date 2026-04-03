import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000" # <-- TU NÚMERO
ALIAS_MP = "caniche.food.mp"     # <-- TU ALIAS

st.set_page_config(page_title="Caniche Food", page_icon="🍔")

# Inicializar el carrito en la sesión si no existe
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = []

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 2. INTERFAZ ---
st.title("🍔 Caniche Food")

df = cargar_datos()

if not df.empty:
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    # Pestañas por categoría
    categorias = list(df['Categoria'].unique())
    tabs = st.tabs(categorias)

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df[df['Categoria'] == cat]
            for _, row in items.iterrows():
                with st.container(border=True):
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if pd.notna(row.get('Imagen')):
                            st.image(row['Imagen'], use_container_width=True)
                    with col_info:
                        st.subheader(row['Producto'])
                        try:
                            p_valor = float(row['Precio'])
                            st.write(f"**${p_valor:,.0f}**")
                        except:
                            p_valor = 0.0
                        
                        if st.button(f"➕ Agregar", key=f"add_{row['Producto']}"):
                            # Agregamos al carrito
                            st.session_state['carrito'].append({"nombre": row['Producto'], "precio": p_valor})
                            st.toast(f"Agregado: {row['Producto']}")

    # --- 3. SECCIÓN DEL CARRITO (Sidebar o Abajo) ---
    st.divider()
    st.header("🛒 Tu Carrito")

    if len(st.session_state['carrito']) > 0:
        # Agrupar productos repetidos para mostrar "2x Hamburguesa"
        df_carrito = pd.DataFrame(st.session_state['carrito'])
        resumen = df_carrito.groupby('nombre').agg({'precio': ['count', 'sum']}).reset_index()
        resumen.columns = ['Producto', 'Cant', 'Subtotal']
        
        total_final = resumen['Subtotal'].sum()

        # Mostrar tabla del carrito
        for _, item in resumen.iterrows():
            st.write(f"🔹 {item['Cant']}x **{item['Producto']}** — ${item['Subtotal']:,.0f}")
        
        st.write(f"## Total: ${total_final:,.0f}")
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = []
            st.rerun()

        st.info(f"🏦 Alias: `{ALIAS_MP}`")

        # --- 4. ENVÍO A WHATSAPP ---
        detalle_pedido = ""
        for _, item in resumen.iterrows():
            detalle_pedido += f"✅ {item['Cant']}x {item['Producto']} (${item['Subtotal']:,.0f})\n"
        
        mensaje_wa = (
            f"¡Hola Caniche Food! 🐩\n\n"
            f"Este es mi pedido:\n"
            f"{detalle_pedido}\n"
            f"💰 *Total a pagar: ${total_final:,.0f}*\n\n"
            f"¿Me confirman el pedido?"
        )
        
        link_final = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(mensaje_wa)}"
        st.link_button("🚀 ENVIAR PEDIDO POR WHATSAPP", link_final, use_container_width=True)
    else:
        st.write("Tu carrito está vacío. ¡Elegí algo rico!")

else:
    st.error("Error al cargar el menú.")

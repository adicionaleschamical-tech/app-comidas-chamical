import streamlit as st
import pandas as pd
import urllib.parse

# --- CONFIGURACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000" # <-- CAMBIA POR TU CELULAR
ALIAS_MP = "caniche.food.mp"     # <-- TU ALIAS

st.set_page_config(page_title="Caniche Food", page_icon="🍕")

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- ESTILOS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; }
    .producto-card { border: 1px solid #ddd; padding: 10px; border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- APP ---
st.title("🍕 Caniche Food")
st.subheader("Hacé tu pedido online")

df = cargar_datos()

if not df.empty:
    # Filtrar solo lo que tenés hoy
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    # Pestañas por categoría
    categorias = list(df['Categoria'].unique())
    tabs = st.tabs(categorias)

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df[df['Categoria'] == cat]
            for _, row in items.iterrows():
                # Contenedor de producto
                with st.container():
                    col_img, col_info = st.columns([1.2, 1.8])
                    
                    with col_img:
                        img_url = row.get('Imagen')
                        if pd.notna(img_url):
                            st.image(img_url, use_container_width=True)
                    
                    with col_info:
                        st.markdown(f"### {row['Producto']}")
                        st.markdown(f"**${row['Precio']:,.0f}**")
                        
                        if st.button(f"Seleccionar {row['Producto']}", key=f"btn_{row['Producto']}"):
                            st.session_state['seleccionado'] = {"nombre": row['Producto'], "precio": row['Precio']}
                            st.toast(f"Agregaste {row['Producto']}")

    # --- CIERRE DE PEDIDO ---
    if 'seleccionado' in st.session_state:
        st.divider()
        st.header("🛒 Tu Pedido")
        prod = st.session_state['seleccionado']
        
        cant = st.number_input(f"¿Cuántos {prod['nombre']} querés?", min_value=1, value=1)
        total = prod['precio'] * cant
        notas = st.text_input("Notas (ej: sin cebolla, bien cocido)")
        
        st.info(f"💰 Total a pagar: **${total:,.0f}**\n\nAlias: `{ALIAS_MP}`")
        
        # WhatsApp Link
        msg = urllib.parse.quote(
            f"¡Hola! Quiero hacer un pedido:\n\n"
            f"✅ *{cant}x {prod['nombre']}*\n"
            f"📝 *Detalles:* {notas if notas else 'Sin notas'}\n"
            f"💰 *Total:* ${total:,.0f}"
        )
        link = f"https://wa.me/{NUMERO_WHATSAPP}?text={msg}"
        
        st.link_button("🚀 ENVIAR PEDIDO POR WHATSAPP", link, use_container_width=True)

else:
    st.error("No se pudo cargar el menú. Revisá tu Google Sheet.")

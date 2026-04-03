import streamlit as st
import pandas as pd
import urllib.parse

# --- CONFIGURACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000"  # <-- PONÉ TU NÚMERO AQUÍ (con código de país)
ALIAS_PAGO = "comida.rapida.mp"    # <-- TU ALIAS DE MERCADO PAGO

st.set_page_config(page_title="Menú Digital", page_icon="🍔", layout="centered")

# Función para cargar datos desde Google Sheets
@st.cache_data(ttl=300) # Guarda en memoria por 5 min para que sea más rápida
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        # Limpiamos nombres de columnas (quita espacios y errores de carga)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar con el menú: {e}")
        return pd.DataFrame()

# --- LÓGICA DE LA APP ---
st.title("🍔 Realizá tu Pedido")
st.write("Seleccioná tus productos y envianos el pedido por WhatsApp.")

df = cargar_datos()

if not df.empty:
    # 1. Filtrar solo productos disponibles
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    # 2. Selección de Categoría (Opcional)
    if 'Categoria' in df.columns:
        categorias = ["Todos"] + list(df['Categoria'].unique())
        cat_seleccionada = st.selectbox("¿Qué buscás hoy?", categorias)
        if cat_seleccionada != "Todos":
            df = df[df['Categoria'] == cat_seleccionada]

    # 3. Selección de Producto
    producto_lista = df['Producto'].tolist()
    seleccion = st.selectbox("Elegí un producto:", producto_lista)
    
    # Obtener el precio del producto elegido
    precio_unitario = df[df['Producto'] == seleccion]['Precio'].values[0]

    # 4. Personalización
    col1, col2 = st.columns(2)
    with col1:
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with col2:
        st.write(f"### Subtotal: \n ${precio_unitario * cantidad:,.0f}")

    notas = st.text_input("Notas adicionales", placeholder="Ej: Sin cebolla, extra mayonesa...")

    st.divider()

    # 5. Resumen y Pago
    total_final = precio_unitario * cantidad
    st.success(f"### Total a pagar: ${total_final:,.0f}")
    st.info(f"🏦 **Pagar al Alias:** {ALIAS_PAGO}")

    # 6. Botón de Envío
    texto_mensaje = (
        f"¡Hola! Quiero hacer un pedido:\n\n"
        f"✅ *{cantidad}x {seleccion}*\n"
        f"📝 *Notas:* {notas if notas else 'Ninguna'}\n"
        f"💰 *Total:* ${total_final:,.0f}\n\n"
        f"¿Me confirman el pedido?"
    )
    
    mensaje_url = urllib.parse.quote(texto_mensaje)
    link_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={mensaje_url}"

    if st.button("🚀 Confirmar Pedido por WhatsApp", use_container_width=True):
        st.markdown(f'<a href="{link_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:12px;border-radius:8px;text-align:center;font-weight:bold;">¡Hacé clic aquí para abrir WhatsApp!</div></a>', unsafe_allow_html=True)
        st.balloons()
else:
    st.warning("No hay productos disponibles en este momento. Volvé a intentar más tarde.")

st.caption("Desarrollado con Python y Streamlit")

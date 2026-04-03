import streamlit as st
import pandas as pd
import urllib.parse

# --- CONFIGURACIÓN ---
# Este es el link que me pasaste
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"

# Configuración visual de la App
st.set_page_config(page_title="Menú Digital", page_icon="🍔")

# --- FUNCIONES ---
def cargar_datos():
    try:
        # Leemos el CSV directamente desde Google
        df = pd.read_csv(SHEET_URL)
        # Limpiamos espacios en blanco en los nombres de columnas por las dudas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al conectar con el menú: {e}")
        return pd.DataFrame()

# --- LÓGICA DE LA APP ---
df_menu = cargar_datos()

if df_menu.empty:
    st.warning("No se encontraron productos. Verifica que la hoja de Google Sheets tenga datos y esté publicada.")
else:
    st.title("🍕 Realizá tu Pedido")
    st.write("Seleccioná tus productos y envíanos el pedido por WhatsApp.")

    # 1. Filtro por Categoría (Si tenés una columna 'Categoria')
    if 'Categoria' in df_menu.columns:
        categorias = df_menu['Categoria'].unique()
        cat_seleccionada = st.selectbox("¿Qué te gustaría comer?", categorias)
        productos_mostrar = df_menu[df_menu['Categoria'] == cat_seleccionada]
    else:
        productos_mostrar = df_menu

    # 2. Selección de Producto
    # Asumimos que las columnas se llaman 'Producto' y 'Precio'
    opciones = productos_mostrar['Producto'].tolist()
    seleccion = st.selectbox("Elegí un producto:", opciones)
    
    # Obtener el precio del producto elegido
    precio_unitario = productos_mostrar[productos_mostrar['Producto'] == seleccion]['Precio'].values[0]

    # 3. Extras y Personalización
    st.subheader("Personalización")
    cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
    notas = st.text_input("Notas (sin cebolla, punto de la carne, etc.)", placeholder="Ej: Sin aderezos")

    # 4. Totales
    total_final = precio_unitario * cantidad
    st.markdown(f"### Total a pagar: **${total_final:,}**")
    
    # Datos de pago (Podrías poner esto también en el Google Sheet)
    st.info("🏦 **Alias:** comida.rapida.mp \n\n Titular: Juan Pérez")

    # 5. Botón de Envío a WhatsApp
    numero_local = "5493804000000" # <--- CAMBIA ESTO POR TU NÚMERO (con código de país)
    
    mensaje = f"¡Hola! Quiero hacer un pedido:\n\n" \
              f"✅ *{cantidad}x {seleccion}*\n" \
              f"📝 *Notas:* {notas}\n" \
              f"💰 *Total:* ${total_final}\n\n" \
              f"¿Me confirman el pedido?"
    
    # Codificamos el mensaje para que sea válido en una URL
    mensaje_url = urllib.parse.quote(mensaje)
    link_wa = f"https://wa.me/{numero_local}?text={mensaje_url}"

    if st.button("🚀 Enviar Pedido por WhatsApp"):
        st.markdown(f'<a href="{link_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-align:center;">Abrir WhatsApp para confirmar</div></a>', unsafe_allow_html=True)

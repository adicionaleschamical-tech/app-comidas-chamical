import streamlit as st
import pandas as pd
import urllib.parse

# --- CONFIGURACIÓN ---
# Tu link de Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"

st.set_page_config(page_title="Menú Digital", page_icon="🍔")

# --- FUNCIÓN DE CARGA OPTIMIZADA ---
def cargar_datos():
    try:
        # Leemos el CSV y eliminamos filas vacías
        df = pd.read_csv(SHEET_URL).dropna(how='all')
        # Limpiamos los nombres de las columnas (quitamos espacios y pasamos a mayúscula la primera letra)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return pd.DataFrame()

# --- EJECUCIÓN ---
df_menu = cargar_datos()

# ESTO ES PARA DEBUREAR (Solo tú lo verás mientras lo arreglamos)
# st.write("Columnas detectadas:", df_menu.columns.tolist()) 

if df_menu.empty:
    st.error("⚠️ El sistema no detecta datos en el Excel.")
    st.info("Revisa que en el Excel la fila 1 tenga: Producto | Precio | Categoria")
    if st.button("Reintentar carga"):
        st.rerun()
else:
    st.title("🍔 Pedidos Online")
    
    # Verificamos que existan las columnas necesarias
    if 'Producto' in df_menu.columns and 'Precio' in df_menu.columns:
        
        # Agrupador por Categoría (si existe la columna)
        if 'Categoria' in df_menu.columns:
            lista_cat = df_menu['Categoria'].unique()
            elegir_cat = st.selectbox("Seleccioná una categoría", lista_cat)
            items = df_menu[df_menu['Categoria'] == elegir_cat]
        else:
            items = df_menu

        # Selección de producto
        seleccion = st.selectbox("¿Qué vas a pedir?", items['Producto'].tolist())
        
        # Obtener precio
        precio = items[items['Producto'] == seleccion]['Precio'].values[0]
        
        st.write(f"### Precio unitario: ${precio:,.2f}")
        
        cantidad = st.number_input("Cantidad", min_value=1, value=1)
        notas = st.text_input("Notas (ej: sin cebolla)")
        
        total = precio * cantidad
        st.subheader(f"Total: ${total:,.2f}")
        
        # Botón WhatsApp
        # Cambia el número por el tuyo (con código de país, ej: 549...)
        nro_tel = "5493804000000" 
        msg = urllib.parse.quote(f"Hola! Quiero pedir {cantidad} {seleccion}. Total: ${total}. Notas: {notas}")
        link = f"https://wa.me/{nro_tel}?text={msg}"
        
        if st.button("Confirmar Pedido"):
            st.markdown(f' <a href="{link}" target="_blank" style="text-decoration:none; color:white; background-color:green; padding:10px; border-radius:5px;">👉 Enviar a WhatsApp</a>', unsafe_allow_html=True)
    else:
        st.warning("Las columnas no tienen los nombres correctos (Producto, Precio).")

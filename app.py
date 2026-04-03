import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURACIÓN INICIAL ---
# Reemplaza con tu link de Google Sheets (formato CSV)
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000"  # <-- PONÉ TU CELULAR AQUÍ
ALIAS_MP = "caniche.food.mp"     # <-- TU ALIAS DE MERCADO PAGO

st.set_page_config(page_title="Caniche Food", page_icon="🍔", layout="centered")

# --- 2. FUNCIÓN PARA CARGAR DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        # Limpiamos nombres de columnas (quita espacios y asegura mayúscula inicial)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar con el menú: {e}")
        return pd.DataFrame()

# --- 3. ESTILOS VISUALES (CSS) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE LA APP ---
st.title("🍔 Caniche Food")
st.subheader("Hacé tu pedido online")

df = cargar_datos()

if not df.empty:
    # Filtrar solo productos que marcaste como "SI" en Disponible
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    # Crear pestañas por Categoría
    if 'Categoria' in df.columns:
        listado_cat = list(df['Categoria'].unique())
        tabs = st.tabs(listado_cat)

        for i, cat in enumerate(listado_cat):
            with tabs[i]:
                productos_cat = df[df['Categoria'] == cat]
                
                for _, row in productos_cat.iterrows():
                    # Contenedor para cada producto (Tarjeta)
                    with st.container(border=True):
                        # Definimos las columnas para Imagen e Info
                        col_img, col_info = st.columns([1.2, 1.8])
                        
                        with col_img:
                            img_url = row.get('Imagen')
                            if pd.notna(img_url) and str(img_url).startswith('http'):
                                st.image(img_url, use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                        
                        with col_info:
                            st.markdown(f"### {row['Producto']}")
                            
                            # Manejo de error en el Precio
                            try:
                                p_valor = float(row['Precio'])
                                st.markdown(f"**Precio: ${p_valor:,.0f}**")
                            except:
                                p_valor = 0.0
                                st.markdown(f"**Precio: {row['Precio']}**")

                            # Botón de selección
                            if st.button(f"Seleccionar {row['Producto']}", key=f"btn_{row['Producto']}"):
                                st.session_state['pedido_actual'] = {
                                    "nombre": row['Producto'],
                                    "precio": p_valor
                                }
                                st.toast(f"Agregaste {row['Producto']}")
                                st.rerun()

    # --- 5. SECCIÓN DE CIERRE (Solo aparece al elegir algo) ---
    if 'pedido_actual' in st.session_state:
        st.divider()
        st.header("📝 Confirmar Pedido")
        item = st.session_state['pedido_actual']
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            cant = st.number_input(f"¿Cuántos {item['nombre']}?", min_value=1, value=1)
        with col_res2:
            total = item['precio'] * cant
            st.write(f"### Total: ${total:,.0f}")
            
        notas = st.text_input("Detalles (ej: sin cebolla, bien cocido)")
        
        st.info(f"🏦 **Alias para transferencia:** `{ALIAS_MP}`")
        
        # Link de WhatsApp
        mensaje_texto = (
            f"¡Hola Caniche Food! 🐩\n\n"
            f"Quiero pedir: *{cant}x {item['nombre']}*\n"
            f"📝 *Detalles:* {notas if notas else 'Sin notas'}\n"
            f"💰 *Total:* ${total:,.0f}\n\n"
            f"¿Me confirman el pedido?"
        )
        
        msg_encoded = urllib.parse.quote(mensaje_texto)
        link_final = f"https://wa.me/{NUMERO_WHATSAPP}?text={msg_encoded}"
        
        st.link_button("🚀 ENVIAR PEDIDO POR WHATSAPP", link_final, use_container_width=True)

else:
    st.error("⚠️ No se pudo cargar el menú.")
    st.info("Revisá que el link de Google Sheets sea el correcto y la hoja tenga datos.")

st.divider()
st.caption("Chamical, La Rioja | 2026")

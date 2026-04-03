import streamlit as st
import pandas as pd
import urllib.parse
import re

# --- 1. CONFIGURACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000" # <-- CAMBIA POR TU NÚMERO
ALIAS_MP = "caniche.food.mp"

st.set_page_config(page_title="Caniche Food", page_icon="🍔")

# Inicializar carrito
if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- 2. FUNCIÓN DE LIMPIEZA DE PRECIOS ---
def limpiar_precio(valor):
    """Convierte cualquier texto sucio ($5.000, 5.000,00) en un número limpio (5000)"""
    if pd.isna(valor):
        return 0.0
    # Eliminar todo lo que no sea número o coma/punto decimal
    texto = re.sub(r'[^\d,.]', '', str(valor))
    # Si usaste coma para decimales (ej: 1500,50), la pasamos a punto
    if ',' in texto and '.' not in texto:
        texto = texto.replace(',', '.')
    # Si hay puntos de miles (ej: 5.000), los quitamos
    if '.' in texto and len(texto.split('.')[-1]) > 2:
        texto = texto.replace('.', '')
    
    try:
        return float(texto)
    except:
        return 0.0

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        # Aplicamos la limpieza a la columna Precio
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except:
        return pd.DataFrame()

# --- 3. LOGICA DE CONTROL ---
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

# --- 4. INTERFAZ ---
st.title("🍔 Caniche Food")
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
                    col_img, col_info, col_btns = st.columns([1, 1.5, 1])
                    
                    with col_img:
                        if pd.notna(row.get('Imagen')):
                            st.image(row['Imagen'], use_container_width=True)
                    
                    with col_info:
                        st.subheader(row['Producto'])
                        # Mostramos el precio ya limpio
                        st.write(f"**${row['Precio_Num']:,.0f}**")
                    
                    with col_btns:
                        # Control de cantidades
                        c_res, c_num, c_add = st.columns([1,1,1])
                        with c_add:
                            if st.button("➕", key=f"add_{row['Producto']}"):
                                modificar_cantidad(row['Producto'], row['Precio_Num'], "sumar")
                                st.rerun()
                        with c_num:
                            cant = st.session_state['carrito'].get(row['Producto'], {}).get('cant', 0)
                            st.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                        with c_res:
                            if st.button("➖", key=f"res_{row['Producto']}"):
                                modificar_cantidad(row['Producto'], row['Precio_Num'], "restar")
                                st.rerun()

    # --- 5. CARRITO ---
    st.divider()
    st.header("🛒 Tu Pedido")

    if st.session_state['carrito']:
        total_gral = 0
        detalle = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_gral += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            detalle += f"✅ {info['cant']}x {p} (${sub:,.0f})\n"

        st.markdown(f"## Total: ${total_gral:,.0f}")
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state['carrito'] = {}
            st.rerun()

        # Botón WhatsApp
        msj = urllib.parse.quote(f"¡Hola! Mi pedido:\n{detalle}\n💰 *Total: ${total_gral:,.0f}*")
        st.link_button("🚀 ENVIAR A WHATSAPP", f"https://wa.me/{NUMERO_WHATSAPP}?text={msj}", use_container_width=True)
    else:
        st.info("Sumá productos con el botón ➕")
else:
    st.error("Error al cargar el menú. Revisá el Google Sheet.")

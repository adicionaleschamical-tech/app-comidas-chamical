import streamlit as st
from config import cargar_config, cargar_productos, limpiar_precio, formatear_moneda
import pandas as pd

def apply_custom_theme():
    """Aplica tema personalizado"""
    config = cargar_config()
    primary = config.get('tema_primario', '#FF4B4B')
    secondary = config.get('tema_secundario', '#FF6B6B')
    background = config.get('background_color', '#FFFFFF')
    
    custom_css = f"""
    <style>
        .stButton > button {{
            background-color: {primary} !important;
            color: white !important;
            border-radius: 12px !important;
        }}
        h1, h2, h3 {{
            color: {primary} !important;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def mostrar_header():
    config = cargar_config()
    st.markdown(f"<h1 style='text-align: center;'>{config['icono']} {config['nombre_local']}</h1>", unsafe_allow_html=True)

def mostrar_productos():
    df = cargar_productos()
    if df.empty:
        st.warning("No hay productos")
        return
    
    for _, row in df.iterrows():
        with st.container():
            st.subheader(row['producto'])
            precio = limpiar_precio(row.get('precio', '0'))
            st.write(f"{formatear_moneda(precio)}")
            
            item_id = row['producto']
            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
            
            if st.button("➕ Agregar", key=f"add_{item_id}"):
                st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': precio}
                st.rerun()

def mostrar_productos_por_categoria(df, categoria):
    mostrar_productos()

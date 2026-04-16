import streamlit as st
from config import cargar_config, cargar_productos, limpiar_precio, formatear_moneda, obtener_categorias
import pandas as pd

def apply_custom_theme():
    """Aplica tema personalizado desde Google Sheets"""
    config = cargar_config()
    
    primary = config.get('tema_primario', '#FF4B4B')
    secondary = config.get('tema_secundario', '#FF6B6B')
    background = config.get('background_color', '#FFFFFF')
    font_family = config.get('font_family', "'Poppins', sans-serif")
    
    # CSS personalizado
    custom_css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');
        
        * {{
            font-family: {font_family} !important;
        }}
        
        .stApp {{
            background-color: {background} !important;
        }}
        
        .stButton > button {{
            background-color: {primary} !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            border: none !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            background-color: {secondary} !important;
        }}
        
        h1, h2, h3 {{
            color: {primary} !important;
            font-weight: 700 !important;
        }}
        
        div[data-testid="stContainer"] {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stContainer"]:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: transparent;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: {secondary}20;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {primary} !important;
            color: white !important;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }}
        
        .producto-card {{
            margin-bottom: 20px;
        }}
        
        .precio-producto {{
            font-size: 24px;
            font-weight: bold;
            color: {primary};
        }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def mostrar_header():
    """Muestra header personalizado"""
    config = cargar_config()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if config.get('logo_url') and config['logo_url']:
            st.image(config['logo_url'], use_container_width=True)
        else:
            st.markdown(f"<h1 style='text-align: center;'>{config['icono']} {config['nombre_local']}</h1>", unsafe_allow_html=True)
        
        if config.get('horario'):
            st.caption(f"🕒 {config['horario']}")
        if config.get('telefono'):
            st.caption(f"📱 {config['telefono']}")

def mostrar_productos():
    """Muestra productos agrupados por categoría"""
    df = cargar_productos()
    
    if df.empty:
        st.warning("No hay productos disponibles")
        return
    
    # Filtrar solo productos disponibles
    if 'disponible' in df.columns:
        df_disponibles = df[df['disponible'].str.upper() == 'SI']
    else:
        df_disponibles = df
    
    if df_disponibles.empty:
        st.warning("No hay productos disponibles momentáneamente")
        return
    
    # Obtener categorías
    categorias = df_disponibles['categoria'].unique()
    
    if len(categorias) > 1:
        tabs = st.tabs([f"{categoria}" for categoria in categorias])
        for tab, categoria in zip(tabs, categorias):
            with tab:
                mostrar_productos_por_categoria(df_disponibles, categoria)
    else:
        mostrar_productos_por_categoria(df_disponibles, categorias[0] if len(categorias) > 0 else None)

def mostrar_productos_por_categoria(df, categoria):
    """Muestra productos de una categoría específica"""
    productos_cat = df[df['categoria'] == categoria] if categoria else df
    
    for _, row in productos_cat.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                img_url = row.get('imagen', '')
                if pd.notna(img_url) and str(img_url).startswith('http'):
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
            
            with col2:
                st.subheader(row['producto'])
                
                # Procesar variedades
                variedades = str(row.get('variedades', 'Única')).split(';')
                ingredientes = str(row.get('ingredientes', '')).split(';') if pd.notna(row.get('ingredientes')) else []
                precios = str(row.get('precio', '0')).split(';')
                
                if len(variedades) > 1:
                    for i, var in enumerate(variedades):
                        precio = limpiar_precio(precios[i]) if i < len(precios) else 0
                        ing = ingredientes[i] if i < len(ingredientes) else ""
                        
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        with col_a:
                            st.markdown(f"**{var.strip()}**")
                            if ing:
                                st.caption(ing.strip())
                        with col_b:
                            st.markdown(f"**{formatear_moneda(precio)}**")
                        with col_c:
                            item_id = f"{row['producto']} ({var.strip()})"
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            
                            if st.button("➕", key=f"add_{item_id}"):
                                st.session_state.carrito[item_id] = {
                                    'cant': cant + 1,
                                    'precio': precio,
                                    'categoria': row['categoria']
                                }
                                st.rerun()
                            if cant > 0:
                                st.caption(f"Cant: {cant}")
                else:
                    precio = limpiar_precio(precios[0]) if precios else 0
                    ing = ingredientes[0] if ingredientes else ""
                    if ing:
                        st.info(f"✨ {ing}")
                    
                    col_a, col_b = st.columns([1, 1])
                    with col_a:
                        st.markdown(f"### {formatear_moneda(precio)}")
                    with col_b:
                        item_id = row['producto']
                        cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                        
                        if st.button("➕", key=f"add_{item_id}"):
                            st.session_state.carrito[item_id] = {
                                'cant': cant + 1,
                                'precio': precio,
                                'categoria': row['categoria']
                            }
                            st.rerun()
                        if cant > 0:
                            st.caption(f"En carrito: {cant}")

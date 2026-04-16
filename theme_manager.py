import streamlit as st
from config import cargar_config

def apply_custom_theme():
    """Aplica tema personalizado desde Google Sheets"""
    config = cargar_config()
    
    primary = config.get('tema_primario', '#FF4B4B')
    secondary = config.get('tema_secundario', '#FF6B6B')
    
    # CSS personalizado
    custom_css = f"""
    <style>
        /* Fuente personalizada */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        * {{
            font-family: '{config.get("font_family", "Poppins")}', sans-serif !important;
        }}
        
        /* Colores principales */
        .stApp {{
            background-color: {config.get('background_color', '#FFFFFF')};
        }}
        
        /* Botones principales */
        .stButton > button {{
            background-color: {primary} !important;
            color: white !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            background-color: {secondary} !important;
        }}
        
        /* Títulos */
        h1, h2, h3 {{
            color: {primary} !important;
            font-weight: 700 !important;
        }}
        
        /* Cards de productos */
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
        
        /* Pestañas (tabs) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
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
        
        /* Badges y etiquetas */
        .stAlert {{
            border-radius: 12px;
            border-left-color: {primary} !important;
        }}
        
        /* Animaciones */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stApp {{
            animation: fadeIn 0.5s ease-out;
        }}
        
        /* Footer personalizado */
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }}
        
        /* Loading spinner */
        .stSpinner > div {{
            border-color: {primary} !important;
        }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Configurar layout
    st.set_page_config(
        page_title=config.get('Nombre_Local', 'Mi Negocio'),
        page_icon=config.get('icono', '🍔'),
        layout="centered",
        initial_sidebar_state="collapsed"
    )

def mostrar_header():
    """Muestra header personalizado con logo"""
    config = cargar_config()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if config.get('logo_url'):
            st.image(config['logo_url'], use_container_width=True)
        else:
            st.markdown(f"<h1 style='text-align: center;'>🍔 {config['Nombre_Local']}</h1>", unsafe_allow_html=True)
        
        # Horario y contacto
        if config.get('horario'):
            st.caption(f"🕒 {config['horario']}")
        if config.get('whatsapp'):
            st.caption(f"📱 WhatsApp: {config['whatsapp']}")

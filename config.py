import streamlit as st
import requests
import pandas as pd
from io import StringIO
import time
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intentar cargar secrets
try:
    TELEGRAM_TOKEN = st.secrets["telegram"]["token"]
    TELEGRAM_CHAT_ID = st.secrets["telegram"]["chat_id"]
    ID_SHEET = st.secrets["sheets"]["id_sheet"]
    GID_CONFIG = st.secrets["sheets"]["gid_config"]
    GID_PRODUCTOS = st.secrets["sheets"]["gid_productos"]
    GID_PEDIDOS = st.secrets["sheets"]["gid_pedidos"]
except:
    # Fallback para desarrollo local
    TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
    TELEGRAM_CHAT_ID = "7860013984"
    ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
    GID_CONFIG = "612320365"
    GID_PRODUCTOS = "0"
    GID_PEDIDOS = "1395505058"

# URLs de Google Sheets
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

@st.cache_data(ttl=300)
def cargar_config():
    """Carga configuración del negocio desde Google Sheets"""
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), header=None)
        
        config = {}
        
        # Recorrer todas las filas del CSV
        for _, row in df.iterrows():
            if pd.notna(row[0]):  # Si la primera columna no está vacía
                key = str(row[0]).strip()
                value = str(row[1]).strip() if pd.notna(row[1]) else ""
                config[key] = value
        
        # Leer credenciales directamente (usando los nombres exactos de tu sheet)
        admin_dni = config.get('Admin_DNI', '')
        admin_pass = config.get('Admin_Pass', '')
        user = config.get('User', '')
        user_pass = config.get('User_Pass', '')
        
        # Si no se encontraron, intentar con mayúsculas/minúsculas
        if not admin_dni:
            admin_dni = config.get('admin_dni', '')
        if not admin_pass:
            admin_pass = config.get('admin_pass', '')
        if not user:
            user = config.get('user', '')
        if not user_pass:
            user_pass = config.get('user_pass', '')
        
        # Configuración del negocio
        config_nueva = {
            # Datos del negocio
            'nombre_local': config.get('Nombre_Local', 'Mi Negocio'),
            'logo_url': config.get('Logo_URL', ''),
            'direccion_local': config.get('Direccion_Local', ''),
            'alias': config.get('Alias', ''),
            'costo_delivery': limpiar_precio(config.get('Costo_Delivery', 0)),
            'telefono': config.get('Telefono', ''),
            'whatsapp': config.get('WhatsApp', ''),
            'horario': config.get('Horario', 'Lun-Dom: 19-24hs'),
            'icono': config.get('icono', '🍔'),
            
            # Credenciales
            'admin_dni': str(admin_dni).strip(),
            'admin_pass': str(admin_pass).strip(),
            'user': str(user).strip(),
            'user_pass': str(user_pass).strip(),
            
            # Modo mantenimiento (acepta "NO", "false", "False", etc.)
            'modo_mantenimiento': config.get('MODO_MANTENIMIENTO', 'false').upper() in ['SI', 'TRUE', 'YES', '1'],
            
            # Configuración visual
            'tema_primario': config.get('Tema_Primario', '#FF6B35'),
            'tema_secundario': config.get('Tema_Secundario', '#FF6B35'),
            'background_color': config.get('Background_Color', '#FFF8F0'),
            'font_family': config.get('Font_Family', "'Poppins', sans-serif'),
        }
        
        return config_nueva
        
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        # Retornar valores por defecto (con tus credenciales)
        return {
            'nombre_local': 'HAMBUR LOCOS',
            'costo_delivery': 500,
            'tema_primario': '#FF6B35',
            'tema_secundario': '#FF6B35',
            'modo_mantenimiento': False,
            'admin_dni': '30588807',
            'admin_pass': '124578',
            'user': 'usuario',
            'user_pass': 'usuario123',
            'telefono': '3826430724',
            'whatsapp': '3826430724',
            'horario': 'Lun-Dom 19:00 a 00:30',
            'direccion_local': 'AVDA. SAN FRANCISCO KM 4 1/2',
            'logo_url': '',
            'alias': 'tomas.jesus.banco',
            'icono': '🍔',
            'background_color': '#FFF8F0',
            'font_family': "'Poppins', sans-serif"
        }

@st.cache_data(ttl=60)
def cargar_productos():
    """Carga productos desde Google Sheets"""
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}", timeout=10)
        resp_p.raise_for_status()
        df_p = pd.read_csv(StringIO(resp_p.text))
        # Normalizar nombres de columnas a minúsculas
        df_p.columns = [c.strip().lower() for c in df_p.columns]
        return df_p
    except Exception as e:
        logger.error(f"Error cargando productos: {e}")
        return pd.DataFrame()

def limpiar_precio(texto):
    """Limpia formato de precio"""
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    # Eliminar puntos y comas
    texto_limpio = str(texto).replace('.', '').replace(',', '')
    # Extraer solo números
    numeros = re.findall(r'\d+', texto_limpio)
    return int(''.join(numeros)) if numeros else 0

def formatear_moneda(valor):
    """Formatea moneda al estilo argentino"""
    return f"$ {int(valor):,}".replace(",", ".")

def obtener_categorias(df):
    """Obtiene lista única de categorías"""
    if df.empty:
        return []
    if 'categoria' in df.columns:
        return df['categoria'].unique().tolist()
    return []

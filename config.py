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

# Intentar cargar secrets, si no existen usar valores por defecto
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
        
        for _, row in df.iterrows():
            if pd.notna(row[0]):
                key = str(row[0]).strip()
                value = str(row[1]).strip() if pd.notna(row[1]) else ""
                config[key] = value
        
        # Configuración del negocio
        config_nueva = {
            'nombre_local': config.get('Nombre_Local', 'Mi Negocio'),
            'logo_url': config.get('Logo_URL', ''),
            'direccion_local': config.get('Direccion_Local', ''),
            'alias': config.get('Alias', ''),
            'costo_delivery': limpiar_precio(config.get('Costo_Delivery', 0)),
            'telefono': config.get('Telefono', ''),
            'admin_dni': config.get('Admin_DNI', ''),
            'admin_pass_hash': config.get('Admin_Pass', ''),
            'user': config.get('User', 'admin'),
            'user_pass': config.get('User_Pass', 'admin123'),
            'modo_mantenimiento': config.get('MODO_MANTENIMIENTO', 'false').lower() == 'true',
            # Configuración visual
            'tema_primario': config.get('Tema_Primario', '#FF4B4B'),
            'tema_secundario': config.get('Tema_Secundario', '#FF6B6B'),
            'background_color': config.get('Background_Color', '#FFFFFF'),
            'font_family': config.get('Font_Family', "'Poppins', sans-serif"),
            'horario': config.get('Horario', 'Lun-Dom: 19-24hs'),
            'whatsapp': config.get('WhatsApp', ''),
            'icono': config.get('icono', '🍔')
        }
        
        return config_nueva
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        return {
            'nombre_local': 'Mi Negocio',
            'costo_delivery': 0,
            'tema_primario': '#FF4B4B',
            'tema_secundario': '#FF6B6B',
            'modo_mantenimiento': False
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
    texto_limpio = str(texto).replace('.', '').replace(',', '')
    numeros = re.findall(r'\d+', texto_limpio)
    return int(''.join(numeros)) if numeros else 0

def formatear_moneda(valor):
    """Formatea moneda al estilo argentino"""
    return f"$ {int(valor):,}".replace(",", ".")

def obtener_categorias(df):
    """Obtiene lista única de categorías"""
    if df.empty:
        return []
    return df['categoria'].unique().tolist()

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

# IDs de Google Sheets
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365"
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

# Tokens de Telegram
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# URLs de exportación directa (funcionan con compartir público)
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

def limpiar_precio(texto):
    """Limpia formato de precio - EVITA CONCATENACIÓN"""
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    
    texto_str = str(texto).strip()
    
    # Si ya es un número, devolverlo directamente
    if texto_str.isdigit():
        return int(texto_str)
    
    # Buscar números en el texto
    numeros = re.findall(r'\d+', texto_str)
    
    if numeros:
        # Tomar el número más largo (el verdadero precio)
        numeros_ordenados = sorted(numeros, key=len, reverse=True)
        return int(numeros_ordenados[0])
    
    return 0

def formatear_moneda(valor):
    try:
        return f"$ {int(valor):,}".replace(",", ".")
    except:
        return f"$ 0"

@st.cache_data(ttl=300)
def cargar_config():
    """Carga configuración del negocio desde Google Sheets"""
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        resp.raise_for_status()
        
        # Forzar codificación UTF-8
        resp.encoding = 'utf-8'
        df = pd.read_csv(StringIO(resp.text), header=None, encoding='utf-8')
        
        config = {}
        for _, row in df.iterrows():
            if pd.notna(row[0]):
                key = str(row[0]).strip()
                value = str(row[1]).strip() if pd.notna(row[1]) else ""
                config[key] = value
        
        # Obtener icono y limpiar si está corrupto
        icono_raw = config.get('icono', '🍔')
        if 'ð' in icono_raw or 'Ÿ' in icono_raw or 'Ã' in icono_raw or len(icono_raw) > 2:
            icono_raw = '🍔'
        
        return {
            'nombre_local': config.get('Nombre_Local', 'HAMBUR LOCOS'),
            'logo_url': config.get('Logo_URL', ''),
            'direccion_local': config.get('Direccion_Local', 'AVDA. SAN FRANCISCO KM 4 1/2'),
            'costo_delivery': limpiar_precio(config.get('Costo_Delivery', 500)),
            'telefono': config.get('Telefono', '3826430724'),
            'admin_dni': config.get('Admin_DNI', '30588807'),
            'admin_pass': config.get('Admin_Pass', '124578'),
            'user': config.get('User', 'usuario'),
            'user_pass': config.get('User_Pass', 'usuario123'),
            'modo_mantenimiento': config.get('MODO_MANTENIMIENTO', 'NO').upper() == 'SI',
            'tema_primario': config.get('Tema_Primario', '#FF6B35'),
            'tema_secundario': config.get('Tema_Secundario', '#FF6B35'),
            'horario': config.get('Horario', 'Lun-Dom 19:00 a 00:30'),
            'whatsapp': config.get('WhatsApp', '3826430724'),
            'icono': icono_raw,
            'background_color': config.get('Background_Color', '#FFF8F0'),
        }
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        return {
            'nombre_local': 'HAMBUR LOCOS',
            'costo_delivery': 500,
            'admin_dni': '30588807',
            'admin_pass': '124578',
            'user': 'usuario',
            'user_pass': 'usuario123',
            'telefono': '3826430724',
            'direccion_local': 'AVDA. SAN FRANCISCO KM 4 1/2',
            'modo_mantenimiento': False,
            'tema_primario': '#FF6B35',
            'tema_secundario': '#FF6B35',
            'horario': 'Lun-Dom 19:00 a 00:30',
            'whatsapp': '3826430724',
            'icono': '🍔',
            'background_color': '#FFF8F0',
        }

@st.cache_data(ttl=60)
def cargar_productos():
    """Carga productos desde Google Sheets"""
    try:
        resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}", timeout=10)
        resp_p.raise_for_status()
        resp_p.encoding = 'utf-8'
        df_p = pd.read_csv(StringIO(resp_p.text), encoding='utf-8')
        df_p.columns = [c.strip().lower() for c in df_p.columns]
        return df_p
    except Exception as e:
        logger.error(f"Error cargando productos: {e}")
        return pd.DataFrame()

def obtener_categorias(df):
    """Obtiene lista única de categorías"""
    if df.empty:
        return []
    if 'categoria' in df.columns:
        return df['categoria'].unique().tolist()
    return []

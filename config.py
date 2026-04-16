import streamlit as st
import requests
import pandas as pd
from io import StringIO
import time
import re

# Cargar secrets
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

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

@st.cache_data(ttl=300)
def cargar_config():
    """Carga configuración del negocio con caché y mejor manejo de errores"""
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
        
        # Configuración de personalización visual
        config['tema_primario'] = config.get('Tema Primario', '#FF4B4B')
        config['tema_secundario'] = config.get('Tema Secundario', '#FF6B6B')
        config['logo_url'] = config.get('Logo URL', '')
        config['horario'] = config.get('Horario', 'Lun-Dom: 19-24hs')
        config['whatsapp'] = config.get('WhatsApp', '')
        
        return config
    except Exception as e:
        st.error(f"Error al cargar configuración: {e}")
        return {
            'Nombre_Local': 'Mi Negocio',
            'Costo Delivery': '0',
            'tema_primario': '#FF4B4B',
            'tema_secundario': '#FF6B6B'
        }

def limpiar_precio(texto):
    """Limpia formato de precio más robusto"""
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    texto_limpio = str(texto).replace('.', '').replace(',', '')
    numeros = re.findall(r'\d+', texto_limpio)
    return int(''.join(numeros)) if numeros else 0

def formatear_moneda(valor):
    """Formatea moneda al estilo argentino"""
    return f"$ {int(valor):,}".replace(",", ".")

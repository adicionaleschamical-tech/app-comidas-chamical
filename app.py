import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
import json
from datetime import datetime
import threading

# ==================== CONFIGURACIÓN ====================
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwtcGVzIGbgJNo6Gmf92TkFEdDd8Okw_iO1yDhu_kzT2c9knUck34ecvgze48hXqWR4JQ/exec"

ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365"
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

TELEGRAM_TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es"
TELEGRAM_CHAT_ID = "7860013984"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# ==================== FUNCIONES GENERALES ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

def cargar_datos_sin_cache(url):
    try:
        timestamp = int(time.time() * 1000)
        resp = requests.get(f"{url}&_={timestamp}", timeout=10)
        resp.raise_for_status()
        contenido = resp.content.decode('utf-8-sig')
        return pd.read_csv(StringIO(contenido))
    except Exception as e:
        return pd.DataFrame()

def obtener_toda_configuracion():
    try:
        df = cargar_datos_sin_cache(URL_CONFIG)
        config = {}
        
        if df.empty:
            return config
        
        for i in range(len(df)):
            clave = str(df.iloc[i, 0]).strip()
            valor = str(df.iloc[i, 1]).strip() if len(df.columns) > 1 else ""
            
            if valor == "nan" or valor == "None":
                valor = ""
            
            valor = valor.replace("Â°", "°").replace("NÂ°", "N°")
            
            if clave and clave != "nan":
                config[clave] = valor
        
        return config
    except Exception as e:
        return {}

def obtener_valor_config(clave_exacta):
    config = obtener_toda_configuracion()
    
    if clave_exacta in config:
        valor = config[clave_exacta]
        return valor if valor and valor != "nan" else ""
    
    return ""

def obtener_nombre_local():
    nombre = obtener_valor_config("Nombre_Local")
    if nombre:
        return nombre
    return "MI NEGOCIO"

def verificar_credenciales(tipo, valor_ingresado):
    if tipo == "admin":
        pass_correcta = obtener_valor_config("Admin_Pass")
        dni_correcto = obtener_valor_config("Admin_DNI")
        
        if valor_ingresado == pass_correcta or valor_ingresado == dni_correcto:
            return "admin"
    
    elif tipo == "usuario":
        user_correcto = obtener_valor_config("User")
        pass_correcta = obtener_valor_config("User_Pass")
        
        if valor_ingresado == user_correcto or valor_ingresado == pass_correcta:
            return "usuario"
    
    return None

def esta_en_mantenimiento():
    modo = obtener_valor_config("MODO_MANTENIMIENTO")
    return modo.upper() == "SI"

def aplicar_tema():
    tema_primario = obtener_valor_config("Tema_Primario")
    if not tema_primario:
        tema_primario = "#FF6B35"
    
    tema_secundario = obtener_valor_config("Tema_Secundario")
    if not tema_secundario:
        tema_secundario = "#FF6B35"
    
    bg_color = obtener_valor_config("Background_Color")
    if not bg_color:
        bg_color = "#FFF8F0"
    
    font_family = obtener_valor_config("Font_Family")
    if not font_family:
        font_family = "'Poppins', sans-serif"
    
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {bg_color};
        }}
        .stButton > button {{
            background-color: {tema_primario};
            color: white;
            font-weight: bold;
        }}
        .stButton > button:hover {{
            background-color: {tema_secundario};
        }}
        .product-card {{
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: white;
        }}
        </style>
    """, unsafe_allow_html=True)

def mostrar_logo():
    logo_url = obtener_valor_config("Logo_URL")
    if logo_url and logo_url != "" and logo_url != "nan":
        try:
            st.image(logo_url, width=150)
        except:
            pass

def guardar_configuracion(parametro, valor):
    params = {
        "accion": "guardar_config",
        "parametro": parametro,
        "valor": valor
    }
    try:
        r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        return "OK" in r.text
    except:
        return False

def enviar_mensaje_telegram(mensaje, parse_mode="Markdown"):
    """Envía un mensaje de prueba a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": parse_mode
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

# ==================== POLLING PARA TELEGRAM ====================
def procesar_callback(callback_data, callback_id, message):
    """Procesa el callback cuando alguien presiona un botón"""
    partes = callback_data.split('_')
    
    if len(partes) >= 3 and partes[0] == 'est':
        nuevo_estado = partes[1]
        dni = partes[2]
        
        # Actualizar en Google Sheets
        params = {
            "accion": "actualizar_estado",
            "dni": dni,
            "estado": nuevo_estado
        }
        try:
            response = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
            if "OK" in response.text:
                # Responder al callback
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
                requests.post(url, json={"callback_query_id": callback_id, "text": f"✅ Pedido actualizado a: {nuevo_estado}"})
                
                # Editar mensaje para quitar botones
                nuevo_mensaje = message.get('text', '') + f"\n\n✅ *Estado actual: {nuevo_estado}*"
                url_edit = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
                requests.post(url_edit, json={
                    "chat_id": message['chat']['id'],
                    "message_id": message['message_id'],
                    "text": nuevo_mensaje,
                    "parse_mode": "Markdown"
                })
        except Exception as e:
            print(f"Error procesando callback: {e}")

def polling_telegram():
    """Revisa periódicamente si hay callbacks de Telegram"""
    ultimo_update_id = 0
    
    while True:
        try:
            # Obtener actualizaciones de Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": ultimo_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                for update in data['result']:
                    ultimo_update_id = update['update_id']
                    
                    # Procesar callback_query (botón presionado)
                    if 'callback_query' in update:
                        callback = update['callback_query']
                        procesar_callback(
                            callback.get('data', ''),
                            callback.get('id', ''),
                            callback.get('message', {})
                        )
        
        except Exception as e:
            print(f"Error en polling: {e}")
            time.sleep(5)

def iniciar_polling():
    """Inicia el polling en un hilo separado"""
    hilo = threading.Thread(target=polling_telegram, daemon=True)
    hilo.start()

# ==================== CLASE PEDIDO ====================
class PedidoManager:
    def registrar(self, dni, nombre, detalle, total, direccion):
        params = {
            "accion": "nuevo",
            "tel": dni,
            "nombre": nombre,
            "detalle": detalle,
            "total": total,
            "dir": direccion
        }
        try:
            r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
            return "OK" in r.text
        except:
            return False

    def notificar_telegram(self, nombre, dni, direccion, detalle, total):
        """Envía notificación a Telegram con botones inline"""
        # Limpiar caracteres especiales para Markdown
        detalle_limpio = str(detalle).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        
        total_formateado = formatear_moneda(total)
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "👨‍🍳 Preparando", "callback_data": f"est_Preparando_{dni}"},
                    {"text": "🛵 Enviado", "callback_data": f"est_Enviado_{dni}"}
                ],
                [
                    {"text": "✅ Finalizado", "callback_data": f"est_Finalizado_{dni}"}
                ]
            ]
        }
        
        msg = f"""🔔 *NUEVO PEDIDO*

👤 *{nombre}*
🆔 DNI: `{dni}`
📍 *Dirección:* {direccion}

📝 *Detalle del pedido:*

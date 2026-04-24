from flask import Flask, request, jsonify
import requests
import json
import re
import logging
import os
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
TELEGRAM_TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwtcGVzIGbgJNo6Gmf92TkFEdDd8Okw_iO1yDhu_kzT2c9knUck34ecvgze48hXqWR4JQ/exec"

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================== FUNCIONES ====================
def actualizar_estado_pedido(dni, nuevo_estado):
    """Actualiza el estado del pedido en Google Sheets"""
    try:
        params = {
            "accion": "actualizar_estado",
            "dni": dni,
            "estado": nuevo_estado
        }
        response = requests.get(URL_APPS_SCRIPT, params=params, timeout=15)
        logger.info(f"Actualizando estado {dni} -> {nuevo_estado}: {response.text}")
        return "OK" in response.text
    except Exception as e:
        logger.error(f"Error actualizando estado: {e}")
        return False

def responder_callback(callback_id, texto, mostrar_alerta=False):
    """Responde al callback de Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
        data = {
            "callback_query_id": callback_id,
            "text": texto,
            "show_alert": mostrar_alerta
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error respondiendo callback: {e}")
        return False

def editar_mensaje(chat_id, message_id, nuevo_texto):
    """Edita el mensaje original para quitar los botones"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": nuevo_texto,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error editando mensaje: {e}")
        return False

def enviar_menu_bienvenida(chat_id):
    """Envía mensaje de bienvenida con comandos disponibles"""
    mensaje = """
🤖 *Bot de Pedidos Activo*

Comandos disponibles:
/start - Mostrar este mensaje
/help - Ayuda

Los pedidos nuevos se notificarán automáticamente aquí.
Usa los botones para actualizar el estado de cada pedido.
"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Error enviando bienvenida: {e}")

def enviar_ayuda(chat_id):
    """Envía mensaje de ayuda"""
    mensaje = """
📖 *Ayuda del Bot*

• Cuando llega un nuevo pedido, recibirás un mensaje con botones
• Presiona el botón correspondiente para actualizar el estado del pedido
• Los estados disponibles son:
  - 👨‍🍳 Preparando
  - 🛵 Enviado  
  - ✅ Finalizado

• Cada vez que cambies el estado, se actualizará automáticamente en Google Sheets
"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Error enviando ayuda: {e}")

# ==================== WEBHOOK PRINCIPAL ====================
@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Maneja los callbacks de los botones de Telegram"""
    try:
        data = request.get_json()
        logger.info(f"Webhook recibido: {json.dumps(data, indent=2)}")
        
        # Procesar callback_query (cuando se presiona un botón)
        if 'callback_query' in data:
            callback = data['callback_query']
            callback_data = callback.get('data', '')
            callback_id = callback.get('id', '')
            message = callback.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            message_id = message.get('message_id')
            mensaje_original = message.get('text', '')
            
            # Parsear el callback_data: formato "est_Estado_DNI"
            # Ejemplo: "est_Preparando_12345678"
            partes = callback_data.split('_')
            
            if len(partes) >= 3 and partes[0] == 'est':
                nuevo_estado = partes[1]  # Preparando, Enviado, Finalizado
                dni = partes[2]
                
                logger.info(f"Procesando: DNI={dni}, Estado={nuevo_estado}")
                
                # Actualizar estado en Google Sheets
                if actualizar_estado_pedido(dni, nuevo_estado):
                    # Responder al callback (feedback visual al usuario)
                    responder_callback(callback_id, f"✅ Pedido actualizado a: {nuevo_estado}")
                    
                    # Editar mensaje original para quitar botones y mostrar nuevo estado
                    nuevo_mensaje = mensaje_original + f"\n\n✅ *Estado actual: {nuevo_estado}*"
                    editar_mensaje(chat_id, message_id, nuevo_mensaje)
                    
                    logger.info(f"Estado actualizado correctamente: {dni} -> {nuevo_estado}")
                else:
                    responder_callback(callback_id, "❌ Error al actualizar el estado", True)
                    logger.error(f"Error al actualizar estado: {dni} -> {nuevo_estado}")
            
            elif callback_data.startswith('ver_'):
                # Para botones de ver detalles (si los agregas)
                pedido_id = callback_data.replace('ver_', '')
                responder_callback(callback_id, f"📋 Detalles del pedido #{pedido_id}")
            
            else:
                logger.warning(f"Callback no reconocido: {callback_data}")
                responder_callback(callback_id, "Opción no válida")
        
        # Procesar mensajes normales (opcional)
        elif 'message' in data:
            message = data['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            if text == '/start':
                enviar_menu_bienvenida(chat_id)
            elif text == '/help':
                enviar_ayuda(chat_id)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ==================== RUTAS DE PRUEBA Y CONFIGURACIÓN ====================
@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar que el bot está funcionando"""
    return jsonify({
        "status": "ok",
        "message": "Telegram bot is running",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configura el webhook (ejecutar una vez)"""
    # Obtener la URL base desde el entorno o usar la que viene en la request
    base_url = request.headers.get('X-Forwarded-Host', request.host)
    if not base_url.startswith('https'):
        base_url = f"https://{base_url}"
    
    webhook_url = f"{base_url}/webhook/{TELEGRAM_TOKEN}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    data = {"url": webhook_url}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return jsonify(response.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    """Elimina el webhook (para debugging)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
    try:
        response = requests.post(url, timeout=10)
        return jsonify(response.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_webhook_info', methods=['GET'])
def get_webhook_info():
    """Obtiene información del webhook actual"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=10)
        return jsonify(response.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== INICIO ====================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

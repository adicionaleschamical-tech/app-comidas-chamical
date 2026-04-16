import requests
import json
import logging
from datetime import datetime
import streamlit as st
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, URL_APPS_SCRIPT

logger = logging.getLogger(__name__)

class PedidoManager:
    def __init__(self):
        self.url_apps_script = URL_APPS_SCRIPT
        self.telegram_token = TELEGRAM_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
    
    def registrar_pedido(self, dni, nombre, detalle, total, direccion):
        """Registra pedido en Google Sheets"""
        try:
            params = {
                "accion": "nuevo",
                "tel": dni,
                "nombre": nombre,
                "detalle": detalle,
                "total": total,
                "dir": direccion
            }
            response = requests.get(self.url_apps_script, params=params, timeout=10)
            response.raise_for_status()
            logger.info(f"Pedido registrado - DNI: {dni}, Total: {total}")
            return True
        except Exception as e:
            logger.error(f"Error registrando pedido: {e}")
            st.error("Error al registrar el pedido. Por favor intentá nuevamente.")
            return False
    
    def enviar_notificacion(self, nombre, dni, direccion, detalle, total, formatear_moneda_func):
        """Envía notificación a Telegram con botones interactivos"""
        try:
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Aceptar", "callback_data": f"est_Preparando_{dni}"},
                        {"text": "🛵 En Camino", "callback_data": f"est_Enviado_{dni}"},
                        {"text": "🏁 Listo", "callback_data": f"est_Listo_{dni}"}
                    ],
                    [
                        {"text": "❌ Cancelar", "callback_data": f"est_Cancelado_{dni}"}
                    ]
                ]
            }
            
            msg = (
                f"🔔 *NUEVO PEDIDO*\n\n"
                f"👤 *Cliente:* {nombre}\n"
                f"🆔 *DNI:* {dni}\n"
                f"📍 *Dirección:* {direccion}\n\n"
                f"*Detalle:*\n{detalle}\n\n"
                f"💰 *TOTAL: {formatear_moneda_func(total)}*\n"
                f"🕒 *Hora:* {datetime.now().strftime('%H:%M:%S')}"
            )
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                data={
                    "chat_id": self.telegram_chat_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(keyboard)
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Notificación enviada a Telegram - DNI: {dni}")
            return True
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
            st.error("Error al enviar notificación al local")
            return False

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
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    def enviar_notificacion(self, nombre, dni, direccion, detalle, total, formatear_func):
        try:
            msg = f"🔔 NUEVO PEDIDO\n\nCliente: {nombre}\nDNI: {dni}\nDirección: {direccion}\n\nDetalle:\n{detalle}\n\nTOTAL: {formatear_func(total)}"
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                data={"chat_id": self.telegram_chat_id, "text": msg}
            )
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

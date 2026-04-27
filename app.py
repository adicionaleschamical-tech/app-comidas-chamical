import streamlit as st
import requests

# --- CONFIGURACIÓN ---
# Reemplaza con tu URL de Google Apps Script (la de la implementación)
URL_GOOGLE_SCRIPT = "TU_URL_DE_APPS_SCRIPT_AQUI"
# Reemplaza con tu Token de BotFather
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
# Reemplaza con tu ID de Chat (donde llegan los pedidos)
TELEGRAM_CHAT_ID = "6168988457"

def enviar_pedido_a_google(datos):
    """Envía los datos al doGet de Google Apps Script"""
    try:
        response = requests.get(URL_GOOGLE_SCRIPT, params=datos)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False

def notificar_telegram(datos):
    """Envía el mensaje con botones a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    dni = datos.get("tel") # Usamos el DNI/Tel como identificador único
    
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO!*\n\n"
        f"👤 *Cliente:* {datos['nombre']}\n"
        f"🆔 *DNI/Tel:* {dni}\n"
        f"📍 *Dirección:* {datos['dir']}\n"
        f"📝 *Detalle:* {datos['detalle']}\n"
        f"💰 *Total:* ${datos['total']}\n"
        f"---------------------------\n"
        f"Cambiar estado:"
    )

    # Estos callback_data deben coincidir con lo que espera el Google Apps Script
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

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Error al notificar por Telegram: {e}")

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Sistema de Pedidos", page_icon="🍕")

st.title("🍕 Realizá tu Pedido")
st.write("Completá los datos para procesar tu compra.")

with st.form("form_pedido", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo")
    dni_tel = st.text_input("DNI o Teléfono (Sin puntos ni espacios)")
    direccion = st.text_input("Dirección de Entrega")
    detalle = st.text_area("¿Qué vas a pedir?")
    total = st.number_input("Total a pagar", min_value=0)
    
    boton_enviar = st.form_submit_button("Confirmar Pedido")

if boton_enviar:
    if nombre and dni_tel and direccion and detalle:
        datos_pedido = {
            "accion": "nuevo",
            "nombre": nombre,
            "tel": dni_tel,
            "dir": direccion,
            "detalle": detalle,
            "total": total
        }
        
        with st.spinner("Procesando..."):
            # 1. Guardar en Google Sheets
            exito_sheet = enviar_pedido_a_google(datos_pedido)
            
            # 2. Enviar alerta a Telegram
            if exito_sheet:
                notificar_telegram(datos_pedido)
                st.success("¡Pedido enviado con éxito! Ya lo estamos procesando.")
            else:
                st.error("Hubo un problema al guardar el pedido. Reintentá.")
    else:
        st.warning("Por favor, completá todos los campos.")

# --- MANTENIMIENTO ---
# (Opcional) Mostrar si el sistema está en mantenimiento según la lógica de tu Sheets
# st.sidebar.info("Estado del Sistema: Operativo")

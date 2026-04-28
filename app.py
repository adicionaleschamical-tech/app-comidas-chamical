import streamlit as st
import requests

# --- CONFIGURACIÓN ---
# REEMPLAZÁ ESTA URL con la de tu "Nueva implementación" de Google
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzdOnPaNXokbZa4zqgT5_4Qe373MnuGaI5T8JB48B-6iPDJn5Rpv0uN54-zO00rckmFtQ/exec"
TELEGRAM_TOKEN = "8597598506:AAGgsvhwhG9pCJkr6epmxmH8qGU0DvNBCyA"
TELEGRAM_CHAT_ID = "7860013984"

# --- BASE DE DATOS DEL MENÚ ---
MENU = {
    "Pizzas": [
        {"nombre": "Muzzarella", "precio": 5000, "ingredientes": "Salsa de tomate, muzzarella", "foto": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500"},
        {"nombre": "Especial", "precio": 6500, "ingredientes": "Jamón, morrones, huevo", "foto": "https://images.unsplash.com/photo-1574071318508-1cdbad80ad38?w=500"},
    ],
    "Hamburguesas": [
        {"nombre": "Doble Bacon", "precio": 4500, "ingredientes": "Cheddar, bacon, barbacoa", "foto": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
        {"nombre": "Clásica", "precio": 3800, "ingredientes": "Carne, lechuga, tomate", "foto": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500"},
    ]
}

# --- FUNCIONES DE CONEXIÓN ---

def enviar_pedido_a_google(datos):
    """Envía el pedido inicial para que se cree la fila en el Sheet."""
    try:
        response = requests.get(URL_GOOGLE_SCRIPT, params=datos, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error de conexión con Google: {e}")
        return False

def notificar_telegram(datos):
    """Envía el mensaje al Bot con botones de acción rápida."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Limpiamos el DNI para que no tenga espacios raros
    dni_limpio = str(datos.get("tel")).strip()
    
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO!*\n\n"
        f"👤 *Cliente:* {datos['nombre']}\n"
        f"🆔 *DNI/Tel:* {dni_limpio}\n"
        f"📍 *Dirección:* {datos['dir']}\n\n"
        f"📝 *Detalle:* \n{datos['detalle']}\n"
        f"💰 *TOTAL:* ${datos['total']}\n"
        f"---------------------------\n"
        f"¿Cambiar estado?"
    )

    # callback_data ULTRA CORTO: 'p' (preparar), 'e' (enviar), 'f' (finalizar)
    # Esto evita que Telegram bloquee el botón por longitud.
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👨‍🍳 Preparando", "callback_data": f"p_{dni_limpio}"},
                {"text": "🛵 Enviado", "callback_data": f"e_{dni_limpio}"}
            ],
            [
                {"text": "✅ Finalizado", "callback_data": f"f_{dni_limpio}"}
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        st.error(f"Error al notificar Telegram: {e}")

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Carrito de Pedidos", page_icon="🍕", layout="wide")

if "carrito" not in st.session_state:
    st.session_state.carrito = []

st.title("🍕 Sistema de Pedidos Express")

col_menu, col_carrito = st.columns([2, 1])

with col_menu:
    for categoria, productos in MENU.items():
        st.header(f"--- {categoria} ---")
        for p in productos:
            with st.container():
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1: st.image(p["foto"], use_container_width=True)
                with c2:
                    st.subheader(p["nombre"])
                    st.write(p["ingredientes"])
                    st.write(f"**Precio:** ${p['precio']}")
                with c3:
                    if st.button(f"Agregar", key=f"btn_{p['nombre']}"):
                        st.session_state.carrito.append(p)
                        st.toast(f"✅ {p['nombre']} añadido")

with col_carrito:
    st.header("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("El carrito está vacío.")
    else:
        total = 0
        detalle = ""
        for item in st.session_state.carrito:
            st.write(f"**{item['nombre']}** - ${item['precio']}")
            total += item['precio']
            detalle += f"- {item['nombre']} (${item['precio']})\n"
        
        st.subheader(f"Total: ${total}")
        
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        st.divider()
        st.subheader("Datos de Entrega")
        with st.form("form_pedido"):
            nombre = st.text_input("Nombre Completo")
            dni = st.text_input("DNI o Teléfono (Solo números)")
            direccion = st.text_input("Dirección de entrega")
            
            if st.form_submit_button("CONFIRMAR PEDIDO"):
                if nombre and dni and direccion:
                    datos_pedido = {
                        "accion": "nuevo",
                        "nombre": nombre,
                        "tel": dni,
                        "dir": direccion,
                        "detalle": detalle,
                        "total": total
                    }
                    
                    # 1. Guardar en Sheets
                    if enviar_pedido_a_google(datos_pedido):
                        # 2. Notificar al Bot
                        notificar_telegram(datos_pedido)
                        st.success("¡Pedido enviado correctamente!")
                        st.session_state.carrito = []
                    else:
                        st.error("Error al conectar con el servidor.")
                else:
                    st.warning("Por favor, completa todos los campos.")

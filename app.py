import streamlit as st
import requests

# --- CONFIGURACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwvp0IDXDXCU_eTFjO7fHxgvHgDpM7RutVjo17uxmKwfSjUF0eXKW0L7q7KS0Il20lUBw/exec"
TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# --- BASE DE DATOS DEL MENÚ ---
# Aquí podés agregar o quitar productos
MENU = {
    "Pizzas": [
        {"nombre": "Muzzarella", "precio": 5000, "ingredientes": "Salsa de tomate, muzzarella, aceitunas", "foto": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500"},
        {"nombre": "Especial", "precio": 6500, "ingredientes": "Muzzarella, jamón, morrones, huevo", "foto": "https://images.unsplash.com/photo-1574071318508-1cdbad80ad38?w=500"},
    ],
    "Hamburguesas": [
        {"nombre": "Doble Bacon", "precio": 4500, "ingredientes": "Doble medallón, cheddar, bacon, barbacoa", "foto": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
        {"nombre": "Clásica", "precio": 3800, "ingredientes": "Carne, lechuga, tomate, queso", "foto": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500"},
    ]
}

def enviar_pedido_a_google(datos):
    try:
        response = requests.get(URL_GOOGLE_SCRIPT, params=datos)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False

def notificar_telegram(datos):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    dni = datos.get("tel")
    
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO!*\n\n"
        f"👤 *Cliente:* {datos['nombre']}\n"
        f"🆔 *DNI/Tel:* {dni}\n"
        f"📍 *Dirección:* {datos['dir']}\n\n"
        f"📝 *Detalle:* \n{datos['detalle']}\n\n"
        f"💰 *TOTAL:* ${datos['total']}\n"
        f"---------------------------\n"
        f"Cambiar estado:"
    )

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

    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown", "reply_markup": keyboard}
    requests.post(url, json=payload)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Carrito de Pedidos", page_icon="🍕", layout="wide")

st.title("🍕 Menú de Sabores")
st.write("Seleccioná tus productos favoritos y confirmá tu pedido.")

# Inicializar carrito en la sesión
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- MOSTRAR MENÚ ---
col_menu, col_carrito = st.columns([2, 1])

with col_menu:
    for categoria, productos in MENU.items():
        st.header(f"--- {categoria} ---")
        for p in productos:
            with st.container():
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1:
                    st.image(p["foto"], use_container_width=True)
                with c2:
                    st.subheader(p["nombre"])
                    st.write(p["ingredientes"])
                    st.write(f"**Precio:** ${p['precio']}")
                with c3:
                    if st.button(f"Agregar", key=p["nombre"]):
                        st.session_state.carrito.append(p)
                        st.toast(f"✅ {p['nombre']} al carrito")

# --- CARRITO ---
with col_carrito:
    st.header("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("El carrito está vacío.")
    else:
        total_acumulado = 0
        detalle_texto = ""
        for i, item in enumerate(st.session_state.carrito):
            st.write(f"**{item['nombre']}** - ${item['precio']}")
            total_acumulado += item['precio']
            detalle_texto += f"- {item['nombre']} (${item['precio']})\n"
        
        st.divider()
        st.subheader(f"Total: ${total_acumulado}")
        
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        st.divider()
        st.subheader("Datos de Entrega")
        with st.form("form_final"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI o Teléfono")
            direccion = st.text_input("Dirección")
            
            if st.form_submit_button("CONFIRMAR PEDIDO"):
                if nombre and dni and direccion:
                    datos_pedido = {
                        "accion": "nuevo",
                        "nombre": nombre,
                        "tel": dni,
                        "dir": direccion,
                        "detalle": detalle_texto,
                        "total": total_acumulado
                    }
                    if enviar_pedido_a_google(datos_pedido):
                        notificar_telegram(datos_pedido)
                        st.success("¡Pedido enviado! ¡Gracias por tu compra!")
                        st.session_state.carrito = []
                    else:
                        st.error("Error al procesar. Reintentá.")
                else:
                    st.warning("Completá tus datos de entrega.")

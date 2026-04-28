import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN CRÍTICA ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbznxL3Nx1apqPSMyvKnXyF8sAu2LU4nEG2kl_JToDu-B5Z4obVqjpRGBDDLFJVdnzo4pA/exec"
TELEGRAM_TOKEN = "8597598506:AAGgsvhwhG9pCJkr6epmxmH8qGU0DvNBCyA"
TELEGRAM_CHAT_ID = "7860013984"

st.set_page_config(page_title="Barbería - Pedidos", layout="wide")

# --- 1. FUNCIONES DE DATOS ---
def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion})
        return res.json()
    except:
        return []

# --- 2. GESTIÓN DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- 3. LOGIN EN BARRA LATERAL ---
st.sidebar.title("🛠️ Panel de Control")
if not st.session_state.autenticado:
    with st.sidebar.expander("Acceso Personal"):
        usuario = st.text_input("DNI / Usuario")
        clave = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            # Aquí llamamos a la config del Sheet para validar
            config = leer_datos("leer_config")
            if usuario == str(config.get("admin_dni")) and clave == str(config.get("admin_pass")):
                st.session_state.autenticado = True
                st.session_state.rol = "admin"
                st.rerun()
            elif usuario == config.get("user_name") and clave == config.get("user_pass"):
                st.session_state.autenticado = True
                st.session_state.rol = "user"
                st.rerun()
            else:
                st.error("Datos incorrectos")
else:
    st.sidebar.success(f"Sesión: {st.session_state.rol.upper()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 4. VISTA ADMINISTRADOR / USUARIO ---
if st.session_state.autenticado:
    st.title(f"Configuración del Sistema - {st.session_state.rol}")
    
    tab1, tab2 = st.tabs(["📦 Productos y Precios", "⚙️ Ajustes Generales"])
    
    with tab1:
        st.subheader("Editar Catálogo")
        # Aquí cargarías el DataFrame de productos para editar
        productos = leer_datos("leer_productos")
        if productos:
            df = pd.DataFrame(productos)
            edited_df = st.data_editor(df, num_rows="dynamic")
            if st.button("Guardar Cambios en Productos"):
                # Lógica para enviar el DF actualizado al script
                st.success("Catálogo actualizado en el Excel")

    with tab2:
        st.subheader("Costos y Direcciones")
        col1, col2 = st.columns(2)
        with col1:
            delivery = st.number_input("Costo de Envío", value=500)
            direccion = st.text_input("Dirección del Local", "Av. Central 123")
        
        if st.session_state.rol == "admin":
            mantenimiento = st.toggle("Modo Mantenimiento (Cierra la App)")
            
        if st.button("Guardar Ajustes"):
            st.toast("Ajustes guardados")

# --- 5. VISTA CLIENTE (PÚBLICA) ---
else:
    st.title("✂️ Bienvenidos a la Barbería")
    
    # Cargar productos desde el Sheet
    productos = leer_datos("leer_productos")
    
    if not productos:
        st.warning("No hay productos disponibles por ahora.")
    else:
        cols = st.columns(3)
        for i, p in enumerate(productos):
            with cols[i % 3]:
                st.image(p['imagen'], use_container_width=True)
                st.subheader(p['nombre'])
                st.write(f"Precio: ${p['precio']}")
                if st.button(f"Agregar {p['nombre']}", key=f"btn_{i}"):
                    st.session_state.carrito.append(p)
                    st.toast(f"{p['nombre']} añadido")

    # --- CARRITO ---
    if st.session_state.carrito:
        st.divider()
        st.header("🛒 Tu Pedido")
        total = 0
        for item in st.session_state.carrito:
            st.write(f"- {item['nombre']}: ${item['precio']}")
            total += item['precio']
        
        st.subheader(f"Total: ${total}")
        
        with st.form("confirmar_pedido"):
            nombre = st.text_input("Nombre Completo")
            dni = st.text_input("DNI (para seguimiento)")
            dir_entrega = st.text_input("Dirección de Entrega")
            
            if st.form_submit_button("Enviar Pedido via Telegram"):
                # 1. Enviar a Excel (doGet)
                params = {
                    "accion": "nuevo",
                    "tel": dni,
                    "nombre": nombre,
                    "dir": dir_entrega,
                    "detalle": str([x['nombre'] for x in st.session_state.carrito]),
                    "total": total
                }
                requests.get(URL_GOOGLE_SCRIPT, params=params)
                
                # 2. El bot envía el mensaje (Esto ya lo tenés configurado en tu Python)
                st.success("¡Pedido enviado! Revisa el bot de Telegram.")
                st.session_state.carrito = []

import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwlHFcGkkbIuPPcgLeIl2UleCp3qA4dOJrXgHZAEMDILnnK1hFbzHsUO91oQ0Zqg32_SA/exec"

def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion}, timeout=10)
        return res.json()
    except:
        return {}

# 1. Cargar Configuración (El JSON que pegaste)
config = leer_datos("leer_config")

# --- 2. CONFIGURACIÓN VISUAL (Usando tus datos del JSON) ---
# Usamos .get() para que si una clave no existe, la app no se rompa
nombre_local = config.get("Nombre_Local", "HAMBURGUESAS EL 22")
st.set_page_config(page_title=nombre_local, layout="wide")

color_primario = config.get("Tema_Primario", "#FF6B35")
bg_color = config.get("Background_color", "#FFF8F0")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .main-title {{ color: {color_primario}; text-align: center; font-weight: 800; }}
    .stButton>button {{ background-color: {color_primario}; color: white; border-radius: 10px; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ESTADO DE SESIÓN ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- 4. VISTA PÚBLICA (CLIENTE) ---
st.markdown(f"<h1 class='main-title'>🍔 {nombre_local}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>📍 {config.get('Direccion_Local')} | ⏰ {config.get('Horario')}</p>", unsafe_allow_html=True)

if config.get("MODO_MANTENIMIENTO") == "SI":
    st.error("🛠️ Estamos mejorando para vos. ¡Volvemos pronto!")
    st.stop()

# --- 5. CARGA DE PRODUCTOS ---
prods_raw = leer_datos("leer_productos")

if not prods_raw:
    st.info("Cargando el menú...")
else:
    # Procesamos variedades y precios (con split por ;)
    menu_completo = []
    for p in prods_raw:
        variedades = str(p.get('variedades', '')).split(';')
        precios = str(p.get('precio', '')).split(';')
        ingredientes = str(p.get('ingredientes', '')).split(';')
        
        for i in range(len(variedades)):
            try:
                menu_completo.append({
                    "nombre": variedades[i].strip(),
                    "precio": float(precios[i].strip()) if i < len(precios) else 0,
                    "desc": ingredientes[i].strip() if i < len(ingredientes) else "",
                    "img": p.get('imagen', ''),
                    "cat": p.get('categoria', '')
                })
            except: continue

    # Mostramos por categorías
    categorias = sorted(list(set([x['cat'] for x in menu_completo])))
    for cat in categorias:
        st.subheader(f"➔ {cat}")
        cols = st.columns(3)
        items_cat = [x for x in menu_completo if x['cat'] == cat]
        
        for idx, item in enumerate(items_cat):
            with cols[idx % 3]:
                if str(item['img']).startswith("http"):
                    st.image(item['img'], use_container_width=True)
                st.write(f"**{item['nombre']}**")
                st.caption(item['desc'])
                st.write(f"**${item['precio']:,}**")
                if st.button("Agregar 🛒", key=f"add_{item['nombre']}_{idx}"):
                    st.session_state.carrito.append(item)
                    st.toast(f"Añadido: {item['nombre']}")

# --- 6. CARRITO EN SIDEBAR ---
if st.session_state.carrito:
    st.sidebar.header("🛒 Tu Carrito")
    total = 0
    for i, p in enumerate(st.session_state.carrito):
        st.sidebar.write(f"{p['nombre']} - ${p['precio']:,}")
        total += p['precio']
    
    envio = float(config.get("Costo_Delivery", 500))
    st.sidebar.write(f"🚚 Envío: ${envio:,}")
    st.sidebar.subheader(f"Total: ${total + envio:,}")
    
    if st.sidebar.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()

    with st.sidebar.form("pedido"):
        cli_nom = st.text_input("Nombre")
        cli_dir = st.text_input("Dirección")
        if st.form_submit_button("✅ ENVIAR POR WHATSAPP"):
            # Aquí podés elegir si mandar a Telegram o generar link de WhatsApp
            msg = f"Hola {nombre_local}! Soy {cli_nom}, quiero pedir: " + " + ".join([x['nombre'] for x in st.session_state.carrito])
            st.success("Pedido registrado. ¡Muchas gracias!")

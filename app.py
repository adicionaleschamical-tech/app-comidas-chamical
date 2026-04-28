import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyyIyOtzYzgMjfdFDcdouI_x1w2mG5JeicwdVExuKzFhWWNlyx9xTNsS_dEvtrGXhwOwQ/exec"

def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion}, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# 1. Cargar Configuración
config_raw = leer_datos("leer_config")

if "error" in config_raw or not config_raw:
    st.error("No se pudo cargar la configuración. Revisa el Google Script.")
    st.stop()

# Normalizar claves de Config a minúsculas para evitar errores
config = {str(k).lower().strip(): v for k, v in config_raw.items()}

# --- 2. CONFIGURACIÓN VISUAL ---
nombre_local = config.get("nombre_local", "HAMBURGUESAS EL 22")
st.set_page_config(page_title=nombre_local, layout="wide")

color_p = config.get("tema_primario", "#FF6B35")
bg_c = config.get("background_color", "#FFF8F0")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_c}; }}
    .main-title {{ color: {color_p}; text-align: center; font-weight: 800; font-size: 2.5rem; margin-bottom:0; }}
    .stButton>button {{ background-color: {color_p}; color: white; border-radius: 10px; width: 100%; border: none; }}
    .card {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ENCABEZADO ---
st.markdown(f"<h1 class='main-title'>🍔 {nombre_local}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>📍 {config.get('direccion_local', '')} | ⏰ {config.get('horario', '')}</p>", unsafe_allow_html=True)

if config.get("modo_mantenimiento") == "SI":
    st.warning("🛠️ Estamos en mantenimiento. Volvemos pronto.")
    st.stop()

# --- 4. CARGA Y PROCESAMIENTO DE PRODUCTOS ---
prods_raw = leer_datos("leer_productos")

if isinstance(prods_raw, dict) and "error" in prods_raw:
    st.error("Error al cargar productos. Revisa que la pestaña se llame 'Productos'.")
else:
    menu_final = []
    for p in prods_raw:
        # Normalizamos las claves del producto para que no importe mayúsculas/minúsculas
        p_norm = {str(k).lower().strip(): v for k, v in p.items()}
        
        variedades = str(p_norm.get('variedades', '')).split(';')
        precios = str(p_norm.get('precio', '')).split(';')
        ingredientes = str(p_norm.get('ingredientes', '')).split(';')
        
        for i in range(len(variedades)):
            try:
                nombre_v = variedades[i].strip()
                if nombre_v:
                    menu_final.append({
                        "nombre": nombre_v,
                        "precio": float(precios[i].strip()) if i < len(precios) else 0,
                        "desc": ingredientes[i].strip() if i < len(ingredientes) else "",
                        "img": p_norm.get('imagen', ''),
                        "cat": p_norm.get('categoria', 'Otros')
                    })
            except: continue

    if not menu_final:
        st.info("No hay productos disponibles en este momento.")
    else:
        # Mostrar por Categorías
        categorias = sorted(list(set([x['cat'] for x in menu_final])))
        for cat in categorias:
            st.markdown(f"### ➔ {cat}")
            cols = st.columns(3)
            items_cat = [x for x in menu_final if x['cat'] == cat]
            
            for idx, item in enumerate(items_cat):
                with cols[idx % 3]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if str(item['img']).startswith("http"):
                        st.image(item['img'], use_container_width=True)
                    st.write(f"**{item['nombre']}**")
                    if item['desc']:
                        st.caption(item['desc'])
                    st.write(f"### **${item['precio']:,}**")
                    if st.button("Añadir 🛒", key=f"add_{cat}_{idx}"):
                        if "carrito" not in st.session_state: st.session_state.carrito = []
                        st.session_state.carrito.append(item)
                        st.toast(f"✅ {item['nombre']} añadido")
                    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CARRITO LATERAL ---
if "carrito" in st.session_state and st.session_state.carrito:
    st.sidebar.header("🛒 Tu Pedido")
    total = sum(x['precio'] for x in st.session_state.carrito)
    for p in st.session_state.carrito:
        st.sidebar.write(f"• {p['nombre']} (${p['precio']:,})")
    
    envio = float(config.get("costo_delivery", 0))
    st.sidebar.divider()
    st.sidebar.write(f"Subtotal: ${total:,}")
    st.sidebar.write(f"Envío: ${envio:,}")
    st.sidebar.subheader(f"Total: ${total + envio:,}")
    
    if st.sidebar.button("Borrar todo"):
        st.session_state.carrito = []
        st.rerun()

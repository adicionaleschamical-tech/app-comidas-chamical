import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Asegúrate de que esta URL sea la de tu implementación más reciente
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwlHFcGkkbIuPPcgLeIl2UleCp3qA4dOJrXgHZAEMDILnnK1hFbzHsUO91oQ0Zqg32_SA/exec"

def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion}, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        return {}
    return {}

# 1. Cargar Configuración Inicial
config_raw = leer_datos("leer_config")
config = {str(k).lower(): v for k, v in config_raw.items()}

# --- DISEÑO DINÁMICO ---
nombre_local = config.get("nombre_local", "Hamburguesas El 22")
st.set_page_config(page_title=nombre_local, layout="wide")

color_primario = config.get("tema_primario", "#FF6B35")
bg_color = config.get("background_color", "#FFF8F0")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .main-title {{ color: {color_primario}; text-align: center; font-weight: 800; font-size: 3rem; margin-bottom: 0; }}
    .stButton>button {{ background-color: {color_primario}; color: white; border-radius: 8px; width: 100%; }}
    .card {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- BARRA LATERAL (LOGIN) ---
st.sidebar.title("🔐 Acceso")
if not st.session_state.autenticado:
    with st.sidebar.expander("Personal"):
        u = st.text_input("Usuario / DNI")
        p = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            if u == str(config.get("admin_dni")) and p == str(config.get("admin_pass")):
                st.session_state.autenticado, st.session_state.rol = True, "admin"
                st.rerun()
            elif u == config.get("user_name") and p == config.get("user_pass"):
                st.session_state.autenticado, st.session_state.rol = True, "user"
                st.rerun()
            else:
                st.error("Error de acceso")
else:
    st.sidebar.success(f"Hola, {st.session_state.rol}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTA ADMINISTRATIVA ---
if st.session_state.autenticado:
    st.title(f"Panel Administrativo - {nombre_local}")
    tab1, tab2 = st.tabs(["📦 Productos", "⚙️ Configuración"])
    
    with tab1:
        prods = leer_datos("leer_productos")
        if prods:
            st.data_editor(pd.DataFrame(prods), num_rows="dynamic")
            st.button("Actualizar Catálogo en Excel")
    
    with tab2:
        st.write(f"Costo Delivery: ${config.get('costo_delivery')}")
        if st.session_state.rol == "admin":
            st.toggle("Modo Mantenimiento", value=(config.get("modo_mantenimiento") == "SI"))

# --- VISTA PÚBLICA ---
else:
    # Header
    st.markdown(f"<h1 class='main-title'>{nombre_local}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>📍 {config.get('direccion_local')} | ⏰ {config.get('horario')}</p>", unsafe_allow_html=True)

    if config.get("modo_mantenimiento") == "SI":
        st.error("Estamos en mantenimiento. Volvemos pronto.")
        st.stop()

    # Procesar Productos
    prods_raw = leer_datos("leer_productos")
    if not prods_raw:
        st.warning("No se pudo cargar el menú.")
    else:
        menu_final = []
        for p in prods_raw:
            v_list = str(p.get('variedades', '')).split(';')
            i_list = str(p.get('ingredientes', '')).split(';')
            p_list = str(p.get('precio', '')).split(';')
            
            for i in range(len(v_list)):
                try:
                    menu_final.append({
                        "nombre": v_list[i].strip(),
                        "desc": i_list[i].strip() if i < len(i_list) else "",
                        "precio": float(p_list[i].strip()) if i < len(p_list) else 0,
                        "img": p.get('imagen', ''),
                        "cat": p.get('categoria', '')
                    })
                except: continue

        # Mostrar por Categorías
        categorias = sorted(list(set([x['cat'] for x in menu_final])))
        for cat in categorias:
            st.subheader(f"--- {cat} ---")
            cols = st.columns(3)
            prods_cat = [x for x in menu_final if x['cat'] == cat]
            
            for idx, prod in enumerate(prods_cat):
                with cols[idx % 3]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if str(prod['img']).startswith("http"):
                        st.image(prod['img'], use_container_width=True)
                    st.markdown(f"**{prod['nombre']}**")
                    st.caption(prod['desc'])
                    st.markdown(f"**${prod['precio']:,}**")
                    if st.button("Añadir 🛒", key=f"btn_{cat}_{idx}"):
                        st.session_state.carrito.append(prod)
                        st.toast(f"Añadido: {prod['nombre']}")
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- CARRITO ---
    if st.session_state.carrito:
        st.sidebar.divider()
        st.sidebar.header("🛒 Tu Pedido")
        total_items = 0
        for i, item in enumerate(st.session_state.carrito):
            st.sidebar.write(f"{item['nombre']} - ${item['precio']:,}")
            total_items += item['precio']
        
        delivery = float(config.get("costo_delivery", 0))
        st.sidebar.write(f"🚚 Envío: ${delivery:,}")
        st.sidebar.subheader(f"Total: ${total_items + delivery:,}")
        
        with st.sidebar.form("pedido"):
            nom = st.text_input("Tu nombre")
            dni = st.text_input("Tu DNI")
            dire = st.text_input("Dirección de entrega")
            if st.form_submit_button("ENVIAR PEDIDO"):
                detalles = " + ".join([x['nombre'] for x in st.session_state.carrito])
                res = requests.get(URL_GOOGLE_SCRIPT, params={
                    "accion": "nuevo", "tel": dni, "nombre": nom,
                    "dir": dire, "detalle": detalles, "total": total_items + delivery
                })
                if res.text == "OK":
                    st.success("Pedido enviado!")
                    st.session_state.carrito = []
                    st.rerun()

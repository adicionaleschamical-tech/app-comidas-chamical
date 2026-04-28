import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyha0CeITBxjVIbd4gpgnI_1Hoxu1OK2n7GMWStEq-x8CIAWDVUrj8dbjlFyi6rrbKeaA/exec"

def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion}, timeout=10)
        return res.json()
    except: return {}

# 1. Cargar Configuración
config_raw = leer_datos("leer_config")
config = {str(k).lower().strip(): v for k, v in config_raw.items()}

# --- DISEÑO ---
st.set_page_config(page_title=config.get("nombre_local", "Hamburguesas El 22"), layout="wide")
color_p = config.get("tema_primario", "#FF6B35")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {config.get("background_color", "#FFF8F0")}; }}
    .main-title {{ color: {color_p}; text-align: center; font-weight: 800; font-size: 2.5rem; margin-bottom:0; }}
    .stButton>button {{ background-color: {color_p}; color: white; border-radius: 10px; width: 100%; border: none; }}
    .card {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; height: 100%; }}
    .pedido-card {{ background: white; padding: 15px; border-radius: 10px; border-left: 5px solid {color_p}; margin-bottom: 10px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1); }}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "carrito" not in st.session_state: st.session_state.carrito = []
if "rol" not in st.session_state: st.session_state.rol = "cliente"

# --- SIDEBAR: INGRESO PERSONAL ---
with st.sidebar:
    st.image(config.get("logo_url", ""), width=100) if config.get("logo_url") else None
    if st.session_state.rol == "cliente":
        with st.expander("🔐 Acceso Personal"):
            u = st.text_input("Usuario/DNI")
            p = st.text_input("Clave", type="password")
            if st.button("Ingresar"):
                if u == str(config.get("admin_dni")) and p == str(config.get("admin_pass")):
                    st.session_state.rol = "admin"
                    st.rerun()
                elif u == config.get("user") and p == config.get("user_pass"):
                    st.session_state.rol = "usuario"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    else:
        st.success(f"Sesión: {st.session_state.rol.upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state.rol = "cliente"
            st.rerun()

# --- VISTA ADMINISTRATIVA / USUARIO ---
if st.session_state.rol in ["admin", "usuario"]:
    st.title(f"Panel de Control - {st.session_state.rol.upper()}")
    tab_pedidos, tab_config = st.tabs(["📋 Gestión de Pedidos", "⚙️ Configuración"])
    
    with tab_pedidos:
        pedidos = leer_datos("leer_pedidos")
        if pedidos:
            df = pd.DataFrame(pedidos)
            st.dataframe(df)
        else: st.info("No hay pedidos registrados aún.")
    st.stop() # Detiene la ejecución para que el admin no vea el menú de clientes abajo

# --- VISTA PÚBLICA (CLIENTES) ---
st.markdown(f"<h1 class='main-title'>🍔 {config.get('nombre_local', 'Hamburguesas El 22')}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>📍 {config.get('direccion_local')} | ⏰ {config.get('horario')}</p>", unsafe_allow_html=True)

if config.get("modo_mantenimiento") == "SI":
    st.warning("🛠️ Estamos mejorando para vos. Volvemos pronto.")
    st.stop()

tab_menu, tab_carrito, tab_rastreo = st.tabs(["🍴 LA CARTA", "🛒 MI PEDIDO", "🔍 RASTREAR PEDIDO"])

# --- TAB 1: MENÚ ---
with tab_menu:
    prods_raw = leer_datos("leer_productos")
    if prods_raw:
        menu = []
        for p in prods_raw:
            p_n = {str(k).lower(): v for k, v in p.items()}
            v = str(p_n.get('variedades', '')).split(';')
            pr = str(p_n.get('precio', '')).split(';')
            ing = str(p_n.get('ingredientes', '')).split(';')
            for i in range(len(v)):
                try:
                    menu.append({
                        "nombre": v[i].strip(),
                        "precio": float(pr[i].strip()),
                        "desc": ing[i].strip() if i < len(ing) else "",
                        "cat": p_n.get('categoria', 'Otros'),
                        "img": p_n.get('imagen', '')
                    })
                except: continue

        for cat in sorted(list(set([x['cat'] for x in menu]))):
            st.subheader(f"➔ {cat}")
            cols = st.columns(3)
            items = [x for x in menu if x['cat'] == cat]
            for idx, it in enumerate(items):
                with cols[idx % 3]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if str(it['img']).startswith("http"): st.image(it['img'], use_container_width=True)
                    st.write(f"**{it['nombre']}**")
                    st.caption(it['desc'])
                    st.write(f"### ${it['precio']:,}")
                    if st.button("Agregar 🛒", key=f"add_{it['nombre']}_{idx}"):
                        st.session_state.carrito.append(it)
                        st.toast(f"✅ {it['nombre']} añadido")
                    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: CARRITO Y REGISTRO ---
with tab_carrito:
    if not st.session_state.carrito:
        st.info("Tu carrito está vacío. ¡Mira nuestra carta!")
    else:
        st.header("Resumen del Pedido")
        total_p = 0
        for i, item in enumerate(st.session_state.carrito):
            c1, c2 = st.columns([4, 1])
            c1.write(f"• {item['nombre']}")
            c2.write(f"${item['precio']:,}")
            total_p += item['precio']
        
        envio = float(config.get("costo_delivery", 0))
        st.divider()
        st.write(f"Subtotal: ${total_p:,}")
        st.write(f"Envío: ${envio:,}")
        st.subheader(f"TOTAL: ${total_p + envio:,}")

        with st.form("registro_pedido"):
            st.write("📝 **Completa tus datos para el envío**")
            nombre = st.text_input("Nombre y Apellido")
            dni = st.text_input("DNI (Obligatorio para rastrear tu pedido)")
            dire = st.text_input("Dirección de entrega")
            if st.form_submit_button("🚀 CONFIRMAR PEDIDO"):
                if nombre and dni and dire:
                    detalles = " + ".join([x['nombre'] for x in st.session_state.carrito])
                    res = requests.get(URL_GOOGLE_SCRIPT, params={
                        "accion": "nuevo", "tel": dni, "nombre": nombre,
                        "dir": dire, "detalle": detalles, "total": total_p + envio
                    })
                    if res.text == "OK":
                        st.balloons()
                        st.success(f"¡Pedido enviado! Podrás rastrearlo con tu DNI: {dni}")
                        st.session_state.carrito = []
                    else: st.error("Error al conectar con el servidor.")
                else: st.warning("Por favor, completa todos los campos.")

# --- TAB 3: RASTREO ---
with tab_rastreo:
    st.header("¿Dónde está mi pedido?")
    dni_r = st.text_input("Ingresa tu DNI")
    if st.button("Buscar"):
        peds = leer_datos("leer_pedidos")
        if peds:
            encontrados = [p for p in peds if str(p['DNI']).strip() == dni_r.strip()]
            if encontrados:
                for ped in encontrados:
                    st.markdown(f"""
                    <div class="pedido-card">
                        <b>Cliente:</b> {ped['NOMBRE']}<br>
                        <b>Estado:</b> <span style="color:{color_p}; font-weight:bold;">{ped['ESTADO']}</span><br>
                        <b>Detalle:</b> {ped['DETALLE']}<br>
                        <b>Total:</b> ${ped['TOTAL']}<br>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.warning("No hay pedidos registrados con ese DNI.")

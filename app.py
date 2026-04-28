import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyuj1O98ChTKRgn7y7scCoFsNeAxWAkghQHXL2QZyaDBIsTf8nz8xKtOG1UBTZ8cLX_Fw/exec"

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
    .main-title {{ color: {color_p}; text-align: center; font-weight: 800; }}
    .stButton>button {{ background-color: {color_p}; color: white; border-radius: 10px; width: 100%; }}
    .pedido-card {{ background: white; padding: 20px; border-radius: 15px; border-left: 5px solid {color_p}; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "carrito" not in st.session_state: st.session_state.carrito = []
if "autenticado" not in st.session_state: st.session_state.autenticado = False

# --- PANTALLA DE INGRESO (LOGIN) ---
if not st.session_state.autenticado:
    st.markdown(f"<h1 class='main-title'>🍔 {config.get('nombre_local', 'BIENVENIDOS')}</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Ingresar para comprar")
        user_input = st.text_input("DNI o Usuario")
        pass_input = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            # Verificación contra el Excel
            is_admin = user_input == str(config.get("admin_dni")) and pass_input == str(config.get("admin_pass"))
            is_user = user_input == config.get("user") and pass_input == config.get("user_pass")
            
            if is_admin or is_user:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("DNI o Clave incorrectos")
    st.stop()

# --- SI ESTÁ AUTENTICADO, MOSTRAR APP ---

# TABS PRINCIPALES
tab_menu, tab_carrito, tab_mis_pedidos = st.tabs(["🍴 MENÚ", "🛒 MI CARRITO", "🔍 ESTADO DE MI PEDIDO"])

# --- TAB 1: MENÚ ---
with tab_menu:
    st.markdown(f"<h1 class='main-title'>{config.get('nombre_local')}</h1>", unsafe_allow_html=True)
    prods_raw = leer_datos("leer_productos")
    
    if prods_raw:
        # Procesar filas del Excel
        menu_final = []
        for p in prods_raw:
            p_n = {str(k).lower(): v for k, v in p.items()}
            vars = str(p_n.get('variedades', '')).split(';')
            pres = str(p_n.get('precio', '')).split(';')
            for i in range(len(vars)):
                try:
                    menu_final.append({
                        "nombre": vars[i].strip(),
                        "precio": float(pres[i].strip()),
                        "cat": p_n.get('categoria', 'Varios'),
                        "img": p_n.get('imagen', '')
                    })
                except: continue

        cats = sorted(list(set([x['cat'] for x in menu_final])))
        for c in cats:
            st.write(f"### {c}")
            cols = st.columns(4)
            items = [x for x in menu_final if x['cat'] == c]
            for idx, it in enumerate(items):
                with cols[idx % 4]:
                    if str(it['img']).startswith("http"): st.image(it['img'])
                    st.write(f"**{it['nombre']}**")
                    st.write(f"${it['precio']:,}")
                    if st.button("Agregar", key=f"add_{it['nombre']}_{idx}"):
                        st.session_state.carrito.append(it)
                        st.toast(f"✅ {it['nombre']} al carrito")

# --- TAB 2: CARRITO Y PAGO ---
with tab_carrito:
    st.header("🛒 Detalle de tu compra")
    if not st.session_state.carrito:
        st.info("Tu carrito está vacío.")
    else:
        total_items = 0
        for idx, item in enumerate(st.session_state.carrito):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{item['nombre']}**")
            col_b.write(f"${item['precio']:,}")
            total_items += item['precio']
        
        envio = float(config.get("costo_delivery", 0))
        st.divider()
        st.write(f"Subtotal: ${total_items:,}")
        st.write(f"Envío: ${envio:,}")
        st.subheader(f"TOTAL A PAGAR: ${total_items + envio:,}")

        with st.form("form_pago"):
            st.subheader("Datos de entrega")
            nombre_cliente = st.text_input("Nombre completo")
            direccion_entrega = st.text_input("Dirección exacta (Calle, N°, Barrio)")
            dni_cliente = st.text_input("DNI (para seguimiento)")
            notas = st.text_area("Notas adicionales (ej: sin cebolla)")
            
            if st.form_submit_button("🚀 CONFIRMAR Y PAGAR"):
                if nombre_cliente and direccion_entrega and dni_cliente:
                    detalles = " + ".join([x['nombre'] for x in st.session_state.carrito])
                    res = requests.get(URL_GOOGLE_SCRIPT, params={
                        "accion": "nuevo", "tel": dni_cliente, "nombre": nombre_cliente,
                        "dir": direccion_entrega, "detalle": detalles, "total": total_items + envio
                    })
                    if res.text == "OK":
                        st.success("¡Pedido enviado con éxito! Puedes seguirlo en la pestaña 'Estado de mi pedido'")
                        st.session_state.carrito = []
                    else: st.error("Error al guardar pedido.")
                else: st.warning("Por favor completa todos los datos.")

# --- TAB 3: BUSCADOR DE PEDIDOS ---
with tab_mis_pedidos:
    st.header("🔍 Seguimiento de Pedido")
    dni_busqueda = st.text_input("Ingresa tu DNI para consultar")
    if st.button("BUSCAR"):
        # Leemos la hoja de pedidos (esto requiere que en tu .gs tengas una accion 'leer_pedidos')
        pedidos_raw = leer_datos("leer_pedidos") # Debes agregar esta funcion al Script de Google
        if pedidos_raw:
            encontrados = [p for p in pedidos_raw if str(p['DNI']).strip() == dni_busqueda.strip()]
            if encontrados:
                for ped in encontrados:
                    st.markdown(f"""
                    <div class="pedido-card">
                        <h4>Pedido de: {ped['NOMBRE']}</h4>
                        <p><b>Estado:</b> {ped['ESTADO']}</p>
                        <p><b>Detalle:</b> {ped['DETALLE']}</p>
                        <p><b>Total:</b> ${ped['TOTAL']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.warning("No se encontraron pedidos con ese DNI.")

import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE ENLACES ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_PEDIDOS = "1395505058"
GID_CONFIG = "612320365" 

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# --- 2. FUNCIONES NÚCLEO ---

@st.cache_data(ttl=5) # Actualización rápida cada 5 segundos
def cargar_config():
    try:
        resp = requests.get(URL_CONFIG, timeout=10)
        resp.encoding = 'utf-8' # Crucial para el símbolo ° y la Ñ
        df = pd.read_csv(StringIO(resp.text), header=None)
        
        # Diccionario dinámico: busca el nombre en Col A y toma el valor de Col B
        config_dict = {}
        for _, row in df.iterrows():
            if pd.notna(row[0]):
                param = str(row[0]).strip()
                valor = str(row[1]).strip() if pd.notna(row[1]) else ""
                config_dict[param] = valor
        return config_dict
    except Exception:
        return {}

def formatear_moneda(valor):
    try:
        v = int(float(str(valor).replace('$', '').replace('.', '').replace(',', '').strip()))
        return f"${v:,}".replace(",", ".")
    except:
        return f"${valor}"

def limpiar_precio(valor):
    if pd.isna(valor): return 0
    if isinstance(valor, (int, float)): return int(valor)
    solo_numeros = re.sub(r'[^\d]', '', str(valor))
    return int(solo_numeros) if solo_numeros else 0

# --- 3. PROCESAMIENTO DE VARIABLES ---
conf = cargar_config()

# Asignación de parámetros del Sheet con nombres exactos
nombre_local = conf.get('Nombre_Local', 'Cargando...')
logo_url = conf.get('Logo_URL', '')
direccion_local = conf.get('Direccion Local', '') # Aquí tomará "AVDA. PERON N° 10"
alias_pago = conf.get('Alias', 'No definido')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))
modo_mantenimiento = conf.get('MODO_MANTENIMIENTO', 'NO')

st.set_page_config(page_title=nombre_local, page_icon="🍟", layout="centered")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. CABECERA ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    if logo_url and str(logo_url).startswith("http"):
        try: st.image(logo_url, width=90)
        except: st.markdown("## 🍔")
    else: st.markdown("## 🍔")

with col_tit:
    st.title(nombre_local)
    if direccion_local:
        st.caption(f"📍 {direccion_local}")

st.write("---")

# --- 5. LÓGICA DE BLOQUEO ---
if modo_mantenimiento == "SI":
    st.error("⚠️ Local en mantenimiento. Volvemos pronto.")
    if st.button("🔑 Acceso Personal"):
        st.session_state.vista = 'login'; st.rerun()
    st.stop()

# --- 6. VISTAS DE NAVEGACIÓN ---

# VISTA: INICIO
if st.session_state.vista == 'inicio':
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🍔 HACER PEDIDO", use_container_width=True, type="primary"):
            st.session_state.vista = 'pedir'; st.rerun()
    with c2:
        if st.button("📦 MI PEDIDO", use_container_width=True):
            st.session_state.vista = 'consultar'; st.rerun()
    st.write("---")
    if st.button("🔑 Acceso Personal"):
        st.session_state.vista = 'login'; st.rerun()

# VISTA: LOGIN
if st.session_state.vista == 'login':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    st.subheader("Ingreso de Personal")
    u_dni = st.text_input("DNI")
    u_pass = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u_dni == str(conf.get('Admin_DNI')) and u_pass == str(conf.get('Admin_Pass')):
            st.session_state.rol = 'admin'; st.session_state.vista = 'admin_panel'; st.rerun()
        else:
            st.error("DNI o Clave incorrectos.")

# VISTA: CONSULTAR (CON AUTO-REFRESCO)
if st.session_state.vista == 'consultar':
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    st.subheader("Estado de tu pedido")
    dni_q = st.text_input("DNI del pedido:", value=st.session_state.get('user_dni', ""))
    if st.button("🔍 BUSCAR"):
        try:
            resp = requests.get(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
            df_peds = pd.read_csv(StringIO(resp.text))
            df_peds.columns = [c.strip().upper() for c in df_peds.columns]
            df_peds['D_CLEAN'] = df_peds['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[.,\s]', '', regex=True)
            dni_busq = re.sub(r'[^\d]', '', str(dni_q))
            match = df_peds[df_peds['D_CLEAN'] == dni_busq]
            if not match.empty:
                res = match.iloc[-1]
                st.success(f"Hola {res['NOMBRE']}, tu pedido está: **{res['ESTADO']}**")
                if str(res['ESTADO']).upper() not in ["ENTREGADO", "FINALIZADO"]:
                    time.sleep(10); st.rerun()
            else: st.warning("No encontramos pedidos con ese DNI.")
        except: st.error("No se pudo conectar con la base de datos.")

# VISTA: PEDIR
if st.session_state.vista == 'pedir':
    if st.button("⬅ Menú"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        with st.container(border=True):
            n = st.text_input("Nombre")
            d = st.text_input("DNI (solo números)")
            if st.button("Ingresar"):
                if n and d.isdigit():
                    st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # Productos
    df_prod = pd.read_csv(URL_PRODUCTOS)
    df_prod.columns = [c.strip().upper() for c in df_prod.columns]
    
    for idx, row in df_prod.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1.5])
                c1.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                c2.markdown(f"**{row['PRODUCTO']}**")
                p_unit = limpiar_precio(row['PRECIO'])
                c2.write(formatear_moneda(p_unit))
                
                p_name = row['PRODUCTO']
                cant = st.session_state.carrito.get(p_name, 0)
                
                b1, b_txt, b2 = c3.columns([1, 1, 1])
                if b1.button("➖", key=f"m_{idx}"):
                    if cant > 0:
                        st.session_state.carrito[p_name] -= 1
                        if st.session_state.carrito[p_name] == 0: del st.session_state.carrito[p_name]
                        st.rerun()
                b_txt.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                if b2.button("➕", key=f"p_{idx}"):
                    st.session_state.carrito[p_name] = cant + 1
                    st.rerun()

    # CARRITO
    if st.session_state.carrito:
        st.write("---")
        st.header("🛒 Tu Carrito")
        total_acum = 0
        txt_detalle = ""
        for p, q in st.session_state.carrito.items():
            pre = limpiar_precio(df_prod[df_prod['PRODUCTO']==p]['PRECIO'].iloc[0])
            sub = pre * q
            total_acum += sub
            txt_detalle += f"- {q}x {p}\n"
            st.write(f"**{q}x** {p} ({formatear_moneda(sub)})")
        
        opcion = st.radio("Entrega:", ["Retiro en Local", "Delivery"])
        envio = costo_delivery if opcion == "Delivery" else 0
        total_f = total_acum + envio
        
        if envio > 0: st.write(f"Envío: {formatear_moneda(envio)}")
        st.markdown(f"## TOTAL: {formatear_moneda(total_f)}")
        st.info(f"💰 Alias: **{alias_pago}**")
        
        ubi = st.text_input("Dirección:") if opcion == "Delivery" else "Retiro"
        
        if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
            params = {"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":txt_detalle, "total":total_f, "dir":ubi}
            requests.get(URL_APPS_SCRIPT, params=params)
            msg = f"🔔 *NUEVO PEDIDO*\n👤 {st.session_state.user_name}\n📍 {ubi}\n{txt_detalle}\n💰 TOTAL: {formatear_moneda(total_f)}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.session_state.carrito = {}; st.session_state.vista = 'consultar'; st.rerun()

# PANEL ADMIN
if st.session_state.vista == 'admin_panel':
    st.header("Panel Administrativo")
    if st.button("Cerrar Sesión"): st.session_state.vista = 'inicio'; st.rerun()
    try:
        resp = requests.get(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
        st.dataframe(pd.read_csv(StringIO(resp.text)).tail(20), use_container_width=True)
    except: st.error("Error al cargar pedidos.")

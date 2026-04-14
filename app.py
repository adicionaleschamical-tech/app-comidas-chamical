import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO

# --- 1. CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365" 
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzl9dpOIAVs7U3sfiS8pJE__FqPUSj8rTAEPQeSJF6si6ADL8LK-SDdWD4KXrep5rlJPQ/exec"

TELEGRAM_TOKEN = "8793126374:AAG5zIBWrUOq50Ku0zjXEe8joD_JlcCDURI"
TELEGRAM_CHAT_ID = "7860013984"

# --- 2. FUNCIONES ---

@st.cache_data(ttl=5)
def cargar_config():
    try:
        resp = requests.get(f"{URL_CONFIG}&cb={int(time.time())}", timeout=10)
        df = pd.read_csv(StringIO(resp.text), header=None)
        if df.shape[1] < 2: return {}
        return {str(row[0]).strip(): str(row[1]).strip() for _, row in df.iterrows() if pd.notna(row[0])}
    except: return {}

def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "": return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- 3. INICIO ---
conf = cargar_config()
nombre_local = conf.get('Nombre_Local', 'Lomitos El Caniche')
costo_delivery = limpiar_precio(conf.get('Costo Delivery', 0))

st.set_page_config(page_title=nombre_local, page_icon="🍔")

if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

# --- 4. NAVEGACIÓN ---

if st.session_state.vista == 'inicio':
    st.title(nombre_local)
    c1, c2 = st.columns(2)
    if c1.button("🛒 HACER PEDIDO", use_container_width=True, type="primary"):
        st.session_state.vista = 'pedir'; st.rerun()
    if c2.button("🔍 RASTREAR DNI", use_container_width=True):
        st.session_state.vista = 'rastreo'; st.rerun()

elif st.session_state.vista == 'rastreo':
    st.subheader("Estado de tu pedido")
    if st.button("⬅ Volver"): st.session_state.vista = 'inicio'; st.rerun()
    dni_in = st.text_input("DNI:")
    if st.button("Buscar"):
        resp = requests.get(f"{URL_PEDIDOS_BASE}&cb={int(time.time())}")
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        d_l = re.sub(r'[^\d]', '', str(dni_in))
        df['DNI_L'] = df['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'[^\d]', '', regex=True)
        res = df[df['DNI_L'] == d_l].tail(1)
        if not res.empty:
            st.success(f"Estado: {res.iloc[0]['ESTADO']}")
        else: st.warning("Sin pedidos.")

elif st.session_state.vista == 'pedir':
    if st.button("⬅ Menú Principal"): st.session_state.vista = 'inicio'; st.rerun()
    
    if 'user_dni' not in st.session_state:
        n = st.text_input("Nombre"); d = st.text_input("DNI")
        if st.button("Ingresar"):
            st.session_state.user_name = n; st.session_state.user_dni = d; st.rerun()
        st.stop()

    # --- LISTADO DE PRODUCTOS ---
    resp_p = requests.get(f"{URL_PRODUCTOS}&cb={int(time.time())}")
    df_p = pd.read_csv(StringIO(resp_p.text))
    df_p.columns = [c.strip().upper() for c in df_p.columns]

    for _, row in df_p.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            st.write(f"### {row['PRODUCTO']}") # Nombre de la categoría (Hamburguesa, Lomo)
            
            # Separamos los datos por punto y coma (;)
            lista_vars = str(row['VARIEDADES']).split(';')
            lista_ings = str(row['INGREDIENTES']).split(';')
            lista_pres = str(row['PRECIO']).split(';')

            # Por cada variedad, creamos una "tarjeta"
            for i in range(len(lista_vars)):
                v_nom = lista_vars[i].strip()
                v_ing = lista_ings[i].strip() if i < len(lista_ings) else ""
                v_pre = limpiar_precio(lista_pres[i]) if i < len(lista_pres) else 0
                
                item_id = f"{row['PRODUCTO']} - {v_nom}"
                
                with st.container(border=True):
                    col_det, col_btn = st.columns([3, 1])
                    
                    with col_det:
                        st.markdown(f"**{v_nom}**")
                        if v_ing: st.caption(v_ing)
                        st.write(f"**{formatear_moneda(v_pre)}**")
                    
                    with col_btn:
                        cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                        if st.button("➕", key=f"add_{item_id}"):
                            st.session_state.carrito[item_id] = {'cant': cant + 1, 'precio': v_pre}
                            st.rerun()
                        if cant > 0:
                            st.write(f"En carrito: {cant}")
                            if st.button("➖", key=f"res_{item_id}"):
                                st.session_state.carrito[item_id]['cant'] -= 1
                                if st.session_state.carrito[item_id]['cant'] == 0: del st.session_state.carrito[item_id]
                                st.rerun()

    # --- FINALIZAR PEDIDO ---
    if st.session_state.carrito:
        st.write("---")
        total = sum(v['cant'] * v['precio'] for v in st.session_state.carrito.values())
        st.subheader(f"Total: {formatear_moneda(total)}")
        
        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True, type="primary"):
            det = "\n".join([f"{v['cant']}x {k}" for k, v in st.session_state.carrito.items()])
            requests.get(URL_APPS_SCRIPT, params={"accion":"nuevo", "tel":st.session_state.user_dni, "nombre":st.session_state.user_name, "detalle":det, "total":total, "dir":"Local"})
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": f"NUEVO: {st.session_state.user_name}\n{det}\nTotal: {formatear_moneda(total)}"})
            st.session_state.carrito = {}; st.session_state.vista = 'rastreo'; st.rerun()

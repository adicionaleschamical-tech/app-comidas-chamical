import streamlit as st
import pandas as pd
import requests
import re
from io import StringIO

# --- CONFIGURACIÓN ---
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=0"

def limpiar_precio(texto):
    if pd.isna(texto): return 0
    num = re.sub(r'[^\d]', '', str(texto))
    return int(num) if num else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

# --- CARGA DE DATOS ---
@st.cache_data(ttl=10)
def cargar_productos():
    try:
        resp = requests.get(URL_PRODUCTOS)
        resp.encoding = 'utf-8'
        df = pd.read_csv(StringIO(resp.text))
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🍔 Lomitos El Caniche")

df = cargar_productos()

if not df.empty:
    for _, row in df.iterrows():
        if str(row.get('DISPONIBLE', '')).upper() == "SI":
            with st.container(border=True):
                col_img, col_info = st.columns([1, 2])
                
                with col_img:
                    st.image(row['IMAGEN'] if pd.notna(row['IMAGEN']) else "https://via.placeholder.com/150")
                
                with col_info:
                    st.header(row['PRODUCTO'])
                    
                    # Separar las listas por el punto y coma
                    vars_lista = [v.strip() for v in str(row['VARIEDADES']).split(';')]
                    ings_lista = [i.strip() for i in str(row['INGREDIENTES']).split(';')]
                    pres_lista = [p.strip() for p in str(row['PRECIO']).split(';')]

                    # BOTONES DE SELECCIÓN (RADIO HORIZONTAL)
                    seleccion = st.pills(
                        "Seleccioná variedad:", 
                        vars_lista, 
                        key=f"pills_{row['PRODUCTO']}",
                        selection_mode="single"
                    )

                    if seleccion:
                        # Buscamos el índice de la opción elegida
                        idx = vars_lista.index(seleccion)
                        
                        # Mostramos ingredientes y precio de ESA variedad
                        st.info(f"📝 {ings_lista[idx] if idx < len(ings_lista) else ''}")
                        precio_v = limpiar_precio(pres_lista[idx]) if idx < len(pres_lista) else 0
                        st.subheader(formatear_moneda(precio_v))

                        # CONTROL DE CARRITO
                        item_id = f"{row['PRODUCTO']} ({seleccion})"
                        if 'carrito' not in st.session_state: st.session_state.carrito = {}
                        
                        cant = st.session_state.carrito.get(item_id, 0)
                        c1, c2, c3 = st.columns([1, 1, 1])
                        if c1.button("➖", key=f"m_{item_id}"):
                            if cant > 0:
                                st.session_state.carrito[item_id] = cant - 1
                                st.rerun()
                        c2.markdown(f"<h3 style='text-align:center;'>{cant}</h3>", unsafe_allow_html=True)
                        if c3.button("➕", key=f"p_{item_id}"):
                            st.session_state.carrito[item_id] = cant + 1
                            st.rerun()
else:
    st.error("No se pudo cargar el menú. Verificá tu Google Sheet.")

# --- BARRA LATERAL DEL CARRITO ---
if 'carrito' in st.session_state and any(v > 0 for v in st.session_state.carrito.values()):
    with st.sidebar:
        st.header("🛒 Tu Pedido")
        total_final = 0
        for item, q in st.session_state.carrito.items():
            if q > 0:
                st.write(f"**{q}x** {item}")
        st.button("🚀 ENVIAR PEDIDO")

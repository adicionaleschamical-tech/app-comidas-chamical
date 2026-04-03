import streamlit as st
import pandas as pd
import urllib.parse
import re

# ==========================================
# ⚙️ CONFIGURACIÓN GENERAL (Ajustá esto aquí)
# ==========================================
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpM4wEf5Flx7VTs99aGebJBJDmsD8jhoZ0-Hl3xv3PGj5hdSH_acG-fKr4rgg3At1GuLgKAGNgewI8/pub?output=csv"
NUMERO_WHATSAPP = "5493804000000"  # Tu celular con código de área
ALIAS_PAGO = "caniche.food.mp"     # Tu Alias de Mercado Pago o Banco
COSTO_DELIVERY = 800               # El precio del envío en Chamical
# ==========================================

st.set_page_config(page_title="Caniche Food", page_icon="🍔")

if 'carrito' not in st.session_state:
    st.session_state['carrito'] = {}

# --- FUNCIONES DE APOYO ---
def limpiar_precio(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    solo_numeros = "".join(filter(str.isdigit, str(valor)))
    try: return float(solo_numeros)
    except: return 0.0

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        if 'Precio' in df.columns:
            df['Precio_Num'] = df['Precio'].apply(limpiar_precio)
        return df
    except: return pd.DataFrame()

def modificar_cantidad(producto, precio, operacion):
    if operacion == "sumar":
        if producto in st.session_state['carrito']:
            st.session_state['carrito'][producto]['cant'] += 1
        else:
            st.session_state['carrito'][producto] = {'precio': precio, 'cant': 1}
    elif operacion == "restar":
        if producto in st.session_state['carrito']:
            st.session_state['carrito'][producto]['cant'] -= 1
            if st.session_state['carrito'][producto]['cant'] <= 0:
                del st.session_state['carrito'][producto]

# --- MENÚ DE PRODUCTOS ---
st.title("🍔 Caniche Food")
df = cargar_datos()

if not df.empty:
    if 'Disponible' in df.columns:
        df = df[df['Disponible'].str.upper() == 'SI']

    categorias = list(df['Categoria'].unique())
    tabs = st.tabs(categorias)

    for i, cat in enumerate(categorias):
        with tabs[i]:
            items = df[df['Categoria'] == cat]
            for _, row in items.iterrows():
                with st.container(border=True):
                    c_img, c_info, c_btns = st.columns([1, 1.5, 1])
                    with c_img:
                        if pd.notna(row.get('Imagen')): st.image(row['Imagen'], use_container_width=True)
                    with c_info:
                        st.subheader(row['Producto'])
                        st.write(f"**${row['Precio_Num']:,.0f}**")
                    with c_btns:
                        r, n, s = st.columns([1,1,1])
                        with s: 
                            if st.button("➕", key=f"add_{row['Producto']}"): 
                                modificar_cantidad(row['Producto'], row['Precio_Num'], "sumar")
                                st.rerun()
                        with n: 
                            cant = st.session_state['carrito'].get(row['Producto'], {}).get('cant', 0)
                            st.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                        with r: 
                            if st.button("➖", key=f"res_{row['Producto']}"): 
                                modificar_cantidad(row['Producto'], row['Precio_Num'], "restar")
                                st.rerun()

    # --- SECCIÓN FINAL DEL PEDIDO ---
    if st.session_state['carrito']:
        st.divider()
        st.header("🛒 Tu Carrito")
        
        total_productos = 0
        resumen_texto = ""
        for p, info in st.session_state['carrito'].items():
            sub = info['precio'] * info['cant']
            total_productos += sub
            st.write(f"✅ {info['cant']}x **{p}** — ${sub:,.0f}")
            resumen_texto += f"- {info['cant']}x {p} (${sub:,.0f})\n"

        # --- DATOS DEL CLIENTE ---
        st.divider()
        st.subheader("📍 Datos de Entrega")
        
        nombre = st.text_input("Tu Nombre", placeholder="Escribí tu nombre aquí")
        entrega = st.radio("¿Cómo recibís tu pedido?", ["Retiro en Local", "Delivery"])
        
        envio_final = 0
        dire = ""
        if entrega == "Delivery":
            dire = st.text_input("Dirección / Barrio", placeholder="Ej: B° Centro, calle falsa 123")
            envio_final = COSTO_DELIVERY
            st.info(f"🛵 Costo de envío: **${COSTO_DELIVERY}**")

        pago = st.selectbox("Medio de Pago", ["Efectivo", "Transferencia / Mercado Pago"])
        
        total_final = total_productos + envio_final
        
        # --- RESUMEN DE PAGO ---
        with st.expander("Ver Resumen de Pago", expanded=True):
            st.write(f"Productos: ${total_productos:,.0f}")
            if envio_final > 0: st.write(f"Envío: ${envio_final:,.0f}")
            st.success(f"### TOTAL A PAGAR: ${total_final:,.0f}")
            
            if "Transferencia" in pago:
                st.warning(f"🏦 **Alias:** `{ALIAS_PAGO}`")

        # --- BOTÓN HACER PEDIDO ---
        if st.button("🚀 HACER PEDIDO", use_container_width=True):
            if not nombre:
                st.error("⚠️ Por favor, ingresá tu nombre para continuar.")
            elif entrega == "Delivery" and not dire:
                st.error("⚠️ Necesitamos tu dirección para el envío.")
            else:
                # Armar mensaje de WhatsApp
                msj = (
                    f"🍔 *NUEVO PEDIDO - CANICHE FOOD*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"--------------------------\n"
                    f"{resumen_texto}"
                    f"--------------------------\n"
                    f"🛵 *Entrega:* {entrega}\n"
                    f"{'📍 *Dirección:* ' + dire if dire else ''}\n"
                    f"💳 *Pago:* {pago}\n"
                    f"💰 *TOTAL: ${total_final:,.0f}*"
                )
                
                url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(msj)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_wa}">', unsafe_allow_html=True)
                st.balloons()
        
        if st.button("🗑️ Vaciar Carrito", type="secondary"):
            st.session_state['carrito'] = {}
            st.rerun()
    else:
        st.info("👋 ¡Hola! Elegí tus productos arriba para armar tu pedido.")
else:
    st.error("No se pudo cargar el menú.")

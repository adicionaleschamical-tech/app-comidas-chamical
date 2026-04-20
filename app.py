import streamlit as st
import pandas as pd
import requests
import time
import re
from io import StringIO
from datetime import datetime
import json

# ==================== CONFIGURACIÓN CRÍTICA ====================
# 1. PEGA AQUÍ TU URL DE GOOGLE APPS SCRIPT (LA QUE TERMINA EN /exec)
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwn1XLeQTH0VI3ROo3iu9-vDy4Cs211ClMCYgTC5RsOOnvIQoafVb7sze22qZVhApQfCQ/exec"

# 2. DATOS DE TU PLANILLA
ID_SHEET = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA"
GID_CONFIG = "612320365"
GID_PRODUCTOS = "0"
GID_PEDIDOS = "1395505058"

# 3. TELEGRAM
TELEGRAM_TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es"
TELEGRAM_CHAT_ID = "7860013984"

# URLs de descarga
URL_PRODUCTOS = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PRODUCTOS}"
URL_CONFIG = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_CONFIG}"
URL_PEDIDOS_BASE = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_PEDIDOS}"

# ==================== FUNCIONES LÓGICAS ====================
def limpiar_precio(texto):
    if pd.isna(texto) or str(texto).strip() == "": return 0
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 0

def formatear_moneda(valor):
    return f"$ {int(valor):,}".replace(",", ".")

@st.cache_data(ttl=60)
def cargar_datos(url):
    try:
        resp = requests.get(f"{url}&cb={int(time.time())}", timeout=10)
        return pd.read_csv(StringIO(resp.text))
    except:
        return pd.DataFrame()

# ==================== CLASE MANAGER ====================
class PedidoManager:
    def registrar(self, dni, nombre, detalle, total, direccion):
        params = {
            "accion": "nuevo",
            "tel": dni,
            "nombre": nombre,
            "detalle": detalle,
            "total": total,
            "dir": direccion
        }
        try:
            r = requests.get(URL_APPS_SCRIPT, params=params, timeout=15, allow_redirects=True)
            return "OK" in r.text
        except Exception as e:
            st.error(f"Error de red: {e}")
            return False

    def notificar_telegram(self, nombre, dni, direccion, detalle, total):
        keyboard = {
            "inline_keyboard": [
                [{"text": "👨‍🍳 Preparando", "callback_data": f"est_Preparando_{dni}"},
                 {"text": "🛵 Enviado", "callback_data": f"est_Enviado_{dni}"}],
                [{"text": "✅ Finalizado", "callback_data": f"est_Listo_{dni}"}]
            ]
        }
        msg = f"🔔 *NUEVO PEDIDO*\n\n👤 {nombre}\n🆔 DNI: {dni}\n📍 {direccion}\n\n*Detalle:*\n{detalle}\n💰 *TOTAL: {formatear_moneda(total)}*"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)})

# ==================== INTERFAZ ====================
if 'vista' not in st.session_state: st.session_state.vista = 'inicio'
if 'carrito' not in st.session_state: st.session_state.carrito = {}

def main():
    st.set_page_config(page_title="Hambur Locos", page_icon="🍔")

    if st.session_state.vista == 'inicio':
        st.title("🍔 HAMBUR LOCOS")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 HACER PEDIDO", use_container_width=True):
                st.session_state.vista = 'pedir'
                st.rerun()
        with col2:
            if st.button("⚙️ ADMIN", use_container_width=True):
                st.session_state.vista = 'admin'
                st.rerun()

    elif st.session_state.vista == 'admin':
        st.subheader("🕵️ Panel de Diagnóstico")
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        st.write("Prueba si Streamlit puede escribir en tu Excel:")
        if st.button("Ejecutar Test de Conexión"):
            res = requests.get(f"{URL_APPS_SCRIPT}?accion=nuevo&tel=000&nombre=TEST&dir=TEST&detalle=TEST&total=0", allow_redirects=True)
            st.code(f"Respuesta de Google: {res.text}")
            if "OK" in res.text: st.success("✅ ¡Conexión Exitosa!")
            else: st.error("❌ Falló. Revisa los permisos en Apps Script.")

    elif st.session_state.vista == 'pedir':
        if st.button("⬅ Volver"):
            st.session_state.vista = 'inicio'
            st.rerun()
        
        if 'user_dni' not in st.session_state:
            with st.form("login"):
                n = st.text_input("Tu Nombre")
                d = st.text_input("Tu DNI (sin puntos)")
                if st.form_submit_button("Entrar a la Carta"):
                    if n and d:
                        st.session_state.user_name = n
                        st.session_state.user_dni = d
                        st.rerun()
            return

        # Cargar Productos
        df = cargar_datos(URL_PRODUCTOS)
        if not df.empty:
            for i, r in df.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['producto']}**")
                    p = limpiar_precio(r['precio'])
                    st.write(formatear_moneda(p))
                    if st.button(f"Añadir {r['producto']}", key=f"btn_{i}"):
                        st.session_state.carrito[r['producto']] = st.session_state.carrito.get(r['producto'], 0) + 1
                        st.toast(f"Añadido: {r['producto']}")

        if st.session_state.carrito:
            st.divider()
            st.subheader("🛒 Tu Carrito")
            resumen = ""
            total = 0
            for k, v in st.session_state.carrito.items():
                st.write(f"{v}x {k}")
                resumen += f"• {v}x {k}\n"
            
            if st.button("🚀 ENVIAR PEDIDO"):
                mgr = PedidoManager()
                if mgr.registrar(st.session_state.user_dni, st.session_state.user_name, resumen, 0, "Local"):
                    mgr.notificar_telegram(st.session_state.user_name, st.session_state.user_dni, "Local", resumen, 0)
                    st.success("¡Pedido enviado!")
                    st.session_state.carrito = {}
                    time.sleep(2)
                    st.session_state.vista = 'inicio'
                    st.rerun()

if __name__ == "__main__":
    main()

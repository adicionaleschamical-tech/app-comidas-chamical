import streamlit as st
import pandas as pd
import requests
import json

# --- CONFIGURACIÓN DE CONEXIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwlHFcGkkbIuPPcgLeIl2UleCp3qA4dOJrXgHZAEMDILnnK1hFbzHsUO91oQ0Zqg32_SA/exec"

# --- FUNCIÓN DE CARGA CON DIAGNÓSTICO ---
def leer_datos(accion):
    try:
        res = requests.get(URL_GOOGLE_SCRIPT, params={"accion": accion}, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return {"error": f"Error HTTP: {res.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# --- PANTALLA DE DIAGNÓSTICO (Solo visible si falla o se activa) ---
def mostrar_diagnostico():
    st.error("🚨 Error de Conexión Detectado")
    with st.expander("🔍 Ver detalles del Diagnóstico"):
        st.write("**1. Probando URL de Google Script...**")
        st.code(URL_GOOGLE_SCRIPT)
        
        test_config = leer_datos("leer_config")
        if "error" in test_config:
            st.write("❌ Fallo al leer 'Config':", test_config["error"])
        else:
            st.write("✅ 'Config' leído correctamente.")
            st.json(test_config)
            
        test_prods = leer_datos("leer_productos")
        if "error" in test_prods:
            st.write("❌ Fallo al leer 'Productos':", test_prods["error"])
        else:
            st.write("✅ 'Productos' leído correctamente.")
            st.write(f"Items encontrados: {len(test_prods)}")

# --- 1. CARGAR CONFIGURACIÓN ---
config_data = leer_datos("leer_config")

# Si no hay datos, mostramos diagnóstico y paramos
if not config_data or "error" in config_data:
    st.title("🍔 Hamburguesas El 22")
    mostrar_diagnostico()
    st.stop()

# --- 2. CONFIGURACIÓN VISUAL ---
config = config_data
nombre_local = config.get("Nombre_Local", "HAMBURGUESAS EL 22")
st.set_page_config(page_title=nombre_local, layout="wide")

color_p = config.get("Tema_Primario", "#FF6B35")
bg_c = config.get("Background_Color", "#FFF8F0")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_c}; }}
    .main-title {{ color: {color_p}; text-align: center; font-weight: 800; font-size: 2.5rem; }}
    .stButton>button {{ background-color: {color_p}; color: white; border-radius: 10px; }}
    .card {{ background: white; padding: 15px; border-radius: 15px; border: 1px solid #ddd; margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. CUERPO DE LA APP ---
st.markdown(f"<h1 class='main-title'>{nombre_local}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>📍 {config.get('Direccion_Local')} | ⏰ {config.get('Horario')}</p>", unsafe_allow_html=True)

if config.get("MODO_MANTENIMIENTO") == "SI":
    st.warning("🛠️ Local en mantenimiento.")
    st.stop()

# --- 4. CARGA DE PRODUCTOS ---
prods_raw = leer_datos("leer_productos")

if not prods_raw or "error" in prods_raw:
    st.info("Esperando productos del Excel...")
    if st.button("Ejecutar Diagnóstico Manual"):
        mostrar_diagnostico()
else:
    # Lógica de Variedades
    menu = []
    for p in prods_raw:
        var = str(p.get('variedades', '')).split(';')
        pre = str(p.get('precio', '')).split(';')
        ing = str(p.get('ingredientes', '')).split(';')
        
        for i in range(len(var)):
            try:
                menu.append({
                    "nombre": var[i].strip(),
                    "precio": float(pre[i].strip()) if i < len(pre) else 0,
                    "desc": ing[i].strip() if i < len(ing) else "",
                    "img": p.get('imagen', ''),
                    "cat": p.get('categoria', '')
                })
            except: continue

    # Renderizado
    cats = sorted(list(set([x['cat'] for x in menu])))
    for c in cats:
        st.subheader(f"➔ {c}")
        cols = st.columns(3)
        items = [x for x in menu if x['cat'] == c]
        for idx, it in enumerate(items):
            with cols[idx % 3]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if str(it['img']).startswith("http"):
                    st.image(it['img'], use_container_width=True)
                st.write(f"**{it['nombre']}**")
                st.caption(it['desc'])
                st.write(f"**${it['precio']:,}**")
                if st.button("Añadir 🛒", key=f"{it['nombre']}_{idx}"):
                    st.toast(f"Añadido {it['nombre']}")
                st.markdown('</div>', unsafe_allow_html=True)

# Botón de emergencia al final
st.sidebar.divider()
if st.sidebar.button("🛠️ Modo Diagnóstico"):
    mostrar_diagnostico()

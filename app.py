# Buscá esta parte en tu código y reemplazala:
with col_info:
    st.markdown(f"### {row['Producto']}")
    
    # Intentamos convertir el precio a número por si hay un error en el Sheet
    try:
        precio_num = float(row['Precio'])
        st.markdown(f"**${precio_num:,.0f}**")
    except:
        # Si falla (porque hay un texto o está vacío), mostramos el valor tal cual
        st.markdown(f"**Precio: {row['Precio']}**")
    
    if st.button(f"Seleccionar {row['Producto']}", key=f"btn_{row['Producto']}"):
        # Guardamos el precio convertido para que no falle el cálculo del total
        try:
            precio_final = float(row['Precio'])
        except:
            precio_final = 0.0
            
        st.session_state['seleccionado'] = {"nombre": row['Producto'], "precio": precio_final}
        st.toast(f"Agregaste {row['Producto']}")

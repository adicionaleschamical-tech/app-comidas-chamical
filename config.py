def mostrar_productos():
    """Muestra productos con sus variedades como tabs separados"""
    df = cargar_productos()
    if df.empty:
        st.warning("No hay productos disponibles")
        return
    
    for idx, row in df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                imagen_url = row.get('imagen', '')
                if pd.notna(imagen_url) and str(imagen_url).strip() != "":
                    try:
                        st.image(imagen_url, use_container_width=True)
                    except:
                        st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
                else:
                    st.image("https://via.placeholder.com/150x150?text=🍔", width=120)
            
            with col2:
                nombre_producto = str(row.get('producto', 'Producto'))
                st.subheader(nombre_producto)
                
                # Obtener variedades, ingredientes y precios
                variedades_raw = row.get('variedades', 'Única')
                ingredientes_raw = row.get('ingredientes', '')
                precios_raw = row.get('precio', '0')
                
                # Separar por punto y coma
                variedades = [v.strip() for v in str(variedades_raw).split(';')]
                ingredientes = [i.strip() for i in str(ingredientes_raw).split(';')] if pd.notna(ingredientes_raw) else []
                precios = [limpiar_precio(p) for p in str(precios_raw).split(';')]
                
                # Asegurar que todas las listas tengan la misma longitud
                while len(ingredientes) < len(variedades):
                    ingredientes.append("")
                while len(precios) < len(variedades):
                    precios.append(0)
                
                # Si hay más de una variedad, mostrar como tabs
                if len(variedades) > 1:
                    tabs = st.tabs(variedades)
                    for i, tab in enumerate(tabs):
                        with tab:
                            # Mostrar ingredientes
                            if ingredientes[i] and ingredientes[i] != "":
                                st.info(f"✨ {ingredientes[i]}")
                            else:
                                st.info("✨ Sin descripción")
                            
                            # Mostrar precio
                            st.markdown(f"### {formatear_moneda(precios[i])}")
                            
                            # Botones para agregar al carrito
                            item_id = f"{nombre_producto}_{variedades[i]}_{idx}"
                            cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                            
                            col_a, col_b, col_c = st.columns([1, 1, 1])
                            with col_a:
                                if st.button("➖", key=f"minus_{item_id}"):
                                    if cant > 0:
                                        if cant == 1:
                                            del st.session_state.carrito[item_id]
                                        else:
                                            st.session_state.carrito[item_id]['cant'] -= 1
                                        st.rerun()
                            with col_b:
                                st.markdown(f"<h3 style='text-align: center;'>{cant}</h3>", unsafe_allow_html=True)
                            with col_c:
                                if st.button("➕", key=f"plus_{item_id}"):
                                    if item_id in st.session_state.carrito:
                                        st.session_state.carrito[item_id]['cant'] += 1
                                    else:
                                        st.session_state.carrito[item_id] = {
                                            'cant': 1, 
                                            'precio': precios[i],
                                            'nombre': f"{nombre_producto} ({variedades[i]})"
                                        }
                                    st.rerun()
                else:
                    # Una sola variedad
                    if ingredientes[0] and ingredientes[0] != "":
                        st.info(f"✨ {ingredientes[0]}")
                    
                    st.markdown(f"### {formatear_moneda(precios[0])}")
                    
                    item_id = f"{nombre_producto}_{idx}"
                    cant = st.session_state.carrito.get(item_id, {}).get('cant', 0)
                    
                    col_a, col_b, col_c = st.columns([1, 1, 1])
                    with col_a:
                        if st.button("➖", key=f"minus_{item_id}"):
                            if cant > 0:
                                if cant == 1:
                                    del st.session_state.carrito[item_id]
                                else:
                                    st.session_state.carrito[item_id]['cant'] -= 1
                                st.rerun()
                    with col_b:
                        st.markdown(f"<h3 style='text-align: center;'>{cant}</h3>", unsafe_allow_html=True)
                    with col_c:
                        if st.button("➕", key=f"plus_{item_id}"):
                            if item_id in st.session_state.carrito:
                                st.session_state.carrito[item_id]['cant'] += 1
                            else:
                                st.session_state.carrito[item_id] = {
                                    'cant': 1, 
                                    'precio': precios[0],
                                    'nombre': nombre_producto
                                }
                            st.rerun()

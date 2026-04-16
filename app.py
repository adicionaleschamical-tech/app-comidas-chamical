def login_admin():
    """Pantalla de login - VERSIÓN SIMPLIFICADA"""
    st.subheader("🔐 Panel de Administración")
    
    # Recargar configuración
    conf_actual = cargar_config()
    
    # Obtener credenciales
    admin_dni = conf_actual.get('admin_dni', '')
    admin_pass = conf_actual.get('admin_pass', '')
    
    # Diagnóstico (lo puedes quitar después)
    with st.expander("🔍 Ver configuración actual"):
        st.write(f"**Admin_DNI:** {admin_dni}")
        st.write(f"**Admin_Pass:** {'*' * len(admin_pass) if admin_pass else 'No encontrada'}")
        st.write(f"**User:** {conf_actual.get('user', '')}")
        st.write(f"**User_Pass:** {'*' * len(conf_actual.get('user_pass', '')) if conf_actual.get('user_pass') else 'No encontrada'}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    
    with col2:
        st.markdown("### Ingresa tus credenciales")
        
        usuario = st.text_input("DNI o Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary", use_container_width=True):
            usuario_limpio = usuario.strip() if usuario else ""
            password_limpia = password.strip() if password else ""
            
            # Verificar ADMIN
            if usuario_limpio == admin_dni and password_limpia == admin_pass:
                st.success("✅ ACCESO ADMINISTRADOR CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "admin"
                time.sleep(1)
                st.rerun()
            
            # Verificar USUARIO
            elif usuario_limpio == conf_actual.get('user', '') and password_limpia == conf_actual.get('user_pass', ''):
                st.success("✅ ACCESO USUARIO CONCEDIDO")
                st.session_state.admin_logged = True
                st.session_state.admin_tipo = "user"
                time.sleep(1)
                st.rerun()
            
            else:
                st.error("❌ DNI/Usuario o contraseña incorrectos")
                
                # Ayuda
                if usuario_limpio == admin_dni:
                    st.warning("El DNI es correcto pero la contraseña no coincide")
                elif admin_dni:
                    st.info(f"El DNI de administrador configurado es: {admin_dni}")

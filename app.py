def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Cargamos el diccionario desde los Secrets
        info_claves = dict(st.secrets["gcp_service_account"])
        
        # Esta línea es la que evita el error de "Invalid private key"
        info_claves["private_key"] = info_claves["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(info_claves, scopes=scope)
        cliente = gspread.authorize(creds)
        return cliente.open_by_key("1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA")
    except Exception as e:
        st.error(f"⚠️ Error de Credenciales: {e}")
        st.stop()

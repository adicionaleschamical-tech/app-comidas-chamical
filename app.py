import pandas as pd
import re

def limpiar_precio_correcto(texto):
    if pd.isna(texto) or str(texto).strip() == "":
        return 0
    texto_str = str(texto).strip()
    numeros = re.findall(r'\d+', texto_str)
    if numeros:
        numeros_ordenados = sorted(numeros, key=len, reverse=True)
        return int(numeros_ordenados[0])
    return 0

# Cargar pedidos
df = pd.read_csv("URL_DE_TU_SHEET_PEDIDOS")

# Limpiar la columna TOTAL
df['TOTAL_CORREGIDO'] = df['TOTAL'].apply(limpiar_precio_correcto)

# Ver resultados
print(df[['DNI', 'TOTAL', 'TOTAL_CORREGIDO']].head())

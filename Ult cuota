
import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Simulador Revolving", layout="wide")
st.title("💳 Simulador de Préstamo Revolving - Método Francés con Opciones de Cuota")

# ---------------- FUNCIONES ----------------
def simulador(capital: float, interes: float, meses: int, cuota_opcional: float):
    saldo = float(capital)
    i = float(interes) / 12 / 100
    cuota = float(cuota_opcional)
    datos = []

    for mes in range(1, int(meses) + 1):
        interes_mes = saldo * i
        cuota_actual = cuota

        # Ajustar la última cuota si es mayor que el saldo restante
        if saldo < cuota - interes_mes:
            cuota_actual = saldo + interes_mes
            saldo = 0
        else:
            saldo -= (cuota - interes_mes)

        datos.append({
            "Mes": mes,
            "Cuota": round(cuota_actual, 2),
            "Intereses": round(interes_mes, 2),
            "Saldo": round(saldo, 2)
        })

        if saldo <= 0:
            break

    return pd.DataFrame(datos)

# ---------------- INPUTS ----------------
capital = float(st.number_input("Capital inicial (€)", 0.0, 1000000.0, 10000.0))
interes = float(st.number_input("Interés anual (%)", 0.0, 100.0, 18.0))
meses = int(st.number_input("Plazo máximo (meses)", 1, 600, 60))

# Opciones de cuota en porcentaje del capital inicial
opciones_cuota = [2.7, 3, 3.5, 4, 5, 6, 7, 8, 9]
cuota_porcentaje = st.selectbox(
    "Selecciona la cuota mensual (% del capital inicial)",
    opciones_cuota
)

cuota_opcional = float(capital * (cuota_porcentaje / 100))

# ---------------- CALCULO ----------------
if st.button("Calcular"):
    tabla = simulador(capital, interes, meses, cuota_opcional)
    st.dataframe(tabla, use_container_width=True)

    st.download_button(
        "Descargar Excel",
        tabla.to_excel(index=False),
        "amortizacion_revolving.xlsx"
    )

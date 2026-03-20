import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 10

st.set_page_config(page_title="Simulador Préstamo", layout="wide")
st.title("💳 Simulador Préstamo con TAE Correcta")

# ------------------------------
# INPUTS
# ------------------------------
dia_recibo = st.selectbox("Día del recibo", list(range(1, 13)))
capital = st.number_input("Importe de financiación (€)", 0.0, 1000000.0, 6000.0)
tin = st.number_input("TIN anual (%)", 0.0, 100.0, 5.0)
fecha_inicio = st.date_input("Fecha de financiación", datetime.today())
comision_pct = st.number_input("Comisión de apertura (%)", 0.0, 100.0, 2.0)
duracion = st.number_input("Duración (meses)", 1, 600, 24)

seguro_opcion = st.selectbox("Seguro", ["No", "Sí"])
seguro_tasa = Decimal("0.006") if seguro_opcion == "Sí" else Decimal("0")

# ------------------------------
# FUNCIONES DE FECHA
# ------------------------------
def primer_recibo(fecha_inicio, dia_recibo):
    year, month = fecha_inicio.year, fecha_inicio.month
    day = min(dia_recibo, calendar.monthrange(year, month)[1])
    fecha = fecha_inicio.replace(day=day)
    if fecha < fecha_inicio:
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        day = min(dia_recibo, calendar.monthrange(year, month)[1])
        fecha = fecha.replace(year=year, month=month, day=day)
    return fecha

def siguiente_recibo(fecha):
    year, month = fecha.year, fecha.month + 1
    if month > 12:
        month = 1
        year += 1
    day = min(fecha.day, calendar.monthrange(year, month)[1])
    return fecha.replace(year=year, month=month, day=day)

def dias_ano(fecha):
    return 366 if calendar.isleap(fecha.year) else 365

# ------------------------------
# INTERESES EXACTOS
# ------------------------------
def interes_preciso(capital, tin, fecha_inicio, fecha_fin):
    capital = Decimal(str(capital))
    tin = Decimal(str(tin)) / Decimal("100")
    fecha_inicio = pd.to_datetime(fecha_inicio).date()
    fecha_fin = pd.to_datetime(fecha_fin).date()
    dias = (fecha_fin - fecha_inicio).days
    base = dias_ano(fecha_inicio)
    interes = (capital * tin * Decimal(dias) / Decimal(base)).quantize(Decimal("0.00001"))
    return interes

# ------------------------------
# CALCULO CUOTA
# ------------------------------
def calcular_cuota(capital, tin, duracion):
    capital = Decimal(str(capital))
    tin = Decimal(str(tin))
    if tin == 0:
        cuota = capital / Decimal(duracion)
    else:
        r = tin / Decimal("100") / Decimal("12")
        cuota = capital * r * (1 + r) ** duracion / ((1 + r) ** duracion - 1)
    return cuota.quantize(Decimal("0.01"), ROUND_HALF_UP)

# ------------------------------
# SIMULADOR
# ------------------------------
def simulador(capital, tin, fecha_inicio, duracion, dia_recibo, comision, seguro_tasa):
    saldo = Decimal(str(capital))
    cuota = calcular_cuota(capital, tin, duracion)
    fecha_pago = primer_recibo(fecha_inicio, dia_recibo)
    fecha_anterior = fecha_inicio
    datos = []

    for mes in range(1, duracion + 1):
        interes = interes_preciso(saldo, tin, fecha_anterior, fecha_pago).quantize(Decimal("0.01"), ROUND_HALF_UP)
        seguro = ((saldo + interes) * seguro_tasa).quantize(Decimal("0.01"))
        if mes == duracion:
            amort = saldo
            cuota_final = (amort + interes).quantize(Decimal("0.01"))
            saldo = Decimal("0")
        else:
            amort = (cuota - interes).quantize(Decimal("0.01"))
            saldo = (saldo - amort).quantize(Decimal("0.01"))
            cuota_final = cuota
        comision_mes = comision if mes == 1 else Decimal("0")
        datos.append({
            "Mes": mes,
            "Fecha": fecha_pago,
            "Cuota (€)": float(cuota_final),
            "Intereses (€)": float(interes),
            "Amortización (€)": float(amort),
            "Saldo (€)": float(saldo),
            "Seguro (€)": float(seguro),
            "Comisión (€)": float(comision_mes),
            "Total recibo (€)": float(cuota_final + seguro + comision_mes)
        })
        fecha_anterior = fecha_pago
        fecha_pago = siguiente_recibo(fecha_pago)
    return pd.DataFrame(datos)

# ------------------------------
# CALCULO TAE (NEWTON-RAPHSON ESTABLE)
# ------------------------------
def calcular_tae(flujos, fechas):
    tiempos = [0.0]
    for i in range(1, len(fechas)):
        f0 = pd.to_datetime(fechas[i-1]).date()
        f1 = pd.to_datetime(fechas[i]).date()
        dias = (f1 - f0).days
        base = 366 if calendar.isleap(f0.year) else 365
        tiempos.append(tiempos[-1] + dias / base)

    def van(tasa):
        return sum(f / ((1 + tasa) ** t) for f, t in zip(flujos, tiempos))

    def dvan(tasa):
        return sum(-t * f / ((1 + tasa) ** (t + 1)) for f, t in zip(flujos, tiempos))

    tasa = 0.05
    for _ in range(100):
        v = van(tasa)
        dv = dvan(tasa)
        if abs(dv) < 1e-10:
            break
        nueva = tasa - v / dv
        if abs(nueva - tasa) < 1e-10:
            return round(nueva * 100, 2)
        tasa = nueva
    return round(tasa * 100, 2)

# ------------------------------
# CALCULAR Y MOSTRAR RESULTADOS
# ------------------------------
if st.button("Calcular"):

    comision = (Decimal(str(capital)) * Decimal(str(comision_pct)) / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    st.write(f"💰 Comisión de apertura: {float(comision)} €")

    tabla = simulador(capital, tin, fecha_inicio, duracion, dia_recibo, comision, seguro_tasa)
    st.dataframe(tabla, use_container_width=True)

    # Flujos TAE (solo comisión en el inicio + cuotas)
    flujo_inicial = float(capital - comision)
    flujos_mensuales = pd.to_numeric(tabla["Cuota (€)"], errors='coerce').astype(float).tolist()
    flujos = [flujo_inicial] + flujos_mensuales
    fechas = [fecha_inicio] + list(tabla["Fecha"])
    tae = calcular_tae(flujos, fechas)

    # Resumen
    resumen = {
        "Concepto": [
            "Duración",
            "Cuota",
            "Total intereses",
            "Total seguro",
            "Comisión apertura",
            "Coste total",
            "TAE (%)"
        ],
        "Valor": [
            duracion,
            float(calcular_cuota(capital, tin, duracion)),
            round(tabla["Intereses (€)"].sum(), 2),
            round(tabla["Seguro (€)"].sum(), 2),
            float(comision),
            round(tabla["Total recibo (€)"].sum(), 2),
            tae
        ]
    }
    st.subheader("Resumen")
    st.table(pd.DataFrame(resumen))

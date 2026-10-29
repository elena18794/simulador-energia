import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURACIÓN GENERAL DE LA APLICACIÓN WEB
# ==============================================================================
st.set_page_config(
    page_title="Simulador Energético & Comparador de Ofertas | Elena Ríos Martín",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Simulador Energético Residencial y Comparador de Ofertas")
st.markdown(
    """**Desarrollado por Elena Ríos Martín** | Grado en Física (UGR) · Data Science & IA  
    Introduce tus tarifas manualmente y compara al instante la transición a autoconsumo solar y aerotermia."""
)
st.divider()

# ==============================================================================
# 2. GESTIÓN DE OFERTAS PERSONALIZADAS
# ==============================================================================
if "lista_ofertas" not in st.session_state:
    st.session_state.lista_ofertas = [
        {"nombre": "Oferta 1: Tarifa Solar + Batería Virtual", "kwh": 0.124, "pot": 0.088, "exc": 0.085, "fee": 0.0, "bono": 0.0},
        {"nombre": "Oferta 2: Mercado Libre Económica", "kwh": 0.115, "pot": 0.092, "exc": 0.050, "fee": 0.0, "bono": 30.0},
        {"nombre": "Oferta 3: Comercializadora Tradicional Promo", "kwh": 0.138, "pot": 0.102, "exc": 0.070, "fee": 2.5, "bono": 50.0},
    ]

with st.sidebar:
    st.header("⚡ 1. Factura y Consumo")
    nombre_cliente = st.text_input("Nombre / Vivienda", value="Estudio Personalizado")
    consumo_elec = st.slider("Consumo Eléctrico Anual (kWh/año)", 1000, 12000, 3600, 100)
    
    col_p1, col_p2 = st.columns(2)
    potencia_kw = col_p1.number_input("Potencia (kW)", 2.3, 15.0, 4.6, 0.1)
    precio_elec_actual = col_p2.number_input("Tu Energía Actual (€/kWh)", 0.060, 0.450, 0.188, 0.005, format="%.3f")
    precio_pot_actual = st.number_input("Tu Potencia Actual (€/kW·día)", 0.030, 0.250, 0.108, 0.005, format="%.3f")

    st.header("🔥 2. Gas Natural y Aerotermia")
    tiene_gas = st.checkbox("¿Vivienda con Gas Natural?", value=True)
    if tiene_gas:
        consumo_gas = st.slider("Consumo Gas Anual (kWh/año)", 500, 15000, 4800, 200)
        cg1, cg2 = st.columns(2)
        precio_gas_actual = cg1.number_input("Gas Actual (€/kWh)", 0.040, 0.250, 0.088, 0.002, format="%.3f")
        fijo_gas_actual = cg2.number_input("Fijo Gas (€/mes)", 3.0, 25.0, 6.80, 0.20)
        
        cg3, cg4 = st.columns(2)
        precio_gas_opt = cg3.number_input("Gas Oferta/TUR (€/kWh)", 0.030, 0.200, 0.058, 0.002, format="%.3f")
        fijo_gas_opt = cg4.number_input("Fijo Oferta Gas (€/mes)", 2.0, 20.0, 5.20, 0.20)
        
        usar_aerotermia = st.checkbox("Simular cambio a Aerotermia (SCOP 3.8)", value=True)
        scop_aero = st.slider("Rendimiento Aerotermia (SCOP)", 2.5, 5.0, 3.8, 0.1) if usar_aerotermia else 1.0
    else:
        consumo_gas, precio_gas_actual, fijo_gas_actual = 0.0, 0.0, 0.0
        precio_gas_opt, fijo_gas_opt, usar_aerotermia, scop_aero = 0.0, 0.0, False, 1.0

    st.header("☀️ 3. Ingeniería Solar")
    provincias_hsp = {
        "Granada / Andalucía Oriental (5.25 HSP)": 5.25,
        "Sevilla / Córdoba / Huelva (5.35 HSP)": 5.35,
        "Málaga / Almería / Murcia (5.15 HSP)": 5.15,
        "Madrid / Zona Centro (4.85 HSP)": 4.85,
        "Barcelona / Levante (4.65 HSP)": 4.65,
        "Bilbao / Coruña / Norte (3.75 HSP)": 3.75
    }
    prov_sel = st.selectbox("Ubicación (HSP)", list(provincias_hsp.keys()), index=0)
    hsp_base = provincias_hsp[prov_sel]

    num_placas = st.slider("Número de Placas Solares", 2, 24, 8, 1)
    cs1, cs2 = st.columns(2)
    pot_placa_w = cs1.selectbox("Potencia Placa (Wp)", [420, 455, 500, 550], index=1)
    orientacion_dict = {"Sur (0° Óptima)": 1.00, "Sureste / Suroeste (-6%)": 0.94, "Este / Oeste (-17%)": 0.83}
    orient_sel = cs2.selectbox("Orientación", list(orientacion_dict.keys()), index=0)
    factor_orientacion = orientacion_dict[orient_sel]

    inclinacion = st.slider("Inclinación Tejado θ (°)", 5, 60, 32, 1)
    bateria_kwh = st.slider("Batería Física (kWh)", 0.0, 15.0, 0.0, 2.5)
    
    ci1, ci2 = st.columns(2)
    coste_instalacion = ci1.number_input("Coste Instalación (€)", 1000, 30000, 4600, 100)
    subvencion = ci2.number_input("Subvención / IBI (€)", 0, 15000, 900, 100)

# ==============================================================================
# 3. BLOQUE INTERACTIVO PARA AÑADIR TARIFA MANUALMENTE
# ==============================================================================
st.subheader("➕ Añade una Nueva Oferta o Tarifa Manualmente")
with st.form("form_nueva_oferta", clear_on_submit=True):
    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
    n_nombre = fc1.text_input("Nombre Oferta", "Oferta Personalizada")
    n_kwh = fc2.number_input("€/kWh", 0.030, 0.350, 0.120, 0.005, format="%.3f")
    n_pot = fc3.number_input("€/kW·día", 0.020, 0.200, 0.085, 0.005, format="%.3f")
    n_exc = fc4.number_input("Exced. €/kWh", 0.010, 0.200, 0.075, 0.005, format="%.3f")
    n_fee = fc5.number_input("Cuota €/mes", 0.0, 20.0, 0.0, 0.5)
    n_bon = fc6.number_input("Bono €/año", 0.0, 200.0, 0.0, 10.0)
    
    btn_agregar = st.form_submit_button("Añadir Oferta a la Comparativa")
    if btn_agregar:
        st.session_state.lista_ofertas.append({
            "nombre": n_nombre,
            "kwh": n_kwh,
            "pot": n_pot,
            "exc": n_exc,
            "fee": n_fee,
            "bono": n_bon
        })
        st.success(f"¡Oferta '{n_nombre}' añadida correctamente!")

# ==============================================================================
# 4. MOTOR FÍSICO Y CÁLCULOS
# ==============================================================================
potencia_pico_kwp = (num_placas * pot_placa_w) / 1000.0
superficie_m2 = num_placas * 2.1
factor_inclinacion = max(0.75, 1.0 - 0.00016 * ((inclinacion - 33.0) ** 2))
pr_efectivo = 0.81 * factor_orientacion * factor_inclinacion
produccion_anual_kwh = potencia_pico_kwp * hsp_base * 365.0 * pr_efectivo

iva_elec = 1.271
iva_gas = 1.21

s1_elec = ((potencia_kw * precio_pot_actual * 365.0) + (consumo_elec * precio_elec_actual)) * iva_elec
s1_gas = ((fijo_gas_actual * 12.0) + (consumo_gas * precio_gas_actual)) * iva_gas if tiene_gas else 0.0
s1_total = s1_elec + s1_gas

gas_opt_anual = ((fijo_gas_opt * 12.0) + (consumo_gas * precio_gas_opt)) * iva_gas if tiene_gas else 0.0

ratio_autoconsumo = min(0.88, 0.44 + (bateria_kwh * 0.042))
autoconsumo_s3 = min(consumo_elec, produccion_anual_kwh * ratio_autoconsumo)
excedentes_s3 = max(0.0, produccion_anual_kwh - autoconsumo_s3)
red_s3 = max(0.0, consumo_elec - autoconsumo_s3)

demanda_extra_aero = (consumo_gas * 0.90 / scop_aero) if (tiene_gas and usar_aerotermia) else 0.0
demanda_total_s4 = consumo_elec + demanda_extra_aero
autoconsumo_s4 = min(demanda_total_s4, produccion_anual_kwh * min(0.90, ratio_autoconsumo + 0.05))
excedentes_s4 = max(0.0, produccion_anual_kwh - autoconsumo_s4)
red_s4 = max(0.0, demanda_total_s4 - autoconsumo_s4)

def calcular_coste(red, exc, pot, of):
    coste_p = pot * of["pot"] * 365.0
    energia_neta = max(0.0, (red * of["kwh"]) - (exc * of["exc"]))
    cuotas = of["fee"] * 12.0
    return max(0.0, ((coste_p + energia_neta + cuotas) * iva_elec) - of["bono"])

resultados = []
for idx, of in enumerate(st.session_state.lista_ofertas):
    sin_p = calcular_coste(consumo_elec, 0.0, potencia_kw, of) + gas_opt_anual
    con_p = (calcular_coste(red_s4, excedentes_s4, potencia_kw, of) if (tiene_gas and usar_aerotermia) else (calcular_coste(red_s3, excedentes_s3, potencia_kw, of) + gas_opt_anual))
    ahorro = max(0.0, s1_total - con_p)
    resultados.append({
        "id": idx,
        "Oferta": of["nombre"],
        "SIN Placas (€/año)": round(sin_p, 0),
        "CON Placas (€/año)": round(con_p, 0),
        "Ahorro Total (€/año)": round(ahorro, 0),
        "_con_p": con_p,
        "_sin_p": sin_p
    })

df_res = pd.DataFrame(resultados)

st.subheader("🏷️ 2. Tabla Comparativa de Ofertas del Cliente")
nombres_ofertas = df_res["Oferta"].tolist()
oferta_elegida = st.selectbox("Selecciona la oferta para analizar en detalle:", nombres_ofertas)

col_b1, col_b2 = st.columns([1, 4])
if col_b1.button("🗑️ Eliminar Oferta Seleccionada"):
    if len(st.session_state.lista_ofertas) > 1:
        idx_borrar = nombres_ofertas.index(oferta_elegida)
        st.session_state.lista_ofertas.pop(idx_borrar)
        st.rerun()
    else:
        st.warning("Debe quedar al menos una oferta.")

st.dataframe(df_res[["Oferta", "SIN Placas (€/año)", "CON Placas (€/año)", "Ahorro Total (€/año)"]], use_container_width=True, hide_index=True)

row_activa = df_res[df_res["Oferta"] == oferta_elegida].iloc[0]
s2_total = row_activa["_sin_p"]
s2_ahorro = max(0.0, s1_total - s2_total)
s4_total = row_activa["_con_p"]
s4_ahorro = max(0.0, s1_total - s4_total)

inversion_neta = max(500.0, coste_instalacion - subvencion)
payback = (inversion_neta / s4_ahorro) if s4_ahorro > 0 else 99.0

st.subheader(f"📊 3. Escenarios para {nombre_cliente}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("1. Situación Actual", f"{s1_total:,.0f} €/año", f"{s1_total/12:,.0f} €/mes")
c2.metric("2. Solo Oferta (Sin Obras)", f"{s2_total:,.0f} €/año", f"Ahorras -{s2_ahorro:,.0f} €/año")
c3.metric("3. Placas + Oferta", f"{s4_total:,.0f} €/año", f"Ahorras -{s4_ahorro:,.0f} €/año")
c4.metric("Amortización (Payback)", f"{payback:.1f} años", f"Inversión neta: {inversion_neta:,.0f} €")

st.divider()

anos = np.arange(1, 26)
acum_actual, acum_solar = [], []
c_act, c_sol = 0.0, inversion_neta
for t in anos:
    f_inf = (1.03) ** (t - 1)
    f_deg = (0.995) ** (t - 1)
    c_act += s1_total * f_inf
    c_sol += (s4_total / f_deg) * f_inf
    acum_actual.append(c_act)
    acum_solar.append(c_sol)

fig = go.Figure()
fig.add_trace(go.Scatter(x=anos, y=acum_actual, name="Gasto Actual Acumulado", line=dict(color="#ef4444", width=3)))
fig.add_trace(go.Scatter(x=anos, y=acum_solar, name="Gasto Con Oferta + Solar", line=dict(color="#10b981", width=4)))
fig.update_layout(title="📈 Evolución del Gasto Acumulado a 25 Años (€)", xaxis_title="Años", yaxis_title="€ Acumulados", template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

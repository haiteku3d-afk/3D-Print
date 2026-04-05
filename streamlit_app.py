import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calculadora 3D - Bambu Lab A1", page_icon="🖨️")

# --- FUNCIONES DE CÁLCULO ---
def calcular_costos(peso_g, tiempo_total_h, costo_kg, kwh_precio, watts, costo_repuesto, vida_util_h, margen_error):
    # Costo Material
    costo_material = (costo_kg / 1000) * peso_g
    
    # Costo Energía
    costo_energia = (watts / 1000) * tiempo_total_h * kwh_precio
    
    # Costo Desgaste (Basado en hotend de Bambu Lab)
    costo_desgaste = (costo_repuesto / vida_util_h) * tiempo_total_h
    
    costo_subtotal = costo_material + costo_energia + costo_desgaste
    costo_total = costo_subtotal * (1 + (margen_error / 100))
    
    return round(costo_total)

# --- INTERFAZ ---
st.title("🖨️ Calculadora de Costos - Bambu Lab A1")

with st.sidebar:
    st.header("⚙️ Configuración Global")
    # Valores típicos para Chile (Ajusta el kWh según tu cuenta de Enel/CGE)
    costo_kg = st.number_input("Precio Filamento (CLP/kg)", value=20000)
    kwh_precio = st.number_input("Precio Energía (CLP/kWh)", value=150)
    watts = st.number_input("Consumo A1 (Watts)", value=130)
    costo_repuesto = st.number_input("Costo Repuesto (Hotend CLP)", value=15000)
    vida_util_h = st.number_input("Vida Útil Repuesto (Horas)", value=2500)
    margen_error = st.slider("Margen de Error (%)", 0, 20, 5)

# Formulario de nueva impresión
with st.container():
    st.subheader("📊 Nueva Impresión")
    
    nombre_pieza = st.text_input("Nombre de la pieza")
    
    col_g, col_h, col_m = st.columns(3)
    with col_g:
        peso_g = st.number_input("Gramos (Slicer)", min_value=0.1, step=0.1)
    with col_h:
        h_input = st.number_input("Horas", min_value=0, step=1)
    with col_m:
        m_input = st.number_input("Minutos", min_value=0, max_value=59, step=1)
    
    # Convertir tiempo a decimal para el cálculo
    tiempo_decimal = h_input + (m_input / 60)
    
    # Selector de estrategia con nombres claros
    dict_estrategias = {
        "3 - Mayorista": 3,
        "4 - Minorista": 4,
        "5 - Llavero": 5
    }
    seleccion_estrategia = st.selectbox("Estrategia de Venta", options=list(dict_estrategias.keys()))
    multiplicador = dict_estrategias[seleccion_estrategia]

    if st.button("Calcular y Guardar"):
        if tiempo_decimal == 0:
            st.error("El tiempo no puede ser 0")
        else:
            costo_final = calcular_costos(peso_g, tiempo_decimal, costo_kg, kwh_precio, watts, costo_repuesto, vida_util_h, margen_error)
            precio_venta = round(costo_final * multiplicador)
            
            # Guardar en Historial
            nueva_fila = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Pieza": nombre_pieza,
                "Costo Fab.": f"${costo_final:,} CLP",
                "Precio Venta": f"${precio_venta:,} CLP",
                "Ganancia": f"${(precio_venta - costo_final):,} CLP"
            }
            
            df_nuevo = pd.DataFrame([nueva_fila])
            
            if not os.path.isfile("historial_3d.csv"):
                df_nuevo.to_csv("historial_3d.csv", index=False)
            else:
                df_nuevo.to_csv("historial_3d.csv", mode='a', header=False, index=False)
                
            st.success(f"✅ ¡Guardado! Costo: ${costo_final:,} | Venta sugerida: ${precio_venta:,} CLP")

# --- SECCIÓN DE HISTORIAL ---
st.divider()
st.subheader("📜 Historial de Impresiones")

if os.path.isfile("historial_3d.csv"):
    historial = pd.read_csv("historial_3d.csv")
    st.dataframe(historial.sort_index(ascending=False), use_container_width=True)
    st.download_button("Descargar Excel (CSV)", historial.to_csv(index=False), "historial_3d.csv", "text/csv")
else:
    st.info("Aún no hay registros.")

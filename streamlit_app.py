import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Bambu Lab A1 - Calculadora Pro", layout="wide")

# --- 1. FUNCIONES DE CÁLCULO ---
def calcular_detalles(peso_g, tiempo_h, c_kg, kwh, w, c_rep, v_util, m_err):
    # Aplicamos el factor de margen (ej: 1.07 para 7%) a cada componente
    factor_margen = 1 + (m_err / 100)
    
    costo_fil = ((c_kg / 1000) * peso_g) * factor_margen
    costo_ene = ((w / 1000) * tiempo_h * kwh) * factor_margen
    costo_des = ((c_rep / v_util) * tiempo_h) * factor_margen
    
    total_con_margen = costo_fil + costo_ene + costo_des
    
    return {
        "total": round(total_con_margen),
        "filamento": round(costo_fil),
        "energia": round(costo_ene),
        "desgaste": round(costo_des)
    }

# --- 2. GESTIÓN DE ARCHIVOS (CSV LOCAL) ---
def cargar_config():
    if os.path.exists('config.csv'):
        try:
            df = pd.read_csv('config.csv')
            return dict(zip(df['Parámetro'], df['Valor']))
        except:
            pass
    return {"costo_kg": 15000, "kwh_precio": 265, "watts": 130, "costo_repuesto": 40000, "vida_util_h": 2500, "margen_error": 7}

def guardar_config(datos):
    df = pd.DataFrame(list(datos.items()), columns=['Parámetro', 'Valor'])
    df.to_csv('config.csv', index=False)

def guardar_historial(nueva_fila):
    archivo = 'impresiones.csv'
    df_nueva = pd.DataFrame([nueva_fila])
    if not os.path.exists(archivo):
        df_nueva.to_csv(archivo, index=False)
    else:
        # Usamos lineterminator para asegurar el salto de línea correcto
        df_nueva.to_csv(archivo, mode='a', header=False, index=False, lineterminator='\n')

# --- 3. CARGAR DATOS INICIALES ---
conf = cargar_config()

# --- 4. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    st.info("Estos valores se usan para todos los cálculos.")
    
    c_kg = st.number_input("Precio Filamento (CLP/kg)", value=int(conf.get("costo_kg", 15000)))
    p_kwh = st.number_input("Precio Energía (CLP/kWh)", value=int(conf.get("kwh_precio", 265)))
    w_avg = st.number_input("Consumo Watts (A1)", value=int(conf.get("watts", 130)))
    c_rep = st.number_input("Costo Repuestos (CLP)", value=int(conf.get("costo_repuesto", 40000)))
    v_util = st.number_input("Vida útil Repuesto (Horas)", value=int(conf.get("vida_util_h", 2500)))
    m_err = st.slider("Margen de Seguridad (%)", 0, 20, int(conf.get("margen_error", 7)))
    
    if st.button("💾 Guardar Precios Permanentes"):
        nuevos_precios = {
            "costo_kg": c_kg, "kwh_precio": p_kwh, "watts": w_avg,
            "costo_repuesto": c_rep, "vida_util_h": v_util, "margen_error": m_err
        }
        guardar_config(nuevos_precios)
        st.success("¡Configuración guardada!")

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🖨️ Calculadora de Costos - Bambu Lab A1")

col_input, col_empty = st.columns([2, 1])

with col_input:
    st.subheader("📊 Datos de la Pieza")
    nombre = st.text_input("Nombre del Proyecto / Pieza", placeholder="Ej: Llavero Oso")
    
    c1, c2, c3 = st.columns(3)
    with c1: gramos = st.number_input("Gramos totales", min_value=0.1, step=0.1)
    with c2: h_in = st.number_input("Horas", min_value=0, step=1)
    with c3: m_in = st.number_input("Minutos", min_value=0, max_value=59, step=1)

    t_decimal = h_in + (m_in / 60)
    
    estrategia = st.selectbox("Estrategia de Venta", ["3 - Mayorista", "4 - Minorista", "5 - Llavero"])
    mult = int(estrategia.split(" - ")[0])

# --- 6. PROCESAR Y MOSTRAR RESULTADOS ---
if st.button("🚀 Calcular y Registrar Impresión", use_container_width=True):
    if nombre == "" or t_decimal == 0:
        st.error("Faltan datos de la pieza o tiempo de impresión.")
    else:
        res = calcular_detalles(gramos, t_decimal, c_kg, p_kwh, w_avg, c_rep, v_util, m_err)
        
        precio_v = round(res["total"] * mult)
        costo_f = res["total"]
        ganancia = precio_v - costo_f

        # DESPLIEGUE DE RESULTADOS (Cuadro Verde)
        st.divider()
        st.success(f"### 💰 Sugerencia de Venta: ${precio_v:,} CLP")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Costo Fabricación", f"${costo_f:,}")
        m2.metric("Ganancia Estimada", f"${ganancia:,}")
        m3.metric("Multiplicador", f"x{mult}")
        
        # GUARDAR EN HISTORIAL
        registro = {
            "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Pieza": nombre,
            "Costo Fab": costo_f,
            "Precio Venta": precio_v,
            "Ganancia": ganancia,
            "Tiempo": f"{h_in}h {m_in}m",
            "Filamento": res["filamento"],
            "Energia": res["energia"],
            "Desgaste": res["desgaste"]
        }
        guardar_historial(registro)
        st.balloons()

# --- 7. HISTORIAL Y BORRADO ---
st.divider()
st.subheader("📜 Historial de Impresiones")

if os.path.exists('impresiones.csv'):
    df_hist = pd.read_csv('impresiones.csv')
    if not df_hist.empty:
        # Mostramos la tabla (lo más nuevo arriba)
        st.dataframe(df_hist.iloc[::-1], use_container_width=True)
        
        # ZONA DE BORRADO
        with st.expander("🗑️ Zona de Peligro: Eliminar Registros"):
            # Creamos lista de opciones identificables
            lista_piezas = df_hist.apply(lambda x: f"{x['Fecha']} | {x['Pieza']}", axis=1).tolist()
            seleccion = st.selectbox("Selecciona el registro a eliminar:", lista_piezas)
            
            if st.button("Confirmar Eliminación", type="primary"):
                # Encontramos el índice real en el dataframe original
                idx_to_remove = lista_piezas.index(seleccion)
                df_hist = df_hist.drop(df_hist.index[idx_to_remove])
                # Guardamos el CSV actualizado
                df_hist.to_csv('impresiones.csv', index=False)
                st.success("Registro eliminado.")
                st.rerun() # Recarga la página para limpiar la tabla
        
        # BOTÓN DE DESCARGA
        with open('impresiones.csv', 'rb') as f:
            st.download_button('📥 Descargar Historial (CSV)', f, file_name='historial_bambu_a1.csv')
    else:
        st.info("El historial está vacío.")
else:
    st.info("No hay datos registrados aún.")
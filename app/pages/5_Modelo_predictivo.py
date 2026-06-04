# -*- coding: utf-8 -*-
import sys
import json
import pickle
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.page_utils import setup_page
from app.narrative import render_cierre_etapa, render_kpis_etapa
from app.text_es import UI
from app.theme import COLOR_PRIMARY, PLOTLY_CONFIG

# Setup Streamlit page using the framework's helper
data = setup_page("modelo")
render_kpis_etapa("modelo", data)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_PATH = PROCESSED_DIR / "random_forest.pkl"
METRICS_PATH = PROCESSED_DIR / "model_metrics.json"
FEATURES_PATH = PROCESSED_DIR / "model_features.json"

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_metadata():
    if not METRICS_PATH.exists() or not FEATURES_PATH.exists():
        return None, None
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
    return metrics, features

pipeline = load_model()
metrics, features_meta = load_metadata()

if pipeline is None or metrics is None or features_meta is None:
    st.error("El modelo predictivo no se encuentra entrenado o faltan los archivos de metadatos.")
    st.info("Por favor, asegúrese de ejecutar primero el pipeline de entrenamiento: `python analysis/run.py`")
    st.stop()

# Layout of the page
st.markdown("### Clasificación de Conflictos Interpersonales")
st.markdown(
    """
    Este modelo utiliza un **Bosque Aleatorio (Random Forest)** supervisado para predecir el vínculo o relación 
    del agresor con la víctima (`presunto_agresor`). A diferencia del análisis puramente descriptivo, 
    este algoritmo analiza las correlaciones entre el perfil de la víctima y el contexto situacional de la agresión 
    para clasificar el hecho en una de 5 dinámicas relacionales diferentes.
    """
)

# Tabs: Simulator vs Technical Report
tab_sim, tab_metrics = st.tabs(["Simulador de Triage", "Ficha Técnica y Métricas"])

with tab_sim:
    st.markdown("##### Ingrese los detalles de la agresión para estimar el vínculo del agresor:")
    
    # Form layout with 3 columns
    c1, c2, c3 = st.columns(3)
    
    # Map raw features to readable Spanish labels
    LABELS = {
        "sexo_victima": "Sexo de la víctima",
        "ciclo_vital": "Ciclo vital de la víctima",
        "zona_hecho": "Zona del hecho",
        "escenario_hecho": "Escenario del hecho",
        "mecanismo_causal": "Mecanismo de la lesión",
        "rango_hora": "Franja horaria",
        "fin_semana": "¿Ocurrió en fin de semana?"
    }

    # Features order and lists from metadata
    with c1:
        sexo = st.selectbox(LABELS["sexo_victima"], features_meta["sexo_victima"])
        ciclo = st.selectbox(LABELS["ciclo_vital"], features_meta["ciclo_vital"])
    
    with c2:
        zona = st.selectbox(LABELS["zona_hecho"], features_meta["zona_hecho"])
        escenario = st.selectbox(LABELS["escenario_hecho"], features_meta["escenario_hecho"])
        
    with c3:
        mecanismo = st.selectbox(LABELS["mecanismo_causal"], features_meta["mecanismo_causal"])
        franja = st.selectbox(LABELS["rango_hora"], features_meta["rango_hora"])
        # Weekend is stored as string 'True'/'False' in unique features metadata
        weekend_options = features_meta["fin_semana"]
        weekend_sel = st.selectbox(
            LABELS["fin_semana"], 
            weekend_options,
            format_func=lambda x: "Sí (Sábado/Domingo)" if x == "True" else "No (Lunes a Viernes)"
        )
    
    # Prediction button
    if st.button("Analizar Conflicto", type="primary", use_container_width=True):
        # Build input row
        input_data = pd.DataFrame([{
            "sexo_victima": sexo,
            "ciclo_vital": ciclo,
            "zona_hecho": zona,
            "escenario_hecho": escenario,
            "mecanismo_causal": mecanismo,
            "fin_semana": True if weekend_sel == "True" else False,
            "rango_hora": franja
        }])
        
        # Run prediction
        try:
            pred_class = pipeline.predict(input_data)[0]
            pred_probs = pipeline.predict_proba(input_data)[0]
            classes = pipeline.classes_
            
            # Map probabilities
            prob_df = pd.DataFrame({
                "Vínculo": classes,
                "Probabilidad": pred_probs
            }).sort_values(by="Probabilidad", ascending=True)
            
            st.markdown("---")
            
            # Visual styling for the predicted class
            st.markdown(
                f"""
                <div style="background-color: #f0f4f8; border-left: 5px solid {COLOR_PRIMARY}; padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                    <h4 style="margin: 0; color: #1e3a8a;">Resultado del Triage:</h4>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 600; color: #0f172a;">
                        Predicción: <span style="color: {COLOR_PRIMARY};">{pred_class}</span>
                    </p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.95rem; color: #475569;">
                        Probabilidad asignada por el modelo: <b>{pred_probs[list(classes).index(pred_class)] * 100:.1f}%</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Plotly Horizontal Bar Chart for Probabilities
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=prob_df["Vínculo"],
                x=prob_df["Probabilidad"] * 100,
                orientation='h',
                marker=dict(color=COLOR_PRIMARY),
                text=[f"{p * 100:.1f}%" for p in prob_df["Probabilidad"]],
                textposition='auto',
                textfont=dict(color='white')
            ))
            fig.update_layout(
                title="Distribución de Probabilidad del Vínculo",
                xaxis_title="Probabilidad (%)",
                yaxis_title="Vínculo Estimado",
                height=350,
                margin=dict(l=20, r=20, t=40, b=40)
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
            
            # Criminological Interpretation
            st.markdown("##### Interpretación y Recomendación de Intervención:")
            interpretations = {
                "Conocido sin trato": (
                    "Este perfil suele estar asociado a altercados comunitarios fortuitos con personas del entorno general "
                    "(por ejemplo, transeúntes habituales o clientes de establecimientos comerciales). "
                    "**Acción recomendada:** Fortalecer la mediación policial en el cuadrante y control de factores detonantes como el consumo de alcohol."
                ),
                "Desconocido/Delincuencia": (
                    "Agresiones perpetradas por personas no identificadas, comúnmente vinculadas a delincuencia común (hurtos) o pandillas en vía pública. "
                    "**Acción recomendada:** Intervención de seguridad pública tradicional (patrullaje selectivo, cámaras de seguridad e iluminación urbana)."
                ),
                "Vecino": (
                    "Conflictos por convivencia ciudadana en entornos residenciales directos (riñas por ruido, linderos o intolerancia local). "
                    "**Acción recomendada:** Activación de **Centros de Conciliación y Mediación Comunitaria** para evitar el escalamiento del conflicto."
                ),
                "Fuerza Pública": (
                    "Registros que involucran agentes de policía, militares o personal de custodia, comúnmente en escenarios de control de orden público o centros de reclusión. "
                    "**Acción recomendada:** Revisión de protocolos de uso de la fuerza y auditoría interna de derechos humanos en el territorio correspondiente."
                ),
                "Amistad/Entorno": (
                    "Hechos de violencia entre amigos, compañeros de estudio o de trabajo en escenarios educativos o laborales. "
                    "**Acción recomendada:** Implementación de programas de convivencia escolar/laboral, rutas de bienestar institucional y canales de resolución no violenta de conflictos."
                )
            }
            st.info(interpretations.get(pred_class, "Patrón de agresión identificado. Requiere análisis situacional estándar."))
            
        except Exception as e:
            st.error(f"Error al realizar la predicción: {e}")

with tab_metrics:
    st.markdown("##### Ficha Técnica del Bosque Aleatorio (Random Forest)")
    st.markdown(
        f"""
        Para evaluar científicamente la calidad de este modelo, se aplicó una división de datos:
        - **80% de los datos** para el entrenamiento del algoritmo.
        - **20% de los datos** para prueba (Test) de generalización.
        
        **Exactitud en el conjunto de prueba (Test Accuracy):** `{metrics["accuracy"] * 100:.2f}%`
        *(Una exactitud del {metrics["accuracy"] * 100:.1f}% es significativa en este dominio, considerando que clasifica de forma balanceada entre 5 categorías bien distribuidas donde una predicción aleatoria sería de solo el 20%).*
        """
    )
    
    # Classification Report DataFrame
    report_dict = metrics["classification_report"]
    report_rows = []
    for cls_name, vals in report_dict.items():
        if cls_name in ["accuracy", "macro avg", "weighted avg"]:
            continue
        report_rows.append({
            "Vínculo": cls_name,
            "Precisión (Precision)": f"{vals['precision'] * 100:.2f}%",
            "Sensibilidad (Recall)": f"{vals['recall'] * 100:.2f}%",
            "F1-Score": f"{vals['f1-score'] * 100:.2f}%",
            "Muestras de Prueba": f"{vals['support']:,}"
        })
    
    report_df = pd.DataFrame(report_rows)
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    
    # Explainability / Feature Importances
    st.markdown("---")
    st.markdown("##### Importancia de Variables en el Bosque Aleatorio")
    st.markdown(
        "Muestra qué características del contexto de la agresión influyen más en la predicción del vínculo del agresor:"
    )
    
    # Process and sum importances by original feature
    classifier = pipeline.named_steps['classifier']
    onehot_features = pipeline.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out()
    importances = classifier.feature_importances_
    
    original_importances = {feat: 0.0 for feat in features_meta.keys()}
    for feat_name, imp in zip(onehot_features, importances):
        for orig in features_meta.keys():
            if feat_name.startswith(orig + "_") or feat_name == orig:
                original_importances[orig] += imp
                break
                
    imp_df = pd.DataFrame([
        {"Variable": LABELS[feat], "Importancia (%)": val * 100}
        for feat, val in original_importances.items()
    ]).sort_values(by="Importancia (%)", ascending=True)
    
    # Plot feature importances
    fig_imp = go.Figure()
    fig_imp.add_trace(go.Bar(
        y=imp_df["Variable"],
        x=imp_df["Importancia (%)"],
        orientation='h',
        marker=dict(color="#4f46e5"),
        text=[f"{val:.1f}%" for val in imp_df["Importancia (%)"]],
        textposition='outside'
    ))
    fig_imp.update_layout(
        xaxis_title="Importancia Relativa (%)",
        yaxis_title="Variable del Contexto",
        height=320,
        margin=dict(l=20, r=50, t=20, b=20)
    )
    st.plotly_chart(fig_imp, use_container_width=True, config=PLOTLY_CONFIG)

render_cierre_etapa("modelo")

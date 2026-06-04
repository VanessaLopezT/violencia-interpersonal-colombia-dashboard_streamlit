# Violencia interpersonal en Colombia (2015-2024)

Proyecto universitario de analítica de datos sobre casos **registrados** de violencia interpersonal. Metodología CRISP-DM, cubo OLAP precomputado y dashboard Streamlit como guion visual para sustentación.

## Ejecución

```bash
pip install -r requirements.txt
python analysis/run.py
streamlit run app/streamlit_app.py
```

`run.py` genera el dataset limpio y cinco agregados para el dashboard:

| Archivo | Rol |
|---------|-----|
| `data/processed/dataset.parquet` | **Formato principal** del pipeline (OLAP, clustering, figuras) |
| `data/processed/dataset_limpio.csv` | Mismas filas y columnas que el parquet; **solo inspección, auditoría y comparación** (UTF-8) |

Ambos tienen **26 columnas analíticas** y **981.611 registros** tras `src/prepare.py`. El dashboard **no** carga el dataset completo; usa agregados OLAP.

`run.py` también genera:
`agg_filtros`, `agg_territorial`, `agg_demografia`, `agg_patrones`, `agg_dia_hora` (más
el modelo `random_forest.pkl`, las métricas de prueba `model_metrics.json` y los metadatos `model_features.json`).
Streamlit **no** carga el dataset completo de ~980k filas; usa solo esos agregados OLAP y el modelo entrenado.

## Estructura

```text
data/raw/                 CSV original (INMLCF)
data/processed/           dataset.parquet, dataset_limpio.csv, agg_*.parquet
src/prepare.py            limpieza y preprocesamiento
analysis/run.py           pipeline CRISP-DM + agregados OLAP
app/
  analytics.py            agregacion OLAP (pandas puro)
  data_loader.py          carga de Parquet
  filters.py              sidebar + cache Streamlit
  charts.py               Plotly
  narrative.py            textos y KPIs por eje
  page_utils.py           setup, pestañas perezosas, cache de figuras
  streamlit_app.py        inicio
  pages/                  5 secciones del dashboard
docs/
  metodologia.md          CRISP-DM completo
  sustentacion.md         guion oral
```

## Dashboard — cinco secciones

| Sección | Página | Contenido |
|---------|--------|-----------|
| Panorama | 1 · Panorama | Casos por año |
| Territorio | 2 · Territorio | Departamentos, zona urbana/rural, municipios |
| Personas y tiempo | 3 · Personas y tiempo | Sexo-edad, ciclo vital, día-hora |
| Patrones | 4 · Patrones | Mecanismos, escenarios, gravedad, agresor |
| Modelo Predictivo | 5 · Modelo Predictivo | Simulador interactivo de triage de agresores y métricas de desempeño |

Filtros globales: periodo, departamento, municipio/ciudad, zona, sexo de la víctima, pertenencia étnica y ciclo vital (panel lateral; aplican a todas las secciones descriptivas).

## Rendimiento (sustentación en vivo)

Para demos fluidas, **copie el proyecto fuera de OneDrive** (p. ej. `C:\dev\violencia-interpersonal`). La sincronización en la nube puede ralentizar la lectura de Parquet y el arranque de Streamlit.

Optimizaciones activas en la capa `app/`: pestañas con render perezoso, `@st.cache_data` en figuras Plotly, `@st.fragment` en drill-downs locales.

## Documentación

- Metodología CRISP-DM: `docs/metodologia.md`
- Guion de sustentación: `docs/sustentacion.md`
- Diccionario de variables: `docs/data_dictionary.md`
- Preparación de datos (Fase 3): `docs/preparacion_datos.md`
- Evidencia comparativa sustentación: `docs/evidencia_sustentacion/comparacion_antes_despues.md`

Verificación reproducible:

```bash
python analysis/verificar_preparacion.py
python analysis/generar_evidencia_sustentacion.py
```

## Advertencia

Los datos son registros administrativos de valoración medicolegal, no la totalidad de la violencia ocurrida.

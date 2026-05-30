# Violencia interpersonal en Colombia (2015-2024)

Proyecto universitario de analítica de datos sobre casos **registrados** de violencia interpersonal. Metodología CRISP-DM, cubo OLAP precomputado y dashboard Streamlit como guion visual para sustentación.

## Ejecución

```bash
pip install -r requirements.txt
python analysis/run.py
streamlit run app/streamlit_app.py
```

`run.py` genera `dataset.parquet` (38 columnas, análisis offline; sin `contexto_hecho`) y cinco agregados para el dashboard:
`agg_filtros`, `agg_territorial`, `agg_demografia`, `agg_patrones`, `agg_dia_hora` (más
`cluster_summary.json` y figura en `articulo/figuras/` para el informe).
Streamlit **no** carga el dataset completo de ~980k filas; usa solo esos agregados OLAP.

## Estructura

```text
data/raw/                 CSV original (INMLCF)
data/processed/           dataset.parquet + agg_*.parquet
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
  pages/                  4 secciones del dashboard
docs/
  metodologia.md          CRISP-DM completo
  sustentacion.md         guion oral
articulo/                 informe LaTeX
```

## Dashboard — cuatro secciones

| Sección | Página | Contenido |
|---------|--------|-----------|
| Panorama | 1 · Panorama | Casos por año |
| Territorio | 2 · Territorio | Departamentos, zona urbana/rural, municipios |
| Personas y tiempo | 3 · Personas y tiempo | Sexo-edad, ciclo vital, día-hora |
| Patrones | 4 · Patrones | Mecanismos, escenarios, gravedad, agresor |

Filtros globales: periodo, departamento, municipio/ciudad, zona, sexo de la víctima, pertenencia étnica y ciclo vital (panel lateral; aplican a todas las secciones).

## Rendimiento (sustentación en vivo)

Para demos fluidas, **copie el proyecto fuera de OneDrive** (p. ej. `C:\dev\violencia-interpersonal`). La sincronización en la nube puede ralentizar la lectura de Parquet y el arranque de Streamlit.

Optimizaciones activas en la capa `app/`: pestañas con render perezoso, `@st.cache_data` en figuras Plotly, `@st.fragment` en drill-downs locales.

## Documentación

- Metodología CRISP-DM: `docs/metodologia.md`
- Guion de sustentación: `docs/sustentacion.md`
- Diccionario de variables: `docs/data_dictionary.md`

## Advertencia

Los datos son registros administrativos de valoración medicolegal, no la totalidad de la violencia ocurrida.

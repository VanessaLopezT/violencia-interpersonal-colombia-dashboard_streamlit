# Metodología CRISP-DM

Proyecto de analítica de datos sobre casos **registrados** de violencia interpersonal en Colombia (2015–2024). El trabajo sigue la metodología CRISP-DM en seis fases y utiliza un cubo OLAP precomputado para el dashboard Streamlit.

## Fase 1 — Comprensión del negocio (Business Understanding)

La violencia interpersonal genera lesiones, incapacidades y costos sociales en Colombia. Parte de estos hechos llega a valoración medicolegal y queda consignada en registros administrativos abiertos del Instituto Nacional de Medicina Legal y Ciencias Forenses (INMLCF).

**Pregunta de investigación:** ¿Cómo han evolucionado y qué patrones temporales, territoriales y victimológicos caracterizan los casos de violencia interpersonal en Colombia entre 2015 y 2024 según factores demográficos y situacionales?

**Objetivos específicos (descriptivos):**
- Describir la evolución temporal de los casos.
- Identificar concentración territorial por departamento, municipio/localidad y zona urbana/rural.
- Caracterizar perfiles demográficos de las víctimas y su concentración por día y franja horaria.
- Examinar la configuración situacional de la lesión (escenario, mecanismo, severidad medicolegal y relación agresor–víctima).

**Universo de análisis:** casos documentados en la fuente oficial, no la totalidad de la violencia ocurrida en la población. Este límite se comunica en el dashboard y en el informe.

## Fase 2 — Comprensión de datos (Data Understanding)

**Fuente:** [Violencia interpersonal. Colombia, años 2015 a 2024. Cifras definitivas](https://www.datos.gov.co/en/Justicia-y-Derecho/Violencia-interpersonal-Colombia-a-os-2015-a-2024-/e3xi-4zq5/about_data), portal Datos Abiertos Colombia.

**Volumen:** ~982.000 filas y 35 columnas en el catálogo; tras limpieza y filtrado temporal, **981.611 registros** (2015–2024) en **38 columnas** analíticas.

**Perfil de calidad:**
- Cero duplicados por identificador.
- Cobertura temporal completa 2015–2024.
- `contexto_hecho` constante en el CSV (100 % una sola categoría): se lee al importar y **se excluye del parquet** analítico.
- Faltantes estandarizados a «Sin informacion» en variables categóricas.
- Variantes ortográficas y taxonómicas detectadas en escenario, circunstancia y presunto agresor (ver Fase 3).

Documentación de variables: `docs/data_dictionary.md`.

## Fase 3 — Preparación de datos (Data Preparation)

Implementada en `src/prepare.py` y reglas de dominio en `app/text_es.py`:

1. Lectura del CSV en `data/raw/` con detección automática de encoding (`utf-8-sig`, `utf-8`, `cp1252`, `latin-1`).
2. Renombrado posicional de columnas a snake_case.
3. Normalización Unicode NFC y equivalencias de dominio (`normalize_text`, `DOMAIN_ALIASES`).
4. Estandarización de faltantes (`MISSING_PATTERNS` → «Sin informacion»).
5. Unificación de franjas horarias (`normalizar_franja` en `rango_hora`).
6. Canonización por frecuencia modal (`canonize_column`) en departamento, municipio, escenario, agresor, mecanismo, zona y circunstancia detallada.
7. Derivación de variables analíticas:
   - `dias_incapacidad_num`: punto medio del intervalo de incapacidad.
   - `severidad_categoria`: clasificación ordinal de severidad medicolegal.
   - `anio_mes`, `fin_semana`: apoyo temporal.
8. Filtrado al rango 2015–2024.
9. **Exclusión de `contexto_hecho`** del dataset exportado.
10. Exportación a `data/processed/dataset.parquet`.

### Homologaciones aplicadas (alcance acordado)

| Variable | Problema | Regla | Casos afectados (aprox.) |
|----------|----------|-------|--------------------------|
| `escenario_hecho` | Tres etiquetas INMLCF para el mismo concepto de vía pública/calle | Alias → «Vía pública o calle»: `Vía Pública`, `Calle (autopista, avenida, dentro de la ciudad)` y variante CSV `Calle (Autopista,Avenida,Dentro de La Ciudad)` | ~523.000 |
| `circunstancia_detallada` | Cuatro pares duplicados solo por mayúsculas/tildes (p. ej. «Violencia Económica» / «Violencia económica») | `canonize_column` conserva la forma modal | ~12.500 |
| `presunto_agresor` | «Amigo (a)» vs «Amigo(a)» | Alias → «Amigo(a)» | ~40.600 |

**No homologado en esta versión** (decisión explícita): mes/día con distinta capitalización, pertenencia étnica, grupo mayor/menor de edad, variantes adicionales de escenario (p. ej. «Vía pública» sin «o calle»), ni fusiones semánticas entre categorías INMLCF distintas en presunto agresor.

## Fase 4 — Modelado (Modeling)

En este proyecto, «modelado» corresponde al **análisis exploratorio descriptivo (EDA)** y a la **construcción del cubo OLAP** para el dashboard. No se emplea predicción supervisada.

**Cubo OLAP** (generado en `analysis/run.py`):

| Elemento | Descripción |
|----------|-------------|
| **Hecho** | Conteo de casos (`casos`) |
| **Dimensiones de filtrado** | `anio_hecho`, `departamento_hecho`, `sexo_victima`, `zona_hecho` |
| **Dimensiones de análisis** | Territorio (depto, municipio, localidad), demografía, día/hora, escenario, mecanismo, severidad, agresor |
| **Operación** | SUM sobre agregados precomputados en `app/filters.py` |

**Archivos generados** (`data/processed/`):
- `agg_filtros.parquet` — cubo base para filtros y totales
- `agg_territorial.parquet` — departamento, municipio, localidad (Bogotá D.C.)
- `agg_demografia.parquet` — sexo, edad, ciclo vital
- `agg_patrones.parquet` — escenario, mecanismo, severidad, agresor
- `agg_dia_hora.parquet` — día de la semana, franja horaria

La serie anual del dashboard se obtiene agregando `agg_filtros` por año.

**Clustering K-means (opcional, secundario):** sobre muestra de 50.000 registros con ocho variables categóricas, k=4. Resultado documentado en el informe LaTeX; no se muestra en el dashboard.

## Fase 5 — Evaluación (Evaluation)

Criterios de validación aplicados:
- Total nacional coherente: 981.611 casos en `agg_filtros`.
- Filtros extremos (un solo año, un departamento) no producen errores.
- Cada gráfico responde una pregunta concreta y es interpretable en sustentación oral.
- Tildes y etiquetas en español correctas en UI y gráficos.
- Homologaciones verificadas post-`run.py` (escenario unificado, circunstancia sin pares casefold, agresor Amigo unificado).

## Fase 6 — Despliegue (Deployment)

**Dashboard Streamlit** (`app/streamlit_app.py`): guion visual en cuatro secciones con navegación superior, KPIs, pestañas y filtros globales.

| Sección | Pregunta guía | Contenido principal |
|---------|---------------|---------------------|
| **1 · Panorama** | Casos registrados por año | KPIs, línea anual, lectura del periodo |
| **2 · Territorio** | Casos por departamento y municipio | Top departamentos, zona urbana/rural, drill municipal o top 5 localidades (Bogotá D.C.) |
| **3 · Personas y tiempo** | Perfil de víctimas y momento del hecho | Sexo × edad, ciclo vital, heatmap día-hora, top franjas |
| **4 · Patrones** | Mecanismo, escenario, gravedad y agresor | Top mecanismos y escenarios, severidad, presunto agresor |

**Filtros globales (sidebar):** rango de años, departamento, municipio/ciudad, zona, sexo de la víctima, pertenencia étnica, ciclo vital; navegación Anterior/Siguiente entre secciones.

**Figura estática:** `articulo/figuras/01_evolucion_anual.png` para el informe LaTeX.

Guion oral de sustentación: `docs/sustentacion.md`.

## Comandos

```bash
pip install -r requirements.txt
python analysis/run.py
streamlit run app/streamlit_app.py
```

## Encoding y normalización

- Lectura CSV: detección automática de encoding; el texto se normaliza a Unicode NFC.
- Alias de dominio y canonización: `app/text_es.py` (`DOMAIN_ALIASES`, `canonize_column`, `CANON_COLS`).
- Almacenamiento Parquet: UTF-8 (PyArrow).

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

**Volumen:** ~982.000 filas y 35 columnas en el catálogo; tras limpieza, filtrado temporal y exclusión de columnas administrativas, **981.611 registros** (2015–2024) en **26 columnas** en `dataset.parquet`.

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
6. Canonización por frecuencia modal (`canonize_column`) en departamento, municipio, escenario, agresor, mecanismo, zona, circunstancia detallada, **mes del hecho** y **día del hecho**.
7. Derivación de variables analíticas:
   - `severidad_categoria`: categorías medicolegales INMLCF (`Sin incapacidad`, `1 a 30`, `31 a 90`, `Más de 90`, `Sin informacion`).
   - `dias_incapacidad_num`: punto medio ordinal de cada intervalo INMLCF (0, 15, 60, 91).
   - `anio_mes`, `fin_semana`: apoyo temporal (fin de semana a partir de día canonizado).
8. Filtrado al rango 2015–2024.
9. **Exclusión** de columnas constantes, redundantes o fuera del cubo OLAP (`contexto_hecho`, códigos DANE, variables de edad redundantes, `dias_incapacidad` texto, campos demográficos de baja utilización en el dashboard).
10. Exportación dual (mismas filas y columnas):
    - `data/processed/dataset.parquet` — formato principal del pipeline.
    - `data/processed/dataset_limpio.csv` — UTF-8 para inspección, auditoría y comparación con la fuente (no lo consume Streamlit).

### Comparación fuente → dataset preparado

| Métrica | Valor |
|---------|-------|
| Filas CSV original (renombrado) | 981.611 |
| Filas dataset final (filtro 2015–2024) | 981.611 |
| Columnas CSV original | 35 |
| Columnas eliminadas | 13 |
| Columnas derivadas añadidas | 4 |
| Columnas finales exportadas | 26 |

**Flujo:** CSV original (`data/raw/`) → limpieza (`src/prepare.py`) → `dataset_limpio.csv` + `dataset.parquet` → agregados OLAP (`analysis/run.py`) → dashboard Streamlit.

Evidencia tabular para sustentación: `docs/evidencia_sustentacion/comparacion_antes_despues.md`. Verificación reproducible: `python analysis/verificar_preparacion.py`.

### Homologaciones aplicadas (alcance acordado)

| Variable | Problema | Regla | Casos afectados (aprox.) |
|----------|----------|-------|--------------------------|
| `escenario_hecho` | Vía pública/calle y variantes de mayúsculas INMLCF | Alias + `canonize_column` | ~574.000 vía pública; ~50.000 pares título/minúsculas |
| `pertenencia_etnica` | «Sin pertenencia étnica» / «Sin Pertenencia Étnica»; ROM/Rom | `canonize_column` (forma modal) | ~792.956 |
| `escolaridad`, `estado_civil`, `actividad_hecho` | Pares por capitalización interna | `canonize_column` | ~1.300–33.000 |
| `sexo_agresor` | «Transgenero» vs «Transgénero» | Alias → «Transgénero» | 39 |
| `mes_hecho`, `dia_hecho` | Duplicados por capitalización | `canonize_column` | ~300.000 |
| `circunstancia_detallada` | Pares por mayúsculas/tildes | `canonize_column` | ~12.500 |
| `presunto_agresor` | «Amigo (a)» vs «Amigo(a)» | Alias → «Amigo(a)» | ~40.600 |
| `dias_incapacidad` | Intervalos INMLCF (`1 a 30`, `31 a 90`, etc.) | Mapeo explícito a `severidad_categoria` | 981.611 |

Documentación detallada de la fase: `docs/preparacion_datos.md`.

**No recodificado a «Sin informacion»** (decisión explícita): «Ninguno»/«Ninguna» en campos donde denotan categoría válida (p. ej. escolaridad); «No había sido implementada» en columnas excluidas del parquet.

## Fase 4 — Modelado (Modeling)

El proyecto implementa tanto modelado descriptivo de datos como aprendizaje automático:

**1. Cubo OLAP** (generado en `analysis/run.py`):
Mapeo multidimensional optimizado para la agregación rápida en la interfaz de usuario.

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

**2. Bosque Aleatorio / Random Forest (Clasificación Supervisada):**
Entrenado con división de datos 80/20 (Train/Test) para predecir el vínculo o relación del agresor (`presunto_agresor`) en **5 macro-categorías** equilibradas:
- *Conocido sin trato*
- *Desconocido / Delincuencia*
- *Vecino*
- *Fuerza Pública / Custodia*
- *Amistad / Entorno*

Variables predictoras utilizadas: `sexo_victima`, `ciclo_vital`, `zona_hecho`, `escenario_hecho`, `mecanismo_causal`, `fin_semana` y `rango_hora`. Se entrena usando un pipeline de Scikit-Learn que contiene codificación de variables mediante `OneHotEncoder` y un clasificador `RandomForestClassifier` con `n_estimators=100` y `max_depth=12` para capturar relaciones no lineales y mejorar la exactitud.

## Fase 5 — Evaluación (Evaluation)

Criterios de validación aplicados:
- Total nacional coherente: 981.611 casos en `agg_filtros`.
- Filtros extremos (un solo año, un departamento) no producen errores.
- Cada gráfico responde una pregunta concreta y es interpretable en sustentación oral.
- Tildes y etiquetas en español correctas en UI y gráficos.
- Homologaciones verificadas post-`run.py` (escenario unificado, circunstancia sin pares casefold, agresor Amigo unificado).

## Fase 6 — Despliegue (Deployment)

**Dashboard Streamlit** (`app/streamlit_app.py`): guion visual en cinco secciones con navegación superior, KPIs, pestañas y filtros globales.

| Sección | Pregunta guía | Contenido principal |
|---------|---------------|---------------------|
| **1 · Panorama** | Casos registrados por año | KPIs, línea anual, lectura del periodo |
| **2 · Territorio** | Casos por departamento y municipio | Top departamentos, zona urbana/rural, drill municipal o top 5 localidades (Bogotá D.C.) |
| **3 · Personas y tiempo** | Perfil de víctimas y momento del hecho | Sexo × edad, ciclo vital, heatmap día-hora, top franjas |
| **4 · Patrones** | Mecanismo, escenario, gravedad y agresor | Top mecanismos y escenarios, severidad, presunto agresor |
| **5 · Modelo Predictivo** | Predicción del vínculo del presunto agresor | Triage interactivo, probabilidades en tiempo real, métricas académicas (Accuracy, Precision, Recall) e importancia de variables |

**Filtros globales (sidebar):** rango de años, departamento, municipio/ciudad, zona, sexo de la víctima, pertenencia étnica, ciclo vital; navegación Anterior/Siguiente entre secciones.


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

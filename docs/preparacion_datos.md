# Fase 3 CRISP-DM — Preparación de datos

Documentación pedagógica y de sustentación del pipeline implementado en [`src/prepare.py`](../src/prepare.py) y reglas de dominio en [`app/text_es.py`](../app/text_es.py).

**Fuente:** CSV INMLCF «Violencia interpersonal. Colombia, años 2015 a 2024. Cifras definitivas» (`data/raw/`).  
**Salida:** `data/processed/dataset.parquet` — **981.611 registros**, **26 columnas** (2024-05).

---

## Flujo general

```text
CSV (35 cols) → lectura/encoding → renombrado → normalize_text (NFC + alias)
→ MISSING_PATTERNS → normalizar_franja (hora) → canonize_column
→ severidad (incapacidad) → filtro años → anio_mes / fin_semana
→ apply_to_dataframe → drop columnas → parquet
```

---

## Paso a paso

### 1. Lectura del CSV (`_read_csv`, `_find_csv`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Exportaciones INMLCF pueden venir en distintos encodings Windows/UTF-8. |
| **Por qué** | Evitar caracteres corruptos antes de cualquier agregación. |
| **Columnas** | Las 35 originales del catálogo. |
| **Impacto** | Texto legible; la normalización NFC posterior corrige presentación Unicode. |

Se prueba, en orden: `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`.

### 2. Renombrado posicional (`_rename_columns`, `COLUMN_RENAME_MAP`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Encabezados largos, tildes y espacios dificultan el código reproducible. |
| **Por qué** | Convención snake_case estable para scripts, OLAP y documentación. |
| **Columnas** | Las 35 del CSV → nombres como `anio_hecho`, `sexo_victima`. |
| **Impacto** | Contrato fijo: si el CSV cambia el número de columnas, el pipeline falla explícitamente. |

### 3. Normalización Unicode y alias (`normalize_text`, `DOMAIN_ALIASES`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Variantes semánticas equivalentes (misma categoría INMLCF, distinta etiqueta). |
| **Por qué** | Reducir fragmentación **solo donde hay equivalencia documentada**. |
| **Columnas** | Todas las categóricas (vía `apply_to_dataframe`); alias puntuales en escenario, agresor, sexo agresor, Bogotá. |
| **Impacto** | p. ej. ~164.314 registros de vía pública/calle unificados en «Vía pública o calle». |

**Alias implementados (evidencia fuente):**

| Alias | → Canónico | Casos aprox. |
|-------|------------|--------------|
| Vía Pública, Vía pública, Calle (autopista…) | Vía pública o calle | ~574.330 |
| Establecimientos dedicados… (minúsculas) | Establecimientos Dedicados… (modal) | 241 |
| Amigo (a) | Amigo(a) | ~40.600 |
| Transgenero | Transgénero | 39 |

### 4. Tratamiento de faltantes (`MISSING_PATTERNS`, `_norm_text`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | La fuente mezcla «Sin información», «No aplica», «No Sabe / No Informa», etc. |
| **Por qué** | Un solo código analítico «Sin informacion» para conteos y filtros. |
| **Columnas** | Todas las categóricas de texto. |
| **Impacto** | Comparabilidad de tasas de missing entre variables exportadas. |

**Patrones recodificados** (tras normalización NFKD minúscula):

- sin informacion / sin información  
- no sabe / no informa  
- no reportado, no aplica, desconocido, no definido, no especificado, ignorado, 999  

**No recodificados** (categoría válida o campo excluido):

| Valor | Columna(s) | Frecuencia | Razón |
|-------|------------|------------|-------|
| Ninguna | escolaridad | 2.102 (0,21 %) | Nivel educativo válido INMLCF |
| Ninguna | tipo_discapacidad (excluida) | 978.749 (99,71 %) | «Sin discapacidad», no faltante |
| Ninguno | pertenencia_grupal (excluida) | 713.776 (72,71 %) | Sin pertenencia grupal declarada |
| No había sido implementada | pueblo_indigena (excluida) | 365.648 (37,25 %) | Código administrativo histórico |

### 5. Franjas horarias (`normalizar_franja`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Espacios dobles en rangos `(18:00 a  20:59)`. |
| **Columnas** | `rango_hora` |
| **Impacto** | 9 categorías estables para heatmap día–hora. |

### 6. Canonización modal (`canonize_column`, `CANON_COLS`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | Duplicados por mayúsculas/tildes (p. ej. «marzo»/«Marzo», «Sin pertenencia étnica»/«Sin Pertenencia Étnica»). |
| **Por qué** | Unificar **ortografía**, no fusionar conceptos distintos. |
| **Columnas** | departamento, municipio, escenario, agresor, mecanismo, zona, circunstancia, mes, día, **pertenencia_etnica**, **escolaridad**, **estado_civil**, **actividad_hecho**, **sexo_agresor** |
| **Impacto** | p. ej. pertenencia étnica: 505.539 + 287.417 → una sola etiqueta modal. |

Regla: por cada grupo `casefold`, se conserva la forma **más frecuente**.

### 7. Severidad medicolegal (`INCAPACIDAD_CATEGORIA_MAP`, `_map_incapacidad`)

| Aspecto | Detalle |
|---------|---------|
| **Problema** | El CSV usa intervalos gruesos INMLCF (`1 a 30`, `31 a 90`, …), no intervalos finos. |
| **Por qué** | Evitar parseo por dígitos que distorsione el significado. |
| **Entrada** | `dias_incapacidad` (texto) |
| **Salida** | `severidad_categoria` + `dias_incapacidad_num` (punto medio: 0, 15, 60, 91) |

| Categoría fuente | severidad_categoria | Casos |
|------------------|---------------------|-------|
| 1 a 30 | 1 a 30 | 815.693 |
| 31 a 90 | 31 a 90 | 64.431 |
| Más de 90 | Más de 90 | 1.546 |
| Cero días / sin días… | Sin incapacidad | 73.888 |
| Sin información | Sin informacion | 26.053 |

### 8. Filtrado temporal

| Aspecto | Detalle |
|---------|---------|
| **Rango** | 2015–2024 (`YEAR_MIN`, `YEAR_MAX`) |
| **Impacto** | Alineación con periodo de estudio; 0 registros fuera de rango en fuente actual. |

### 9. Variables derivadas

| Variable | Fórmula / lógica | Uso |
|----------|------------------|-----|
| `anio_mes` | `anio_hecho` + `-` + `mes_hecho` | Reserva analítica (series mensuales offline) |
| `fin_semana` | sábado o domingo (día canonizado) | Reserva analítica (379.329 casos, 38,6 %) |
| `severidad_categoria` | ver §7 | OLAP, dashboard, artículo |
| `dias_incapacidad_num` | punto medio ordinal | Reserva analítica / extensibilidad |

### 10. Segunda pasada de dominio (`apply_to_dataframe`)

Reaplica `normalize_text` + `canonize_column` en `CANON_COLS` tras derivadas. Idempotente en la práctica.

### 11. Eliminación de columnas (`cols_to_drop`)

Ver tabla en [`data_dictionary.md`](data_dictionary.md). Criterios: constante, redundancia geográfica/edad, reemplazo por derivadas, **exclusión del alcance OLAP** (no borrado del CSV fuente).

### 12. Exportación (`save_dataset`)

| Archivo | Uso |
|---------|-----|
| `dataset.parquet` | Formato principal: `analysis/run.py`, agregados OLAP |
| `dataset_limpio.csv` | Inspección, auditoría, Excel; **mismas filas y columnas** que el parquet (UTF-8) |

El dashboard Streamlit **no** lee el CSV ni el parquet completo (~980k filas).

---

## Para sustentación académica (CRISP-DM Fase 3)

### ¿Qué se limpió?

- Encodings y espacios en texto y franjas horarias.  
- Códigos institucionales de no-información unificados en «Sin informacion» (con exclusiones documentadas).  
- Duplicados ortográficos en dimensiones clave (territorio, tiempo, escenario, etnia, etc.).

### ¿Qué se transformó?

- Intervalos de incapacidad → categorías ordinales INMLCF + puntos medios.  
- Etiquetas equivalentes vía alias semánticos (no fusiones arbitrarias entre categorías distintas).

### ¿Qué se derivó?

- `severidad_categoria`, `dias_incapacidad_num`, `anio_mes`, `fin_semana`.

### ¿Qué se eliminó del parquet?

13 columnas (constantes, DANE, edad redundante, texto de incapacidad, campos demográficos fuera del alcance). **Permanecen en el CSV crudo** para trazabilidad.

### ¿Qué se conservó?

26 columnas: dimensiones OLAP, **reserva analítica** (escolaridad, estado civil, actividad, diagnóstico, sexo agresor, circunstancia), trazabilidad (`id`) y derivadas de extensibilidad (`anio_mes`, `fin_semana`, `dias_incapacidad_num`).

### ¿Por qué es metodológicamente defendible?

1. **Trazabilidad:** cada regla tiene conteo en fuente; reglas en código versionado.  
2. **Conservadurismo:** no se fusionan categorías INMLCF distintas; solo alias documentados o casefold modal.  
3. **Separación de alcances:** parquet analítico ≠ CSV administrativo completo.  
4. **Reproducibilidad:** `python analysis/run.py` regenera parquet y agregados.  
5. **Limitaciones explícitas:** subregistro, homologación parcial residual, severidad ≠ gravedad clínica total.

---

## Comandos

```bash
python analysis/run.py                       # parquet + CSV limpio + agregados
python analysis/verificar_preparacion.py     # verificación casefold (6 cols auditadas)
python analysis/generar_evidencia_sustentacion.py  # tablas antes/después
python analysis/audit_prepare.py
python analysis/profile_homolog_missing.py
```

**Redacción conservadora en sustentación:** la verificación casefold documentada aplica a las seis columnas de homologación explícita (`pertenencia_etnica`, `escenario_hecho`, `sexo_agresor`, `escolaridad`, `estado_civil`, `actividad_hecho`). Otras variables (p. ej. `presunto_agresor`, 57 categorías INMLCF) conservan etiquetas distintas por diseño taxonómico, no necesariamente por error de limpieza.

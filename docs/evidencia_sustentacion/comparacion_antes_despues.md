# Evidencia comparativa — Data Preparation (CRISP-DM Fase 3)

Generado sobre fuente INMLCF con **981,611** registros en CSV crudo renombrado y **981,611** registros en dataset preparado.

## Flujo de datos

```text
CSV original (data/raw/)
  -> lectura + renombrado (35 columnas)
  -> limpieza y preparacion (src/prepare.py)
  -> dataset_limpio.csv   (inspeccion / auditoria / Excel)
  -> dataset.parquet      (formato principal del pipeline)
  -> agregados OLAP (analysis/run.py)
  -> dashboard Streamlit
```

## Comparacion fuente vs dataset preparado

| Metrica | Valor |
|---------|-------|
| Filas CSV original (tras renombrar) | 981,611 |
| Filas dataset final | 981,611 |
| Filas excluidas por filtro 2015-2024 | 0 |
| Columnas originales (CSV) | 35 |
| Columnas eliminadas en prepare | 13 |
| Columnas derivadas anadidas | 4 |
| Columnas finales exportadas | 26 |

### Columnas eliminadas

contexto_hecho, codigo_dane_municipio, codigo_dane_departamento, grupo_mayor_menor_edad, grupo_edad_judicial, dias_incapacidad, orientacion_sexual, identidad_genero, transgenero, pueblo_indigena, tipo_discapacidad, pertenencia_grupal, pais_nacimiento

### Columnas derivadas

severidad_categoria, dias_incapacidad_num, anio_mes, fin_semana

### Columnas finales

`id`, `anio_hecho`, `sexo_victima`, `grupo_edad_quinquenal`, `ciclo_vital`, `escolaridad`, `estado_civil`, `pertenencia_etnica`, `mes_hecho`, `dia_hecho`, `rango_hora`, `municipio_hecho`, `departamento_hecho`, `localidad_hecho`, `zona_hecho`, `escenario_hecho`, `actividad_hecho`, `circunstancia_detallada`, `mecanismo_causal`, `diagnostico_topografico`, `sexo_agresor`, `presunto_agresor`, `severidad_categoria`, `dias_incapacidad_num`, `anio_mes`, `fin_semana`

## 1. Homologacion — pertenencia etnica

Variantes ortograficas del mismo concepto (CSV crudo):

| Etiqueta en fuente | Casos |
|---------------------|------:|
| Sin pertenencia étnica | 505,539 |
| Sin Pertenencia Étnica | 287,417 |
| ROM (Gitano) | 87 |
| Rom (Gitano) | 23 |

Tras preparacion (forma modal unificada):

| Etiqueta | Casos |
|----------|------:|
| Sin pertenencia étnica | 792,956 |
| Sin informacion | 149,155 |

## 2. Homologacion — via publica / calle

| Etiqueta en fuente | Casos |
|---------------------|------:|
| Vía Pública | 113,069 |
| Vía pública | 51,245 |
| Calle (Autopista,Avenida,Dentro de La Ciudad) | 275,062 |
| Calle (autopista, avenida, dentro de la ciudad) | 134,954 |

**Tras preparacion:** categoria unificada «Vía pública o calle» = **574,330** casos (58.5 % del total).

## 3. Faltantes — pertenencia_etnica (ejemplo)

| Momento | % «Sin informacion» |
|---------|--------------------:|
| CSV crudo (antes de estandarizar en prepare) | 15.19 % |
| Dataset preparado | 15.19 % |

Nota: «Sin pertenencia étnica» **no** es faltante; es categoria valida INMLCF.

## 4. Severidad medicolegal — antes vs despues de correccion

**Antes (heuristica incorrecta: primer digito del texto):**

| Categoria erronea | Casos | % |
|-------------------|------:|--:|
| Leve (1-5 dias) | 815,693 | 83.1 % |
| Sin informacion | 99,941 | 10.2 % |
| Muy alta (>30 dias) | 65,977 | 6.7 % |

**Despues (mapeo explicito intervalos INMLCF):**

| Categoria INMLCF | Casos | % |
|------------------|------:|--:|
| 1 a 30 | 815,693 | 83.1 % |
| Sin incapacidad | 73,888 | 7.5 % |
| 31 a 90 | 64,431 | 6.6 % |
| Sin informacion | 26,053 | 2.7 % |
| Más de 90 | 1,546 | 0.2 % |

## 5. Homologacion — sexo_agresor

| Etiqueta fuente | Casos |
|-----------------|------:|
| Transgénero | 45 |
| Transgenero | 39 |

Tras preparacion «Transgénero»: **84** casos.

## Uso en sustentacion

- Mostrar esta pagina o exportar tablas a Excel desde `dataset_limpio.csv`.
- Ejecutar `python analysis/verificar_preparacion.py` para verificacion casefold reproducible.

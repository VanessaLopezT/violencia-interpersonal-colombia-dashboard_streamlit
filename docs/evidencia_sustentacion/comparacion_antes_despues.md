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
| Filas con año inválido o fuera de rango | 0 |
| Columnas originales (CSV) | 35 |
| Columnas finales exportadas | 27 |
| Columnas eliminadas | 12 |
| Columnas derivadas | 4 |

### Columnas eliminadas

`grupo_mayor_menor_edad`, `grupo_edad_judicial`, `pais_nacimiento`, `tipo_discapacidad`, `orientacion_sexual`, `identidad_genero`, `transgenero`, `codigo_dane_municipio`, `codigo_dane_departamento`, `contexto_hecho`, `dias_incapacidad`, `pueblo_indigena`

### Columnas derivadas

`severidad_categoria`, `dias_incapacidad_num`, `anio_mes`, `fin_semana`

### Columnas finales

`id`, `anio_hecho`, `sexo_victima`, `grupo_edad_quinquenal`, `ciclo_vital`, `escolaridad`, `estado_civil`, `pertenencia_etnica`, `pertenencia_grupal`, `mes_hecho`, `dia_hecho`, `rango_hora`, `municipio_hecho`, `departamento_hecho`, `localidad_hecho`, `zona_hecho`, `escenario_hecho`, `actividad_hecho`, `circunstancia_detallada`, `mecanismo_causal`, `diagnostico_topografico`, `sexo_agresor`, `presunto_agresor`, `severidad_categoria`, `dias_incapacidad_num`, `anio_mes`, `fin_semana`

## 1. Faltantes y patrones de limpieza

| Columna | raw_na% | raw_pat% | prep_na% |
|--------|--------:|--------:|--------:|
| localidad_hecho | 0.00 % | 81.56 % | 81.56 % |
| presunto_agresor | 0.00 % | 16.85 % | 16.85 % |
| pertenencia_etnica | 0.00 % | 15.19 % | 15.19 % |
| pertenencia_grupal | 0.00 % | 13.97 % | 13.97 % |
| circunstancia_detallada | 0.00 % | 8.32 % | 8.32 % |
| rango_hora | 0.00 % | 6.92 % | 6.92 % |
| diagnostico_topografico | 0.00 % | 4.88 % | 4.88 % |
| zona_hecho | 0.00 % | 4.61 % | 4.61 % |
| escolaridad | 0.00 % | 3.21 % | 3.21 % |
| sexo_agresor | 0.00 % | 2.93 % | 2.93 % |
| estado_civil | 0.00 % | 2.90 % | 2.90 % |
| escenario_hecho | 0.00 % | 2.18 % | 2.18 % |
| actividad_hecho | 0.00 % | 1.67 % | 1.67 % |
| municipio_hecho | 0.00 % | 0.01 % | 0.01 % |
| departamento_hecho | 0.00 % | 0.01 % | 0.01 % |
| grupo_edad_quinquenal | 0.00 % | 0.00 % | 0.00 % |
| ciclo_vital | 0.00 % | 0.00 % | 0.00 % |
| id | 0.00 % | 0.00 % | 0.00 % |
| anio_hecho | 0.00 % | 0.00 % | 0.00 % |
| sexo_victima | 0.00 % | 0.00 % | 0.00 % |
| mes_hecho | 0.00 % | 0.00 % | 0.00 % |
| dia_hecho | 0.00 % | 0.00 % | 0.00 % |
| mecanismo_causal | 0.00 % | 0.00 % | 0.00 % |
| severidad_categoria | nan % | nan % | 2.65 % |
| dias_incapacidad_num | nan % | nan % | 2.65 % |
| anio_mes | nan % | nan % | 0.00 % |
| fin_semana | nan % | nan % | 0.00 % |

Las columnas anteriores muestran el impacto de la limpieza de faltantes: valores institucionales como 'Sin informacion' y variantes se recodifican antes de exportar el dataset preparado.

## 2. Homologaciones clave

Las siguientes dimensiones se homologan en `src/prepare.py` mediante normalizacion y canonizacion.

### departamento_hecho

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Bogotá, D.C. | 239,220 |
| Antioquia | 104,045 |
| Cundinamarca | 81,221 |
| Valle del Cauca | 67,944 |
| Santander | 56,582 |
| Atlántico | 47,310 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Bogotá D.C. | 239,220 |
| Antioquia | 104,045 |
| Cundinamarca | 81,221 |
| Valle del Cauca | 67,944 |
| Santander | 56,582 |
| Atlántico | 47,310 |

### municipio_hecho

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Bogotá, D.C. | 239,220 |
| Medellín | 53,239 |
| Cali | 36,102 |
| Barranquilla | 30,169 |
| Soacha | 22,726 |
| Bucaramanga | 20,508 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Bogotá D.C. | 239,220 |
| Medellín | 53,239 |
| Cali | 36,102 |
| Barranquilla | 30,169 |
| Soacha | 22,726 |
| Bucaramanga | 20,508 |

### zona_hecho

Valores crudos en la fuente (top 5):

| Etiqueta | Casos |
|--------|------:|
| Cabecera municipal | 865,897 |
| Sin información | 45,212 |
| Parte rural (vereda y campo) | 44,598 |
| Centro poblado (corregimiento, inspección de policía y caserío) | 16,174 |
| Centro poblado(corregimiento, inspección de policía y caserío) | 9,730 |

Valores preparados en el dataset final (top 4):

| Etiqueta | Casos |
|--------|------:|
| Cabecera municipal | 865,897 |
| Sin informacion | 45,212 |
| Parte rural (vereda y campo) | 44,598 |
| Centro poblado (corregimiento, inspección de policía y caserío) | 25,904 |

### pertenencia_etnica

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Sin pertenencia étnica | 505,539 |
| Sin Pertenencia Étnica | 287,417 |
| Sin información | 149,155 |
| Negro/Afrodescendiente | 28,230 |
| Indígena | 7,779 |
| Raizal | 3,247 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Sin pertenencia étnica | 792,956 |
| Sin informacion | 149,155 |
| Negro/Afrodescendiente | 28,230 |
| Indígena | 7,779 |
| Raizal | 3,247 |
| Palenquero | 134 |

### escenario_hecho

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Calle (Autopista,Avenida,Dentro de La Ciudad) | 275,062 |
| Vivienda | 168,276 |
| Calle (autopista, avenida, dentro de la ciudad) | 134,954 |
| Vía Pública | 113,069 |
| Vía pública | 51,245 |
| Establecimiento Comercial (Tienda,Centro Comercial,Almacén,Plaza de Mercado) | 25,096 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Vía pública o calle | 574,330 |
| Vivienda | 168,276 |
| Lugares de Esparcimiento con Expendio de Alcohol | 34,930 |
| Establecimiento Comercial (Tienda,Centro Comercial,Almacén,Plaza de Mercado) | 25,096 |
| Centros de Reclusión | 22,287 |
| Sin informacion | 21,371 |

### sexo_agresor

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Hombre | 746,507 |
| Mujer | 206,123 |
| Sin información | 28,739 |
| Intersexual | 122 |
| Transgénero | 45 |
| Transgenero | 39 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Hombre | 746,507 |
| Mujer | 206,123 |
| Sin informacion | 28,739 |
| Intersexual | 122 |
| Transgénero | 84 |
| No Binario | 36 |

### pertenencia_grupal

Valores crudos en la fuente (top 6):

| Etiqueta | Casos |
|--------|------:|
| Ninguno | 713,776 |
| Sin información | 137,094 |
| Persona adicta a una droga natural o sintética | 27,528 |
| Consumidores de sustancias psicoactivas (drogas, alcohol, etc.) | 21,506 |
| Personas bajo custodia | 18,392 |
| Grupos étnicos | 10,970 |

Valores preparados en el dataset final (top 6):

| Etiqueta | Casos |
|--------|------:|
| Ninguno | 713,776 |
| Sin informacion | 137,094 |
| Personas consumidoras de sustancias psicoactivas | 49,034 |
| Personas bajo custodia | 19,860 |
| Grupos étnicos | 11,518 |
| Funcionarios judiciales | 9,457 |

Modalidades finales completas de `pertenencia_grupal` tras homologacion:

| Etiqueta final | Casos |
|--------|------:|
| Ninguno | 713,776 |
| Sin informacion | 137,094 |
| Personas consumidoras de sustancias psicoactivas | 49,034 |
| Personas bajo custodia | 19,860 |
| Grupos étnicos | 11,518 |
| Funcionarios judiciales | 9,457 |
| Campesinos (as) y/o trabajadores (as) del campo | 7,493 |
| Persona en condición de desplazamiento | 6,252 |
| Sector social LGBTI (OSIGD) | 5,826 |
| Persona privada de la libertad | 3,737 |
| Mujer cabeza de hogar o de familia | 3,688 |
| Servidor público | 3,394 |
| Persona habitante de la calle | 1,936 |
| Otro | 1,780 |
| Pertenencia múltiple | 1,584 |
| Conductores de vehículos de servicio público | 1,184 |
| Personas en situación de prostitución | 778 |
| Personas con capacidades diferentes | 627 |
| Maestro / educador | 552 |
| Personas que ejercen actividades políticas | 409 |
| Persona recluida en establecimientos de rehabilitación y pabellones psiquiátricos | 370 |
| Defensores de derechos humanos | 275 |
| Personas que ejercen actividades gremiales o sindicales | 235 |
| Tribus urbanas | 167 |
| Trabajadores de la salud / Misión Humanitaria | 138 |
| Adolescentes en conflicto con la ley | 109 |
| Personas que ejercen actividades de periodismo | 90 |
| Religiosos | 80 |
| Personas mayores en hogares de cuidado | 76 |
| Niños, niñas y adolescentes bajo protección del ICBF | 57 |
| Personas desmovilizadas o reinsertadas | 16 |
| Líderes cívicos | 11 |
| Niños, niñas y adolescentes en condición de abandono | 3 |
| Ex convictos (as) | 2 |
| Presunto colaborador de grupo ilegal | 2 |
| Reclamante de tierras | 1 |

## 3. Verificacion de limpieza en filtros usados

Se revisan las columnas que alimentan los filtros del dashboard. Para departamentos, zona y pertenencias se detectan tambien diferencias por tildes, puntuacion o espacios; en municipios se conserva la etiqueta oficial para no mezclar municipios distintos que solo difieren por tilde.

- departamento_hecho: OK. 1 grupos duplicados visibles en raw vs 0 en prepared.
  - quindio: 'Quindio', 'Quindío'

- municipio_hecho: OK. 0 grupos duplicados visibles en raw vs 0 en prepared.

- sexo_victima: OK. 0 grupos duplicados visibles en raw vs 0 en prepared.

- zona_hecho: OK. 1 grupos duplicados visibles en raw vs 0 en prepared.
  - centro poblado corregimiento inspeccion de policia y caserio: 'Centro poblado (corregimiento, inspección de policía y caserío)', 'Centro poblado(corregimiento, inspección de policía y caserío)'

- pertenencia_etnica: OK. 2 grupos duplicados visibles en raw vs 0 en prepared.
  - sin pertenencia etnica: 'Sin Pertenencia Étnica', 'Sin pertenencia étnica'
  - rom gitano: 'ROM (Gitano)', 'Rom (Gitano)'

- pertenencia_grupal: OK. 4 grupos duplicados visibles en raw vs 0 en prepared.
  - maestro educador: 'Maestro - educador', 'Maestro / educador', 'Maestro/Educador'
  - persona en condicion de desplazamiento: 'Persona en condición de desplazamiento', 'persona en condición de desplazamiento'
  - persona habitante de la calle: 'Persona habitante de  la calle', 'Persona habitante de la calle'

- ciclo_vital: OK. 0 grupos duplicados visibles en raw vs 0 en prepared.

## 4. Severidad medicolegal

Se corrige la heuristica anterior que solo tomaba el primer digito del texto de días de incapacidad.

| Proceso | Categoria | Casos | % sobre el total |
|--------|----------|------:|------------------:|
| Antes | Leve (1-5 dias) | 815,693 | 83.1 % |
| Antes | Sin informacion | 99,941 | 10.2 % |
| Antes | Muy alta (>30 dias) | 65,977 | 6.7 % |
| Despues | 1 a 30 | 815,693 | 83.1 % |
| Despues | Sin incapacidad | 73,888 | 7.5 % |
| Despues | 31 a 90 | 64,431 | 6.6 % |
| Despues | Sin informacion | 26,053 | 2.7 % |
| Despues | Más de 90 | 1,546 | 0.2 % |

Esta comparacion demuestra la correccion de la categoria de severidad medicolegal antes y despues de la normalizacion en el pipeline.

## 5. Columnas y flujo final

- `data/processed/dataset_limpio.csv`: CSV de inspecton y auditoria con las mismas filas y columnas que el parquet.
- `data/processed/dataset.parquet`: formato principal para analisis y agregados OLAP.
- `analysis/verificar_preparacion.py`: script de verificacion reproducible y generacion de JSON de evidencia.

### Recomendaciones para presentacion

- Exportar el CSV limpio a Excel para mostrar tablas con filas y columnas auditadas.
- Usar este markdown como respaldo tecnico de las transformaciones.
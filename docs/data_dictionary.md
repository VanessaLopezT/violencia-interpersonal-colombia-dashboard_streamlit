# Diccionario de variables

Dataset analítico: violencia interpersonal Colombia 2015–2024. **981.611 registros**, **38 columnas** (35 originales del CSV − `contexto_hecho` + 4 derivadas analíticas).

| Variable | Descripción | Tipo | Uso |
|---|---|---|---|
| id | Identificador del registro | entero | trazabilidad |
| anio_hecho | Año del hecho | entero | temporal |
| sexo_victima | Sexo de la víctima | categórica | victimológico |
| grupo_edad_quinquenal | Grupo etario quinquenal | categórica | victimológico |
| grupo_mayor_menor_edad | Mayoría de edad | categórica | victimológico |
| grupo_edad_judicial | Grupo etario judicial | categórica | victimológico |
| ciclo_vital | Ciclo vital | categórica | victimológico |
| pais_nacimiento | País de nacimiento | categórica | demográfico |
| escolaridad | Escolaridad | categórica | demográfico |
| estado_civil | Estado civil | categórica | demográfico |
| tipo_discapacidad | Tipo de discapacidad | categórica | demográfico |
| pertenencia_etnica | Pertenencia étnica | categórica | demográfico |
| orientacion_sexual | Orientación sexual | categórica | sensible |
| identidad_genero | Identidad de género | categórica | sensible |
| transgenero | Transgénero | categórica | sensible |
| pertenencia_grupal | Pertenencia grupal | categórica | demográfico |
| mes_hecho | Mes del hecho | categórica | temporal |
| dia_hecho | Día del hecho | categórica | temporal |
| rango_hora | Rango horario (3 horas) | categórica | temporal |
| codigo_dane_municipio | Código DANE municipio | entero | territorial |
| municipio_hecho | Municipio | categórica | territorial |
| departamento_hecho | Departamento | categórica | territorial |
| codigo_dane_departamento | Código DANE departamento | entero | territorial |
| localidad_hecho | Localidad | categórica | territorial |
| zona_hecho | Zona urbana/rural | categórica | territorial |
| escenario_hecho | Escenario del hecho | categórica | situacional |
| actividad_hecho | Actividad durante el hecho | categórica | situacional |
| circunstancia_detallada | Circunstancia detallada | categórica | situacional |
| mecanismo_causal | Mecanismo causal | categórica | situacional |
| diagnostico_topografico | Diagnóstico topográfico | categórica | severidad |
| sexo_agresor | Sexo del agresor | categórica | relacional |
| presunto_agresor | Presunto agresor | categórica | relacional |
| dias_incapacidad | Días de incapacidad (intervalo) | categórica | severidad |
| pueblo_indigena | Pueblo indígena | categórica | demográfico |
| dias_incapacidad_num | Punto medio del intervalo (derivada) | numérico | severidad |
| severidad_categoria | Clasificación ordinal (derivada) | categórica | severidad |
| anio_mes | Año-mes concatenado (derivada) | categórica | temporal |
| fin_semana | Indicador fin de semana (derivada) | booleano | temporal |

## Variable excluida: contexto_hecho

En el CSV fuente, **Contexto del Hecho** tiene una sola categoría en el 100 % de los registros (*1 Lesiones no Fatales por Violencia Interpersonal*). Se lee durante la importación posicional, pero **no se exporta** a `dataset.parquet` porque no aporta variación analítica.

## Homologaciones aplicadas (ver `docs/metodologia.md`)

- **Escenario:** tres etiquetas de vía pública/calle unificadas en «Vía pública o calle».
- **Circunstancia detallada:** pares duplicados por mayúsculas/tildes unificados por frecuencia modal.
- **Presunto agresor:** «Amigo (a)» y «Amigo(a)» → «Amigo(a)».

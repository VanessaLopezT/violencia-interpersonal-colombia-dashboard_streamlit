# Diccionario de variables

Dataset analítico exportado: violencia interpersonal Colombia 2015–2024. **981.611 registros**, **26 columnas** en `data/processed/dataset.parquet`.

| Variable | Descripción | Tipo | Uso |
|---|---|---|---|
| id | Identificador del registro | entero | trazabilidad |
| anio_hecho | Año del hecho | entero | temporal / filtros |
| sexo_victima | Sexo de la víctima | categórica | victimológico |
| grupo_edad_quinquenal | Grupo etario quinquenal | categórica | victimológico |
| ciclo_vital | Ciclo vital | categórica | victimológico / filtros |
| escolaridad | Escolaridad | categórica | reserva analítica |
| estado_civil | Estado civil | categórica | reserva analítica |
| pertenencia_etnica | Pertenencia étnica | categórica | demográfico / filtros |
| mes_hecho | Mes del hecho (canonizado) | categórica | temporal |
| dia_hecho | Día del hecho (canonizado) | categórica | temporal |
| rango_hora | Rango horario (3 horas) | categórica | temporal |
| municipio_hecho | Municipio | categórica | territorial / filtros |
| departamento_hecho | Departamento | categórica | territorial / filtros |
| localidad_hecho | Localidad | categórica | territorial (Bogotá D.C.) |
| zona_hecho | Zona urbana/rural | categórica | territorial / filtros |
| escenario_hecho | Escenario del hecho | categórica | situacional |
| actividad_hecho | Actividad durante el hecho | categórica | reserva analítica |
| circunstancia_detallada | Circunstancia detallada | categórica | reserva analítica |
| mecanismo_causal | Mecanismo causal | categórica | situacional |
| diagnostico_topografico | Diagnóstico topográfico | categórica | reserva analítica |
| sexo_agresor | Sexo del agresor | categórica | reserva analítica |
| presunto_agresor | Presunto agresor | categórica | relacional |
| dias_incapacidad_num | Punto medio del intervalo INMLCF (derivada) | numérico | severidad |
| severidad_categoria | Categoría medicolegal INMLCF (derivada) | categórica | severidad |
| anio_mes | Año-mes concatenado (derivada) | categórica | temporal |
| fin_semana | Indicador fin de semana (derivada) | booleano | temporal |

## Columnas leídas del CSV pero excluidas del parquet

Se importan posicionalmente desde el CSV (35 columnas) y se eliminan en `src/prepare.py` por constante, redundancia o baja utilidad en el cubo OLAP actual:

- `contexto_hecho` — constante (100 % «Lesiones no Fatales por Violencia Interpersonal»).
- `codigo_dane_municipio`, `codigo_dane_departamento` — redundantes con nombres DANE.
- `grupo_mayor_menor_edad`, `grupo_edad_judicial` — redundantes con `ciclo_vital` / `grupo_edad_quinquenal`.
- `dias_incapacidad` — reemplazada por `severidad_categoria` y `dias_incapacidad_num`.
- `orientacion_sexual`, `identidad_genero`, `transgenero`, `pueblo_indigena`, `tipo_discapacidad`, `pertenencia_grupal`, `pais_nacimiento`.

## Severidad medicolegal

`severidad_categoria` refleja las categorías INMLCF presentes en la fuente 2015–2024:

| Categoría | Significado |
|---|---|
| Sin incapacidad | Cero días de incapacidad registrados |
| 1 a 30 | Intervalo de 1 a 30 días |
| 31 a 90 | Intervalo de 31 a 90 días |
| Más de 90 | Más de 90 días |
| Sin informacion | Sin dato o no reportado |

`dias_incapacidad_num` almacena el punto medio ordinal de cada intervalo (0, 15, 60, 91) para apoyo analítico offline.

## Homologaciones aplicadas (ver `docs/preparacion_datos.md` y `docs/metodologia.md`)

- **Escenario:** variantes vía pública/calle y administración pública unificadas por alias + canonización.
- **Pertenencia étnica, escolaridad, estado civil, actividad, sexo agresor:** duplicados ortográficos unificados por `canonize_column` (forma modal).
- **Mes y día del hecho:** canonización a 12 y 7 categorías respectivamente.
- **Circunstancia detallada y presunto agresor:** pares por mayúsculas/tildes y alias Amigo(a).

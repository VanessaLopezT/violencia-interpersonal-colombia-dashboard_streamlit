# Guion de sustentación oral

Duración estimada: 10–12 minutos. Recorrido lineal del dashboard en cuatro secciones.

## Inicio (30 segundos)

Abrir **Inicio**. Presentar la fuente del INMLCF: aproximadamente 982.000 casos entre 2015 y 2024. Aclarar que son **casos documentados en valoración medicolegal**, no la totalidad de la violencia ocurrida. Ir a **1 · Panorama**.

## 1 · Panorama (1 minuto 15 segundos)

**Pregunta:** Casos registrados por año.

KPIs: casos en la selección, año de mayor y menor registro, variación entre extremos.

**Tendencia anual:** gráfico de línea con máximo y mínimo.

**Lectura del periodo:** texto por año; caída en 2020 y cierre del periodo.

Resumen: pico en 2015, caída en 2020, repunte parcial hacia 2022–2024.

→ **2 · Territorio**.

## 2 · Territorio (2 minutos)

**Pregunta:** Casos por departamento y municipio.

KPIs: departamento líder, participación del top 3, zona urbana, municipio con más casos.

**Ranking departamental:** top 10.

**Urbano y rural:** cabecera municipal vs rural.

**Detalle territorial:** selectbox de departamento → top 5 municipios; en **Bogotá D.C.**, top 5 **localidades** (la ciudad no tiene desglose municipal DANE).

Resumen: Bogotá D.C., Antioquia y Cundinamarca concentran más del 40 %; ~88 % en cabecera municipal.

→ **3 · Personas y tiempo**.

## 3 · Personas y tiempo (2 minutos)

**Pregunta:** Perfil de víctimas y momento del hecho.

KPIs: % hombre/mujer, grupo etario modal, día y franja más frecuentes.

**Perfil de víctimas:** barras sexo × edad; radio para resaltar ciclo vital por sexo.

**Momento del hecho:** heatmap día × hora y top 5 combinaciones día-franja.

Resumen: ~66 % víctimas masculinas; adultos jóvenes; picos en fines de semana y tarde-noche.

→ **4 · Patrones**.

## 4 · Patrones (2 minutos)

**Pregunta:** Mecanismo, escenario, gravedad y agresor.

KPIs: mecanismo principal, escenario principal, gravedad modal, agresor más frecuente.

**Mecanismos de lesión** y **Escenarios del hecho:** top 8 (escenarios homologados: vía pública/calle unificada).

**Gravedad y vínculo:** días de incapacidad y presunto agresor.

**Resumen:** párrafo interpretativo, limitaciones y enlace INMLCF.

→ **Volver al inicio**.

## Limitaciones (1 minuto)

- Subregistro y sesgo de denuncia.
- Acceso desigual a valoración medicolegal entre territorios.
- No permite inferencia causal.
- Homologación parcial de categorías fuente (solo escenario vía pública/calle, circunstancia y formato Amigo); otras variantes INMLCF pueden seguir fragmentadas.

## Cierre oral (30 segundos)

CRISP-DM sobre datos abiertos del INMLCF, ~981.000 registros, cuatro secciones con filtros de periodo y departamento.

## Uso de filtros (si el jurado pregunta)

**Globales (panel lateral, aplican a todas las secciones y gráficas):**
- Periodo (años)
- Departamento y **municipio / ciudad** (con departamento se listan todos sus municipios; sin departamento, top 50 nacional)
- Zona del hecho (cabecera, rural, etc.)
- Sexo de la víctima, pertenencia étnica y ciclo vital

«Restablecer filtros» vuelve al periodo completo y valores por defecto. Botones **Anterior / Siguiente** bajo «Sección X de 4». Los selectores locales en Territorio (drill municipal/localidad) no alteran la selección global.

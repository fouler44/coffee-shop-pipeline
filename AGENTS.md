# Contexto compartido del proyecto

## Objetivo y forma de colaborar

Proyecto de práctica de ingeniería de datos. El usuario tiene experiencia con
datos cargados directamente en plataformas como Databricks y quiere aprender
ingesta desde S3, Snowflake y transformaciones con dbt, evitando complejidad sin
una finalidad concreta.

Actúa como asesor experto de ingeniería de datos: recomienda una opción adecuada
al ejercicio, explica sus implicaciones y cuestiona decisiones cuando haya razones.
Responde en español, con ejemplos concretos y distinguiendo hechos, supuestos y
recomendaciones. No presentes convenciones de nombres como requisitos universales.
En consultas conceptuales, explica y orienta; no implementes automáticamente el
pipeline ni cambies su arquitectura por el mero hecho de discutir alternativas.

## Arquitectura acordada

El usuario aceptó esta dirección de diseño:

```text
Archivos de origen
  -> S3: landing con archivos originales organizados por entidad y lote
  -> COPY INTO
  -> Snowflake bronze: tablas de datos recibidos y metadata de ingesta
  -> dbt silver: limpieza, tipos y normalización
  -> dbt gold: modelos para análisis
```

- Usar inicialmente una base de datos con esquemas bronze, silver y gold.
  Estos nombres identifican las capas de recepción, transformación y análisis.
- Las tablas bronze se declaran como sources de dbt; los modelos siguientes usan
  source() y ref() según corresponda. Declarar sources no carga ni crea las tablas.
- S3 conserva archivos; bronze conserva los registros cargados. Son garantías
  diferentes: desde S3 se puede repetir la lectura y desde bronze las transformaciones.
- No añadir otra zona de recepción ni una copia previa a bronze salvo una necesidad
  concreta, como aceptación de lotes o retención diferente. silver es la capa de
  transformación dbt.
- Conservar fidelidad al origen en bronze y añadir metadata técnica. La limpieza,
  deduplicación y reglas de negocio se resuelven después.

## Metadata y cargas

- Capturar en la primera carga a bronze: _batch_id, _source_file,
  _source_row_number y _ingested_at.
- Definir qué identifica el lote; distinguir lote de origen, lote de ingesta e
  intento de ejecución si se necesitan por separado. No generar un ID por fila
  cuando se pretende identificar una misma carga.
- Preservar el batch_id y delivered_at que ya aporta el generador; no
  sobrescribirlos con metadata de la ejecución. Documentar la relación con _batch_id.
- Separar fecha del evento, actualización en origen, entrega, ingesta y
  procesamiento. No usar created_at como garantía de llegada ordenada.
- Diseñar incrementales considerando registros tardíos, reintentos y duplicados;
  no asumir que un filtro fecha > max(fecha) resuelve todos esos casos.
- Un ensayo útil incluye carga inicial, segundo lote, repetición sin duplicados
  inesperados y reconstrucción de transformaciones desde bronze.

## Estado y límites de este contexto

Esta es una decisión de diseño, no una afirmación de que S3 y Snowflake estén
configurados. Antes de describir el estado real, revisar los archivos pertinentes.
El README documenta un generador con seis lotes CSV y una plantilla dbt con
DuckDB; distinguir ese punto de partida de la arquitectura objetivo.

Formato acordado: CSV UTF-8 con encabezado, nulos `\N` y booleanos `true`/`false`.
Leer README.md para el contrato de datos. Usar solo los datos raw como entrada al
pipeline; reference sirve para validación y no para completar o corregir el origen.
No confundir los modelos y seeds de ejemplo de Jaffle Shop con el pipeline objetivo.

Mantener este archivo breve. Cuando el usuario acepte un cambio de arquitectura,
actualizar las decisiones relevantes y sus motivos; no registrar cada alternativa
discutida como una decisión. Respetar las instrucciones más recientes del usuario.

## Referencias de la discusión

- https://www.kahandatasolutions.com/startermds
- https://github.com/darshilparmar/zomato-ai-data-engineering-end-to-end-project
- https://github.com/anshlambagit/Airbnb_Snowflake_DBT_Data_Engineer_Project

Los tutoriales son referencias comparativas, no especificaciones obligatorias.

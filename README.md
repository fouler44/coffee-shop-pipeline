# Coffee shop: datos para un pipeline incremental y SCD tipo 2

Simulación reproducible de enero a junio de 2025. Produce seis entregas mensuales,
con cambios reales de negocio y errores controlados. No implementa el pipeline
de limpieza ni construye las dimensiones SCD: esos son los ejercicios posteriores.

## Ejecutar

Desde la raíz del proyecto (dependencias fijadas en `uv.lock`):

```powershell
uv sync --locked
uv run python coffee-data-generator/generate.py
uv run python -m unittest discover -s coffee-data-generator/tests -v
```

La salida predeterminada es `data/coffee_2025`. Para otra ejecución:

```powershell
uv run python coffee-data-generator/generate.py --seed 42 --output data/otra_ejecucion
```

No se sobrescriben carpetas existentes. Misma semilla, configuración y versiones
de dependencias producen los mismos datos. Las fechas de la simulación son fijas,
independientes del día real de ejecución. Importar `generate.py` no ejecuta nada.

## Archivos

```text
data/coffee_2025/
  manifest.json
  raw/
    batch_001/ ... batch_006/
      customers.jsonl
      products.jsonl
      orders.jsonl
      order_items.jsonl
      payments.jsonl
  reference/
    batch_001/ ... batch_006/  (las mismas cinco tablas, correctas)
    business_changes.jsonl
    injected_issues.jsonl
```

JSONL contiene un objeto JSON por línea, en UTF-8. Mantiene `true`, `false` y `null`
sin convertirlos en texto. Fechas y horas se exportan en formato ISO 8601. Los
timestamps representan hora local de Ciudad de México, sin offset UTC.

`batch_001` corresponde a enero, entregado el 1 de febrero; el último corresponde
a junio y se entrega el 1 de julio. Los periodos son [inicio, fin): incluyen el
inicio y excluyen el primer instante del mes siguiente. `manifest.json` contiene
la configuración, los periodos, las entregas y los conteos de ambas capas.

## Contrato de las fuentes

- Cada fila contiene `source_record_id`, `batch_id` y `delivered_at`.
- `source_record_id` identifica un registro de origen y se conserva en duplicados
  y entregas tardías. Para deduplicar se usa junto con el nombre de tabla.
- Los IDs de negocio se mantienen durante toda la simulación. Los IDs de órdenes,
  artículos y pagos no reinician cada mes. Una nueva ejecución es una nueva
  simulación, no una continuación de la anterior.
- Clientes y productos son **estados completos después de cada cambio**, no
  parches de campos. Cada versión tiene `source_updated_at`, independiente de
  `delivered_at`, y un `source_record_id` distinto. Las filas raw se mezclan:
  deben ordenarse por fecha de origen para procesar su historia.
- Los clientes existentes al 1 de enero se entregan como estado inicial en enero;
  los registrados después se entregan por primera vez en el mes de registro.
  Los cambios posteriores solo afectan `phone`, `email` y `marketing_opt_in`.
- Todos los 36 productos aparecen inicialmente en enero. Solo cambia `price`:
  no se agregan ni se desactivan productos. Hay clientes y productos sin cambios.
- En los siguientes batches las dimensiones contienen solo nuevos registros o
  versiones modificadas; la ausencia de una entidad no representa una baja.
- Una venta usa el precio válido en `ordered_at`. El artículo guarda ese precio
  en `unit_price`, y el subtotal y pago corresponden a esos importes históricos.
- `marketing_opt_in` correcto siempre es booleano. Un `null` en raw es un error
  de origen, no equivale a `false`.
- Para este ejercicio se define que el correo se compara con `strip().lower()`.
  Un cambio de espacios o mayúsculas no debe crear una versión SCD.

El generador entrega fechas de origen, pero no columnas `valid_from`, `valid_to`
o `is_current`. Tu pipeline las construirá usando el ID de negocio y comparando
los atributos normalizados. Un duplicado no es una versión nueva. Los metadatos
de entrega tampoco deben contarse como cambios de negocio. Para unir ventas a
precios históricos, usa `ordered_at` dentro de [valid_from, valid_to).

## Cambios y errores configurables

Cada mes se selecciona aproximadamente un 5% del total de clientes y un 15% de
productos para cambios, dentro de una mitad del catálogo habilitada para cambiar.
Esto preserva entidades sin modificaciones. Cada entidad seleccionada cambia un
atributo en un instante aleatorio del mes, posterior a su versión anterior.

Las tasas de errores se aplican a filas de la tabla correspondiente en cada batch
y se redondean al entero más próximo; una tabla pequeña puede no recibir errores.

| Parámetro CLI | Predeterminado | Efecto |
|---|---:|---|
| `--customers` | 2000 | Total de clientes |
| `--customer-change-rate` | 0.05 | Selección mensual de clientes que cambian |
| `--product-change-rate` | 0.15 | Selección mensual de productos que suben de precio |
| `--duplicate-rate` | 0.01 | Duplicados exactos en cada tabla |
| `--formatting-rate` | 0.02 | Espacios/mayúsculas en email y categoría; espacios/minúsculas en método de pago |
| `--missing-rate` | 0.02 | Teléfonos ausentes |
| `--invalid-rate` | 0.005 | Correos inválidos, consentimiento ausente y cantidades negativas |
| `--late-payment-rate` | 0.01 | Pagos de enero a mayo que llegan un batch después |

Las tasas de cambios se limitan a las entidades elegibles disponibles. Los campos
de un registro pueden recibir varias alteraciones; el reporte las enumera en el
orden aplicado. Las reglas de errores usan un generador aleatorio separado:
cambiar su tasa no modifica las ventas correctas ni los cambios de negocio.

Los pagos tardíos conservan `paid_at`, ID e importe; cambia el batch de entrega.
No se retrasa ningún pago de junio, para que al concluir los seis batches no falten
registros. Los duplicados pueden aumentar el conteo bruto, pero tras deduplicar
todos los IDs de la referencia deben estar presentes.

## Uso de la referencia

Alimenta el pipeline **solo con `raw`**. `reference` es una respuesta de control
separada, agrupada por mes del evento antes de aplicar retrasos y errores. Sus
metadatos representan la entrega prevista; los de raw representan la real.
Por ello no compares directamente los conteos de pagos de un solo mes entre ambas
capas: reconcilia por ID y considera las entregas siguientes.

`business_changes.jsonl` enumera entidad, campo, valor anterior, valor nuevo y
fecha efectiva. `injected_issues.jsonl` enumera las alteraciones con el ID del
registro; para datos tardíos indica el batch previsto y el real.

Los espacios y duplicados pueden corregirse. Un teléfono eliminado o correo
inválido no siempre puede recuperarse desde raw: conserva el desconocido o envía
el registro a cuarentena según tu política. Nunca uses la referencia como entrada
para completar datos. La comparación con la referencia sirve para medir registros
aceptados, normalizados y rechazados, no para asumir que toda corrupción es reversible.

Las pruebas verifican reproducibilidad, entidades sin cambios, precios vigentes,
integridad de ventas y pagos, cobertura de IDs entre batches, retrasos y exportación.

# Coffee shop: datos para un pipeline incremental y SCD tipo 2

Simulación reproducible de enero a junio de 2025. El generador produce seis
entregas mensuales con cambios de negocio y errores controlados. Los scripts de
`warehouse/` cargan Bronze en DuckDB. dbt construye Silver, las snapshots SCD
y las tablas Gold para análisis.

## Entornos de dbt

Cada target usa un archivo DuckDB distinto. La macro `generate_schema_name`
agrupa las salidas de dbt en un esquema para `dev` y `ci`. El source de Bronze
resuelve su esquema según el target y la ingesta debe escribir en ese mismo
esquema.

| Target | Archivo predeterminado | Esquemas |
|---|---|---|
| `dev` | `data/coffee_shop.duckdb` | Todas las capas en `dev` |
| `ci` | `data/coffee_shop_ci.duckdb` | Todas las capas en `ci` |
| `prod` | `data/coffee_shop_prod.duckdb` | `bronze`, `silver` (incluye snapshots), `gold` |

Desde la raíz del repositorio, instala las dependencias fijadas en `uv.lock`.
GitHub Actions usa dbt v2.0.9, que incorpora el adaptador de DuckDB.

```powershell
uv sync --locked
uv tool install --python 3.13 dbt==2.0.9
dbt --version
```

Si todavía no tienes un perfil local, copia `coffee_shop/profiles.example.yml` a
`coffee_shop/profiles.yml`. Si ya tienes uno, puedes incorporar los targets que
te falten conservando los valores de tu perfil. Git ignora el perfil local.

```powershell
Copy-Item coffee_shop/profiles.example.yml coffee_shop/profiles.yml
dbt deps --project-dir coffee_shop --profiles-dir coffee_shop --target dev
```

Para iniciar Bronze en desarrollo, ejecuta lo siguiente desde la raíz. Después
puedes cargar un CSV con `warehouse/03_load_bronze.py --batch batch_001 --entity customers`.

```powershell
uv run --locked python warehouse/01_setup.py
uv run --locked python warehouse/02_bronze_tables.py
```

## CI y despliegue de producción

CI valida los PR hacia `main` en un runner limpio. Ejecuta las pruebas del
generador, carga las cinco entidades de cada lote en un archivo DuckDB aislado
y ejecuta `dbt build` después de cada lote. Así se prueban también las versiones
que capturan las snapshots.

El despliegue se ejecuta cuando se actualiza `main` o se lanza manualmente desde
esa rama. Reconstruye los seis lotes sintéticos en orden y publica el archivo de
producción y las cinco tablas Gold en Parquet como artefacto de la ejecución.
En GitHub, abre **Actions → Deploy dbt (Production)**, elige una ejecución
exitosa y descarga `coffee-shop-prod-<commit>` de **Artifacts**. Los artefactos
tienen la retención configurada en el repositorio.

Para obtener los mismos archivos localmente, ejecuta desde la raíz:

```powershell
uv run --locked python warehouse/build_duckdb.py --target prod
```

El script requiere una ruta de base nueva. Para conservar una construcción anterior,
usa `--database data/otra_revision.duckdb`. También puedes reproducir CI localmente
con `--target ci`.

En Power BI Desktop, usa **Obtener datos → Parquet** e importa las tres
dimensiones y los dos hechos de `data/coffee_shop_prod_gold/`. La producción
provisional se reconstruye desde los lotes sintéticos en cada despliegue. Cuando
el proyecto migre a S3 y Snowflake, se sustituirá esta implementación de
`warehouse/` y Power BI podrá leer Gold desde Snowflake.

## Ejecutar el generador

Desde la raíz del proyecto (dependencias fijadas en `uv.lock`):

```powershell
uv sync --locked
uv run python coffee-data-generator/generate.py
uv run python -m unittest discover -s coffee-data-generator/tests -v
```

La salida predeterminada es `data/coffee_2025_csv`. Para otra ejecución:

```powershell
uv run python coffee-data-generator/generate.py --seed 42 --output data/otra_ejecucion
```

No se sobrescriben carpetas existentes. Misma semilla, configuración y versiones
de dependencias producen los mismos datos. Las fechas de la simulación son fijas,
independientes del día real de ejecución. Importar `generate.py` no ejecuta nada.

## Archivos

```text
data/coffee_2025_csv/
  manifest.json
  raw/
    batch_001/ ... batch_006/
      customers.csv
      products.csv
      orders.csv
      order_items.csv
      payments.csv
  reference/
    batch_001/ ... batch_006/  (las mismas cinco tablas, correctas)
    business_changes.csv
    injected_issues.csv
```

CSV en UTF-8 sin BOM, con encabezado fijo incluso en archivos vacíos, separador
coma y salto de línea LF. Los campos con comas, comillas o saltos de línea se
encierran entre comillas dobles; las comillas internas se duplican. Los nulos se
representan con `\N` (reservado; no se admite como texto literal); un campo vacío
es texto vacío. Los booleanos se escriben `true` y `false`, y los números usan
punto decimal sin separador de miles. CSV no almacena tipos: deben interpretarse
según el contrato de columnas. No recortar espacios durante la lectura de RAW.
Fechas: `YYYY-MM-DD`; timestamps: `YYYY-MM-DDTHH:MM:SS`, hora local de Ciudad de
México sin offset UTC. `manifest.json` conserva formato JSON y declara `csv_format`.

La salida predeterminada es ahora `data/coffee_2025_csv`; los archivos JSONL de
una ejecución anterior en `data/coffee_2025` se conservan. Para regenerar utiliza
otra carpeta si la salida CSV ya existe.

`batch_001` corresponde a enero, entregado el 1 de febrero; el último corresponde
a junio y se entrega el 1 de julio. Los periodos son [inicio, fin): incluyen el
inicio y excluyen el primer instante del mes siguiente. `manifest.json` contiene
la configuración, los periodos, las entregas y los conteos de ambas capas.

## Contrato de las fuentes

### Columnas y tipos lógicos

Los tipos siguientes son los esperados después de interpretar el CSV, no una
garantía de calidad de RAW: los errores intencionales se conservan. Los importes
se deben interpretar como decimales, por ejemplo `DECIMAL(12,2)`; el archivo no
incluye código de moneda. Los teléfonos son texto, no números.

Columnas comunes a las cinco entidades:

| Columna | Tipo | Significado |
|---|---|---|
| `source_record_id` | texto | Identificador del registro de origen dentro de la entidad; se repite en duplicados |
| `batch_id` | texto | Lote de entrega del origen, de `batch_001` a `batch_006` |
| `delivered_at` | timestamp local | Fecha de entrega, no fecha del evento ni de ingesta |

| Archivo | Columnas propias y tipos |
|---|---|
| `customers.csv` | `customer_id` entero; `first_name`, `last_name`, `email`, `phone` texto; `birth_date`, `registered_at` fecha; `marketing_opt_in` booleano; `source_updated_at` timestamp local |
| `products.csv` | `product_id` entero; `sku`, `name`, `category`, `size` texto; `price` decimal; `sales_weight` entero; `active` booleano; `source_updated_at` timestamp local |
| `orders.csv` | `order_id`, `customer_id`, `item_count` entero; `ordered_at` timestamp local; `subtotal` decimal |
| `order_items.csv` | `order_item_id`, `order_id`, `product_id`, `quantity` entero; `unit_price`, `line_total` decimal |
| `payments.csv` | `payment_id`, `order_id` entero; `payment_method`, `status` texto; `amount` decimal; `paid_at` timestamp local |

- **Grano:** clientes y productos entregan un estado completo por versión; órdenes,
  artículos y pagos entregan una fila por registro, más los duplicados inyectados.
  `item_count` es la suma de unidades de la orden, no el número de líneas.
- **Nulos:** `orders.customer_id` nulo es una venta sin cliente identificado y es
  válido. `products.size` nulo indica que el tamaño no aplica al producto.
  `customers.phone` puede faltar en RAW. `marketing_opt_in` nulo es un
  error y no equivale a `false`. Las demás columnas de las cinco entidades no
  tienen nulos previstos por este generador.
- **Relaciones:** `orders.customer_id` apunta a clientes cuando no es nulo;
  `order_items.order_id` y `payments.order_id` apuntan a órdenes;
  `order_items.product_id` apunta a productos. Clientes y productos tienen varias
  versiones: su ID de negocio no es único en el histórico recibido.
- **Importes correctos:** `quantity > 0`, `line_total = quantity * unit_price`,
  `subtotal = SUM(line_total)` por orden y `amount = subtotal`. En RAW puede haber
  cantidades negativas inyectadas sin recalcular los demás importes; deben
  detectarse, no aceptarse como devoluciones.
- **Pagos:** en la simulación hay un pago por orden antes de duplicados;
  `status` es `COMPLETED` y el método normalizado pertenece a `CREDIT_CARD`,
  `DEBIT_CARD`, `CASH` o `DIGITAL_WALLET`. Un pago puede llegar en el siguiente lote.
- **Catálogo:** `sales_weight` es un peso utilizado para simular la selección de
  productos; no mide ventas observadas. Hay 36 productos y `active` es `true`.

Los reportes de validación también son CSV. `business_changes.csv` contiene
`table,entity_id,field,before,after,source_updated_at`; `injected_issues.csv`
contiene `batch_id,table,source_record_id,kind,field,before,after,expected_batch,actual_batch`.
En ambos, `before` y `after` contienen valores JSON dentro de la celda CSV para
preservar su tipo variable: `null`, booleano, número o texto entrecomillado JSON.
Una columna no aplicable usa `\N`; se distingue del valor JSON `null` registrado
explícitamente. Estos reportes solo sirven para validación.

### Reglas de entrega e historia

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
  Un cliente nuevo puede cambiar a partir del mes siguiente a su primera entrega.
- Todos los 36 productos aparecen inicialmente en enero. Solo cambia `price`:
  no se agregan ni se desactivan productos. Hay clientes y productos sin cambios.
- Enero contiene solo estados iniciales, sin cambios de negocio. Desde febrero
  se permite como máximo un cambio por entidad y mes. Cada lote contiene como
  máximo una versión por cliente o producto, antes de los duplicados intencionales.
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

Bronze conserva las versiones recibidas. Tras deduplicar por `source_record_id`,
`silver_products` y `silver_customers` seleccionan la última versión por
`product_id` y `customer_id`, respectivamente, según `source_updated_at`.
Para practicar snapshots de dbt, carga un lote, actualiza esos modelos y ejecuta
las snapshots antes de cargar el siguiente. Las snapshots guardan el historial
que observan en cada ejecución. Usa datos del generador actual para este
ejercicio, ya que las ejecuciones anteriores conservan su comportamiento original.

## Cambios y errores configurables

Desde febrero, cada mes se selecciona aproximadamente un 5% del total de clientes
y un 15% de productos para cambios, dentro de una mitad del catálogo habilitada para cambiar.
Esto preserva entidades sin modificaciones. Cada entidad seleccionada cambia un
atributo en un instante aleatorio del mes, posterior a su versión anterior.
Solo son elegibles las entidades entregadas en meses anteriores.

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

`business_changes.csv` enumera entidad, campo, valor anterior, valor nuevo y
fecha efectiva. `injected_issues.csv` enumera las alteraciones con el ID del
registro; para datos tardíos indica el batch previsto y el real.

Los espacios y duplicados pueden corregirse. Un teléfono eliminado o correo
inválido no siempre puede recuperarse desde raw: conserva el desconocido o envía
el registro a cuarentena según tu política. Nunca uses la referencia como entrada
para completar datos. La comparación con la referencia sirve para medir registros
aceptados, normalizados y rechazados, no para asumir que toda corrupción es reversible.

Las pruebas verifican reproducibilidad, entidades sin cambios, precios vigentes,
integridad de ventas y pagos, cobertura de IDs entre batches, retrasos y exportación.

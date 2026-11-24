# Reporte de Power BI

Abre [coffee-shop-powerbi.pbix](coffee-shop-powerbi.pbix) en Power BI Desktop.
El reporte usa datos sintéticos de enero a junio de 2025 y tiene tres páginas:

- **Ventas** muestra el importe mensual, los pedidos, las unidades y el ticket promedio.
- **Productos** muestra los rankings por importe y unidades, y las ventas por categoría.
- **Clientes** muestra los compradores identificados y la recompra por cohorte mensual.

## Actualizar los datos

1. En GitHub, abre **Actions → Deploy dbt (Production)** y descarga el artefacto
   `coffee-shop-prod-<commit>` de una ejecución exitosa.
2. Descomprime el ZIP. En Power BI Desktop, abre **Transformar datos** y cambia
   el paso **Origen** de cada consulta para que lea su archivo Parquet en la
   carpeta `coffee_shop_prod_gold` del mismo artefacto.
3. Selecciona **Cerrar y aplicar**.

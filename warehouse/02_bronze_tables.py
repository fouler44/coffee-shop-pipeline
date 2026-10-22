from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "coffee_shop.duckdb"

def create_bronze_tables():
    """Crea las tablas de la capa bronce en el esquema dev."""
    with duckdb.connect(str(DB_PATH)) as conn:
        conn.execute("SET SCHEMA = 'dev'")

        # Crear tabla customers
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id          VARCHAR,
                first_name           VARCHAR,
                last_name            VARCHAR,
                email                VARCHAR,
                phone                VARCHAR,
                birth_date           VARCHAR,
                registered_at        VARCHAR,
                marketing_opt_in     VARCHAR,
                source_updated_at    VARCHAR,
                source_record_id     VARCHAR,
                batch_id             VARCHAR,
                delivered_at         VARCHAR,

                -- Metadata añadida durante la carga
                _batch_id            VARCHAR NOT NULL,
                _source_file         VARCHAR NOT NULL,
                _source_row_number   BIGINT NOT NULL,
                _ingested_at         TIMESTAMPTZ NOT NULL
            )
        """)

        # Crear tabla orders
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id             VARCHAR,
                customer_id          VARCHAR,
                ordered_at           VARCHAR,
                item_count           VARCHAR,
                subtotal             VARCHAR,
                source_record_id     VARCHAR,
                batch_id             VARCHAR,
                delivered_at         VARCHAR,

                -- Metadata añadida durante la carga
                _batch_id            VARCHAR NOT NULL,
                _source_file         VARCHAR NOT NULL,
                _source_row_number   BIGINT NOT NULL,
                _ingested_at         TIMESTAMPTZ NOT NULL
            )
        """)

        # Crear tabla products
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id           VARCHAR,
                sku                  VARCHAR,
                name                 VARCHAR,
                category             VARCHAR,
                size                 VARCHAR,
                price                VARCHAR,
                sales_weight         VARCHAR,
                active               VARCHAR,
                source_updated_at    VARCHAR,
                source_record_id     VARCHAR,
                batch_id             VARCHAR,
                delivered_at         VARCHAR,

                -- Metadata añadida durante la carga
                _batch_id            VARCHAR NOT NULL,
                _source_file         VARCHAR NOT NULL,
                _source_row_number   BIGINT NOT NULL,
                _ingested_at         TIMESTAMPTZ NOT NULL
            )
        """)

        # Crear tabla order_items
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id        VARCHAR,
                order_id             VARCHAR,
                product_id           VARCHAR,
                quantity             VARCHAR,
                unit_price           VARCHAR,
                line_total           VARCHAR,
                source_record_id     VARCHAR,
                batch_id             VARCHAR,
                delivered_at         VARCHAR,

                -- Metadata añadida durante la carga
                _batch_id            VARCHAR NOT NULL,
                _source_file         VARCHAR NOT NULL,
                _source_row_number   BIGINT NOT NULL,
                _ingested_at         TIMESTAMPTZ NOT NULL
            )
        """)

        # Crear tabla payments
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id           VARCHAR,
                order_id             VARCHAR,
                payment_method       VARCHAR,
                amount               VARCHAR,
                status               VARCHAR,
                paid_at              VARCHAR,
                source_record_id     VARCHAR,
                batch_id             VARCHAR,
                delivered_at         VARCHAR,

                -- Metadata añadida durante la carga
                _batch_id            VARCHAR NOT NULL,
                _source_file         VARCHAR NOT NULL,
                _source_row_number   BIGINT NOT NULL,
                _ingested_at         TIMESTAMPTZ NOT NULL
            )
        """)


if __name__ == "__main__":
    create_bronze_tables()
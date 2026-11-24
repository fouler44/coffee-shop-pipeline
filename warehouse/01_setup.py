import duckdb

from duckdb_config import BRONZE_SCHEMA, DB_PATH


def setup_database():
    """Prepara la base y el esquema de las tablas de origen."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DB_PATH)) as conn:
        quoted_schema = BRONZE_SCHEMA.replace('"', '""')
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{quoted_schema}"')

    print(f"Base de datos: {DB_PATH}")
    print(f"Esquema disponible: {BRONZE_SCHEMA}")


if __name__ == "__main__":
    setup_database()

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "coffee_shop.duckdb"


def setup_database():
    """Prepara la base persistente y el esquema de desarrollo."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DB_PATH)) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS dev")

    print(f"Base de datos: {DB_PATH}")
    print("Esquema disponible: dev")


if __name__ == "__main__":
    setup_database()

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(
    os.environ.get("COFFEE_DUCKDB_PATH", PROJECT_ROOT / "data" / "coffee_shop.duckdb")
)
BRONZE_SCHEMA = os.environ.get("COFFEE_BRONZE_SCHEMA", "dev")
RAW_ROOT = Path(
    os.environ.get("COFFEE_RAW_ROOT", PROJECT_ROOT / "data" / "coffee_2025_csv" / "raw")
)

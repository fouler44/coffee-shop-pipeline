"""Reconstruye el pipeline DuckDB a partir de lotes sintéticos."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import duckdb

from duckdb_config import PROJECT_ROOT


ENTITIES = ("customers", "products", "orders", "order_items", "payments")
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_SCHEMAS = {"ci": "ci", "prod": "bronze"}
GOLD_TABLES = ("dim_customers", "dim_date", "dim_products", "fct_order_items", "fct_payments")


def export_gold(database):
    output = database.with_name(f"{database.stem}_gold")
    output.mkdir(exist_ok=True)
    with duckdb.connect(str(database), read_only=True) as conn:
        for table in GOLD_TABLES:
            conn.table(f"gold.{table}").write_parquet(str(output / f"{table}.parquet"))
    print(f"Gold para Power BI: {output}")


def build(target, database, dbt):
    DATA_DIR.mkdir(exist_ok=True)
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        raise SystemExit(f"La base ya existe: {database}. Usa una ruta nueva.")

    with TemporaryDirectory(prefix=f"{target}-raw-", dir=DATA_DIR) as temp_dir:
        deliveries = Path(temp_dir) / "deliveries"
        raw_root = deliveries / "raw"
        env = {
            **os.environ,
            "COFFEE_DUCKDB_PATH": str(database),
            "COFFEE_BRONZE_SCHEMA": BRONZE_SCHEMAS[target],
            "COFFEE_RAW_ROOT": str(raw_root),
        }
        dbt_args = [
            "--project-dir", "coffee_shop",
            "--profiles-dir", "coffee_shop",
            "--target", target,
        ]

        def run(*args):
            subprocess.run(args, cwd=PROJECT_ROOT, env=env, check=True)

        run(sys.executable, "coffee-data-generator/generate.py", "--output", deliveries)
        run(sys.executable, "warehouse/01_setup.py")
        run(sys.executable, "warehouse/02_bronze_tables.py")
        run(dbt, "deps", *dbt_args)

        for batch in sorted(raw_root.iterdir()):
            print(f"Procesando {batch.name} en {target}", flush=True)
            for entity in ENTITIES:
                run(
                    sys.executable, "warehouse/03_load_bronze.py",
                    "--batch", batch.name, "--entity", entity,
                )
            run(dbt, "build", *dbt_args)

    if target == "prod":
        export_gold(database)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=BRONZE_SCHEMAS)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--dbt", default="dbt", help="Ejecutable de dbt")
    args = parser.parse_args()
    database = args.database or DATA_DIR / f"coffee_shop_{args.target}.duckdb"
    build(args.target, database.resolve(), args.dbt)

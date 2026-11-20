import duckdb
import csv
import argparse

from duckdb_config import BRONZE_SCHEMA, DB_PATH, RAW_ROOT

parser = argparse.ArgumentParser(description="Carga archivos a bronze")

parser.add_argument(
    "--batch",
    required=True,
    help="Lote que se cargará, por ejemplo batch_001",
)

parser.add_argument(
    "--entity",
    required=True,
    choices=["customers", "products", "orders", "order_items", "payments"],
    help="Entidad que se cargará",
)

args = parser.parse_args()
BATCH_ID = args.batch

ENTITY = args.entity
CSV_PATH = RAW_ROOT / BATCH_ID / f"{ENTITY}.csv"
SOURCE_FILE = CSV_PATH.relative_to(RAW_ROOT).as_posix()

def load_bronze():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"No existe el archivo: {CSV_PATH}")
    
    with CSV_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader)  # Saltar el encabezado
        expected_rows = sum(1 for _ in reader)

    with duckdb.connect(str(DB_PATH)) as conn:
        conn.execute("SET SCHEMA = ?", [BRONZE_SCHEMA])
        result = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM {ENTITY}
            WHERE _batch_id = ?
              AND _source_file = ?
            """,
            [BATCH_ID, SOURCE_FILE],
        ).fetchone()

        print(f"Filas ya cargadas de este archivo: {result[0]}")
        
        if result[0] > 0:
            if result[0] != expected_rows:
                raise ValueError(
                    f"La carga existente tiene {result[0]} filas, "
                    f"pero el CSV contiene {expected_rows}."
                )
            print("El archivo ya está cargado. Se omite.")
            return
        
        conn.execute("BEGIN TRANSACTION")

        try:
            conn.execute(
                rf"""
                INSERT INTO {ENTITY} BY NAME
                SELECT
                    * EXCLUDE (ordinality),
                    ? AS _batch_id,
                    ? AS _source_file,
                    ordinality AS _source_row_number,
                    current_timestamp AS _ingested_at
                FROM read_csv(
                    ?,
                    header = true,
                    delim = ',',
                    all_varchar = true,
                    nullstr = '\N'
                ) WITH ORDINALITY
                """,
                [BATCH_ID, SOURCE_FILE, str(CSV_PATH)],
            )

            loaded_rows = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM {ENTITY}
                WHERE _batch_id = ?
                  AND _source_file = ?
                """,
                [BATCH_ID, SOURCE_FILE],
            ).fetchone()[0]
            
            if loaded_rows != expected_rows:
                raise ValueError(
                    f"Conteo incorrecto: CSV={expected_rows}, "
                    f"tabla={loaded_rows}"
                )

            conn.execute("COMMIT")

        except Exception:
            conn.execute("ROLLBACK")
            raise

        print(f"Carga completada: {loaded_rows} filas.")


if __name__ == "__main__":
    load_bronze()

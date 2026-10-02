"""Monthly source deliveries and a separate clean oracle for pipeline exercises."""

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import random

from generators.customers import generate_customers
from generators.products import products
from generators.orders import generate_orders
from generators.order_items import generate_order_items
from generators.payments import generate_payments


TABLES = ("customers", "products", "orders", "order_items", "payments")
PRIMARY_KEYS = {
    "customers": "customer_id", "products": "product_id",
    "orders": "order_id", "order_items": "order_item_id",
    "payments": "payment_id",
}


@dataclass(frozen=True)
class Config:
    seed: int = 42
    customer_count: int = 2000
    customer_change_rate: float = 0.05
    product_change_rate: float = 0.15
    duplicate_rate: float = 0.01
    formatting_rate: float = 0.02
    missing_rate: float = 0.02
    invalid_rate: float = 0.005
    late_payment_rate: float = 0.01

    def validate(self):
        if self.customer_count < 1:
            raise ValueError("customer_count must be positive")
        for name, value in asdict(self).items():
            if name.endswith("_rate") and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


def monthly_bounds():
    return [
        (datetime(2025, month, 1), datetime(2025, month + 1, 1))
        for month in range(1, 7)
    ]


def stamp_versions(rows, prefix):
    for index, row in enumerate(rows, 1):
        row["source_record_id"] = f"{prefix}-{index:06d}"
    return rows


def dimension_history(config):
    rng = random.Random(config.seed + 100)
    customers = generate_customers(
        config.customer_count, seed=config.seed,
        reference_date=date(2025, 6, 30),
        registered_start_date=date(2023, 1, 1),
        registered_end_date=date(2025, 6, 30),
    )
    for customer in customers:
        customer["email"] = customer["email"].strip().lower()
        customer["marketing_opt_in"] = rng.random() < 0.6
        customer["source_updated_at"] = max(
            datetime(2025, 1, 1),
            datetime.combine(customer["registered_at"], datetime.min.time()),
        )
    catalog = deepcopy(products)
    for product in catalog:
        product["source_updated_at"] = datetime(2025, 1, 1)

    customer_events = deepcopy(customers)
    product_events = deepcopy(catalog)
    changes = []
    # Only this stable subset can change; the rest exercise unchanged SCD rows.
    mutable_customers = rng.sample(customers, int(len(customers) * 0.5))
    mutable_products = rng.sample(catalog, len(catalog) // 2)
    for start, end in monthly_bounds():
        for table, candidates, rate, events in (
            ("customers", mutable_customers, config.customer_change_rate, customer_events),
            ("products", mutable_products, config.product_change_rate, product_events),
        ):
            eligible = [row for row in candidates if row["source_updated_at"] < end]
            count = min(len(eligible), round(
                (len(customers) if table == "customers" else len(catalog)) * rate
            ))
            for row in rng.sample(eligible, count):
                earliest = max(start, row["source_updated_at"]) + timedelta(seconds=1)
                seconds = int((end - earliest).total_seconds())
                changed_at = earliest + timedelta(seconds=rng.randrange(seconds))
                if table == "products":
                    field = "price"
                    value = row[field] + rng.choice((2, 3, 5))
                else:
                    field = rng.choice(("email", "phone", "marketing_opt_in"))
                    if field == "email":
                        value = f"customer{row['customer_id']}.{len(changes)}@example.com"
                    elif field == "phone":
                        value = f"+52{rng.randrange(1000000000, 10000000000)}"
                        while value == row[field]:
                            value = f"+52{rng.randrange(1000000000, 10000000000)}"
                    else:
                        value = not row[field]
                changes.append({
                    "table": table, "entity_id": row[PRIMARY_KEYS[table]],
                    "field": field, "before": row[field], "after": value,
                    "source_updated_at": changed_at,
                })
                row[field] = value
                row["source_updated_at"] = changed_at
                events.append(deepcopy(row))

    customer_events.sort(key=lambda row: (row["source_updated_at"], row["customer_id"]))
    product_events.sort(key=lambda row: (row["source_updated_at"], row["product_id"]))
    return (customers, stamp_versions(customer_events, "customer"),
            stamp_versions(product_events, "product"), changes)


def corrupt(rows, table, config, rng, issues, batch_id):
    result = deepcopy(rows)

    def apply(rate, field, kind, transform):
        # Disjoint selection within a field is unnecessary: log every mutation in order.
        for row in rng.sample(result, round(len(result) * rate)):
            before = row[field]
            row[field] = transform(before)
            issues.append({
                "batch_id": batch_id, "table": table,
                "source_record_id": row["source_record_id"],
                "kind": kind, "field": field,
                "before": before, "after": row[field],
            })

    if table == "customers":
        apply(config.formatting_rate, "email", "formatting", lambda v: f" {v.upper()} ")
        apply(config.missing_rate, "phone", "missing", lambda v: None)
        apply(config.invalid_rate, "marketing_opt_in", "missing", lambda v: None)
        apply(config.invalid_rate, "email", "invalid", lambda v: "invalid-email")
    elif table == "products":
        apply(config.formatting_rate, "category", "formatting", lambda v: f" {v.upper()} ")
    elif table == "order_items":
        apply(config.invalid_rate, "quantity", "invalid", lambda v: -v)
    elif table == "payments":
        apply(config.formatting_rate, "payment_method", "formatting", lambda v: f" {v.lower()} ")

    for row in rng.sample(result, round(len(result) * config.duplicate_rate)):
        result.append(deepcopy(row))
        issues.append({
            "batch_id": batch_id, "table": table,
            "source_record_id": row["source_record_id"], "kind": "duplicate",
        })
    rng.shuffle(result)
    return result


def build_dataset(config=Config()):
    config.validate()
    customers, customer_events, product_events, changes = dimension_history(config)
    orders = generate_orders(
        customers, date(2025, 1, 1), date(2025, 6, 30),
        rng=random.Random(config.seed + 1),
    )
    orders.sort(key=lambda row: row["ordered_at"])
    for index, order in enumerate(orders, 1):
        order["order_id"] = index
    items = generate_order_items(
        orders, products, rng=random.Random(config.seed + 2), price_history=product_events,
    )
    payments = generate_payments(orders, rng=random.Random(config.seed + 3))
    for table, rows in (("orders", orders), ("order_items", items), ("payments", payments)):
        stamp_versions(rows, table)

    order_month = {row["order_id"]: row["ordered_at"].month for row in orders}
    clean = {month: {table: [] for table in TABLES} for month in range(1, 7)}
    for table, rows in (("customers", customer_events), ("products", product_events)):
        for row in rows:
            clean[row["source_updated_at"].month][table].append(row)
    for row in orders:
        clean[row["ordered_at"].month]["orders"].append(row)
    for row in items:
        clean[order_month[row["order_id"]]]["order_items"].append(row)
    for row in payments:
        clean[row["paid_at"].month]["payments"].append(row)

    delivered = deepcopy(clean)
    issues = []
    late_rng = random.Random(config.seed + 4)
    # Select from original cohorts, so a delayed record is never delayed twice.
    for month in range(1, 6):
        delayed = late_rng.sample(clean[month]["payments"], round(
            len(clean[month]["payments"]) * config.late_payment_rate
        ))
        ids = {row["payment_id"] for row in delayed}
        delivered[month]["payments"] = [
            row for row in delivered[month]["payments"] if row["payment_id"] not in ids
        ]
        delivered[month + 1]["payments"].extend(deepcopy(delayed))
        for row in delayed:
            issues.append({
                "kind": "late_arrival", "table": "payments",
                "source_record_id": row["source_record_id"],
                "expected_batch": f"batch_{month:03d}",
                "actual_batch": f"batch_{month + 1:03d}",
            })

    batches = []
    dirty_rng = random.Random(config.seed + 5)
    for month, (start, end) in enumerate(monthly_bounds(), 1):
        batch_id = f"batch_{month:03d}"
        metadata = {"batch_id": batch_id, "delivered_at": end}
        reference, raw = {}, {}
        for table in TABLES:
            reference[table] = [dict(row, **metadata) for row in clean[month][table]]
            source_rows = [dict(row, **metadata) for row in delivered[month][table]]
            raw[table] = corrupt(source_rows, table, config, dirty_rng, issues, batch_id)
        batches.append({
            "batch_id": batch_id, "period_start": start, "period_end_exclusive": end,
            "delivered_at": end, "reference": reference, "raw": raw,
        })
    return {"config": asdict(config), "batches": batches,
            "changes": changes, "issues": issues}


def json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)}")


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=json_default, ensure_ascii=False) + "\n")


def export_dataset(dataset, output):
    output = Path(output)
    # Never silently overwrite a previous exercise or a user's pipeline output.
    output.mkdir(parents=True, exist_ok=False)
    summary = []
    for batch in dataset["batches"]:
        counts = {}
        for layer in ("raw", "reference"):
            directory = output / layer / batch["batch_id"]
            directory.mkdir(parents=True)
            counts[layer] = {}
            for table, rows in batch[layer].items():
                write_jsonl(directory / f"{table}.jsonl", rows)
                counts[layer][table] = len(rows)
        summary.append({
            key: value for key, value in batch.items() if key not in ("raw", "reference")
        } | {"counts": counts})
    write_jsonl(output / "reference" / "business_changes.jsonl", dataset["changes"])
    write_jsonl(output / "reference" / "injected_issues.jsonl", dataset["issues"])
    manifest = {"config": dataset["config"], "batches": summary,
                "timezone": "America/Mexico_City (local timestamps without UTC offset)",
                "reference_grouping": "event month before delays and corruption"}
    with (output / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, default=json_default, ensure_ascii=False, indent=2)
    return output

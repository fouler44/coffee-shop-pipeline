from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from batches import Config, TABLES, build_dataset, export_dataset


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = Config(customer_count=100)
        cls.dataset = build_dataset(cls.config)
        cls.rows = {
            table: [row for batch in cls.dataset["batches"] for row in batch["reference"][table]]
            for table in TABLES
        }

    def test_reproducible_and_source_catalog_not_mutated(self):
        self.assertEqual(self.dataset, build_dataset(self.config))

    def test_history_and_unchanged_entities(self):
        for table, key in (("customers", "customer_id"), ("products", "product_id")):
            versions = defaultdict(list)
            for row in self.rows[table]:
                versions[row[key]].append(row)
            self.assertTrue(any(len(rows) == 1 for rows in versions.values()))
            self.assertTrue(any(len(rows) > 1 for rows in versions.values()))
            for rows in versions.values():
                dates = [row["source_updated_at"] for row in rows]
                self.assertEqual(dates, sorted(set(dates)))
        self.assertEqual(len({r["product_id"] for r in self.rows["products"]}), 36)
        self.assertTrue(all(r["active"] for r in self.rows["products"]))
        fields = {change["field"] for change in self.dataset["changes"]}
        self.assertEqual(fields, {"phone", "email", "marketing_opt_in", "price"})

    def test_clean_relationships_and_historical_prices(self):
        orders = {row["order_id"]: row for row in self.rows["orders"]}
        customers = {row["customer_id"]: row for row in self.rows["customers"]}
        versions = defaultdict(list)
        for product in self.rows["products"]:
            versions[product["product_id"]].append(product)
        totals, units = defaultdict(float), defaultdict(int)
        for item in self.rows["order_items"]:
            order = orders[item["order_id"]]
            price = [p for p in versions[item["product_id"]]
                     if p["source_updated_at"] <= order["ordered_at"]][-1]["price"]
            self.assertEqual(item["unit_price"], price)
            self.assertGreater(item["quantity"], 0)
            self.assertEqual(item["line_total"], price * item["quantity"])
            totals[order["order_id"]] += item["line_total"]
            units[order["order_id"]] += item["quantity"]
        for order in orders.values():
            self.assertEqual(order["subtotal"], totals[order["order_id"]])
            self.assertEqual(order["item_count"], units[order["order_id"]])
            if order["customer_id"] is not None:
                self.assertLessEqual(customers[order["customer_id"]]["registered_at"],
                                     order["ordered_at"].date())
        for payment in self.rows["payments"]:
            order = orders[payment["order_id"]]
            self.assertEqual(payment["amount"], order["subtotal"])
            self.assertGreater(payment["paid_at"], order["ordered_at"])
        self.assertEqual(len(self.rows["payments"]), len(orders))

    def test_batches_errors_and_late_data_reconcile(self):
        self.assertEqual(len(self.dataset["batches"]), 6)
        for table in TABLES:
            expected = {r["source_record_id"] for r in self.rows[table]}
            self.assertEqual(len(expected), len(self.rows[table]))
            actual = {r["source_record_id"] for b in self.dataset["batches"] for r in b["raw"][table]}
            self.assertEqual(actual, expected)
        kinds = {issue["kind"] for issue in self.dataset["issues"]}
        self.assertEqual(kinds, {"formatting", "missing", "invalid", "duplicate", "late_arrival"})
        for month, batch in enumerate(self.dataset["batches"], 1):
            self.assertEqual(batch["delivered_at"], datetime(2025, month + 1, 1))
            for order in batch["raw"]["orders"]:
                self.assertEqual(order["ordered_at"].month, month)
        for issue in self.dataset["issues"]:
            if issue["kind"] == "late_arrival":
                original = int(issue["expected_batch"][-3:]) - 1
                arrival = int(issue["actual_batch"][-3:]) - 1
                before = self.dataset["batches"][original]["raw"]["payments"]
                after = self.dataset["batches"][arrival]["raw"]["payments"]
                self.assertFalse(any(r["source_record_id"] == issue["source_record_id"] for r in before))
                self.assertTrue(any(r["source_record_id"] == issue["source_record_id"] for r in after))

    def test_export_round_trip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = export_dataset(self.dataset, Path(directory) / "exercise")
            self.assertEqual(len(list(path.glob("raw/*/*.jsonl"))), 30)
            for table in TABLES:
                for batch in self.dataset["batches"]:
                    for layer in ("raw", "reference"):
                        file = path / layer / batch["batch_id"] / f"{table}.jsonl"
                        rows = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()]
                        self.assertEqual(len(rows), len(batch[layer][table]))
            with self.assertRaises(FileExistsError):
                export_dataset(self.dataset, path)


if __name__ == "__main__":
    unittest.main()

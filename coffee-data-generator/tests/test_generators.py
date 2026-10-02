from datetime import date, datetime
from pathlib import Path
import random
import sys
import unittest


GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT))

from generators.customers import generate_customers
from generators.order_items import choose_order_type, get_day_period
from generators.orders import generate_orders


class PredictableRandom:
    def gauss(self, mean, standard_deviation):
        return 1

    def choices(self, population, weights, k):
        return [population[0]]

    def randint(self, start, end):
        return start

    def random(self):
        return 0

    def choice(self, population):
        return population[0]


class CustomerGenerationTests(unittest.TestCase):
    def test_same_seed_generates_same_customers(self):
        arguments = {
            "num_customers": 5,
            "seed": 42,
            "reference_date": date(2025, 1, 1),
            "registered_start_date": date(2024, 1, 1),
            "registered_end_date": date(2025, 1, 1),
        }

        first_run = generate_customers(**arguments)
        second_run = generate_customers(**arguments)

        self.assertEqual(first_run, second_run)


class OrderGenerationTests(unittest.TestCase):
    def test_only_customers_registered_by_order_date_are_assigned(self):
        customers = [
            {"customer_id": 1, "registered_at": date(2025, 1, 2)},
            {"customer_id": 2, "registered_at": date(2025, 1, 1)},
        ]

        orders = generate_orders(
            customers,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            rng=PredictableRandom(),
        )

        self.assertEqual(orders[0]["customer_id"], 2)

    def test_date_range_is_configurable_and_inclusive(self):
        orders = generate_orders(
            [],
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 2),
            rng=PredictableRandom(),
        )

        self.assertEqual(
            [order["ordered_at"] for order in orders],
            [datetime(2025, 2, 1, 7), datetime(2025, 2, 2, 7)],
        )

        self.assertNotIn("order_date", orders[0])
        self.assertNotIn("hour", orders[0])
        self.assertNotIn("minute", orders[0])

    def test_same_random_seed_generates_same_orders(self):
        arguments = {
            "customers": [],
            "start_date": date(2025, 1, 1),
            "end_date": date(2025, 1, 2),
        }

        first_run = generate_orders(**arguments, rng=random.Random(42))
        second_run = generate_orders(**arguments, rng=random.Random(42))

        self.assertEqual(first_run, second_run)


class TimeBasedBasketTests(unittest.TestCase):
    def test_day_period_boundaries(self):
        self.assertEqual(get_day_period(11), "morning")
        self.assertEqual(get_day_period(12), "afternoon")
        self.assertEqual(get_day_period(16), "afternoon")
        self.assertEqual(get_day_period(17), "evening")

    def test_breakfast_is_not_selected_in_the_evening(self):
        rng = random.Random(42)

        selected_types = {
            choose_order_type(hour=20, rng=rng)
            for _ in range(500)
        }

        self.assertNotIn("breakfast", selected_types)


if __name__ == "__main__":
    unittest.main()

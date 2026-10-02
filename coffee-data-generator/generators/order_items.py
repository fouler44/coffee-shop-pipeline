import random
from bisect import bisect_right

from collections import Counter


ORDER_TYPES = {
    "coffee_only": {
        "weight": 25,
        "categories": {
            "Coffee": [1, 1, 1, 2],
        },
    },

    "coffee_and_pastry": {
        "weight": 30,
        "categories": {
            "Coffee": [1, 1, 1, 2],
            "Bakery": [1, 1, 2],
        },
    },

    "breakfast": {
        "weight": 15,
        "categories": {
            "Coffee": [1, 1, 2],
            "Food": [1],
        },
    },

    "snack": {
        "weight": 15,
        "categories": {
            "Coffee": [1],
            "Desserts": [1, 1, 2],
        },
    },

    "cold_drink_and_dessert": {
        "weight": 10,
        "categories": {
            "Cold Drinks": [1, 1, 2],
            "Desserts": [1],
        },
    },

    "tea_and_pastry": {
        "weight": 5,
        "categories": {
            "Tea": [1],
            "Bakery": [1, 1, 2],
        },
    },
}

ORDER_TYPE_WEIGHTS_BY_PERIOD = {
    "morning": {
        "coffee_only": 20,
        "coffee_and_pastry": 30,
        "breakfast": 30,
        "snack": 5,
        "cold_drink_and_dessert": 5,
        "tea_and_pastry": 10,
    },
    "afternoon": {
        "coffee_only": 25,
        "coffee_and_pastry": 25,
        "breakfast": 5,
        "snack": 20,
        "cold_drink_and_dessert": 15,
        "tea_and_pastry": 10,
    },
    "evening": {
        "coffee_only": 30,
        "coffee_and_pastry": 25,
        "breakfast": 0,
        "snack": 25,
        "cold_drink_and_dessert": 15,
        "tea_and_pastry": 5,
    },
}


def get_day_period(hour):
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def weighted_choice(products, rng=None):
    if rng is None:
        rng = random

    return rng.choices(
        products,
        weights=[p["sales_weight"] for p in products],
        k=1
    )[0]


def choose_order_type(hour=None, rng=None):
    if rng is None:
        rng = random

    order_types = list(ORDER_TYPES.keys())

    if hour is None:
        weights = [
            ORDER_TYPES[order_type]["weight"]
            for order_type in order_types
        ]
    else:
        period = get_day_period(hour)
        period_weights = ORDER_TYPE_WEIGHTS_BY_PERIOD[period]
        weights = [
            period_weights[order_type]
            for order_type in order_types
        ]

    return rng.choices(
        order_types,
        weights=weights,
        k=1
    )[0]


def choose_product_from_category(category, products, rng=None):
    candidates = [
        product
        for product in products
        if product["category"] == category
        and product["active"]
    ]

    if not candidates:
        return weighted_choice(products, rng=rng)

    return weighted_choice(candidates, rng=rng)


def generate_basket(products, order=None, rng=None):
    if rng is None:
        rng = random

    hour = order["ordered_at"].hour if order is not None else None
    order_type = choose_order_type(hour=hour, rng=rng)

    config = ORDER_TYPES[order_type]

    selected_products = []

    for category, possible_counts in config["categories"].items():

        count = rng.choice(possible_counts)

        main_product = choose_product_from_category(
            category,
            products,
            rng=rng,
        )

        selected_products.append(main_product)

        for _ in range(count - 1):

            if rng.random() < 0.70:
                selected_products.append(main_product)

            else:
                another_product = choose_product_from_category(
                    category,
                    products,
                    rng=rng,
                )

                selected_products.append(another_product)

    return selected_products


def generate_order_items(orders, products, rng=None, price_history=None):
    if rng is None:
        rng = random

    order_items = []
    order_item_id = 1

    product_lookup = {
        product["product_id"]: product
        for product in products
    }

    active_products = [
        product
        for product in products
        if product["active"]
    ]

    price_versions = {}
    for version in price_history or []:
        price_versions.setdefault(version["product_id"], []).append(version)
    for versions in price_versions.values():
        versions.sort(key=lambda row: row["source_updated_at"])
    price_dates = {
        product_id: [row["source_updated_at"] for row in versions]
        for product_id, versions in price_versions.items()
    }

    for order in orders:

        selected_products = generate_basket(
            active_products,
            order=order,
            rng=rng,
        )

        product_counts = Counter(
            product["product_id"]
            for product in selected_products
        )

        subtotal = 0

        for product_id, quantity in product_counts.items():

            product = product_lookup[product_id]

            unit_price = product["price"]
            if product_id in price_versions:
                index = bisect_right(
                    price_dates[product_id], order["ordered_at"]
                ) - 1
                if index < 0:
                    raise ValueError("No price valid at the order timestamp")
                unit_price = price_versions[product_id][index]["price"]
            line_total = unit_price * quantity

            order_items.append({
                "order_item_id": order_item_id,
                "order_id": order["order_id"],
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            })

            subtotal += line_total

            order_item_id += 1

        order["item_count"] = sum(product_counts.values())

        order["subtotal"] = round(
            subtotal,
            2
        )

    return order_items

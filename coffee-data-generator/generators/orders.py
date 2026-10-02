from datetime import date, datetime, time, timedelta
import random


def generate_orders(
    customers,
    start_date=date(2025, 1, 1),
    end_date=None,
    rng=None,
):
    if end_date is None:
        end_date = date.today()

    if start_date > end_date:
        raise ValueError("start_date must be earlier than or equal to end_date")

    if rng is None:
        rng = random

    current_date = start_date

    orders = []

    average_orders = {
        0: 100,  # Monday
        1: 105,
        2: 110,
        3: 115,
        4: 140,
        5: 170,
        6: 150
    }

    hours = [
        7, 8, 9, 10, 11, 12, 13,
        14, 15, 16, 17, 18, 19, 20
    ]

    hour_weights = [
        4, 10, 10, 7, 5, 5, 6,
        5, 4, 5, 7, 8, 6, 3
    ]
    
    order_id = 1
    
    while current_date <= end_date:
        eligible_customers = [
            customer
            for customer in customers
            if customer["registered_at"] <= current_date
        ]
        mean = average_orders[current_date.weekday()]

        orders_today = max(
            0,
            int(rng.gauss(mean, mean * 0.15))
        )
        
        for _ in range(orders_today):
            
            hour = rng.choices(
                hours,
                weights=hour_weights,
                k=1
            )[0]
            
            minute = rng.randint(0, 59)
            
            if eligible_customers and rng.random() < 0.40:
                customer_id = rng.choice(
                    eligible_customers
                )["customer_id"]
            else:
                customer_id = None

            ordered_at = datetime.combine(
                current_date,
                time(hour=hour, minute=minute),
            )
            
            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "ordered_at": ordered_at,
                "item_count": None,
                "subtotal": None
            })
            
            order_id += 1
            
        current_date += timedelta(days=1)
        
    return orders

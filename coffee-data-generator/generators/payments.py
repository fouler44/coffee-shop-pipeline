import random

from datetime import timedelta


PAYMENT_METHODS = [
    "CREDIT_CARD",
    "DEBIT_CARD",
    "CASH",
    "DIGITAL_WALLET"
]

PAYMENT_WEIGHTS = [
    40,
    30,
    20,
    10
]

def generate_payments(orders, rng=None):
    if rng is None:
        rng = random

    payments = []
    
    payment_id = 1
    
    for order in orders:
        
        payment_method = rng.choices(
            PAYMENT_METHODS,
            weights=PAYMENT_WEIGHTS,
            k=1
        )[0]
        
        payment_delay = rng.randint(1, 10)
        
        paid_at = order['ordered_at'] + timedelta(
            minutes=payment_delay
        )
        
        payments.append({
            "payment_id": payment_id,
            "order_id": order['order_id'],
            "payment_method": payment_method,
            "amount": order['subtotal'],
            "status": "COMPLETED",
            "paid_at": paid_at
        })
        
        payment_id += 1
    
    return payments

select
    payment_id,
    order_id,
    payment_method,
    amount,
    status,
    paid_at,
    paid_at :: date as payment_date
from {{ ref('silver_payments') }}

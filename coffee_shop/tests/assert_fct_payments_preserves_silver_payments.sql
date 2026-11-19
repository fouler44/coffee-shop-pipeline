select
    s.payment_id as silver_payment_id,
    f.payment_id as fact_payment_id,
    s.amount as silver_amount,
    f.amount as fact_amount,
    s.paid_at as silver_paid_at,
    f.paid_at as fact_paid_at,
    cast(s.paid_at as date) as expected_payment_date,
    f.payment_date
from {{ ref('silver_payments') }} as s
full outer join {{ ref('fct_payments') }} as f
    on s.payment_id = f.payment_id
where s.payment_id is null
    or f.payment_id is null
    or s.order_id is distinct from f.order_id
    or s.payment_method is distinct from f.payment_method
    or s.amount is distinct from f.amount
    or s.status is distinct from f.status
    or s.paid_at is distinct from f.paid_at
    or cast(s.paid_at as date) is distinct from f.payment_date

select
    p.payment_id,
    p.order_id,
    p.amount,
    o.subtotal
from {{ ref('silver_payments') }} as p
left join {{ ref('silver_orders') }} as o
    on p.order_id = o.order_id
where
    o.order_id is null
    or p.amount is distinct from o.subtotal
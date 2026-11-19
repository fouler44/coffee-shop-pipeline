select
    f.order_item_id,
    f.order_id,
    o.customer_id
from {{ ref('fct_order_items') }} as f
inner join {{ ref('silver_orders') }} as o
    on f.order_id = o.order_id
where o.customer_id is not null
    and f.customer_sk is null

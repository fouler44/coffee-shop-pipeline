select
    s.order_item_id as silver_order_item_id,
    f.order_item_id as fact_order_item_id,
    s.order_id as silver_order_id,
    f.order_id as fact_order_id,
    s.quantity as silver_quantity,
    f.quantity as fact_quantity,
    s.unit_price as silver_unit_price,
    f.unit_price as fact_unit_price,
    s.line_total as silver_line_total,
    f.line_total as fact_line_total
from {{ ref('silver_order_items') }} as s
full outer join {{ ref('fct_order_items') }} as f
    on s.order_item_id = f.order_item_id
where s.order_item_id is null
    or f.order_item_id is null
    or s.order_id is distinct from f.order_id
    or s.quantity is distinct from f.quantity
    or s.unit_price is distinct from f.unit_price
    or s.line_total is distinct from f.line_total

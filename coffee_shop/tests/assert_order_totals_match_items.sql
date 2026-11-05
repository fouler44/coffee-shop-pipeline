with item_totals as (
    select
        order_id,
        sum(quantity) as total_units,
        sum(line_total) as calculated_subtotal
    from {{ ref('silver_order_items') }}
    group by order_id
)

select
    o.order_id,
    o.item_count,
    i.total_units,
    o.subtotal,
    i.calculated_subtotal
from {{ ref('silver_orders') }} as o
left join item_totals as i
    on o.order_id = i.order_id
where
    i.order_id is null
    or o.item_count is distinct from i.total_units
    or o.subtotal is distinct from i.calculated_subtotal
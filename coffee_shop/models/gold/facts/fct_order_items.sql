with order_items as (
    select *
    from {{ ref('silver_order_items') }}
),

dim_products as (
    select *
    from {{ ref('dim_products') }}
),

dim_customers as (
    select *
    from {{ ref('dim_customers') }}
),

orders as (
    select *
    from {{ ref('silver_orders') }}
),

final as (
    select
        oi.order_item_id,

        oi.order_id,

        -- Dimension Keys
        dc.customer_sk,
        dp.product_sk,

        -- Numeric Values
        oi.quantity,
        oi.unit_price,
        oi.line_total,

        -- Dates
        o.ordered_at :: date as order_date

    from order_items oi

    left join orders o
        on oi.order_id = o.order_id

    left join dim_customers dc
        on o.customer_id = dc.customer_id
        and o.ordered_at >= dc.dbt_valid_from
        and (o.ordered_at < dc.dbt_valid_to or dc.dbt_valid_to is null)

    left join dim_products dp
        on oi.product_id = dp.product_id
        and o.ordered_at >= dp.dbt_valid_from
        and (o.ordered_at < dp.dbt_valid_to or dp.dbt_valid_to is null)
)

select *
from final

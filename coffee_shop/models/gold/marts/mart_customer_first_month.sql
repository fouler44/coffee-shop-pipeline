with orders as (
    select *
    from {{ ref('silver_orders') }}
),

first_month_month as (
    select
        customer_id,
        cast(date_trunc('month', min(ordered_at)) as date) as first_order_date
    from orders
    where customer_id is not null
    group by customer_id
),

all_orders_month as (
    select
        o.customer_id,
        cast(date_trunc('month', o.ordered_at) as date) as order_month,
    from orders o
    where customer_id is not null
    group by customer_id, order_month
),

final as (
    select
        f.customer_id,
        a.order_month,
        f.first_order_date
    from all_orders_month a
    left join first_month_month f
    on a.customer_id = f.customer_id
)

select * 
from final

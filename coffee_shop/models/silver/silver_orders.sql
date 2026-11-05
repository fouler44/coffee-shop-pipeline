with orders as (
    select *
    from {{ source('bronze', 'orders') }}
),

clean as (
    select
        order_id :: int as order_id,
        customer_id :: int as customer_id,
        ordered_at :: timestamp as ordered_at,
        item_count :: int as item_count,
        subtotal :: decimal(12, 2) as subtotal,
        source_record_id,
        batch_id,
        delivered_at :: timestamp as delivered_at,
        _batch_id,
        _source_file,
        _source_row_number,
        _ingested_at
    from orders
),

ranked as (
    select
        *,
        row_number() over (
            partition by source_record_id
            order by 
                _ingested_at,
                _source_file,
                _source_row_number
        ) as duplicate_rank
    from clean
),

deduplicated as (
    select * exclude (duplicate_rank)
    from ranked
    where duplicate_rank = 1
)

select *
from deduplicated
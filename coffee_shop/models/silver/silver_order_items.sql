with order_items as (
    select *
    from {{ source('bronze', 'order_items') }}
),

clean as (
    select
        order_item_id :: int as order_item_id,
        order_id :: int as order_id,
        product_id :: int as product_id,
        case
            when quantity::int < 0
                and unit_price::decimal(12, 2) > 0
                and line_total::decimal(12, 2)
                = -quantity::int * unit_price::decimal(12, 2)
            then -quantity::int
            else quantity::int
        end as quantity,
        case
            when quantity::int < 0
                and unit_price::decimal(12, 2) > 0
                and line_total::decimal(12, 2)
                = -quantity::int * unit_price::decimal(12, 2)
            then true
            else false
        end as quantity_was_corrected,
        unit_price :: decimal(12, 2) as unit_price,
        line_total :: decimal(12, 2) as line_total,
        source_record_id,
        batch_id,
        delivered_at :: timestamp as delivered_at,
        _batch_id,
        _source_file,
        _source_row_number,
        _ingested_at
    from order_items
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
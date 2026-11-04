with payments as (
    select *
    from {{ source('bronze', 'payments') }}
),

clean as (
    select
        payment_id :: int as payment_id,
        order_id :: int as order_id,
        trim(upper(payment_method)) as payment_method,
        amount :: decimal(12, 2) as amount,
        status,
        paid_at :: timestamp as paid_at,
        source_record_id,
        batch_id,
        delivered_at :: timestamp as delivered_at,
        _batch_id,
        _source_file,
        _source_row_number,
        _ingested_at
    from payments
),

ranked as(
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
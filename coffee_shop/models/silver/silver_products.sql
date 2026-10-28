with products as (
    select *
    from {{ source('bronze', 'products') }}
),

clean as (
    select
        product_id :: int as product_id,
        trim(sku) as sku,
        trim(name) as name,
        {{ init_cap('lower(trim(category))') }} as category,
        size,
        price :: decimal(12, 2) as price,
        active :: boolean as active,
        source_updated_at :: timestamp as source_updated_at,
        source_record_id,
        batch_id,
        delivered_at :: timestamp as delivered_at,
        _batch_id,
        _source_file,
        _source_row_number,
        _ingested_at
    from products
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
with customers as (
    select * 
    from {{ source('bronze', 'customers') }}
),

clean as (
    select
        customer_id :: int as customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(trim(email)) as email,
        coalesce(
            regexp_full_match(
                lower(trim(email)),
                '[^@\s]+@[^@\s]+\.[^@\s]+'
            ),
            false
        ) as email_is_valid,
        phone,
        regexp_replace(
            trim(phone),
            '[[:space:]().-]',
            '',
            'g'
        ) as phone_normalized,
        birth_date :: date as birth_date,
        registered_at :: date as registered_at,
        marketing_opt_in :: boolean as marketing_opt_in,
        marketing_opt_in is null as marketing_opt_in_is_missing,
        source_updated_at :: timestamp as source_updated_at,
        source_record_id,
        batch_id,
        delivered_at :: timestamp as delivered_at,
        _batch_id,
        _source_file,
        _source_row_number,
        _ingested_at
    from customers
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
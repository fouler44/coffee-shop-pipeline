with customers as (
    select * from {{ ref('customers_snapshot')}}
),

final as (
    select
        -- Surroagate Key
        {{ dbt_utils.generate_surrogate_key(['source_record_id']) }} as customer_sk,

        -- Descriptive Values
        customer_id,
        first_name,
        last_name,
        email,
        email_is_valid,
        phone,
        phone_normalized,
        birth_date,
        registered_at,
        marketing_opt_in,
        marketing_opt_in_is_missing,

        -- Metadata
        source_record_id,

        -- DW Values
        dbt_valid_from,
        dbt_valid_to,

    from customers
)

select *
from final
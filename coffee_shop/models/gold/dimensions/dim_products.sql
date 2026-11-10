with products as (
    select * from {{ ref('products_snapshot')}}
),

final as (
    select
        -- Surroagate Key
        {{ dbt_utils.generate_surrogate_key(['source_record_id']) }} as product_sk,

        -- Descriptive Values
        product_id,
        sku,
        name,
        category,
        size,
        price,
        active,

        -- Metadata
        source_record_id,

        -- DW Values
        dbt_valid_from,
        dbt_valid_to,

        from
            products
)

select *
from final
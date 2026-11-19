with days as (

    {{ 
        dbt.date_spine(
            'day',
            "make_date(2025, 1, 1)",
            "make_date(2026, 1, 1)"
        ) 
    }}
),

final as (
    select
        date_day :: date as date_day,
        year(date_day) as calendar_year,
        quarter(date_day) as calendar_quarter,
        month(date_day) as month_number,
        cast(date_trunc('month', date_day) as date) as month_start_date,
        isodow(date_day) as iso_day_of_week,
        isodow(date_day) in (6, 7) as is_weekend

    from days
)

select *
from final
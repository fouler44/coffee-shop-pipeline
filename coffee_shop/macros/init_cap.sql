{% macro init_cap(expression) %}
    list_reduce(
        list_transform(
            regexp_split_to_array({{ expression }}, '\s+'),
            w -> upper(w[1]) || w[2:]
        ),
        (x, y) -> x || ' ' || y
    )
{% endmacro %}
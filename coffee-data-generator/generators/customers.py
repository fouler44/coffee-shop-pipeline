from datetime import date, timedelta

from faker import Faker


def years_before(reference_date, years):
    try:
        return reference_date.replace(year=reference_date.year - years)
    except ValueError:
        return reference_date.replace(
            year=reference_date.year - years,
            day=28,
        )


def generate_customers(
    num_customers=2000,
    seed=None,
    reference_date=None,
    registered_start_date=None,
    registered_end_date=None,
):
    if reference_date is None:
        reference_date = date.today()

    if registered_start_date is None:
        registered_start_date = years_before(reference_date, 2)

    if registered_end_date is None:
        registered_end_date = reference_date

    fake = Faker("es_MX")

    if seed is not None:
        fake.seed_instance(seed)

    customers = []

    for customer_id in range(1, num_customers + 1):
        customers.append({
            "customer_id": customer_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "birth_date": fake.date_between_dates(
                date_start=(
                    years_before(reference_date, 71)
                    + timedelta(days=1)
                ),
                date_end=years_before(reference_date, 18),
            ),
            "registered_at": fake.date_between(
                start_date=registered_start_date,
                end_date=registered_end_date,
            ),
        })

    return customers

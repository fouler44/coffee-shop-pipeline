import argparse
from pathlib import Path

from batches import Config, build_dataset, export_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate six monthly coffee-shop batches")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data" / "coffee_2025_csv")
    for name, value in Config().__dict__.items():
        if name.endswith("_rate"):
            parser.add_argument("--" + name.replace("_", "-"), type=float, default=value)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new --output directory")
    options = vars(args).copy()
    output = options.pop("output")
    options["customer_count"] = options.pop("customers")
    config = Config(**options)
    try:
        config.validate()
    except ValueError as error:
        parser.error(str(error))
    dataset = build_dataset(config)
    export_dataset(dataset, output)
    for batch in dataset["batches"]:
        print(f"{batch['batch_id']}: {len(batch['reference']['orders'])} orders, "
              f"delivery {batch['delivered_at'].date()}")
    print(f"Business changes: {len(dataset['changes'])}")
    print(f"Injected issues (including delayed payments): {len(dataset['issues'])}")
    print(f"Saved to: {output.resolve()}")


if __name__ == "__main__":
    main()

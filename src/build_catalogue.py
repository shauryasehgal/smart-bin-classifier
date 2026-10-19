
import json
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(r"C:\Users\ADMIN\Downloads\archive\metadata.db")
ASIN_PATH = Path("data/selected_catalogue_asins.csv")
OUTPUT_PATH = Path("catalogue.csv")


def format_measure(value):
    """Convert a measurement dictionary into readable text."""
    if isinstance(value, dict):
        number = value.get("value")
        unit = value.get("unit", "")

        if number is not None:
            try:
                number = f"{float(number):.2f}".rstrip("0").rstrip(".")
            except (ValueError, TypeError):
                pass

            return f"{number} {unit}".strip()

    return ""


if not DB_PATH.exists():
    raise FileNotFoundError(f"Metadata database not found: {DB_PATH}")

# Load the five catalogue ASINs and their selected-bin frequencies
asin_df = pd.read_csv(ASIN_PATH)
target_asins = set(asin_df["asin"])

products = {}

# Open the database in read-only mode
connection = sqlite3.connect(
    f"file:{DB_PATH.as_posix()}?mode=ro",
    uri=True
)

try:
    cursor = connection.execute(
        "SELECT metadata FROM metadata"
    )

    for (metadata_text,) in cursor:
        try:
            metadata = json.loads(metadata_text)
        except (json.JSONDecodeError, TypeError):
            continue

        bin_products = metadata.get("BIN_FCSKU_DATA", {})
        if not isinstance(bin_products, dict):
            continue

        for asin, product in bin_products.items():
            if asin not in target_asins or asin in products:
                continue

            if not isinstance(product, dict):
                continue

            products[asin] = {
                "asin": asin,
                "product_name": product.get("name", ""),
                "height": format_measure(product.get("height")),
                "length": format_measure(product.get("length")),
                "width": format_measure(product.get("width")),
                "weight": format_measure(product.get("weight")),
            }

        if target_asins.issubset(products.keys()):
            break
finally:
    connection.close()

# Ensure every selected catalogue ASIN has a metadata record
missing = target_asins - set(products)

if missing:
    raise ValueError(
        f"Could not find product metadata for ASINs: {sorted(missing)}"
    )

# Add the observed frequency in the selected 2,000 bins
catalogue = pd.DataFrame(
    products[asin] for asin in sorted(target_asins)
)

catalogue = catalogue.merge(
    asin_df,
    on="asin",
    how="left",
    validate="one_to_one"
)

catalogue.to_csv(OUTPUT_PATH, index=False)

print(f"Catalogue saved to: {OUTPUT_PATH.resolve()}")
print(f"Number of catalogue products: {len(catalogue)}")
print("\nCatalogue preview:")
print(catalogue.to_string(index=False))

# Basic correctness checks
assert catalogue["asin"].is_unique
assert len(catalogue) == 5
assert (catalogue["selected_bin_frequency"] >= 100).all()

print("\nAll catalogue checks passed.")

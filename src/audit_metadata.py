
import sqlite3
import json
from pathlib import Path
from collections import Counter

# Update this path only if your database moves.
DB_PATH = Path(
    r"C:\Users\ADMIN\Downloads\archive\metadata.db"
)

connection = sqlite3.connect(
    DB_PATH.as_uri() + "?mode=ro",
    uri=True
)

cursor = connection.cursor()

total_records = 0
valid_expected = 0
zero_expected = 0
invalid_expected = 0
matching_quantities = 0
mismatching_quantities = 0
empty_product_data = 0
missing_product_data = 0

expected_counts = Counter()
asin_counts = Counter()
filename_counts = Counter()

cursor.execute("SELECT name, metadata FROM metadata")

for filename, metadata_text in cursor:
    total_records += 1
    filename_counts[filename] += 1

    try:
        metadata = json.loads(metadata_text)
    except (json.JSONDecodeError, TypeError):
        invalid_expected += 1
        continue

    expected = metadata.get("EXPECTED_QUANTITY")

    if isinstance(expected, int) and not isinstance(expected, bool):
        expected_counts[expected] += 1

        if expected == 0:
            zero_expected += 1
        elif 1 <= expected <= 5:
            valid_expected += 1
        else:
            invalid_expected += 1
    else:
        invalid_expected += 1

    products = metadata.get("BIN_FCSKU_DATA")

    if not isinstance(products, dict):
        missing_product_data += 1
        continue

    if not products:
        empty_product_data += 1
        continue

    product_quantity_sum = 0
    quantities_valid = True

    for asin, product in products.items():
        asin_counts[asin] += 1

        quantity = product.get("quantity")

        if (
            isinstance(quantity, int)
            and not isinstance(quantity, bool)
            and quantity >= 0
        ):
            product_quantity_sum += quantity
        else:
            quantities_valid = False

    if quantities_valid and isinstance(expected, int):
        if product_quantity_sum == expected:
            matching_quantities += 1
        else:
            mismatching_quantities += 1

print("\n===== METADATA AUDIT =====")
print("Total records:", total_records)
print("Expected quantity 1-5:", valid_expected)
print("Expected quantity 0:", zero_expected)
print("Expected quantity outside 0-5 or invalid:", invalid_expected)
print("Empty product dictionaries:", empty_product_data)
print("Missing/invalid product dictionaries:", missing_product_data)
print("Product quantity sum matches expected:", matching_quantities)
print("Product quantity sum mismatches expected:", mismatching_quantities)
print("Unique ASINs:", len(asin_counts))
print("Duplicate filename records:", sum(
    count - 1 for count in filename_counts.values() if count > 1
))

print("\nExpected quantity distribution:")
for quantity, count in sorted(expected_counts.items()):
    print(f"  {quantity}: {count}")

print("\nMost frequent ASINs (record frequency):")
for asin, count in asin_counts.most_common(10):
    print(f"  {asin}: {count}")

connection.close()


import sqlite3
import json
import csv
from pathlib import Path
from collections import Counter

DB_PATH = Path(r"C:\Users\ADMIN\Downloads\archive\metadata.db")
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

connection = sqlite3.connect(
    DB_PATH.as_uri() + "?mode=ro",
    uri=True
)
cursor = connection.cursor()
cursor.execute("SELECT name, metadata FROM metadata")

candidates = []
asin_counts = Counter()
rejected_quantity = 0
rejected_metadata = 0
rejected_mismatch = 0

for filename, raw_metadata in cursor:
    try:
        metadata = json.loads(raw_metadata)
        expected = metadata.get("EXPECTED_QUANTITY")
        products = metadata.get("BIN_FCSKU_DATA")

        if (
            not isinstance(expected, int)
            or isinstance(expected, bool)
            or not 1 <= expected <= 5
            or not isinstance(products, dict)
            or not products
        ):
            rejected_quantity += 1
            continue

        quantities = []
        product_names = {}

        for asin, product in products.items():
            quantity = product.get("quantity")

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity < 0
            ):
                raise ValueError("Invalid product quantity")

            quantities.append(quantity)
            product_names[asin] = product.get("name", "")

        if sum(quantities) != expected:
            rejected_mismatch += 1
            continue

        asins = list(products.keys())

        candidates.append({
            "filename": filename,
            "expected_quantity": expected,
            "asins": asins,
            "product_names": product_names
        })

        # Count how many eligible bins contain each ASIN.
        asin_counts.update(set(asins))

    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        rejected_metadata += 1

connection.close()

# Save the candidate records for the next selection stage.
with open(OUTPUT_DIR / "candidate_pool.csv", "w",
          newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f, fieldnames=["filename", "expected_quantity", "asins"]
    )
    writer.writeheader()

    for row in candidates:
        writer.writerow({
            "filename": row["filename"],
            "expected_quantity": row["expected_quantity"],
            "asins": json.dumps(row["asins"])
        })

# Save ASIN frequencies within the eligible candidate pool.
asin_names = {}

for row in candidates:
    asin_names.update(row["product_names"])

with open(OUTPUT_DIR / "asin_frequency.csv", "w",
          newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["asin", "product_name", "candidate_bin_frequency"])

    for asin, count in asin_counts.most_common():
        writer.writerow([asin, asin_names.get(asin, ""), count])

print("\n===== CANDIDATE POOL =====")
print("Eligible bins:", len(candidates))
print("Rejected by quantity/empty product data:", rejected_quantity)
print("Rejected due to quantity mismatch:", rejected_mismatch)
print("Rejected due to invalid metadata:", rejected_metadata)
print("Unique ASINs in eligible bins:", len(asin_counts))

print("\nTop 20 ASINs in eligible bins:")
for asin, count in asin_counts.most_common(20):
    print(f"{asin}: {count} bins | {asin_names.get(asin, '')[:70]}")

print("\nSaved:")
print(OUTPUT_DIR / "candidate_pool.csv")
print(OUTPUT_DIR / "asin_frequency.csv")

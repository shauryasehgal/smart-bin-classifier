
import json
import pandas as pd
from pathlib import Path
import ast

SPLIT_DIR = Path("data/splits")
CATALOGUE_PATH = Path("catalogue.csv")

catalogue = pd.read_csv(CATALOGUE_PATH)
split_names = ["train", "validation", "test", "blind"]

results = []

for split_name in split_names:
    split_path = SPLIT_DIR / f"{split_name}.csv"
    df = pd.read_csv(split_path)

    # Each row's "asins" field contains the products in that bin.
    df["asins"] = df["asins"].apply(ast.literal_eval)

    row = {"split": split_name, "total_bins": len(df)}

    for asin in catalogue["asin"]:
        count = df["asins"].apply(
            lambda products: asin in products
        ).sum()
        row[asin] = int(count)

    results.append(row)

distribution = pd.DataFrame(results)

print("\nProduct presence by split (number of bins):")
print(distribution.to_string(index=False))

print("\nProduct presence percentages:")
for _, row in distribution.iterrows():
    print(f"\n{row['split']} ({row['total_bins']} bins)")
    for asin in catalogue["asin"]:
        percentage = row[asin] / row["total_bins"] * 100
        print(f"  {asin}: {row[asin]} bins ({percentage:.1f}%)")

OUTPUT_PATH = SPLIT_DIR / "product_distribution.csv"
distribution.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved distribution report to: {OUTPUT_PATH}")

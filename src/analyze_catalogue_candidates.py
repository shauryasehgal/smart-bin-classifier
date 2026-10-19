
import csv
import json
from collections import Counter
from pathlib import Path

candidate_file = Path("data/candidate_pool.csv")

rows = []
asin_frequency = Counter()

with open(candidate_file, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        asins = json.loads(row["asins"])
        rows.append({
            "filename": row["filename"],
            "asins": set(asins)
        })
        asin_frequency.update(set(asins))

print("===== CATALOGUE CANDIDATE ANALYSIS =====")
print("Eligible bins:", len(rows))
print("Unique ASINs:", len(asin_frequency))

for threshold in [25, 50, 100, 150, 200]:
    count = sum(
        1 for frequency in asin_frequency.values()
        if frequency >= threshold
    )
    print(f"ASINs appearing in at least {threshold} bins: {count}")

frequent_asins = {
    asin for asin, frequency in asin_frequency.items()
    if frequency >= 100
}

bins_with_frequent_products = sum(
    bool(row["asins"] & frequent_asins)
    for row in rows
)

print(
    "\nBins containing at least one ASIN appearing in 100+ "
    "candidate bins:",
    bins_with_frequent_products
)

print("\nTop 50 ASINs:")
for asin, count in asin_frequency.most_common(50):
    print(f"{asin}: {count} bins")

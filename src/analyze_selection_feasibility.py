
import json
import pandas as pd
from collections import Counter

# Load the eligible candidate pool
df = pd.read_csv("data/candidate_pool.csv")

# Convert the ASIN column from JSON text to Python lists
df["asins"] = df["asins"].apply(json.loads)

# Count how many eligible bins contain each ASIN
asin_frequency = Counter(
    asin
    for asin_list in df["asins"]
    for asin in set(asin_list)
)

# Products appearing in at least 100 eligible bins
frequent_asins = {
    asin
    for asin, count in asin_frequency.items()
    if count >= 100
}

# Count bins where every product belongs to this frequent-ASIN set
fully_supported = df[
    df["asins"].apply(
        lambda asins: bool(asins)
        and set(asins).issubset(frequent_asins)
    )
]

print("===== SELECTION FEASIBILITY =====")
print(f"Eligible bins: {len(df):,}")
print(f"Unique ASINs: {len(asin_frequency):,}")
print(f"ASINs appearing in 100+ eligible bins: {len(frequent_asins):,}")
print(
    "Bins containing only these frequent ASINs:",
    f"{len(fully_supported):,}"
)

print("\nTop 15 ASINs by bin frequency:")
for asin, count in asin_frequency.most_common(15):
    print(f"{asin}: {count} bins")

print("\nBins needed: 2,000")
print(
    "Enough fully supported bins:",
    len(fully_supported) >= 2000
)



import json
from collections import Counter
from pathlib import Path

import pandas as pd

SEED = 42
TARGET_BINS = 2000

# Load the eligible candidate pool
df = pd.read_csv("data/candidate_pool.csv")
df["asins"] = df["asins"].apply(json.loads)

# Count each ASIN at most once per bin
asin_frequency = Counter(
    asin
    for asins in df["asins"]
    for asin in set(asins)
)

# Select the five most frequent ASINs
core_asins = [
    asin for asin, _ in asin_frequency.most_common(5)
]
core_asin_set = set(core_asins)

print("Core ASINs:", core_asins)

# Keep every eligible bin containing at least one core ASIN
core_mask = df["asins"].apply(
    lambda asins: bool(set(asins) & core_asin_set)
)
core_bins = df[core_mask].copy()
other_bins = df[~core_mask].copy()

print(f"Bins containing core ASINs: {len(core_bins):,}")

# Check that the core bins leave enough room for 2,000 bins
if len(core_bins) > TARGET_BINS:
    raise ValueError(
        "Core bins exceed 2,000. We need a different selection strategy."
    )

# Fill the remaining places reproducibly
remaining_count = TARGET_BINS - len(core_bins)

fill_bins = other_bins.sample(
    n=remaining_count,
    random_state=SEED
)

# Combine and shuffle deterministically
selected = pd.concat(
    [core_bins, fill_bins],
    ignore_index=True
).sample(frac=1, random_state=SEED).reset_index(drop=True)

# Verify the selected subset
assert len(selected) == TARGET_BINS
assert selected["filename"].nunique() == TARGET_BINS

selected_frequency = Counter(
    asin
    for asins in selected["asins"]
    for asin in set(asins)
)

# Catalogue includes only ASINs appearing in at least 100 selected bins
catalogue_rows = sorted(
    [
        {
            "asin": asin,
            "selected_bin_frequency": count
        }
        for asin, count in selected_frequency.items()
        if count >= 100
    ],
    key=lambda row: (-row["selected_bin_frequency"], row["asin"])
)

# Save the selection and catalogue ASIN list locally
Path("data").mkdir(exist_ok=True)

selected.to_csv("data/selected_bins.csv", index=False)
pd.DataFrame(catalogue_rows).to_csv(
    "data/selected_catalogue_asins.csv",
    index=False
)

print("\n===== SELECTION RESULTS =====")
print(f"Selected bins: {len(selected):,}")
print(f"Unique filenames: {selected['filename'].nunique():,}")
print(f"Catalogue ASINs (100+ selected bins): {len(catalogue_rows)}")

print("\nCatalogue ASIN frequencies:")
for row in catalogue_rows:
    print(f"{row['asin']}: {row['selected_bin_frequency']} bins")

print("\nSaved:")
print("data/selected_bins.csv")
print("data/selected_catalogue_asins.csv")

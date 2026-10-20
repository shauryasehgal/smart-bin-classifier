
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Paths
INPUT_PATH = Path("data/selected_bins.csv")
OUTPUT_DIR = Path("data/splits")

# Reproducibility
RANDOM_SEED = 42

# Check input exists
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Could not find {INPUT_PATH}. Run src/select_bins.py first."
    )

# Load the fixed selection
df = pd.read_csv(INPUT_PATH)

# Validate the selection
assert len(df) == 2000, f"Expected 2000 bins, found {len(df)}"
assert df["filename"].is_unique, "Duplicate bin filenames found"

# 70% training, 30% remaining
train_df, remaining_df = train_test_split(
    df,
    test_size=0.30,
    random_state=RANDOM_SEED,
    shuffle=True,
)

# Divide the remaining 30% equally:
# 10% validation, 10% test, 10% blind
validation_df, remaining_df = train_test_split(
    remaining_df,
    test_size=2 / 3,
    random_state=RANDOM_SEED,
    shuffle=True,
)

test_df, blind_df = train_test_split(
    remaining_df,
    test_size=0.50,
    random_state=RANDOM_SEED,
    shuffle=True,
)

splits = {
    "train": train_df,
    "validation": validation_df,
    "test": test_df,
    "blind": blind_df,
}

# Check sizes and ensure no overlap
expected_sizes = {
    "train": 1400,
    "validation": 200,
    "test": 200,
    "blind": 200,
}

for name, split_df in splits.items():
    assert len(split_df) == expected_sizes[name], (
        f"{name}: expected {expected_sizes[name]}, got {len(split_df)}"
    )
    assert split_df["filename"].is_unique, (
        f"Duplicate filenames within {name}"
    )

filename_sets = {
    name: set(split_df["filename"])
    for name, split_df in splits.items()
}

names = list(filename_sets)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        overlap = filename_sets[names[i]] & filename_sets[names[j]]
        assert not overlap, (
            f"Leakage between {names[i]} and {names[j]}: {len(overlap)} bins"
        )

# Save split manifests. These stay under the ignored data/ directory.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, split_df in splits.items():
    output_path = OUTPUT_DIR / f"{name}.csv"
    split_df.to_csv(output_path, index=False)
    print(f"{name:10s}: {len(split_df):4d} bins -> {output_path}")

print("\nAll split checks passed.")
print("Total bins:", sum(len(split_df) for split_df in splits.values()))
print("Random seed:", RANDOM_SEED)

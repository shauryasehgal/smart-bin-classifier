import pandas as pd
from pathlib import Path

folder = Path("data/processed")

for split in ["train", "validation", "test"]:
    file = folder / f"{split}_labels.csv"

    print(f"\n--- {split.upper()} ---")

    if not file.exists():
        print(f"ERROR: File not found: {file}")
        continue

    df = pd.read_csv(file)

    print("Label rows:", len(df))
    print("Columns:", list(df.columns))
    print("Missing values:", int(df.isna().sum().sum()))
    print(df.head(2).to_string(index=False))
import pandas as pd
from pathlib import Path

root = Path("data/processed")
products = [
    "B00O4OR4GQ",
    "B013UJS35G",
    "B0159A0LH2",
    "B019D9HESO",
    "B01B1GE6KG",
]

errors = []

for split in ["train", "validation", "test"]:
    image_dir = root / split
    labels = pd.read_csv(root / f"{split}_labels.csv")

    image_names = {p.name for p in image_dir.glob("*.jpg")}
    label_names = labels["filename"].astype(str)

    missing_images = set(label_names) - image_names
    missing_labels = image_names - set(label_names)

    quantity_data = labels[
        [f"qty_{asin}" for asin in products]
    ]

    invalid_quantities = (
        (quantity_data < 0) |
        (quantity_data % 1 != 0)
    ).any().any()

    duplicate_labels = label_names.duplicated().sum()

    print(f"\n--- {split.upper()} ---")
    print("Images:", len(image_names))
    print("Label rows:", len(labels))
    print("Labels without images:", len(missing_images))
    print("Images without labels:", len(missing_labels))
    print("Duplicate label filenames:", duplicate_labels)
    print("Invalid quantities:", invalid_quantities)

    if missing_images or missing_labels or duplicate_labels or invalid_quantities:
        errors.append(split)

print("\nFINAL RESULT:", "CHECK FAILED" if errors else "CHECKS PASSED")
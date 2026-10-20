
import ast
import json
import shutil
import sqlite3
from pathlib import Path

import pandas as pd

# Update these paths only if your dataset is stored elsewhere.
DB_PATH = Path(r"D:\smart bin dataset\metadata.db")
IMAGE_DIR = Path(r"D:\smart bin dataset\images")

SPLIT_DIR = Path("data/splits")
OUTPUT_DIR = Path("data/processed")

CATALOGUE_PATH = Path("catalogue.csv")
CATALOGUE_ASINS = pd.read_csv(CATALOGUE_PATH)["asin"].astype(str).tolist()

SPLITS = ["train", "validation", "test", "blind"]


def read_metadata(connection, filename):
    """Retrieve metadata for one bin image."""
    row = connection.execute(
        "SELECT metadata FROM metadata WHERE name = ?",
        (filename,),
    ).fetchone()

    if row is None:
        raise ValueError(f"No metadata found for image: {filename}")

    metadata = json.loads(row[0])
    return metadata


def get_product_quantities(metadata):
    """Return quantities for the selected catalogue ASINs."""
    product_data = metadata.get("BIN_FCSKU_DATA", {})

    if not isinstance(product_data, dict):
        product_data = {}

    quantities = {}

    for asin in CATALOGUE_ASINS:
        product = product_data.get(asin, {})
        quantity = product.get("quantity", 0) if isinstance(product, dict) else 0

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 0

        quantities[f"qty_{asin}"] = quantity

    return quantities


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

    if not CATALOGUE_PATH.exists():
        raise FileNotFoundError(f"Catalogue not found: {CATALOGUE_PATH}")

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )

    try:
        all_filenames = set()

        # Check split manifests before copying any images.
        for split_name in SPLITS:
            manifest_path = SPLIT_DIR / f"{split_name}.csv"

            if not manifest_path.exists():
                raise FileNotFoundError(
                    f"Missing split manifest: {manifest_path}"
                )

            df = pd.read_csv(manifest_path)

            if "filename" not in df.columns:
                raise ValueError(
                    f"'filename' column missing from {manifest_path}"
                )

            if df["filename"].duplicated().any():
                raise ValueError(
                    f"Duplicate filenames in {manifest_path}"
                )

            overlap = all_filenames.intersection(df["filename"])
            if overlap:
                raise ValueError(
                    f"Bin leakage detected in {split_name}: {len(overlap)}"
                )

            all_filenames.update(df["filename"])

        if len(all_filenames) != 2000:
            raise ValueError(
                f"Expected 2000 unique bins, found {len(all_filenames)}"
            )

        print("Split manifests verified: 2000 unique bins, no overlap.")

        # Prepare each split.
        for split_name in SPLITS:
            manifest_path = SPLIT_DIR / f"{split_name}.csv"
            df = pd.read_csv(manifest_path)

            image_output_dir = OUTPUT_DIR / split_name
            image_output_dir.mkdir(parents=True, exist_ok=True)

            labels = []

            for _, row in df.iterrows():
                filename = str(row["filename"])
                source_image = IMAGE_DIR / filename
                destination_image = image_output_dir / filename

                if not source_image.is_file():
                    raise FileNotFoundError(
                        f"Image missing: {source_image}"
                    )

                if not destination_image.exists():
                    shutil.copy2(source_image, destination_image)

                # Blind split: copy photos only, do not export labels.
                if split_name != "blind":
                    metadata = read_metadata(connection, filename)
                    quantities = get_product_quantities(metadata)

                    label_row = {
                        "filename": filename,
                        **quantities,
                    }
                    labels.append(label_row)

            if split_name != "blind":
                labels_path = OUTPUT_DIR / f"{split_name}_labels.csv"
                pd.DataFrame(labels).to_csv(labels_path, index=False)
                print(
                    f"{split_name}: {len(df)} images; "
                    f"labels saved to {labels_path}"
                )
            else:
                print(
                    f"{split_name}: {len(df)} images; "
                    "no label file created."
                )

        print("\nDataset preparation completed.")
        print(f"Images and labels are under: {OUTPUT_DIR.resolve()}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()

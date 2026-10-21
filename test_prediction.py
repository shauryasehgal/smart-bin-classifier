
from pathlib import Path

import pandas as pd

from src.predict import load_models, predict_image, PRODUCTS

project_root = Path(__file__).resolve().parent

# Use a training image for this initial test.
image_dir = project_root / "data" / "processed" / "train"
image_path = next(image_dir.glob("*.jpg"))

print("Testing image:", image_path.name)

presence_model, feature_extractor, quantity_models = load_models()

result = predict_image(
    image_path,
    presence_model,
    feature_extractor,
    quantity_models,
)

catalogue = pd.read_csv(project_root / "catalogue.csv")
product_names = catalogue.set_index("asin")["product_name"]

print("\nPredictions:")
for asin in PRODUCTS:
    print(
        f"{product_names[asin]}: "
        f"quantity={result['quantities'][asin]}, "
        f"presence_probability={result['probabilities'][asin]:.3f}"
    )

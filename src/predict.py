
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "models"
CATALOGUE_PATH = PROJECT_ROOT / "catalogue.csv"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

catalogue = pd.read_csv(CATALOGUE_PATH)
PRODUCTS = catalogue["asin"].astype(str).tolist()

IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


@torch.inference_mode()
def load_models():
    # Load the fine-tuned ResNet-18 presence model.
    presence_model = models.resnet18(weights=None)
    presence_model.fc = torch.nn.Linear(
        presence_model.fc.in_features,
        len(PRODUCTS),
    )

    checkpoint = torch.load(
        MODEL_DIR / "resnet18_finetuned_best.pth",
        map_location=DEVICE,
        weights_only=True,
    )
    presence_model.load_state_dict(checkpoint)
    presence_model = presence_model.to(DEVICE)
    presence_model.eval()

    # Reuse the ResNet-18 feature extractor for quantity prediction.
    feature_extractor = models.resnet18(weights=None)
    feature_extractor.fc = torch.nn.Linear(
        feature_extractor.fc.in_features,
        len(PRODUCTS),
    )
    feature_extractor.load_state_dict(checkpoint)
    feature_extractor.fc = torch.nn.Identity()
    feature_extractor = feature_extractor.to(DEVICE)
    feature_extractor.eval()

    quantity_models = joblib.load(
        MODEL_DIR / "positive_quantity_models.joblib"
    )

    return presence_model, feature_extractor, quantity_models


@torch.inference_mode()
def predict_image(image, presence_model, feature_extractor, quantity_models):
    if isinstance(image, (str, Path)):
        image = Image.open(image)

    image = image.convert("RGB")
    image_tensor = IMAGE_TRANSFORM(image).unsqueeze(0).to(DEVICE)

    # Predict whether each catalogue product is present.
    logits = presence_model(image_tensor)
    probabilities = torch.sigmoid(logits).cpu().numpy()[0]
    present = probabilities >= 0.5

    # Extract features for quantity prediction.
    features = (
        feature_extractor(image_tensor)
        .cpu()
        .numpy()
    )

    predicted_quantities = {}

    for index, asin in enumerate(PRODUCTS):
        if not present[index]:
            predicted_quantities[asin] = 0
            continue

        quantity_model = quantity_models[asin]
        quantity = quantity_model.predict(features)[0]

        predicted_quantities[asin] = max(1, int(round(quantity)))

    return {
        "quantities": predicted_quantities,
        "probabilities": {
            asin: float(probabilities[index])
            for index, asin in enumerate(PRODUCTS)
        },
    }

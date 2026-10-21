
from pathlib import Path
import time

import pandas as pd
import streamlit as st
from PIL import Image

from src.predict import load_models, predict_image, PRODUCTS
from src.order_validation import validate_order
from src.validation_logger import log_validation


PROJECT_ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Smart Bin Classifier",
    layout="wide",
)

st.title("Smart Bin Classifier")
st.write(
    "Select a bin image, enter an order, and check whether "
    "the detected quantities match the requested quantities."
)


train_dir = PROJECT_ROOT / "data" / "processed" / "train"
validation_dir = PROJECT_ROOT / "data" / "processed" / "validation"
blind_dir = PROJECT_ROOT / "data" / "processed" / "blind"

train_validation_available = (
    train_dir.is_dir()
    and validation_dir.is_dir()
    and (PROJECT_ROOT / "data" / "processed" / "train_labels.csv").is_file()
    and (PROJECT_ROOT / "data" / "processed" / "validation_labels.csv").is_file()
)

blind_available = (
    blind_dir.is_dir()
    and any(
        path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        for path in blind_dir.iterdir()
    )
)

available_modes = ["Image upload demo"]

if train_validation_available:
    available_modes.append("Train/validation demo")

if blind_available:
    available_modes.append("Blind evaluation")

mode = st.radio(
    "Choose validation mode",
    available_modes,
    horizontal=True,
)


catalogue = pd.read_csv(PROJECT_ROOT / "catalogue.csv")
product_names = catalogue.set_index("asin")["product_name"].to_dict()


@st.cache_resource
def get_models():
    return load_models()


with st.spinner("Loading trained models..."):
    presence_model, feature_extractor, quantity_models = get_models()

st.success("Models loaded successfully.")

# --------------------------------------------------
# 1. Enter the order first
# --------------------------------------------------
st.subheader("1. Enter the order")
st.caption(
    "Set the requested quantity for each product. "
    "Leave products not ordered at zero."
)

ordered_quantities = {}
cols = st.columns(2)

for index, asin in enumerate(PRODUCTS):
    with cols[index % 2]:
        ordered_quantities[asin] = st.number_input(
            product_names[asin],
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key=f"order_{asin}",
        )

active_order = {
    asin: int(qty)
    for asin, qty in ordered_quantities.items()
    if qty > 0
}

# --------------------------------------------------
# 2. Select an image
# --------------------------------------------------
st.subheader("2. Select a bin image")

image = None
image_id = None

if mode == "Image upload demo":
    uploaded_file = st.file_uploader(
        "Choose a bin image",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        image_id = uploaded_file.name
        st.image(image, caption=image_id, width=400)

elif mode == "Train/validation demo":
    split = st.selectbox(
        "Choose the dataset split",
        ["train", "validation"],
    )

    labels_path = PROJECT_ROOT / "data" / "processed" / f"{split}_labels.csv"
    image_dir = PROJECT_ROOT / "data" / "processed" / split

    if not labels_path.exists() or not image_dir.exists():
        st.error(f"Could not find the processed {split} data or labels.")
    elif not active_order:
        st.info("Enter at least one non-zero order quantity above.")
    else:
        labels = pd.read_csv(labels_path)

        # Find images whose label quantities match every ordered item.
        matching = labels.copy()

        for asin, requested_qty in active_order.items():
            column = f"qty_{asin}"

            if column not in matching.columns:
                st.error(f"Missing label column: {column}")
                matching = matching.iloc[0:0]
                break

            matching = matching[
                pd.to_numeric(matching[column], errors="coerce")
                == requested_qty
            ]

        matching_names = sorted(
            filename
            for filename in matching.get(
                "filename", pd.Series(dtype=str)
            ).astype(str).tolist()
            if (image_dir / filename).is_file()
        )

        if matching_names:
            selected_name = st.selectbox(
                f"Choose a {split} image matching this order",
                matching_names,
            )

            selected_path = image_dir / selected_name
            image_id = selected_path.name
            image = Image.open(selected_path).convert("RGB")
            st.image(image, caption=f"{split}: {image_id}", width=400)

            st.caption(
                "The labels are used only to find a matching demo image. "
                "The model prediction below uses the image."
            )
        else:
            st.warning(
                "No matching image was found for this order in this split. "
                "Try a different order or choose the other split."
            )

else:
    # Blind mode uses only the blind image directory.
    # Do not read blind labels or ground-truth metadata here.
    blind_dir = PROJECT_ROOT / "data" / "processed" / "blind"

    blind_images = sorted(
        path for path in blind_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ) if blind_dir.exists() else []

    if blind_images:
        selected_name = st.selectbox(
            "Select a blind image",
            options=[path.name for path in blind_images],
        )

        selected_path = blind_dir / selected_name
        image_id = selected_path.name
        image = Image.open(selected_path).convert("RGB")
        st.image(image, caption=f"Blind image: {image_id}", width=400)
    else:
        st.error("No images found in data/processed/blind.")

# --------------------------------------------------
# 3. Predict, validate, and log
# --------------------------------------------------
st.subheader("3. Validate the order")

if st.button("Validate bin", type="primary"):
    if image is None:
        st.error("Please select a valid image first.")
    elif not active_order:
        st.warning("Please order at least one product.")
    else:
        start_time = time.perf_counter()

        try:
            with st.spinner("Analysing the bin image..."):
                prediction = predict_image(
                    image,
                    presence_model,
                    feature_extractor,
                    quantity_models,
                )

                predicted_quantities = prediction["quantities"]

                result = validate_order(
                    active_order,
                    predicted_quantities,
                )

            duration = time.perf_counter() - start_time

            log_validation(
                mode=mode,
                image_id=image_id,
                ordered_quantities=active_order,
                predicted_quantities=predicted_quantities,
                presence_probabilities=prediction["probabilities"],
                overall_result=result["overall_status"],
                duration_seconds=duration,
            )

            if result["overall_status"] == "PASS":
                st.success("Overall result: PASS")
            else:
                st.error("Overall result: FAIL")

            rows = []

            for item in result["items"]:
                asin = item["asin"]
                rows.append({
                    "Product": product_names.get(asin, asin),
                    "Ordered": item["ordered_quantity"],
                    "Found": item["found_quantity"],
                    "Presence probability": round(
                        prediction["probabilities"][asin], 3
                    ),
                    "Status": item["status"],
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Prediction and validation time: {duration:.2f} seconds"
            )

            with st.expander("View all model predictions"):
                all_rows = [
                    {
                        "Product": product_names[asin],
                        "Predicted quantity": predicted_quantities[asin],
                        "Presence probability": round(
                            prediction["probabilities"][asin], 3
                        ),
                    }
                    for asin in PRODUCTS
                ]

                st.dataframe(
                    pd.DataFrame(all_rows),
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as error:
            st.error(f"Validation failed: {error}")

# Smart Bin Classifier

An image-based inventory validation system that predicts the quantities of catalogue products visible in a bin image and checks whether those quantities match a requested order.

## 1. Project Overview

The Smart Bin Classifier uses computer vision and machine learning to automate bin-level order validation.

Given a bin image and an order, the system:
- Predicts which catalogue products are present.
- Estimates the quantity of each catalogue product.
- Compares predicted quantities with ordered quantities.
- Returns a PASS or FAIL result for each ordered product and for the overall order.
- Logs validation attempts, model predictions, timestamps, and execution times.

Products present in the bin but not included in the order are ignored during order validation.

## 2. Catalogue

The project uses a fixed catalogue of five products:

| ASIN | Product |
|---|---|
| B00O4OR4GQ | Fujifilm Instax Mini Instant Film |
| B013UJS35G | TaoTronics TT-AH002 Ultrasonic Humidifier |
| B0159A0LH2 | Pumpkin Pie Quest Bars |
| B019D9HESO | RTIC 30 oz. Tumbler |
| B01B1GE6KG | Laser Lights Outdoor Starry Projector |

The catalogue is defined in `catalogue.csv`.

## 3. Dataset Preparation

The project uses the Amazon Bin Image Dataset supplied for the assignment.

A fixed subset of 2,000 distinct bins was selected using random seed 42.

The dataset was divided into:

| Split | Number of bins | Percentage |
|---|---:|---:|
| Training | 1,400 | 70% |
| Validation | 200 | 10% |
| Test | 200 | 10% |
| Blind | 200 | 10% |
| **Total** | **2,000** | **100%** |

The splits were generated using seed 42. The split manifests were checked for duplicate filenames and overlap.

The blind directory contains images only. Blind ground-truth labels are not used by the blind evaluation application.

The dataset preparation workflow includes:
- Filtering eligible bin records and checking product quantity consistency.
- Selecting the fixed subset and generating `catalogue.csv`.
- Creating split manifests.
- Preparing image folders and catalogue quantity labels.
- Checking image-to-label matching and basic label validity.

The selected catalogue contains five ASINs, each appearing in at least 100 selected bins.

**Dataset citation:** Amazon Bin Image Dataset supplied for this assignment. Insert the original Kaggle dataset URL and the required attribution here, following the assignment instructions.

## 4. Project Structure

```text
Smart bin classifier/
├── app.py
├── catalogue.csv
├── README.md
├── .gitignore
├── notebooks/
│   ├── 01_data_eda.ipynb
│   ├── 02_baseline_model.ipynb
│   ├── 03_train_cnn.ipynb
│   └── 04_test_evaluation.ipynb
├── src/
│   ├── build_candidate_pool.py
│   ├── build_catalogue.py
│   ├── create_splits.py
│   ├── order_validation.py
│   ├── predict.py
│   ├── prepare_dataset.py
│   ├── select_bins.py
│   └── validation_logger.py
├── data/
│   ├── splits/
│   └── processed/
└── models/
```

Dataset files, trained model weights, logs, and other generated artifacts are excluded from Git where appropriate.

## 5. Machine Learning Approaches

### Approach 1: HOG + Linear SVM

A baseline model uses Histogram of Oriented Gradients (HOG) image features and a Linear Support Vector Machine classifier for multi-label product-presence prediction.

Validation results:

- Macro F1-score: 0.4053
- Micro F1-score: 0.4431

### Approach 2: Fine-tuned ResNet-18

A pretrained ResNet-18 model was fine-tuned for product-presence prediction. Its image features were also used by separate Random Forest models for positive product-quantity prediction.

The presence model uses a sigmoid probability threshold of 0.5 to determine whether a catalogue product is present. Products predicted as absent receive quantity zero; positive products are assigned a quantity by the corresponding quantity model.

Validation results:

- Macro F1-score: 0.8601
- Micro F1-score: 0.8723

The ResNet-18 approach achieved substantially better validation product-presence performance than the HOG + Linear SVM baseline.

## 6. Final Test Results

The test set contains 200 bins. The test evaluation produced the following results:

| Metric | Result |
|---|---:|
| Quantity exact-match accuracy | 63.00% |
| Quantity mean absolute error (MAE) | 0.095 |
| Test bins containing at least one catalogue product | 153 |
| Test bins containing no catalogue products from the selected catalogue | 47 |

Exact-match accuracy measures the proportion of bins for which all five predicted catalogue quantities match their labels. MAE measures the average absolute quantity error across catalogue products.

The test metrics describe performance on this selected dataset and should not be interpreted as a guarantee of real-world performance.

## 7. Order Validation Evaluation

A controlled order-validation evaluation was performed on the 153 test bins containing at least one catalogue product.

For each eligible bin:
- A PASS order was constructed from its ground-truth positive catalogue quantities.
- A FAIL order was constructed by increasing the requested quantity of one product present in the bin by one.

This produced 306 orders: 153 PASS and 153 FAIL.

| Metric | Result |
|---|---:|
| Overall decision accuracy | 80.07% |
| FAIL precision | 0.73 |
| FAIL recall | 0.97 |
| PASS precision | 0.95 |
| PASS recall | 0.63 |

Confusion matrix, with rows representing actual outcomes and columns representing predicted outcomes:

| Actual / Predicted | FAIL | PASS |
|---|---:|---:|
| FAIL | 148 | 5 |
| PASS | 56 | 97 |

The system detected most constructed FAIL orders, but it also incorrectly rejected a substantial number of constructed PASS orders.

This is a controlled evaluation rather than an independent benchmark of naturally occurring warehouse orders. The 47 test bins with no catalogue products were excluded from this order evaluation.

## 8. Running the Application

### Requirements

- Python 3.13 environment
- Packages used by the project, including PyTorch, torchvision, pandas, Pillow, joblib, and Streamlit
- Prepared dataset files and trained model artifacts available locally

### Setup

Create and activate a virtual environment, then install the required dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch torchvision pandas pillow joblib streamlit
```

Install any additional packages required by the notebooks and dataset-preparation scripts.

### Prepare the dataset and models

Run the dataset preparation and model-training notebooks/scripts in the appropriate order. The application requires the following trained artifacts in the local `models/` directory:

- `resnet18_finetuned_best.pth`
- `positive_quantity_models.joblib`

These artifacts are not committed to the repository. They must be generated locally using the project training workflow.

### Launch the application

From the project root:

```powershell
streamlit run app.py
```

## 9. Application Modes

### Image upload demo

Upload an image manually, enter an order, and run image-based validation.

### Train/validation demo

Choose the training or validation split, enter an order, and select an image whose recorded catalogue quantities match the requested quantities. Metadata-derived labels are used to locate a matching demonstration image. Model predictions are then generated from the image.

### Blind evaluation

Select an image from the blind directory and enter an order. The application uses the image and the entered order for validation without reading blind ground-truth labels.

## 10. Validation Logging

Validation attempts are appended to `logs/validation_log.csv`.

The log records:
- Timestamp
- Application mode
- Image identifier
- Ordered quantities
- Predicted quantities
- Product-presence probabilities
- Overall PASS/FAIL result
- Prediction and validation duration

The log directory is excluded from Git to avoid committing generated operational records.

## 11. Limitations and Failure Analysis

- The model predicts only the five products in the selected catalogue. Other products are outside the prediction scope.
- Image occlusion, tape, packaging, lighting, and image quality can affect recognition.
- Product quantity prediction is more challenging than product-presence prediction, particularly for products with limited examples of quantities greater than one.
- A correct software validation result does not guarantee that the underlying image prediction is correct.
- The order evaluation uses constructed PASS and FAIL orders and does not fully represent real-world order distributions.
- The current application depends on locally available trained model artifacts.
- Blind evaluation results should be assessed separately against ground truth after the blind evaluation procedure is complete.

## 12. Production Deployment Plan

A production implementation could:
1. Receive bin images and order information from a warehouse system through an API.
2. Validate incoming image files and order quantities.
3. Run the trained model on a suitable inference server.
4. Compare predicted quantities against the requested quantities.
5. Return structured item-level and overall validation results.
6. Record timestamps, image IDs, model outputs, results, and latency.
7. Monitor false acceptance, false rejection, inference latency, and prediction drift.
8. Retrain and revalidate the model when sufficient reviewed examples become available.

For warehouse deployment, the system should be tested on representative operational images and evaluated against independently collected order outcomes before being used for consequential inventory decisions.

## 13. Git and Reproducibility

The source code and project history are maintained in Git.

Repository: https://github.com/shauryasehgal/smart-bin-classifier

The assignment requires at least ten meaningful commits. The final submission archive must retain the `.git` directory and exclude prohibited dataset files, blind ground-truth labels, model weights where required, logs, secrets, and virtual environments.

## 14. Deployment Status

**Hosted application:** https://smart-bin-classifier.streamlit.app/

The Smart Bin Classifier is deployed using Streamlit Community Cloud.

The hosted application supports image uploads, product quantity inputs, model predictions, order validation, PASS/FAIL results, and validation logging.

The Train/validation Demo and Blind Evaluation modes are available when running the application locally with the prepared dataset files. These modes are hidden in the hosted version because the dataset images and labels are not included in the public deployment repository.

To run the full application locally, follow the setup instructions in this README and provide the required dataset files and trained model artifacts..

## 15. AI Tool Use and Assumptions

AI assistance was used to support project implementation, debugging, documentation, and development workflow.

Key assumptions:
- The project validates quantities only for the five selected catalogue ASINs.
- Products not included in the order are ignored.
- A product is considered present when its predicted presence probability meets the configured threshold.
- The controlled order evaluation defines FAIL orders by increasing the requested quantity of one product known to be present.
- Blind ground-truth labels must remain separate from the application validation process.

All reported metrics should be reproducible from the corresponding evaluation notebooks and available model artifacts.

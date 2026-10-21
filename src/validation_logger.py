
import csv
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "validation_log.csv"

COLUMNS = [
    "timestamp",
    "mode",
    "image_id",
    "ordered_quantities",
    "predicted_quantities",
    "presence_probabilities",
    "overall_result",
    "duration_seconds",
]


def log_validation(
    mode,
    image_id,
    ordered_quantities,
    predicted_quantities,
    presence_probabilities,
    overall_result,
    duration_seconds,
):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = LOG_FILE.exists()

    with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)

        if not file_exists or LOG_FILE.stat().st_size == 0:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "mode": mode,
            "image_id": image_id,
            "ordered_quantities": json.dumps(ordered_quantities),
            "predicted_quantities": json.dumps(predicted_quantities),
            "presence_probabilities": json.dumps(
                presence_probabilities
            ),
            "overall_result": overall_result,
            "duration_seconds": round(duration_seconds, 3),
        })

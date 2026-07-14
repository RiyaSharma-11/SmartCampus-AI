from pathlib import Path
from typing import Any

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "isolation_forest_model.pkl"


# Load model when this file is imported
# Raises clear error if model file is missing
if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "ML model is missing. Run: python ml_model/train_model.py"
    )

model = joblib.load(MODEL_PATH)


def predict_anomaly(pm25_value: float) -> dict[str, Any]:
    """
    Predict whether a PM2.5 value is normal or anomalous.

    Isolation Forest returns:
     1  means normal
    -1  means anomaly
    """

    if pm25_value is None:
        raise ValueError("PM2.5 value cannot be None.")

    pm25_value = float(pm25_value)

    if pm25_value < 0:
        raise ValueError("PM2.5 cannot be negative.")

    # Model needs data in DataFrame format
    features = pd.DataFrame([{"pm25": pm25_value}])

    # Get prediction: 1 = normal, -1 = anomaly
    prediction = int(model.predict(features)[0])

    # Get anomaly score: more negative = more anomalous
    anomaly_score = float(model.decision_function(features)[0])

    is_anomaly = prediction == -1

    return {
        "pm25": pm25_value,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": anomaly_score,
        "status": "Anomaly" if is_anomaly else "Normal",
    }


if __name__ == "__main__":
    # Quick test with different values
    test_values = [5, 20, 25, 180, 250]

    for value in test_values:
        result = predict_anomaly(value)
        print(result)
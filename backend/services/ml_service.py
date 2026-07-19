from typing import Any, Dict

from backend.logger import logger
from ml_model.predict import predict_anomaly


def classify_pm25(
    pm25: float,
) -> Dict[str, Any]:
    """Classify a PM2.5 reading using the ML model."""

    logger.info(
        "Running ML prediction for PM2.5=%s",
        pm25,
    )

    result = predict_anomaly(pm25)

    logger.info(
        "ML prediction completed | Status=%s | Score=%s",
        result["status"],
        result["anomaly_score"],
    )

    return result
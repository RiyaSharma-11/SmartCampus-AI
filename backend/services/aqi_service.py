from datetime import datetime
from typing import Any, Dict, Optional

from alerts.email_service import send_anomaly_alert
from backend.database.queries import insert_aqi_reading
from backend.logger import logger
from backend.services.ml_service import classify_pm25


def convert_datetime(
    recorded_at: Optional[str],
) -> Optional[datetime]:
    """Convert an ISO timestamp string into a Python datetime."""

    if not recorded_at:
        return None

    try:
        cleaned_timestamp = recorded_at.replace(
            "Z",
            "+00:00",
        )

        return datetime.fromisoformat(
            cleaned_timestamp
        ).replace(tzinfo=None)

    except ValueError:
        logger.warning(
            "Invalid recorded_at timestamp received: %s",
            recorded_at,
        )
        return None


def validate_pm25(
    pm25_value: Any,
) -> Optional[float]:
    """Validate and convert a PM2.5 value."""

    if pm25_value is None:
        logger.warning(
            "Message skipped because PM2.5 is missing."
        )
        return None

    try:
        converted_value = float(pm25_value)

    except (TypeError, ValueError):
        logger.warning(
            "Message skipped because PM2.5 is invalid: %s",
            pm25_value,
        )
        return None

    if converted_value < 0:
        logger.warning(
            "Message skipped because PM2.5 is negative: %s",
            converted_value,
        )
        return None

    return converted_value


def process_aqi_message(
    message_data: Dict[str, Any],
) -> Optional[int]:
    """
    Validate, classify and store one AQI event.

    Returns the inserted database row ID.
    Returns None when the message is invalid.
    """

    logger.info(
        "Processing AQI message: %s",
        message_data,
    )

    pm25_value = validate_pm25(
        message_data.get("pm25")
    )

    if pm25_value is None:
        return None

    ml_result = classify_pm25(pm25_value)

    reading_id = insert_aqi_reading(
        city=message_data.get("city") or "Unknown",
        pm25=pm25_value,
        latitude=message_data.get("latitude"),
        longitude=message_data.get("longitude"),
        recorded_at=convert_datetime(
            message_data.get("recorded_at")
        ),
        is_anomaly=bool(
            ml_result["is_anomaly"]
        ),
        anomaly_score=float(
            ml_result["anomaly_score"]
        ),
        status=ml_result["status"],
    )

    logger.info(
        "AQI message processed successfully | "
        "ID=%s | PM2.5=%s | Status=%s | Score=%s",
        reading_id,
        pm25_value,
        ml_result["status"],
        ml_result["anomaly_score"],
    )

    if ml_result["is_anomaly"]:
        try:
            send_anomaly_alert(
                city=message_data.get("city") or "Unknown",
                pm25=pm25_value,
                anomaly_score=ml_result["anomaly_score"],
                recorded_at=message_data.get("recorded_at"),
            )

            logger.info(
                "Anomaly email alert sent successfully."
            )

        except Exception:
            logger.exception(
                "AQI reading was stored, but the anomaly "
                "email could not be sent."
            )

    return reading_id
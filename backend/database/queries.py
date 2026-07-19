from datetime import datetime
from typing import Any, Dict, Optional

from backend.database.connection import (
    close_database_connection,
    get_database_connection,
)
from backend.logger import logger


def insert_aqi_reading(
    city: str,
    pm25: float,
    latitude: Optional[float],
    longitude: Optional[float],
    recorded_at: Optional[datetime],
    is_anomaly: bool,
    anomaly_score: float,
    status: str,
) -> int:
    """Insert one processed AQI reading into MySQL."""

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO aqi_readings (
                city,
                pm25,
                latitude,
                longitude,
                recorded_at,
                is_anomaly,
                anomaly_score,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            city,
            pm25,
            latitude,
            longitude,
            recorded_at,
            is_anomaly,
            anomaly_score,
            status,
        )

        cursor.execute(sql, values)
        connection.commit()

        reading_id = cursor.lastrowid

        if reading_id is None:
            raise RuntimeError(
                "MySQL did not return an inserted row ID."
            )

        logger.info(
            "AQI reading inserted into database | ID=%s",
            reading_id,
        )

        return int(reading_id)

    except Exception:
        if connection is not None:
            connection.rollback()

        logger.exception(
            "Failed to insert AQI reading into database."
        )
        raise

    finally:
        if cursor is not None:
            cursor.close()

        close_database_connection(connection)


def get_latest_aqi_reading() -> Optional[Dict[str, Any]]:
    """Return the latest AQI reading from MySQL."""

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                city,
                pm25,
                latitude,
                longitude,
                recorded_at,
                is_anomaly,
                anomaly_score,
                status,
                created_at
            FROM aqi_readings
            ORDER BY id DESC
            LIMIT 1
        """

        cursor.execute(sql)
        result = cursor.fetchone()

        return result

    except Exception:
        logger.exception(
            "Failed to fetch latest AQI reading."
        )
        raise

    finally:
        if cursor is not None:
            cursor.close()

        close_database_connection(connection)
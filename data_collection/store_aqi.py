import os
from datetime import datetime
from typing import Optional

import mysql.connector
import requests
from dotenv import load_dotenv

from ml_model.predict import predict_anomaly


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

OPENAQ_URL = (
    "https://api.openaq.org/v3/parameters/2/latest?limit=5"
)


def convert_openaq_time(
    recorded_at_string: Optional[str],
) -> Optional[datetime]:
    """
    Convert OpenAQ UTC timestamp to Python datetime.

    OpenAQ sends:  2024-03-15T10:30:00Z
    MySQL needs:   2024-03-15 10:30:00
    """

    if not recorded_at_string:
        return None

    # Replace Z with +00:00 so Python can parse it
    cleaned = recorded_at_string.replace("Z", "+00:00")

    # Remove timezone info so MySQL accepts it
    return datetime.fromisoformat(cleaned).replace(
        tzinfo=None
    )


def get_database_connection():
    """Create and return a MySQL connection using .env values."""

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv(
            "MYSQL_DATABASE",
            "smartcampus_ai",
        ),
    )


def fetch_first_valid_reading() -> Optional[dict]:
    """
    Fetch readings from OpenAQ and return
    the first one with a valid PM2.5 value.
    """

    if not API_KEY:
        raise ValueError(
            "OPENAQ_API_KEY is missing from .env."
        )

    response = requests.get(
        OPENAQ_URL,
        headers={"X-API-Key": API_KEY},
        timeout=15,
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    for item in results:
        value = item.get("value")

        # Return first reading that has a valid value
        if value is not None and float(value) >= 0:
            return item

    return None


def store_reading() -> None:
    """
    Full pipeline:
    Fetch → Validate → ML prediction → Store in MySQL
    """

    try:
        item = fetch_first_valid_reading()

        if item is None:
            print("No valid PM2.5 reading found.")
            return

        # Extract all the fields we need
        value = float(item["value"])

        coordinates = item.get("coordinates") or {}
        datetime_info = item.get("datetime") or {}
        location = item.get("location") or {}

        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")
        recorded_at = convert_openaq_time(
            datetime_info.get("utc")
        )
        city = location.get("name") or "Unknown"

        # Run through ML model
        ml_result = predict_anomaly(value)

        # Connect to MySQL and insert the row
        connection = get_database_connection()
        cursor = connection.cursor()

        try:
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

            # %s placeholders prevent SQL injection attacks
            values = (
                city,
                value,
                latitude,
                longitude,
                recorded_at,
                bool(ml_result["is_anomaly"]),
                float(ml_result["anomaly_score"]),
                ml_result["status"],
            )

            cursor.execute(sql, values)
            connection.commit()

        finally:
            cursor.close()
            connection.close()

        print("AQI reading stored successfully!")
        print("City      :", city)
        print("PM2.5     :", value)
        print("ML Status :", ml_result["status"])
        print("Score     :", ml_result["anomaly_score"])

    except requests.RequestException as error:
        print("OpenAQ request failed:", error)

    except mysql.connector.Error as error:
        print("MySQL error:", error)

    except (ValueError, TypeError) as error:
        print("Invalid data:", error)


if __name__ == "__main__":
    store_reading()
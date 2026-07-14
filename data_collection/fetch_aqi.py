import os

import requests
from dotenv import load_dotenv

from ml_model.predict import predict_anomaly


# Load values from your .env file
load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

# Parameter 2 = PM2.5 in OpenAQ's system
# limit=5 means fetch 5 readings at once
OPENAQ_URL = (
    "https://api.openaq.org/v3/parameters/2/latest?limit=5"
)


def fetch_latest_readings() -> None:
    """Fetch and print the latest PM2.5 readings from OpenAQ."""

    if not API_KEY:
        raise ValueError(
            "OPENAQ_API_KEY is missing from .env file."
        )

    # API key goes in headers — like showing ID at the door
    headers = {
        "X-API-Key": API_KEY
    }

    try:
        response = requests.get(
            OPENAQ_URL,
            headers=headers,
            timeout=15,         # Wait max 15 seconds
        )

        # Raises error if status code is 4xx or 5xx
        response.raise_for_status()

    except requests.RequestException as error:
        print("OpenAQ request failed:", error)
        return

    # Parse JSON response into Python dictionary
    response_data = response.json()

    # All readings are inside the 'results' key
    results = response_data.get("results", [])

    if not results:
        print("No PM2.5 readings returned.")
        return

    print("\nLatest PM2.5 readings:\n")

    for item in results:
        value = item.get("value")

        # Skip missing or physically impossible values
        if value is None or float(value) < 0:
            print("Skipped invalid value:", value)
            print("-" * 40)
            continue

        # Extract nested data safely using .get()
        location = item.get("location") or {}
        coordinates = item.get("coordinates") or {}
        datetime_info = item.get("datetime") or {}

        location_name = (
            location.get("name") or "Unknown location"
        )

        unit_name = item.get("unit") or "µg/m³"

        # Run the value through your ML model
        ml_result = predict_anomaly(float(value))

        print("Location  :", location_name)
        print("PM2.5     :", value, unit_name)
        print("ML Status :", ml_result["status"])
        print("Score     :", ml_result["anomaly_score"])
        print("Time      :", datetime_info.get("utc"))
        print("Latitude  :", coordinates.get("latitude"))
        print("Longitude :", coordinates.get("longitude"))
        print("-" * 40)


if __name__ == "__main__":
    fetch_latest_readings()
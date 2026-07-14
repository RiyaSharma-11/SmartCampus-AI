import os
import time
import csv
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

# OpenAQ location ID for Delhi Anand Vihar — one of India's
# most monitored stations, very close to Ghaziabad
# Location ID 8118 = Delhi Anand Vihar CPCB station
LOCATION_ID = 8118

# How many readings to fetch — more = better model
LIMIT = 1000

OUTPUT_FILE = "data_collection/delhi_aqi_historical.csv"


def fetch_historical_data() -> None:
    """
    Fetch real historical PM2.5 readings from Delhi
    and save them to a CSV file for ML training.
    """

    if not API_KEY:
        raise ValueError(
            "OPENAQ_API_KEY missing from .env"
        )

    headers = {"X-API-Key": API_KEY}

    print(f"Fetching historical PM2.5 data from Delhi...")
    print(f"Location: Anand Vihar (ID {LOCATION_ID})")
    print(f"Requesting up to {LIMIT} readings...\n")

    all_results = []
    page = 1
    per_page = 100       # OpenAQ max per request
    fetched = 0

    while fetched < LIMIT:
        url = (
            f"https://api.openaq.org/v3/locations/"
            f"{LOCATION_ID}/measurements"
            f"?parameter=pm25"
            f"&limit={per_page}"
            f"&page={page}"
        )

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            print(f"Request failed on page {page}: {error}")
            break

        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"No more data after page {page - 1}.")
            break

        for item in results:
            value = item.get("value")

            # Skip invalid readings
            if value is None:
                continue

            value = float(value)

            # Skip physically impossible values
            if value < 0 or value > 2000:
                continue

            datetime_info = (
                item.get("period") or
                item.get("datetime") or
                {}
            )

            timestamp = (
                datetime_info.get("utc") or
                datetime_info.get("datetimeFrom", {}).get("utc") or
                ""
            )

            all_results.append({
                "pm25": value,
                "recorded_at": timestamp,
            })

        fetched += len(results)
        print(f"Page {page} — fetched {fetched} readings so far...")

        page += 1

        # Be polite to the API — small delay between pages
        time.sleep(0.5)

        if fetched >= LIMIT:
            break

    if not all_results:
        print("\nNo valid readings were returned.")
        print("Trying alternative approach...\n")
        fetch_from_parameters()
        return

    # Save to CSV
    save_to_csv(all_results)


def fetch_from_parameters() -> None:
    """
    Alternative: fetch latest PM2.5 readings globally
    filtered to find Indian stations.
    This runs if the location-specific fetch returns nothing.
    """

    headers = {"X-API-Key": API_KEY}
    all_results = []

    print("Fetching from global PM2.5 parameter endpoint...")

    for page in range(1, 11):     # Fetch 10 pages x 100 = 1000 readings
        url = (
            "https://api.openaq.org/v3/parameters/2/latest"
            f"?limit=100&page={page}"
        )

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            print(f"Failed on page {page}: {error}")
            break

        results = response.json().get("results", [])

        if not results:
            break

        for item in results:
            value = item.get("value")

            if value is None:
                continue

            value = float(value)

            if value < 0 or value > 2000:
                continue

            datetime_info = item.get("datetime") or {}

            all_results.append({
                "pm25": value,
                "recorded_at": datetime_info.get("utc", ""),
            })

        print(f"Page {page} — {len(all_results)} total readings...")
        time.sleep(0.5)

    if not all_results:
        print("Could not fetch any data. Check your API key.")
        return

    save_to_csv(all_results)


def save_to_csv(results: list) -> None:
    """Save a list of readings to CSV file."""

    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["pm25", "recorded_at"],
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved {len(results)} readings to {OUTPUT_FILE}")
    print("\nSample values:")

    # Print first 5 rows as preview
    for row in results[:5]:
        print(f"  PM2.5: {row['pm25']:>8.2f}  |  {row['recorded_at']}")

    pm25_values = [r["pm25"] for r in results]

    print(f"\nStats:")
    print(f"  Total readings : {len(pm25_values)}")
    print(f"  Min PM2.5      : {min(pm25_values):.2f}")
    print(f"  Max PM2.5      : {max(pm25_values):.2f}")
    print(f"  Average PM2.5  : {sum(pm25_values)/len(pm25_values):.2f}")


if __name__ == "__main__":
    fetch_historical_data()
import os
from datetime import datetime
from typing import Optional

import mysql.connector
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from kafka_service.producer import send_aqi_message
from backend.database.connection import get_database_connection as get_connection
from backend.scheduler import create_scheduler

load_dotenv()

# Create the FastAPI app instance
# title and description show up in the auto-generated docs
app = FastAPI(
    title="SmartCampus AI API",
    description=(
        "Backend API for real-time PM2.5 monitoring "
        "and anomaly detection."
    ),
    version="1.0.0",
)
# ── Scheduler setup ──────────────────────────────────────────
# lifespan events start/stop the scheduler with FastAPI
# so it runs exactly as long as the server runs

@app.on_event("startup")
def start_scheduler():
    """Start background scheduler when FastAPI starts."""
    scheduler = create_scheduler()
    scheduler.start()
    print(
        f"Scheduler started — fetching AQI data "
        f"every 30 seconds automatically."
    )


@app.on_event("shutdown")
def stop_scheduler():
    """Stop scheduler cleanly when FastAPI shuts down."""
    print("Scheduler stopped.")

OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")

OPENAQ_URL = (
    "https://api.openaq.org/v3/parameters/2/latest?limit=5"
)


# ─── Helper functions ────────────────────────────────────────


def convert_openaq_time(
    timestamp: Optional[str],
) -> Optional[datetime]:
    """Convert OpenAQ UTC timestamp to MySQL-compatible datetime."""

    if not timestamp:
        return None

    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    ).replace(tzinfo=None)


def get_first_valid_reading() -> dict:
    """
    Call OpenAQ API and return first valid PM2.5 reading.
    Raises HTTPException if anything goes wrong —
    FastAPI automatically converts this into a proper
    error response with the right status code.
    """

    if not OPENAQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAQ_API_KEY is missing.",
        )

    try:
        response = requests.get(
            OPENAQ_URL,
            headers={"X-API-Key": OPENAQ_API_KEY},
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAQ request failed: {error}",
        ) from error

    results = response.json().get("results", [])

    for item in results:
        value = item.get("value")

        if value is not None and float(value) >= 0:
            return item

    raise HTTPException(
        status_code=404,
        detail="No valid PM2.5 reading returned.",
    )


# ─── API Endpoints ───────────────────────────────────────────


@app.get("/")
def home():
    """Welcome endpoint — lists all available routes."""

    return {
        "message": "Welcome to SmartCampus AI",
        "available_endpoints": [
            "/latest",
            "/history",
            "/recent",
            "/fetch",
            "/docs",
        ],
    }


@app.get("/latest")
def latest_reading():
    """Return the single most recent AQI reading from MySQL."""

    connection = None
    cursor = None

    try:
        connection = get_connection()

        # dictionary=True makes rows return as dicts
        # instead of plain tuples — much easier to work with
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM aqi_readings
            ORDER BY id DESC
            LIMIT 1
            """
        )

        reading = cursor.fetchone()

        if reading is None:
            raise HTTPException(
                status_code=404,
                detail="No AQI readings found in database.",
            )

        return reading

    except mysql.connector.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}",
        ) from error

    finally:
        # finally block ALWAYS runs — even if there's an error
        # This ensures we never leave a connection open
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.get("/history")
def all_readings():
    """Return every AQI reading ever stored."""

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM aqi_readings
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    except mysql.connector.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}",
        ) from error

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.get("/recent")
def recent_readings(limit: int = 10):
    """
    Return the last N readings.
    limit is a query parameter — caller can pass ?limit=20
    Default is 10 if not specified.
    """

    # Validate limit to prevent abuse
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100.",
        )

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM aqi_readings
            ORDER BY id DESC
            LIMIT %s
            """,
            (limit,),
        )

        return cursor.fetchall()

    except mysql.connector.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}",
        ) from error

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.post("/fetch")
def fetch_and_store_aqi():
    """
    New Kafka pipeline:
    1. Call OpenAQ API
    2. Validate the reading
    3. Send to Kafka topic
    4. Consumer handles ML + MySQL + alerts
    """

    # Step 1 — get data from OpenAQ
    item = get_first_valid_reading()

    # Step 2 — extract all fields
    value = float(item["value"])

    coordinates = item.get("coordinates") or {}
    datetime_info = item.get("datetime") or {}
    location = item.get("location") or {}

    latitude = coordinates.get("latitude")
    longitude = coordinates.get("longitude")
    recorded_at = datetime_info.get("utc")
    city = location.get("name") or "Unknown"

    # Validate PM2.5
    if value < 0:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid PM2.5 value: {value}",
        )

    # Step 3 — build message for Kafka
    message = {
        "city": city,
        "pm25": value,
        "latitude": latitude,
        "longitude": longitude,
        "recorded_at": recorded_at,
    }

    # Step 4 — send to Kafka
    # Consumer will handle ML + MySQL + email alert
    success = send_aqi_message(message)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send message to Kafka.",
        )

    return {
        "message": "AQI reading sent to Kafka pipeline.",
        "city": city,
        "pm25": value,
        "latitude": latitude,
        "longitude": longitude,
        "recorded_at": recorded_at,
        "kafka_status": "Message delivered to topic",
        "next_step": "Consumer will run ML and store in MySQL",
    }
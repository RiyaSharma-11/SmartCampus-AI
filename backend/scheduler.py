import os
import logging
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv


load_dotenv()

# Set up logging so we can see what the scheduler is doing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

logger = logging.getLogger(__name__)

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8000",
)

# How often to fetch in seconds
# 30 seconds for demo — in production use 300 (5 minutes)
FETCH_INTERVAL_SECONDS = 30


def fetch_aqi_job() -> None:
    """
    This function runs automatically every 30 seconds.
    It calls the /fetch endpoint which:
    1. Gets fresh AQI data from OpenAQ
    2. Runs ML anomaly detection
    3. Stores result in MySQL
    4. Sends alert email if anomaly found
    """

    logger.info("Scheduler triggered — fetching AQI data...")

    try:
        response = requests.post(
            f"{FASTAPI_URL}/fetch",
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            ml = result.get("ml_result", {})

            logger.info(
                f"Fetch successful — "
                f"City: {result.get('city', 'Unknown')} | "
                f"PM2.5: {result.get('pm25')} µg/m³ | "
                f"Status: {ml.get('status')} | "
                f"Alert sent: {result.get('alert_sent')}"
            )

        else:
            logger.warning(
                f"Fetch returned status {response.status_code}: "
                f"{response.text[:100]}"
            )

    except requests.exceptions.ConnectionError:
        logger.error(
            "Cannot connect to FastAPI. "
            "Make sure it is running on port 8000."
        )

    except requests.exceptions.Timeout:
        logger.error(
            "Fetch request timed out after 30 seconds."
        )

    except requests.RequestException as error:
        logger.error(f"Fetch failed: {error}")


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure the background scheduler.
    Returns the scheduler (not yet started).
    """

    scheduler = BackgroundScheduler()

    # Add the fetch job — runs every 30 seconds
    scheduler.add_job(
        fetch_aqi_job,
        trigger="interval",
        seconds=FETCH_INTERVAL_SECONDS,
        id="aqi_fetch_job",
        name="AQI data fetch",
        # Run first fetch immediately when scheduler starts
        next_run_time=datetime.now(),
    )

    return scheduler
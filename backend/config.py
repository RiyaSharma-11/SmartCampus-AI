import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


class Settings:

    # -----------------------
    # MySQL Configuration
    # -----------------------

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "smartcampus_ai")

    # -----------------------
    # Kafka
    # -----------------------

    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )

    KAFKA_TOPIC = os.getenv(
        "KAFKA_TOPIC",
        "aqi-data"
    )

    # -----------------------
    # OpenAQ
    # -----------------------

    OPENAQ_API_KEY = os.getenv(
        "OPENAQ_API_KEY"
    )

    # -----------------------
    # Email
    # -----------------------

    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")


settings = Settings()
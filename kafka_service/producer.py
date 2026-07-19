import json
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from backend.config import settings
from backend.logger import logger


def create_producer() -> KafkaProducer:
    """Create and return a Kafka producer with retry logic."""

    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode(
                    "utf-8"
                ),
                # Wait max 10 seconds for broker connection
                request_timeout_ms=10000,
                # Retry sending failed messages 3 times
                retries=3,
            )

            logger.info(
                "Kafka producer connected to %s",
                settings.KAFKA_BOOTSTRAP_SERVERS,
            )

            return producer

        except NoBrokersAvailable:
            logger.warning(
                "Kafka broker unavailable at %s. "
                "Retrying in 5 seconds.",
                settings.KAFKA_BOOTSTRAP_SERVERS,
            )
            time.sleep(5)

        except Exception:
            logger.exception(
                "Unexpected error connecting to Kafka producer. "
                "Retrying in 5 seconds."
            )
            time.sleep(5)


def send_aqi_message(message: dict) -> bool:
    """
    Send one AQI reading to the Kafka topic.
    Returns True if sent successfully, False otherwise.

    message format:
    {
        "city": "Delhi",
        "pm25": 45.2,
        "latitude": 28.6,
        "longitude": 77.2,
        "recorded_at": "2026-07-19T10:30:00Z"
    }
    """

    try:
        producer = create_producer()

        future = producer.send(
            settings.KAFKA_TOPIC,
            message,
        )

        # Block until message is confirmed sent
        # timeout=10 means wait max 10 seconds
        record_metadata = future.get(timeout=10)

        producer.flush()
        producer.close()

        logger.info(
            "AQI message sent to Kafka | "
            "Topic=%s | Partition=%s | Offset=%s",
            record_metadata.topic,
            record_metadata.partition,
            record_metadata.offset,
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send AQI message to Kafka."
        )
        return False


if __name__ == "__main__":
    # Quick test — sends one message directly
    test_message = {
        "city": "Delhi Test",
        "pm25": 85.0,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "recorded_at": "2026-07-19T10:30:00Z",
    }

    print("Sending test message to Kafka...")
    success = send_aqi_message(test_message)


    if success:
        print("Message sent successfully!")
    else:
        print("Message failed to send.")
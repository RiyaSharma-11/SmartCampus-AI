import json
import time

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from backend.config import settings
from backend.logger import logger
from backend.services.aqi_service import process_aqi_message


def create_consumer() -> KafkaConsumer:
    """Create a Kafka consumer and retry until Kafka is available."""

    while True:
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda value: json.loads(
                    value.decode("utf-8")
                ),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id="smartcampus-aqi-consumers-local",
            )

            logger.info(
                "Kafka consumer connected to %s",
                settings.KAFKA_BOOTSTRAP_SERVERS,
            )

            return consumer

        except NoBrokersAvailable:
            logger.warning(
                "Kafka broker is unavailable at %s. "
                "Retrying in 5 seconds.",
                settings.KAFKA_BOOTSTRAP_SERVERS,
            )
            time.sleep(5)

        except Exception:
            logger.exception(
                "Unexpected error while connecting to Kafka. "
                "Retrying in 5 seconds."
            )
            time.sleep(5)


def main() -> None:
    """Start consuming AQI messages."""

    consumer = create_consumer()

    logger.info(
        "Listening continuously to Kafka topic: %s",
        settings.KAFKA_TOPIC,
    )

    try:
        for kafka_message in consumer:
            try:
                process_aqi_message(
                    kafka_message.value
                )

            except Exception:
                logger.exception(
                    "Failed to process Kafka message."
                )

    except KeyboardInterrupt:
        logger.info(
            "Kafka consumer stopped by the user."
        )

    finally:
        consumer.close()

        logger.info(
            "Kafka consumer connection closed."
        )


if __name__ == "__main__":
    main()
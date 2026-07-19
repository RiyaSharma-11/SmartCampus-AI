from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Kafka Producer Connected")
message = {
    "city": "Unknown",
    "pm25": 8,
    "latitude": 35.21815,
    "longitude": 128.57425,
    "recorded_at": "2026-07-14T12:00:00"
}

producer.send("aqi-data", message)
producer.flush()

print("Message sent successfully!")
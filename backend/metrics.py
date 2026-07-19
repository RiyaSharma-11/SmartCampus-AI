from prometheus_client import Counter, Histogram, Gauge


# ── API metrics ──────────────────────────────────────────────

# Counts every HTTP request
# Labels let us filter by endpoint and method
HTTP_REQUESTS_TOTAL = Counter(
    "smartcampus_http_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint", "status"],
)

# Measures how long each request takes
# Buckets define the time ranges we care about
HTTP_REQUEST_DURATION = Histogram(
    "smartcampus_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# ── AQI metrics ──────────────────────────────────────────────

# Total AQI readings stored in MySQL
AQI_READINGS_TOTAL = Counter(
    "smartcampus_aqi_readings_total",
    "Total number of AQI readings stored",
)

# Total anomalies detected by ML model
ANOMALIES_DETECTED_TOTAL = Counter(
    "smartcampus_anomalies_detected_total",
    "Total number of PM2.5 anomalies detected",
)

# Current PM2.5 value (updates on every reading)
CURRENT_PM25 = Gauge(
    "smartcampus_current_pm25",
    "Most recent PM2.5 reading",
)

# ── Kafka metrics ─────────────────────────────────────────────

# Messages sent by producer
KAFKA_MESSAGES_SENT = Counter(
    "smartcampus_kafka_messages_sent_total",
    "Total Kafka messages sent by producer",
)

# Messages successfully processed by consumer
KAFKA_MESSAGES_PROCESSED = Counter(
    "smartcampus_kafka_messages_processed_total",
    "Total Kafka messages processed by consumer",
)

# Messages that failed to process
KAFKA_MESSAGES_FAILED = Counter(
    "smartcampus_kafka_messages_failed_total",
    "Total Kafka messages that failed processing",
)
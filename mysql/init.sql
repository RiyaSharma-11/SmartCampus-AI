USE smartcampus_ai;

CREATE TABLE IF NOT EXISTS aqi_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,

    city VARCHAR(100) DEFAULT 'Unknown',
    pm25 FLOAT NOT NULL,

    latitude DOUBLE,
    longitude DOUBLE,

    recorded_at DATETIME,

    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score FLOAT,
    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
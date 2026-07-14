import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="riyarjun"
)

cursor = connection.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS smartcampus_ai")
cursor.execute("USE smartcampus_ai")

cursor.execute("""
CREATE TABLE IF NOT EXISTS aqi_readings (
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
""")

connection.commit()

print("Database and table created successfully!")

cursor.close()
connection.close()
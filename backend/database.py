import os

import mysql.connector
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """Create and return a new MySQL connection."""

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv(
            "MYSQL_DATABASE",
            "smartcampus_ai",
        ),
    )
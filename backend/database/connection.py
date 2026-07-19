from typing import Optional, Union
import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.pooling import PooledMySQLConnection

from backend.config import settings
from backend.logger import logger



DatabaseConnection = Union[
    MySQLConnection,
    PooledMySQLConnection,
]


def get_database_connection() -> DatabaseConnection:
    """
    Create and return a MySQL database connection.

    The connection settings are loaded from backend.config.
    """

    try:
        connection = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            connection_timeout=10,
        )

        logger.info(
            "Connected to MySQL database at %s:%s",
            settings.MYSQL_HOST,
            settings.MYSQL_PORT,
        )

        return connection

    except mysql.connector.Error:
        logger.exception(
            "Failed to connect to MySQL database at %s:%s",
            settings.MYSQL_HOST,
            settings.MYSQL_PORT,
        )
        raise


def close_database_connection(
    connection: Optional[DatabaseConnection],
) -> None:
    """Close a MySQL connection safely."""

    if connection is None:
        return

    try:
        if connection.is_connected():
            connection.close()
            logger.info("MySQL connection closed.")

    except mysql.connector.Error:
        logger.exception(
            "An error occurred while closing the MySQL connection."
        )
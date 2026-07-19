from backend.database.connection import (
    close_database_connection,
    get_database_connection,
)
from backend.logger import logger


def main() -> None:
    connection = None

    try:
        connection = get_database_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")

        database_name = cursor.fetchone()[0]

        logger.info(
            "Database connection test successful. Database: %s",
            database_name,
        )

        cursor.close()

    except Exception:
        logger.exception(
            "Database connection test failed."
        )

    finally:
        close_database_connection(connection)


if __name__ == "__main__":
    main()
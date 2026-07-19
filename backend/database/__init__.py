from backend.database.connection import (
    get_database_connection,
    close_database_connection,
)

# Alias so old code using get_connection still works
get_connection = get_database_connection

__all__ = [
    "get_connection",
    "get_database_connection", 
    "close_database_connection",
]
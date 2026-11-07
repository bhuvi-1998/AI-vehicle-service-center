
import os
import threading

import pymysql
from psycopg_pool import ConnectionPool, PoolTimeout
from pymysql.err import IntegrityError as MySQLIntegrityError
from psycopg import IntegrityError as PostgreSQLIntegrityError
from dotenv import load_dotenv

INTEGRITY_ERRORS = (MySQLIntegrityError, PostgreSQLIntegrityError)


load_dotenv()


_POSTGRES_POOL_LOCK = threading.Lock()
_postgres_pool = None


def _get_postgresql_connection_kwargs():
    """Build PostgreSQL connection settings from environment variables."""
    db_password = os.getenv("DB_PASSWORD")

    if db_password is None:
        raise RuntimeError(
            "DB_PASSWORD is missing from the environment configuration."
        )

    required_variables = ("DB_HOST", "DB_USER", "DB_NAME")
    missing = [
        name for name in required_variables
        if not os.getenv(name)
    ]

    if missing:
        raise RuntimeError(
            "Missing PostgreSQL configuration: " + ", ".join(missing)
        )

    from psycopg.rows import dict_row

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER"),
        "password": db_password,
        "dbname": os.getenv("DB_NAME"),
        "sslmode": os.getenv("DB_SSLMODE", "require"),
        "connect_timeout": 10,
        "row_factory": dict_row,
    }


def init_database_pool():
    """
    Initialize one reusable PostgreSQL connection pool per process.

    MySQL does not use this pool and retains its existing connection behavior.
    """
    global _postgres_pool

    driver = os.getenv("DB_DRIVER", "mysql").strip().lower()

    if driver not in ("postgres", "postgresql", "psycopg"):
        return None

    with _POSTGRES_POOL_LOCK:
        if _postgres_pool is not None and not _postgres_pool.closed:
            return _postgres_pool

        min_size = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
        max_size = int(os.getenv("DB_POOL_MAX_SIZE", "5"))

        if min_size < 1 or max_size < min_size:
            raise RuntimeError(
                "Invalid database pool sizes: require "
                "1 <= DB_POOL_MIN_SIZE <= DB_POOL_MAX_SIZE."
            )

        pool = ConnectionPool(
            conninfo="",
            kwargs=_get_postgresql_connection_kwargs(),
            min_size=min_size,
            max_size=max_size,
            timeout=float(os.getenv("DB_POOL_TIMEOUT", "10")),
            close_returns=True,
            open=False,
            name="vehicle-service-center-postgres",
        )

        try:
            pool.open(
                wait=True,
                timeout=float(
                    os.getenv("DB_POOL_STARTUP_TIMEOUT", "20")
                ),
            )
        except Exception:
            pool.close()
            raise

        _postgres_pool = pool
        return pool


def close_database_pool():
    """Close the PostgreSQL pool during application shutdown."""
    global _postgres_pool

    with _POSTGRES_POOL_LOCK:
        pool = _postgres_pool
        _postgres_pool = None

    if pool is not None and not pool.closed:
        pool.close(timeout=5)


def get_connection():
    """
    Return a database connection based on DB_DRIVER.

    PostgreSQL connections are borrowed from the shared pool.
    Calling connection.close() returns them to the pool.

    MySQL continues to create and close connections as before.
    """
    driver = os.getenv("DB_DRIVER", "mysql").strip().lower()

    if driver in ("mysql", "mariadb"):
        db_password = os.getenv("DB_PASSWORD")

        if db_password is None:
            raise RuntimeError(
                "DB_PASSWORD is missing from the environment configuration."
            )

        return pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=db_password,
            database=os.getenv(
                "DB_NAME",
                "vehicle_service_center"
            ),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            charset="utf8mb4"
        )

    if driver in ("postgres", "postgresql", "psycopg"):
        pool = init_database_pool()

        try:
            return pool.getconn(
                timeout=float(os.getenv("DB_POOL_TIMEOUT", "10"))
            )
        except PoolTimeout as exc:
            raise RuntimeError(
                "Timed out waiting for an available PostgreSQL connection. "
                "The database may be busy."
            ) from exc

    raise RuntimeError(
        "Unsupported DB_DRIVER. Use 'mysql' or 'postgresql'."
    )
# --------------------------------------------------
# Cross-database compatibility helpers
# --------------------------------------------------

_ALLOWED_ID_COLUMNS = {
    "admins": "admin_id",
    "customers": "customer_id",
    "vehicles": "vehicle_id",
    "appointments": "appointment_id",
    "estimates": "estimate_id",
    "invoices": "invoice_id",
    "parts": "part_id",
    "services": "service_id",
    "technicians": "technician_id",
}


def is_postgresql_connection(connection):
    """Return True when the connection is a Psycopg 3 connection."""
    return connection.__class__.__module__.split(".", 1)[0] == "psycopg"


def get_last_insert_id(connection, cursor, table_name, id_column):
    """
    Get the ID generated by the latest INSERT.

    MySQL uses cursor.lastrowid.
    PostgreSQL reads the current value of the table's identity sequence.
    """
    if not is_postgresql_connection(connection):
        return cursor.lastrowid

    if _ALLOWED_ID_COLUMNS.get(table_name) != id_column:
        raise ValueError("Unsupported table or ID column for generated ID lookup.")

    cursor.execute(
        "SELECT currval(pg_get_serial_sequence(%s, %s)::regclass) AS inserted_id",
        (table_name, id_column),
    )

    row = cursor.fetchone()

    if row is None or row["inserted_id"] is None:
        raise RuntimeError(
            f"Could not retrieve the generated ID for {table_name}.{id_column}."
        )

    return row["inserted_id"]


def begin_transaction(connection):
    """
    Start a transaction on MySQL.

    Psycopg 3 starts a transaction automatically when the first SQL
    statement runs, because autocommit is disabled by default.
    """
    if not is_postgresql_connection(connection):
        connection.begin()

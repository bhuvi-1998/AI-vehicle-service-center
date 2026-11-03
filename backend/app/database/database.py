
import os

import pymysql
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """
    Return a database connection based on DB_DRIVER.

    Supported drivers:
        mysql       - Local MySQL development
        postgresql  - Supabase PostgreSQL production
    """

    driver = os.getenv("DB_DRIVER", "mysql").strip().lower()

    db_password = os.getenv("DB_PASSWORD")

    if db_password is None:
        raise RuntimeError(
            "DB_PASSWORD is missing from the project .env file."
        )

    # --------------------------------------------------
    # MYSQL CONNECTION
    # --------------------------------------------------

    if driver in ("mysql", "mariadb"):

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

    # --------------------------------------------------
    # POSTGRESQL CONNECTION (SUPABASE)
    # --------------------------------------------------

    if driver in ("postgres", "postgresql", "psycopg"):

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires Psycopg 3. "
                "Install it using: "
                "python -m pip install 'psycopg[binary]>=3.2,<4'"
            ) from exc

        required_variables = [
            "DB_HOST",
            "DB_USER",
            "DB_NAME"
        ]

        missing = [
            name for name in required_variables
            if not os.getenv(name)
        ]

        if missing:
            raise RuntimeError(
                "Missing PostgreSQL configuration: "
                + ", ".join(missing)
            )

        return psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER"),
            password=db_password,
            dbname=os.getenv("DB_NAME"),
            sslmode=os.getenv("DB_SSLMODE", "require"),
            connect_timeout=10,
            row_factory=dict_row
        )

    raise RuntimeError(
        "Unsupported DB_DRIVER. Use 'mysql' or 'postgresql'."
    )

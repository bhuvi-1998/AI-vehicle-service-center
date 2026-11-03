
import os

import pymysql
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    db_password = os.getenv("DB_PASSWORD")

    if db_password is None:
        raise RuntimeError(
            "DB_PASSWORD is missing from the project .env file."
        )

    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=db_password,
        database=os.getenv(
            "DB_NAME",
            "vehicle_service_center"
        ),
        cursorclass=pymysql.cursors.DictCursor
    )

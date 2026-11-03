
from fastapi import APIRouter, HTTPException

from backend.app.database.database import get_connection


router = APIRouter(
    prefix="/public",
    tags=["Public Services"]
)


@router.get("/services")
def get_public_services():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    service_id,
                    service_name,
                    description,
                    price
                FROM services
                ORDER BY service_name
                """
            )

            return cursor.fetchall()

    except Exception as error:

        print("Public services error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to load available services."
        )

    finally:
        connection.close()

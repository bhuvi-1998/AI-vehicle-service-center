from backend.app.database.database import get_connection, get_last_insert_id


def create_service(service):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO services (
                    service_name,
                    description,
                    price,
                    vehicle_type
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    service.service_name,
                    service.description,
                    service.price,
                    service.vehicle_type,
                ),
            )

            service_id = get_last_insert_id(connection, cursor, "services", "service_id")

        connection.commit()
        return service_id

    finally:
        connection.close()


def get_all_services():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    service_id,
                    service_name,
                    description,
                    price,
                    vehicle_type
                FROM services
                ORDER BY service_id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_service(service_id, service):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE services
                SET
                    service_name = %s,
                    description = %s,
                    price = %s,
                    vehicle_type = %s
                WHERE service_id = %s
                """,
                (
                    service.service_name,
                    service.description,
                    service.price,
                    service.vehicle_type,
                    service_id,
                ),
            )

            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    finally:
        connection.close()


def delete_service(service_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM services WHERE service_id = %s",
                (service_id,),
            )

            deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    finally:
        connection.close()
from backend.app.database.database import get_connection, get_last_insert_id


def create_technician(technician):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO technicians (
                    technician_name,
                    phone,
                    specialization,
                    experience,
                    vehicle_type
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    technician.technician_name,
                    technician.phone,
                    technician.specialization,
                    technician.experience,
                    technician.vehicle_type,
                ),
            )

            technician_id = get_last_insert_id(connection, cursor, "technicians", "technician_id")

        connection.commit()
        return technician_id

    finally:
        connection.close()


def get_all_technicians():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    technician_id,
                    technician_name,
                    phone,
                    specialization,
                    experience,
                    vehicle_type
                FROM technicians
                ORDER BY technician_id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_technician(technician_id, technician):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE technicians
                SET
                    technician_name = %s,
                    phone = %s,
                    specialization = %s,
                    experience = %s,
                    vehicle_type = %s
                WHERE technician_id = %s
                """,
                (
                    technician.technician_name,
                    technician.phone,
                    technician.specialization,
                    technician.experience,
                    technician.vehicle_type,
                    technician_id,
                ),
            )

            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    finally:
        connection.close()


def delete_technician(technician_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM technicians WHERE technician_id = %s",
                (technician_id,),
            )

            deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    finally:
        connection.close()
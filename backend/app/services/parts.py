from backend.app.database.database import get_connection


def create_part(part):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO parts (
                    part_name,
                    part_number,
                    quantity,
                    price,
                    vehicle_type
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    part.part_name,
                    part.part_number,
                    part.quantity,
                    part.price,
                    part.vehicle_type,
                ),
            )

            part_id = cursor.lastrowid

        connection.commit()
        return part_id

    finally:
        connection.close()


def get_all_parts():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    part_id,
                    part_name,
                    part_number,
                    quantity,
                    price,
                    vehicle_type
                FROM parts
                ORDER BY part_id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_part(part_id, part):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE parts
                SET
                    part_name = %s,
                    part_number = %s,
                    quantity = %s,
                    price = %s,
                    vehicle_type = %s
                WHERE part_id = %s
                """,
                (
                    part.part_name,
                    part.part_number,
                    part.quantity,
                    part.price,
                    part.vehicle_type,
                    part_id,
                ),
            )

            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    finally:
        connection.close()


def delete_part(part_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM parts WHERE part_id = %s",
                (part_id,),
            )

            deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    finally:
        connection.close()
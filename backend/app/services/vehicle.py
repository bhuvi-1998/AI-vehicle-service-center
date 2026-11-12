from backend.app.database.database import get_connection, get_last_insert_id


def create_vehicle(vehicle):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vehicles (
                    customer_id,
                    vehicle_number,
                    brand,
                    model,
                    manufacture_year,
                    vehicle_type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    vehicle.customer_id,
                    vehicle.vehicle_number,
                    vehicle.brand,
                    vehicle.model,
                    vehicle.manufacture_year,
                    vehicle.vehicle_type,
                ),
            )

            vehicle_id = get_last_insert_id(connection, cursor, "vehicles", "vehicle_id")

        connection.commit()
        return vehicle_id

    finally:
        connection.close()


def get_all_vehicles():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    vehicle_id,
                    customer_id,
                    vehicle_number,
                    brand,
                    model,
                    manufacture_year,
                    vehicle_type
                FROM vehicles
                ORDER BY vehicle_id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_vehicle(vehicle_id, vehicle):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE vehicles
                SET
                    customer_id = %s,
                    vehicle_number = %s,
                    brand = %s,
                    model = %s,
                    manufacture_year = %s,
                    vehicle_type = %s
                WHERE vehicle_id = %s
                """,
                (
                    vehicle.customer_id,
                    vehicle.vehicle_number,
                    vehicle.brand,
                    vehicle.model,
                    vehicle.manufacture_year,
                    vehicle.vehicle_type,
                    vehicle_id,
                ),
            )

            updated = cursor.rowcount > 0

        connection.commit()
        return updated

    finally:
        connection.close()


def delete_vehicle(vehicle_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM vehicles WHERE vehicle_id = %s",
                (vehicle_id,),
            )

            deleted = cursor.rowcount > 0

        connection.commit()
        return deleted

    finally:
        connection.close()
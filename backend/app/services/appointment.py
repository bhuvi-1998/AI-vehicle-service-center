from backend.app.database.database import get_connection


def create_appointment(appointment):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT vehicle_id
                FROM vehicles
                WHERE vehicle_id = %s
                AND customer_id = %s
                """,
                (
                    appointment.vehicle_id,
                    appointment.customer_id
                )
            )

            vehicle = cursor.fetchone()

            if not vehicle:
                raise ValueError(
                    "The selected vehicle does not belong to the selected customer."
                )


            cursor.execute(
                """
                SELECT service_id
                FROM services
                WHERE service_id = %s
                """,
                (appointment.service_id,)
            )

            service = cursor.fetchone()

            if not service:
                raise ValueError(
                    "Selected service does not exist."
                )


            if appointment.technician_id is not None:

                cursor.execute(
                    """
                    SELECT technician_id
                    FROM technicians
                    WHERE technician_id = %s
                    """,
                    (appointment.technician_id,)
                )

                technician = cursor.fetchone()

                if not technician:
                    raise ValueError(
                        "Selected technician does not exist."
                    )


            sql = """
                INSERT INTO appointments
                (
                    customer_id,
                    vehicle_id,
                    service_id,
                    technician_id,
                    appointment_date,
                    appointment_time
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (
                    appointment.customer_id,
                    appointment.vehicle_id,
                    appointment.service_id,
                    appointment.technician_id,
                    appointment.appointment_date,
                    appointment.appointment_time
                )
            )

            appointment_id = cursor.lastrowid

        connection.commit()

        return appointment_id

    finally:
        connection.close()


def get_all_appointments():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.customer_id,
                    c.customer_name,
                    a.vehicle_id,
                    v.vehicle_number,
                    v.brand,
                    v.model,
                    a.service_id,
                    s.service_name,
                    s.price,
                    a.technician_id,
                    t.technician_name,
                    a.appointment_date,
                    a.appointment_time,
                    a.status

                FROM appointments a

                INNER JOIN customers c
                    ON a.customer_id = c.customer_id

                INNER JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id

                INNER JOIN services s
                    ON a.service_id = s.service_id

                LEFT JOIN technicians t
                    ON a.technician_id = t.technician_id

                ORDER BY
                    a.appointment_date,
                    a.appointment_time
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_appointment(
    appointment_id,
    appointment
):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT vehicle_id
                FROM vehicles
                WHERE vehicle_id = %s
                AND customer_id = %s
                """,
                (
                    appointment.vehicle_id,
                    appointment.customer_id
                )
            )

            vehicle = cursor.fetchone()

            if not vehicle:
                raise ValueError(
                    "The selected vehicle does not belong to the selected customer."
                )


            sql = """
                UPDATE appointments

                SET
                    customer_id = %s,
                    vehicle_id = %s,
                    service_id = %s,
                    technician_id = %s,
                    appointment_date = %s,
                    appointment_time = %s,
                    status = %s

                WHERE appointment_id = %s
            """

            cursor.execute(
                sql,
                (
                    appointment.customer_id,
                    appointment.vehicle_id,
                    appointment.service_id,
                    appointment.technician_id,
                    appointment.appointment_date,
                    appointment.appointment_time,
                    appointment.status,
                    appointment_id
                )
            )

            updated = cursor.rowcount > 0

        connection.commit()

        return updated

    finally:
        connection.close()


def delete_appointment(appointment_id):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM appointments
                WHERE appointment_id = %s
                """,
                (appointment_id,)
            )

            deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    finally:
        connection.close()
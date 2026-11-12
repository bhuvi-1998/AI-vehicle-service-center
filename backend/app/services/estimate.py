from decimal import Decimal, ROUND_HALF_UP

from backend.app.database.database import (
    begin_transaction,
    get_connection,
    get_last_insert_id,
)


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def create_estimate(data):

    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    s.service_name,
                    s.price
                FROM appointments a
                JOIN services s
                    ON a.service_id = s.service_id
                WHERE a.appointment_id = %s
                """,
                (data.appointment_id,)
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise LookupError(
                    "Appointment not found."
                )

            service_amount = money(appointment["price"])
            parts_amount = Decimal("0.00")
            selected_parts = []
            used_part_ids = set()

            for item in data.parts:

                if item.part_id in used_part_ids:
                    raise ValueError(
                        "Select each part only once."
                    )

                used_part_ids.add(item.part_id)

                cursor.execute(
                    """
                    SELECT
                        part_id,
                        part_name,
                        part_number,
                        price
                    FROM parts
                    WHERE part_id = %s
                    """,
                    (item.part_id,)
                )

                part = cursor.fetchone()

                if not part:
                    raise LookupError(
                        f"Part ID {item.part_id} was not found."
                    )

                unit_price = money(part["price"])

                line_total = money(
                    unit_price * item.quantity
                )

                parts_amount += line_total

                selected_parts.append({
                    "part_id": part["part_id"],
                    "part_name": part["part_name"],
                    "part_number": part["part_number"],
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "line_total": line_total
                })

            total_amount = money(
                service_amount + parts_amount
            )

            cursor.execute(
                """
                INSERT INTO estimates (
                    appointment_id,
                    service_name,
                    service_amount,
                    parts_amount,
                    total_amount,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    data.appointment_id,
                    appointment["service_name"],
                    service_amount,
                    parts_amount,
                    total_amount,
                    data.notes.strip() if data.notes else None
                )
            )

            estimate_id = get_last_insert_id(connection, cursor, "estimates", "estimate_id")

            for part in selected_parts:

                cursor.execute(
                    """
                    INSERT INTO estimate_parts (
                        estimate_id,
                        part_id,
                        part_name,
                        part_number,
                        quantity,
                        unit_price,
                        line_total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        estimate_id,
                        part["part_id"],
                        part["part_name"],
                        part["part_number"],
                        part["quantity"],
                        part["unit_price"],
                        part["line_total"]
                    )
                )

        connection.commit()

        return estimate_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_all_estimates():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    e.estimate_id,
                    e.appointment_id,
                    e.estimate_date,
                    e.service_amount,
                    e.parts_amount,
                    e.total_amount,
                    c.customer_name,
                    v.vehicle_number
                FROM estimates e
                JOIN appointments a
                    ON e.appointment_id = a.appointment_id
                JOIN customers c
                    ON a.customer_id = c.customer_id
                JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                ORDER BY e.estimate_id DESC
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_estimate_details(estimate_id):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    e.estimate_id,
                    e.appointment_id,
                    e.estimate_date,
                    e.service_name,
                    e.service_amount,
                    e.parts_amount,
                    e.total_amount,
                    e.notes,
                    a.appointment_date,
                    a.appointment_time,
                    c.customer_name,
                    c.phone AS customer_phone,
                    c.email AS customer_email,
                    c.address AS customer_address,
                    v.vehicle_number,
                    v.brand,
                    v.model
                FROM estimates e
                JOIN appointments a
                    ON e.appointment_id = a.appointment_id
                JOIN customers c
                    ON a.customer_id = c.customer_id
                JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                WHERE e.estimate_id = %s
                """,
                (estimate_id,)
            )

            estimate = cursor.fetchone()

            if not estimate:
                return None

            cursor.execute(
                """
                SELECT
                    part_id,
                    part_name,
                    part_number,
                    quantity,
                    unit_price,
                    line_total
                FROM estimate_parts
                WHERE estimate_id = %s
                ORDER BY estimate_part_id
                """,
                (estimate_id,)
            )

            estimate["parts"] = cursor.fetchall()

            return estimate

    finally:
        connection.close()
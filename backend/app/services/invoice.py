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


def create_invoice(data):

    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:

            # The appointment must exist and be completed.
            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.status,
                    s.service_name,
                    s.price
                FROM appointments a
                JOIN services s
                    ON a.service_id = s.service_id
                WHERE a.appointment_id = %s
                FOR UPDATE
                """,
                (data.appointment_id,)
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise LookupError("Appointment not found.")

            if str(appointment["status"]).strip().lower() != "completed":
                raise ValueError(
                    "Complete the appointment before generating the final bill."
                )

            # Only one final invoice is allowed per appointment.
            cursor.execute(
                """
                SELECT invoice_id
                FROM invoices
                WHERE appointment_id = %s
                """,
                (data.appointment_id,)
            )

            if cursor.fetchone():
                raise ValueError(
                    "A final invoice already exists for this appointment."
                )

            service_amount = money(appointment["price"])
            parts_amount = Decimal("0.00")
            selected_parts = []
            used_part_ids = set()

            # Fetch actual part prices and lock stock rows.
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
                        quantity,
                        price
                    FROM parts
                    WHERE part_id = %s
                    FOR UPDATE
                    """,
                    (item.part_id,)
                )

                part = cursor.fetchone()

                if not part:
                    raise LookupError(
                        f"Part ID {item.part_id} was not found."
                    )

                if part["quantity"] < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for {part['part_name']}. "
                        f"Available quantity: {part['quantity']}."
                    )

                unit_price = money(part["price"])
                line_total = money(unit_price * item.quantity)

                parts_amount += line_total

                selected_parts.append({
                    "part_id": part["part_id"],
                    "part_name": part["part_name"],
                    "part_number": part["part_number"],
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "line_total": line_total
                })

            parts_amount = money(parts_amount)
            subtotal = money(service_amount + parts_amount)
            discount_amount = money(data.discount_amount)

            if discount_amount > subtotal:
                raise ValueError(
                    "Discount cannot exceed the subtotal."
                )

            total_amount = money(subtotal - discount_amount)

            # Save the final invoice.
            cursor.execute(
                """
                INSERT INTO invoices (
                    appointment_id,
                    service_name,
                    service_amount,
                    parts_amount,
                    discount_amount,
                    total_amount,
                    payment_status,
                    payment_method,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data.appointment_id,
                    appointment["service_name"],
                    service_amount,
                    parts_amount,
                    discount_amount,
                    total_amount,
                    "Pending",
                    None,
                    data.notes.strip() if data.notes else None
                )
            )

            invoice_id = get_last_insert_id(connection, cursor, "invoices", "invoice_id")

            # Save part details and deduct the actual stock used.
            for part in selected_parts:

                cursor.execute(
                    """
                    INSERT INTO invoice_parts (
                        invoice_id,
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
                        invoice_id,
                        part["part_id"],
                        part["part_name"],
                        part["part_number"],
                        part["quantity"],
                        part["unit_price"],
                        part["line_total"]
                    )
                )

                cursor.execute(
                    """
                    UPDATE parts
                    SET quantity = quantity - %s
                    WHERE part_id = %s
                      AND quantity >= %s
                    """,
                    (
                        part["quantity"],
                        part["part_id"],
                        part["quantity"]
                    )
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"Unable to update stock for {part['part_name']}."
                    )

        connection.commit()

        return invoice_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_all_invoices():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    i.invoice_id,
                    i.appointment_id,
                    i.invoice_date,
                    i.service_amount,
                    i.parts_amount,
                    i.discount_amount,
                    i.total_amount,
                    i.payment_status,
                    i.payment_method,
                    c.customer_name,
                    v.vehicle_number
                FROM invoices i
                JOIN appointments a
                    ON i.appointment_id = a.appointment_id
                JOIN customers c
                    ON a.customer_id = c.customer_id
                JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                ORDER BY i.invoice_id DESC
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_invoice_details(invoice_id):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    i.invoice_id,
                    i.appointment_id,
                    i.invoice_date,
                    i.service_name,
                    i.service_amount,
                    i.parts_amount,
                    i.discount_amount,
                    i.total_amount,
                    i.payment_status,
                    i.payment_method,
                    i.notes,
                    a.appointment_date,
                    a.appointment_time,
                    c.customer_name,
                    c.phone AS customer_phone,
                    c.email AS customer_email,
                    c.address AS customer_address,
                    v.vehicle_number,
                    v.brand,
                    v.model
                FROM invoices i
                JOIN appointments a
                    ON i.appointment_id = a.appointment_id
                JOIN customers c
                    ON a.customer_id = c.customer_id
                JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                WHERE i.invoice_id = %s
                """,
                (invoice_id,)
            )

            invoice = cursor.fetchone()

            if not invoice:
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
                FROM invoice_parts
                WHERE invoice_id = %s
                ORDER BY invoice_part_id
                """,
                (invoice_id,)
            )

            invoice["parts"] = cursor.fetchall()

            return invoice

    finally:
        connection.close()


def mark_invoice_paid(invoice_id, payment_method):

    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT payment_status
                FROM invoices
                WHERE invoice_id = %s
                FOR UPDATE
                """,
                (invoice_id,)
            )

            invoice = cursor.fetchone()

            if not invoice:
                raise LookupError("Invoice not found.")

            if invoice["payment_status"] == "Paid":
                raise ValueError(
                    "This invoice is already marked as paid."
                )

            cursor.execute(
                """
                UPDATE invoices
                SET payment_status = 'Paid',
                    payment_method = %s
                WHERE invoice_id = %s
                """,
                (payment_method, invoice_id)
            )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
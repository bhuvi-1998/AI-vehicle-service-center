from backend.app.database.database import get_connection


def create_customer(customer):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                INSERT INTO customers
                (customer_name, phone, email, address)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (
                    customer.customer_name,
                    customer.phone,
                    customer.email,
                    customer.address
                )
            )

            customer_id = cursor.lastrowid

        connection.commit()

        return customer_id

    finally:
        connection.close()


def get_all_customers():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    customer_id,
                    customer_name,
                    phone,
                    email,
                    address
                FROM customers
                ORDER BY customer_id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def update_customer(customer_id, customer):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
                UPDATE customers
                SET
                    customer_name = %s,
                    phone = %s,
                    email = %s,
                    address = %s
                WHERE customer_id = %s
            """

            cursor.execute(
                sql,
                (
                    customer.customer_name,
                    customer.phone,
                    customer.email,
                    customer.address,
                    customer_id
                )
            )

            updated = cursor.rowcount > 0

        connection.commit()

        return updated

    finally:
        connection.close()


def delete_customer(customer_id):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "DELETE FROM customers WHERE customer_id = %s",
                (customer_id,)
            )

            deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    finally:
        connection.close()
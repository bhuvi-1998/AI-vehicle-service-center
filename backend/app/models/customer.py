from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.database.database import get_connection

router = APIRouter()


class Customer(BaseModel):
    customer_name: str
    phone: str
    email: str | None = None
    address: str | None = None


@router.post("/customers")
def add_customer(customer: Customer):

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

        connection.commit()

        return {
            "message": "Customer added successfully"
        }

    finally:
        connection.close()


@router.get("/customers")
def get_customers():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM customers ORDER BY customer_id")
            customers = cursor.fetchall()

        return customers

    finally:
        connection.close()
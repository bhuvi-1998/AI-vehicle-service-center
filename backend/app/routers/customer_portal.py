from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.database.database import (
    get_connection,
    get_last_insert_id,
    INTEGRITY_ERRORS,
)
from backend.app.security import get_current_customer

router = APIRouter(
    prefix="/customer-portal",
    tags=["Customer Portal"]
)


class VehicleInput(BaseModel):
    vehicle_number: str = Field(min_length=1, max_length=20)
    vehicle_type: Literal["Car", "Bike", "Superbike"] = "Car"
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    manufacture_year: int | None = Field(default=None, ge=1886, le=2100)


class AppointmentInput(BaseModel):
    vehicle_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    appointment_date: date
    appointment_time: str


@router.get("/vehicles")
def list_my_vehicles(
    customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT vehicle_id, vehicle_number,
                       COALESCE(vehicle_type, 'Car') AS vehicle_type,
                       brand, model, manufacture_year
                FROM vehicles
                WHERE customer_id = %s
                ORDER BY vehicle_id DESC
                """,
                (customer["customer_id"],)
            )

            return cursor.fetchall()

    finally:
        connection.close()


@router.post("/vehicles")
def add_my_vehicle(
    vehicle: VehicleInput,
    customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vehicles
                    (customer_id, vehicle_type, vehicle_number,
                     brand, model, manufacture_year)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    customer["customer_id"],
                    vehicle.vehicle_type,
                    vehicle.vehicle_number.strip().upper(),
                    vehicle.brand.strip(),
                    vehicle.model.strip(),
                    vehicle.manufacture_year
                )
            )

            vehicle_id = get_last_insert_id(connection, cursor, "vehicles", "vehicle_id")

        connection.commit()

        return {
            "message": "Vehicle added successfully",
            "vehicle_id": vehicle_id
        }

    except INTEGRITY_ERRORS:
        connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="That vehicle number is already registered."
        )

    finally:
        connection.close()


@router.get("/services")
def list_booking_services(
    customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT service_id, service_name, description,
                       COALESCE(vehicle_type, 'Car') AS vehicle_type,
                       price
                FROM services
                ORDER BY service_name
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


@router.post("/appointments")
def book_my_service(
    booking: AppointmentInput,
    customer: dict = Depends(get_current_customer)
):
    if booking.appointment_date < date.today():
        raise HTTPException(
            status_code=422,
            detail="The appointment date cannot be in the past."
        )

    try:
        from datetime import time as time_type

        appointment_time = time_type.fromisoformat(
            booking.appointment_time
        )

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Use a valid time, such as 10:30 or 10:30:00."
        )

    if (
        booking.appointment_date == date.today()
        and appointment_time <= datetime.now().time()
    ):
        raise HTTPException(
            status_code=422,
            detail="Choose a future appointment time."
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Check that the vehicle belongs to this customer.
            cursor.execute(
                """
                SELECT vehicle_id,
                       COALESCE(vehicle_type, 'Car') AS vehicle_type
                FROM vehicles
                WHERE vehicle_id = %s AND customer_id = %s
                """,
                (
                    booking.vehicle_id,
                    customer["customer_id"]
                )
            )

            vehicle = cursor.fetchone()

            if not vehicle:
                raise HTTPException(
                    status_code=404,
                    detail="Vehicle not found in your account."
                )

            # Check that the service exists.
            cursor.execute(
                """
                SELECT service_id,
                       COALESCE(vehicle_type, 'Car') AS vehicle_type
                FROM services
                WHERE service_id = %s
                """,
                (booking.service_id,)
            )

            service = cursor.fetchone()

            if not service:
                raise HTTPException(
                    status_code=404,
                    detail="Selected service was not found."
                )

            # Ensure the service matches the vehicle category.
            if service["vehicle_type"] not in (
                vehicle["vehicle_type"],
                "All"
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "The selected service is not available "
                        "for this vehicle category."
                    )
                )

            cursor.execute(
                """
                INSERT INTO appointments
                    (customer_id, vehicle_id, service_id,
                     appointment_date, appointment_time, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
                """,
                (
                    customer["customer_id"],
                    booking.vehicle_id,
                    booking.service_id,
                    booking.appointment_date,
                    appointment_time
                )
            )

            appointment_id = get_last_insert_id(connection, cursor, "appointments", "appointment_id")

        connection.commit()

        return {
            "message": "Service appointment booked successfully.",
            "appointment_id": appointment_id,
            "status": "Pending"
        }

    finally:
        connection.close()


@router.get("/appointments")
def list_my_appointments(
    customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT a.appointment_id, a.appointment_date,
                    TIME_FORMAT(
                        a.appointment_time, '%%H:%%i:%%s'
                    ) AS appointment_time,
                    a.status,
                    s.service_name, s.price,
                    v.vehicle_number, v.brand, v.model
                FROM appointments a
                JOIN services s
                    ON s.service_id = a.service_id
                JOIN vehicles v
                    ON v.vehicle_id = a.vehicle_id
                WHERE a.customer_id = %s
                ORDER BY
                    a.appointment_date DESC,
                    a.appointment_time DESC
                """,
                (customer["customer_id"],)
            )

            return cursor.fetchall()

    finally:
        connection.close()
# ------------------------------------------
# CUSTOMER APPOINTMENT CANCELLATION
# ------------------------------------------

@router.post("/appointments/{appointment_id}/cancel")
def cancel_my_appointment(
    appointment_id: int,
    customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT appointment_id, status
                FROM appointments
                WHERE appointment_id = %s
                  AND customer_id = %s
                FOR UPDATE
                """,
                (appointment_id, customer["customer_id"])
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found in your account."
                )

            current_status = str(
                appointment["status"]
            ).strip().lower()

            if current_status not in ("pending", "confirmed"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This appointment cannot be cancelled because "
                        "its service progress has already advanced."
                    )
                )

            cursor.execute(
                """
                UPDATE appointments
                SET status = 'Cancelled'
                WHERE appointment_id = %s
                  AND customer_id = %s
                  AND status IN ('Pending', 'Confirmed')
                """,
                (
                    appointment_id,
                    customer["customer_id"]
                )
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="The appointment could not be cancelled."
                )

        connection.commit()

        return {
            "message": "Appointment cancelled successfully.",
            "appointment_id": appointment_id,
            "status": "Cancelled"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ------------------------------------------
# CUSTOMER APPOINTMENT RESCHEDULING
# ------------------------------------------

class AppointmentRescheduleInput(BaseModel):
    appointment_date: date
    appointment_time: str = Field(min_length=1, max_length=8)


def validate_reschedule_datetime(
    appointment_date: date,
    appointment_time_text: str
):
    from datetime import time as time_type

    if appointment_date < date.today():
        raise HTTPException(
            status_code=422,
            detail="The appointment date cannot be in the past."
        )

    try:
        appointment_time = time_type.fromisoformat(
            appointment_time_text
        )

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Use a valid time, such as 10:30 or 10:30:00."
        )

    if (
        appointment_date == date.today()
        and appointment_time <= datetime.now().time()
    ):
        raise HTTPException(
            status_code=422,
            detail="Choose a future appointment time."
        )

    return appointment_time


@router.put("/appointments/{appointment_id}/reschedule")
def reschedule_my_appointment(
    appointment_id: int,
    booking: AppointmentRescheduleInput,
    customer: dict = Depends(get_current_customer)
):
    appointment_time = validate_reschedule_datetime(
        booking.appointment_date,
        booking.appointment_time
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT appointment_id, status
                FROM appointments
                WHERE appointment_id = %s
                  AND customer_id = %s
                FOR UPDATE
                """,
                (appointment_id, customer["customer_id"])
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found in your account."
                )

            current_status = str(
                appointment["status"]
            ).strip().lower()

            if current_status not in ("pending", "confirmed"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This appointment cannot be rescheduled because "
                        "its service progress has already advanced."
                    )
                )

            cursor.execute(
                """
                UPDATE appointments
                SET appointment_date = %s,
                    appointment_time = %s
                WHERE appointment_id = %s
                  AND customer_id = %s
                  AND status IN ('Pending', 'Confirmed')
                """,
                (
                    booking.appointment_date,
                    appointment_time,
                    appointment_id,
                    customer["customer_id"]
                )
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="The appointment could not be rescheduled."
                )

        connection.commit()

        return {
            "message": "Appointment rescheduled successfully.",
            "appointment_id": appointment_id,
            "appointment_date": booking.appointment_date.isoformat(),
            "appointment_time": appointment_time.isoformat(),
            "status": appointment["status"]
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

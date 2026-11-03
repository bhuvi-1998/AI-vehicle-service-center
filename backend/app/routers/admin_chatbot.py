import re
import requests

from datetime import date, datetime, time, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.security import get_current_admin
from backend.app.schemas.appointment import RepairStatus
from backend.app.database.database import begin_transaction, get_connection

from backend.app.services.appointment import get_all_appointments
from backend.app.services.customer import get_all_customers
from backend.app.services.vehicle import get_all_vehicles
from backend.app.services.service import get_all_services
from backend.app.services.technician import get_all_technicians
from backend.app.services.parts import get_all_parts
from backend.app.services.estimate import get_all_estimates
from backend.app.services.invoice import get_all_invoices


router = APIRouter(
    prefix="/admin-chatbot",
    tags=["Admin AI Assistant"]
)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


class AdminChatbotMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)



ALLOWED_STATUS_TRANSITIONS = {
    "Pending": {"Confirmed", "Cancelled"},
    "Confirmed": {"Vehicle Received", "Cancelled"},
    "Vehicle Received": {"In Progress"},
    "In Progress": {"Ready for Pickup"},
    "Ready for Pickup": {"Completed"},
    "Completed": set(),
    "Cancelled": set()
}


class AdminAppointmentStatusUpdate(BaseModel):
    status: RepairStatus


class AdminTechnicianAssignment(BaseModel):
    technician_id: int = Field(gt=0)


class AdminStockAdjustment(BaseModel):
    operation: str = Field(min_length=3, max_length=6)
    quantity: int = Field(gt=0)


class AdminAppointmentReschedule(BaseModel):
    appointment_date: date
    appointment_time: time

def display(value):
    if value is None:
        return "-"

    # PyMySQL can return MySQL TIME columns as timedelta.
    if hasattr(value, "total_seconds"):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def money(value):
    if value is None:
        return "-"

    try:
        return f"INR {float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def search_term(query, ignored_words):
    words = re.sub(
        r"[^a-z0-9@+._-]",
        " ",
        query.lower()
    ).split()

    return " ".join(
        word for word in words
        if word not in ignored_words
    )


def render_rows(title, rows, formatter, maximum=15):
    if not rows:
        return f"No matching {title.lower()} found."

    lines = [
        formatter(row)
        for row in rows[:maximum]
    ]

    result = (
        f"Found {len(rows)} {title.lower()}:\n\n"
        + "\n".join(lines)
    )

    if len(rows) > maximum:
        result += (
            f"\n\nShowing the first {maximum} records "
            f"out of {len(rows)}."
        )

    return result


def appointment_reply(query):
    rows = get_all_appointments()

    if "today" in query:
        today = date.today().isoformat()

        rows = [
            row for row in rows
            if display(row.get("appointment_date")) == today
        ]

    statuses = [
        "ready for pickup",
        "vehicle received",
        "in progress",
        "completed",
        "cancelled",
        "confirmed",
        "pending"
    ]

    selected_status = next(
        (status for status in statuses if status in query),
        None
    )

    if selected_status:
        rows = [
            row for row in rows
            if str(row.get("status", "")).lower()
            == selected_status
        ]

    id_match = re.search(
        r"\bappointment(?:\s+id)?\s*#?\s*(\d+)\b",
        query
    )

    if id_match:
        appointment_id = int(id_match.group(1))

        rows = [
            row for row in rows
            if int(row["appointment_id"]) == appointment_id
        ]

    return render_rows(
        "appointment(s)",
        rows,
        lambda row: (
            f"Appointment #{row['appointment_id']}\n"
            f"Customer: {row['customer_name']}\n"
            f"Vehicle: {row['vehicle_number']} - "
            f"{row['brand']} {row['model']}\n"
            f"Service: {row['service_name']}\n"
            f"Date: {display(row['appointment_date'])} "
            f"at {display(row['appointment_time'])}\n"
            f"Status: {row['status']}\n"
            f"Price: {money(row['price'])}\n"
            f"Technician: {row.get('technician_name') or 'Unassigned'}"
        )
    )


def customer_reply(query):
    rows = get_all_customers()

    ignored = {
        "find", "search", "show", "list", "display", "get",
        "lookup", "look", "up", "customer", "customers",
        "details", "detail", "information", "info",
        "name", "phone", "email", "for", "by", "with",
        "all", "the", "please", "of", "is", "a", "an"
    }

    term = search_term(query, ignored)

    if term:
        rows = [
            row for row in rows
            if term in str(row.get("customer_name", "")).lower()
            or term in str(row.get("phone", "")).lower()
            or term in str(row.get("email", "")).lower()
        ]
    elif "all" not in query and not re.search(
        r"\b(show|list|display)\s+customers?\b",
        query
    ):
        return (
            "Please provide a customer name, phone number or email "
            "so I can search for the correct customer. "
            "You can also ask to show all customers."
        )

    return render_rows(
        "customer(s)",
        rows,
        lambda row: (
            f"Customer ID: {row['customer_id']}\n"
            f"Name: {row['customer_name']}\n"
            f"Phone: {row.get('phone') or '-'}\n"
            f"Email: {row.get('email') or '-'}"
        )
    )


def vehicle_reply(query):
    rows = get_all_vehicles()

    ignored = {
        "find", "search", "show", "list", "display", "get",
        "lookup", "look", "up", "vehicle", "vehicles",
        "registration", "number", "details", "detail",
        "for", "by", "with", "all", "the", "please",
        "information", "info"
    }

    term = search_term(query, ignored)

    if term:
        rows = [
            row for row in rows
            if term in str(row.get("vehicle_number", "")).lower()
            or term in str(row.get("brand", "")).lower()
            or term in str(row.get("model", "")).lower()
            or term in str(row.get("vehicle_type", "")).lower()
        ]

    return render_rows(
        "vehicle(s)",
        rows,
        lambda row: (
            f"Vehicle ID: {row['vehicle_id']}\n"
            f"Customer ID: {row['customer_id']}\n"
            f"Registration: {row['vehicle_number']}\n"
            f"Vehicle: {row['brand']} {row['model']}\n"
            f"Category: {row.get('vehicle_type') or '-'}\n"
            f"Manufacture year: {row.get('manufacture_year') or '-'}"
        )
    )


def services_reply():
    rows = get_all_services()

    return render_rows(
        "service(s)",
        rows,
        lambda row: (
            f"Service ID: {row['service_id']}\n"
            f"Service: {row['service_name']}\n"
            f"Vehicle category: {row.get('vehicle_type') or 'Car'}\n"
            f"Price: {money(row['price'])}\n"
            f"Description: {row.get('description') or '-'}"
        )
    )


def technicians_reply():
    rows = get_all_technicians()

    return render_rows(
        "technician(s)",
        rows,
        lambda row: (
            f"Technician ID: {row['technician_id']}\n"
            f"Name: {row['technician_name']}\n"
            f"Phone: {row.get('phone') or '-'}\n"
            f"Specialization: {row.get('specialization') or '-'}\n"
            f"Experience: {row.get('experience') or '-'}\n"
            f"Vehicle category: {row.get('vehicle_type') or '-'}"
        )
    )


def parts_reply(query):
    rows = get_all_parts()

    threshold = re.search(
        r"\b(?:below|under|less than)\s+(\d+)\b",
        query
    )

    if threshold:
        quantity_limit = int(threshold.group(1))

        rows = [
            row for row in rows
            if int(row.get("quantity") or 0) < quantity_limit
        ]

    return render_rows(
        "part(s)",
        rows,
        lambda row: (
            f"Part ID: {row['part_id']}\n"
            f"Part: {row['part_name']}\n"
            f"Part number: {row.get('part_number') or '-'}\n"
            f"Available quantity: {row['quantity']}\n"
            f"Price: {money(row['price'])}\n"
            f"Vehicle category: {row.get('vehicle_type') or '-'}"
        )
    )


def estimate_reply(query):
    rows = get_all_estimates()

    id_match = re.search(
        r"\bestimate(?:\s+id)?\s*#?\s*(\d+)\b",
        query
    )

    if id_match:
        estimate_id = int(id_match.group(1))

        rows = [
            row for row in rows
            if int(row["estimate_id"]) == estimate_id
        ]

    return render_rows(
        "estimate(s)",
        rows,
        lambda row: (
            f"Estimate ID: {row['estimate_id']}\n"
            f"Appointment ID: {row['appointment_id']}\n"
            f"Customer: {row['customer_name']}\n"
            f"Vehicle: {row['vehicle_number']}\n"
            f"Estimate date: {display(row['estimate_date'])}\n"
            f"Total: {money(row['total_amount'])}"
        )
    )


def invoice_reply(query):
    rows = get_all_invoices()

    if "paid" in query:
        rows = [
            row for row in rows
            if str(row.get("payment_status", "")).lower() == "paid"
        ]
    elif "pending" in query or "unpaid" in query:
        rows = [
            row for row in rows
            if str(row.get("payment_status", "")).lower() == "pending"
        ]

    id_match = re.search(
        r"\binvoice(?:\s+id)?\s*#?\s*(\d+)\b",
        query
    )

    if id_match:
        invoice_id = int(id_match.group(1))

        rows = [
            row for row in rows
            if int(row["invoice_id"]) == invoice_id
        ]

    return render_rows(
        "invoice(s)",
        rows,
        lambda row: (
            f"Invoice ID: {row['invoice_id']}\n"
            f"Appointment ID: {row['appointment_id']}\n"
            f"Customer: {row['customer_name']}\n"
            f"Vehicle: {row['vehicle_number']}\n"
            f"Invoice date: {display(row['invoice_date'])}\n"
            f"Total: {money(row['total_amount'])}\n"
            f"Payment status: {row['payment_status']}"
        )
    )




def business_report_reply():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(status = 'Pending') AS pending,
                    SUM(status = 'Confirmed') AS confirmed,
                    SUM(status = 'Vehicle Received') AS received,
                    SUM(status = 'In Progress') AS in_progress,
                    SUM(status = 'Ready for Pickup') AS ready,
                    SUM(status = 'Completed') AS completed,
                    SUM(status = 'Cancelled') AS cancelled
                FROM appointments
                """
            )
            appointments = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(
                        SUM(CASE WHEN payment_status = 'Paid'
                            THEN total_amount ELSE 0 END), 0
                    ) AS paid_revenue,
                    COALESCE(
                        SUM(CASE WHEN payment_status <> 'Paid'
                            THEN total_amount ELSE 0 END), 0
                    ) AS pending_amount,
                    SUM(payment_status = 'Paid') AS paid_count,
                    SUM(payment_status <> 'Paid') AS pending_count
                FROM invoices
                """
            )
            invoices = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_parts,
                    COALESCE(SUM(quantity), 0) AS total_units,
                    SUM(quantity = 0) AS out_of_stock
                FROM parts
                """
            )
            inventory = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total FROM customers")
            customers = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total FROM vehicles")
            vehicles = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total FROM technicians")
            technicians = cursor.fetchone() or {}

        return (
            "Vehicle Service Center Business Summary\n\n"
            f"Appointments: {appointments.get('total', 0)}\n"
            f"  Pending: {appointments.get('pending', 0) or 0}\n"
            f"  Confirmed: {appointments.get('confirmed', 0) or 0}\n"
            f"  Vehicle Received: {appointments.get('received', 0) or 0}\n"
            f"  In Progress: {appointments.get('in_progress', 0) or 0}\n"
            f"  Ready for Pickup: {appointments.get('ready', 0) or 0}\n"
            f"  Completed: {appointments.get('completed', 0) or 0}\n"
            f"  Cancelled: {appointments.get('cancelled', 0) or 0}\n\n"
            f"Customers: {customers.get('total', 0)}\n"
            f"Vehicles: {vehicles.get('total', 0)}\n"
            f"Technicians: {technicians.get('total', 0)}\n\n"
            f"Invoices: {invoices.get('total', 0)}\n"
            f"Paid invoices: {invoices.get('paid_count', 0) or 0}\n"
            f"Pending invoices: {invoices.get('pending_count', 0) or 0}\n"
            f"Collected revenue: {money(invoices.get('paid_revenue', 0))}\n"
            f"Pending invoice amount: {money(invoices.get('pending_amount', 0))}\n\n"
            f"Part types: {inventory.get('total_parts', 0)}\n"
            f"Total stock units: {inventory.get('total_units', 0)}\n"
            f"Out-of-stock part types: {inventory.get('out_of_stock', 0) or 0}"
        )

    finally:
        connection.close()


def get_admin_data_reply(message):
    query = message.lower()

    # Business reports must be checked before appointment-related routing.
    if any(term in query for term in (
        "business report", "business summary", "analytics",
        "dashboard summary", "overall report", "revenue report"
    )):
        return business_report_reply()

    # Appointment requests.
    if "appointment" in query or "booking" in query:
        return appointment_reply(query)

    # Customer requests.
    if "customer" in query:
        return customer_reply(query)

    # Vehicle requests.
    if "vehicle" in query or "registration" in query:
        return vehicle_reply(query)

    # Service requests.
    if "service" in query and "service center" not in query:
        return services_reply()

    # Technician requests.
    if "technician" in query or "mechanic" in query:
        return technicians_reply()

    # Inventory and spare parts.
    if (
        "part" in query
        or "inventory" in query
        or "stock" in query
    ):
        return parts_reply(query)

    # Estimate requests.
    if "estimate" in query:
        return estimate_reply(query)

    # Invoice and payment requests.
    if "invoice" in query or "payment" in query:
        return invoice_reply(query)

    return None


def ask_ollama(message):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an assistant for the administrator "
                            "of a vehicle service center. Answer general "
                            "questions about vehicle servicing, workshop "
                            "operations and customer service. Be friendly "
                            "and concise. You are operating in read-only "
                            "mode. Do not claim to access live database "
                            "records or to create, update, cancel, delete "
                            "or modify anything. Live administrative "
                            "records are retrieved separately by the "
                            "application."
                        )
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()
        reply = data.get("message", {}).get("content", "").strip()

        if not reply:
            raise HTTPException(
                status_code=502,
                detail="The AI assistant returned an empty response."
            )

        return reply

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="The local AI assistant is unavailable. Please try again."
        )


@router.post("/message")
def admin_chatbot_message(
    payload: AdminChatbotMessage,
    current_admin: dict = Depends(get_current_admin)
):
    try:
        reply = get_admin_data_reply(payload.message)

        if reply is None:
            reply = ask_ollama(payload.message)

        return {"reply": reply}

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve administrative information."
        )


# ------------------------------------------
# ADMIN APPOINTMENT STATUS UPDATE
# ------------------------------------------

@router.put("/appointments/{appointment_id}/status")
def update_admin_appointment_status(
    appointment_id: int,
    payload: AdminAppointmentStatusUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT appointment_id, status
                FROM appointments
                WHERE appointment_id = %s
                FOR UPDATE
                """,
                (appointment_id,)
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found."
                )

            current_status = appointment["status"]
            requested_status = payload.status

            # A repeated status request does not modify the database.
            if current_status == requested_status:
                connection.commit()

                return {
                    "message": "Appointment already has this status.",
                    "appointment_id": appointment_id,
                    "current_status": current_status,
                    "status": current_status,
                    "changed": False
                }

            allowed = ALLOWED_STATUS_TRANSITIONS.get(
                current_status,
                set()
            )

            if requested_status not in allowed:
                allowed_text = (
                    ", ".join(sorted(allowed))
                    if allowed
                    else "No further status changes are allowed"
                )

                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Cannot change appointment from "
                        f"{current_status} to {requested_status}. "
                        f"Allowed next status: {allowed_text}."
                    )
                )

            cursor.execute(
                """
                UPDATE appointments
                SET status = %s
                WHERE appointment_id = %s
                """,
                (requested_status, appointment_id)
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Appointment status was not updated."
                )

        connection.commit()

        return {
            "message": "Appointment status updated successfully.",
            "appointment_id": appointment_id,
            "previous_status": current_status,
            "status": requested_status,
            "changed": True
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update appointment status."
        )

    finally:
        connection.close()

# ------------------------------------------
# ADMIN APPOINTMENT TECHNICIAN ASSIGNMENT
# ------------------------------------------

@router.put("/appointments/{appointment_id}/technician")
def assign_admin_appointment_technician(
    appointment_id: int,
    payload: AdminTechnicianAssignment,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.status,
                    a.technician_id,
                    c.customer_name,
                    v.vehicle_number,
                    v.brand,
                    v.model,
                    v.vehicle_type,
                    s.service_name
                FROM appointments a
                INNER JOIN customers c
                    ON a.customer_id = c.customer_id
                INNER JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                INNER JOIN services s
                    ON a.service_id = s.service_id
                WHERE a.appointment_id = %s
                FOR UPDATE
                """,
                (appointment_id,)
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found."
                )

            if appointment["status"] in {"Completed", "Cancelled"}:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Cannot assign a technician to an appointment "
                        f"with status {appointment['status']}."
                    )
                )

            cursor.execute(
                """
                SELECT
                    technician_id,
                    technician_name,
                    specialization,
                    vehicle_type
                FROM technicians
                WHERE technician_id = %s
                FOR UPDATE
                """,
                (payload.technician_id,)
            )

            technician = cursor.fetchone()

            if not technician:
                raise HTTPException(
                    status_code=404,
                    detail="Technician not found."
                )

            vehicle_category = (
                appointment.get("vehicle_type") or ""
            ).strip()

            technician_category = (
                technician.get("vehicle_type") or "All"
            ).strip()

            if (
                technician_category.lower() != "all"
                and technician_category.lower() != vehicle_category.lower()
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Technician #{payload.technician_id} is assigned "
                        f"to {technician_category} vehicles and cannot "
                        f"be assigned to a {vehicle_category} vehicle."
                    )
                )

            if appointment["technician_id"] == payload.technician_id:
                connection.commit()

                return {
                    "message": "This technician is already assigned.",
                    "appointment_id": appointment_id,
                    "technician_id": payload.technician_id,
                    "technician_name": technician["technician_name"],
                    "status": appointment["status"],
                    "changed": False
                }

            cursor.execute(
                """
                UPDATE appointments
                SET technician_id = %s
                WHERE appointment_id = %s
                """,
                (payload.technician_id, appointment_id)
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Technician assignment was not updated."
                )

        connection.commit()

        return {
            "message": "Technician assigned successfully.",
            "appointment_id": appointment_id,
            "technician_id": payload.technician_id,
            "technician_name": technician["technician_name"],
            "status": appointment["status"],
            "changed": True
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to assign technician to appointment."
        )

    finally:
        connection.close()

# ------------------------------------------
# TECHNICIAN AVAILABILITY AND RECOMMENDATIONS
# ------------------------------------------

@router.get("/appointments/{appointment_id}/technician-recommendations")
def recommend_appointment_technicians(
    appointment_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.appointment_date,
                    a.appointment_time,
                    a.status,
                    s.service_name,
                    v.vehicle_type
                FROM appointments a
                INNER JOIN services s
                    ON a.service_id = s.service_id
                INNER JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                WHERE a.appointment_id = %s
                """,
                (appointment_id,)
            )
            appointment = cursor.fetchone()

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found."
            )

        if appointment["status"] in {"Completed", "Cancelled"}:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Appointment is {appointment['status']}; "
                    "technician recommendations are unavailable."
                )
            )

        technicians = get_all_technicians()
        appointments = get_all_appointments()

        appointment_date = display(appointment["appointment_date"])
        appointment_time = display(appointment["appointment_time"])
        vehicle_type = str(appointment["vehicle_type"]).strip()
        service_name = str(appointment["service_name"]).lower()
        service_compact = re.sub(r"[^a-z0-9]", "", service_name)

        recommendations = []

        for technician in technicians:
            technician_type = str(
                technician.get("vehicle_type") or "All"
            ).strip()

            compatible = (
                technician_type.lower() == "all"
                or technician_type.lower() == vehicle_type.lower()
            )

            if not compatible:
                continue

            busy = any(
                int(item["appointment_id"]) != appointment_id
                and item.get("technician_id") == technician["technician_id"]
                and display(item.get("appointment_date")) == appointment_date
                and display(item.get("appointment_time")) == appointment_time
                and item.get("status") not in {"Completed", "Cancelled"}
                for item in appointments
            )

            specialization = str(
                technician.get("specialization") or ""
            ).lower()
            specialization_compact = re.sub(
                r"[^a-z0-9]", "", specialization
            )

            service_match = bool(
                specialization_compact
                and (
                    specialization_compact in service_compact
                    or service_compact in specialization_compact
                )
            )

            recommendations.append({
                "technician_id": technician["technician_id"],
                "technician_name": technician["technician_name"],
                "vehicle_type": technician_type,
                "specialization": technician.get("specialization"),
                "experience": technician.get("experience"),
                "availability": "Busy" if busy else "Available",
                "matches_service": service_match
            })

        recommendations.sort(
            key=lambda item: (
                item["availability"] == "Busy",
                not item["matches_service"],
                -(item["experience"] or 0),
                item["technician_id"]
            )
        )

        return {
            "appointment_id": appointment_id,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "service_name": appointment["service_name"],
            "vehicle_type": vehicle_type,
            "recommendations": recommendations,
            "availability_scope": (
                "Busy means another active appointment is assigned "
                "to that technician at the exact same date and time. "
                "Appointment duration is not stored, so overlapping "
                "time ranges cannot be calculated."
            )
        }

    finally:
        connection.close()


# ------------------------------------------
# ADMIN SPARE-PARTS STOCK ADJUSTMENT
# ------------------------------------------

@router.post("/parts/{part_id}/stock")
def adjust_admin_part_stock(
    part_id: int,
    payload: AdminStockAdjustment,
    current_admin: dict = Depends(get_current_admin)
):
    operation = payload.operation.strip().lower()

    if operation not in {"add", "remove"}:
        raise HTTPException(
            status_code=422,
            detail="Operation must be 'add' or 'remove'."
        )

    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT part_id, part_name, quantity
                FROM parts
                WHERE part_id = %s
                FOR UPDATE
                """,
                (part_id,)
            )
            part = cursor.fetchone()

            if not part:
                raise HTTPException(
                    status_code=404,
                    detail="Part not found."
                )

            current_quantity = int(part["quantity"])

            if operation == "add":
                new_quantity = current_quantity + payload.quantity
            else:
                if payload.quantity > current_quantity:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Insufficient stock. Available quantity: "
                            f"{current_quantity}."
                        )
                    )
                new_quantity = current_quantity - payload.quantity

            cursor.execute(
                """
                UPDATE parts
                SET quantity = %s
                WHERE part_id = %s
                """,
                (new_quantity, part_id)
            )

        connection.commit()

        return {
            "message": "Stock updated successfully.",
            "part_id": part_id,
            "part_name": part["part_name"],
            "previous_quantity": current_quantity,
            "quantity": new_quantity,
            "operation": operation
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update part stock."
        )

    finally:
        connection.close()

# ------------------------------------------
# ADMIN APPOINTMENT RESCHEDULING
# ------------------------------------------

@router.put("/appointments/{appointment_id}/schedule")
def reschedule_admin_appointment(
    appointment_id: int,
    payload: AdminAppointmentReschedule,
    current_admin: dict = Depends(get_current_admin)
):
    connection = get_connection()

    try:
        begin_transaction(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.status,
                    a.technician_id,
                    a.appointment_date,
                    a.appointment_time,
                    c.customer_name,
                    v.vehicle_number,
                    v.brand,
                    v.model,
                    s.service_name,
                    t.technician_name
                FROM appointments a
                INNER JOIN customers c
                    ON a.customer_id = c.customer_id
                INNER JOIN vehicles v
                    ON a.vehicle_id = v.vehicle_id
                INNER JOIN services s
                    ON a.service_id = s.service_id
                LEFT JOIN technicians t
                    ON a.technician_id = t.technician_id
                WHERE a.appointment_id = %s
                FOR UPDATE
                """,
                (appointment_id,)
            )

            appointment = cursor.fetchone()

            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found."
                )

            if appointment["status"] in {"Completed", "Cancelled"}:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Cannot reschedule an appointment with "
                        f"status {appointment['status']}."
                    )
                )

            requested_datetime = datetime.combine(
                payload.appointment_date,
                payload.appointment_time
            )

            india_offset = timezone(timedelta(hours=5, minutes=30))
            current_datetime = datetime.now(india_offset).replace(
                tzinfo=None
            )

            if requested_datetime <= current_datetime:
                raise HTTPException(
                    status_code=400,
                    detail="The new appointment date and time must be in the future."
                )

            if (
                appointment["appointment_date"] == payload.appointment_date
                and appointment["appointment_time"] == payload.appointment_time
            ):
                connection.commit()

                return {
                    "message": "Appointment already has this date and time.",
                    "appointment_id": appointment_id,
                    "appointment_date": payload.appointment_date.isoformat(),
                    "appointment_time": payload.appointment_time.isoformat(),
                    "changed": False
                }

            # Check exact-time conflicts for the assigned technician.
            # Appointment duration is not stored by this application.
            technician_id = appointment["technician_id"]

            if technician_id is not None:
                cursor.execute(
                    """
                    SELECT appointment_id
                    FROM appointments
                    WHERE technician_id = %s
                      AND appointment_date = %s
                      AND appointment_time = %s
                      AND appointment_id <> %s
                      AND status NOT IN ('Completed', 'Cancelled')
                    FOR UPDATE
                    """,
                    (
                        technician_id,
                        payload.appointment_date,
                        payload.appointment_time,
                        appointment_id
                    )
                )

                conflict = cursor.fetchone()

                if conflict:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Technician {appointment['technician_name']} "
                            "already has another active appointment at "
                            "that exact date and time."
                        )
                    )

            cursor.execute(
                """
                UPDATE appointments
                SET appointment_date = %s,
                    appointment_time = %s
                WHERE appointment_id = %s
                """,
                (
                    payload.appointment_date,
                    payload.appointment_time,
                    appointment_id
                )
            )

        connection.commit()

        return {
            "message": "Appointment rescheduled successfully.",
            "appointment_id": appointment_id,
            "previous_date": display(appointment["appointment_date"]),
            "previous_time": display(appointment["appointment_time"]),
            "appointment_date": payload.appointment_date.isoformat(),
            "appointment_time": payload.appointment_time.isoformat(),
            "changed": True
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to reschedule appointment."
        )

    finally:
        connection.close()

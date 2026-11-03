
from datetime import date, time
from typing import Literal

from pydantic import BaseModel


RepairStatus = Literal[
    "Pending",
    "Confirmed",
    "Vehicle Received",
    "In Progress",
    "Ready for Pickup",
    "Completed",
    "Cancelled",
]


class AppointmentCreate(BaseModel):
    customer_id: int
    vehicle_id: int
    service_id: int
    technician_id: int | None = None
    appointment_date: date
    appointment_time: time


class AppointmentUpdate(BaseModel):
    customer_id: int
    vehicle_id: int
    service_id: int
    technician_id: int | None = None
    appointment_date: date
    appointment_time: time
    status: RepairStatus

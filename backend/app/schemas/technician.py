from typing import Literal
from pydantic import BaseModel

TechnicianCategory = Literal[
    "All",
    "Car",
    "Bike",
    "Superbike"
]


class TechnicianCreate(BaseModel):
    technician_name: str
    phone: str
    specialization: str | None = None
    experience: int | None = None
    vehicle_type: TechnicianCategory = "All"


class TechnicianUpdate(BaseModel):
    technician_name: str
    phone: str
    specialization: str | None = None
    experience: int | None = None
    vehicle_type: TechnicianCategory = "All"
from typing import Literal
from pydantic import BaseModel

ServiceCategory = Literal["Car", "Bike", "Superbike"]


class ServiceCreate(BaseModel):
    service_name: str
    description: str | None = None
    price: float
    vehicle_type: ServiceCategory = "Car"


class ServiceUpdate(BaseModel):
    service_name: str
    description: str | None = None
    price: float
    vehicle_type: ServiceCategory = "Car"
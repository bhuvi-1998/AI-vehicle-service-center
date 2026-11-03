from typing import Literal
from pydantic import BaseModel

VehicleCategory = Literal["Car", "Bike", "Superbike"]


class VehicleCreate(BaseModel):
    customer_id: int
    vehicle_number: str
    brand: str
    model: str
    manufacture_year: int | None = None
    vehicle_type: VehicleCategory = "Car"


class VehicleUpdate(BaseModel):
    customer_id: int
    vehicle_number: str
    brand: str
    model: str
    manufacture_year: int | None = None
    vehicle_type: VehicleCategory = "Car"
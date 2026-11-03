from typing import Literal
from pydantic import BaseModel

PartCategory = Literal[
    "All",
    "Car",
    "Bike",
    "Superbike"
]


class PartCreate(BaseModel):
    part_name: str
    part_number: str
    quantity: int
    price: float
    vehicle_type: PartCategory = "All"


class PartUpdate(BaseModel):
    part_name: str
    part_number: str
    quantity: int
    price: float
    vehicle_type: PartCategory = "All"
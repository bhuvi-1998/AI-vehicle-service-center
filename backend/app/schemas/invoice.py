from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class InvoicePartInput(BaseModel):
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class InvoiceCreate(BaseModel):
    appointment_id: int = Field(gt=0)
    parts: list[InvoicePartInput] = Field(default_factory=list)
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0
    )
    notes: str | None = None


class InvoicePaymentUpdate(BaseModel):
    payment_method: Literal[
        "Cash",
        "UPI",
        "Card",
        "Bank Transfer"
    ]
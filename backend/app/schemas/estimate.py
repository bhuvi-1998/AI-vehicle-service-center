from pydantic import BaseModel, Field


class EstimatePartInput(BaseModel):
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class EstimateCreate(BaseModel):
    appointment_id: int = Field(gt=0)
    parts: list[EstimatePartInput] = Field(default_factory=list)
    notes: str | None = None
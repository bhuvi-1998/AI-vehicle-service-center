from pydantic import BaseModel


class CustomerCreate(BaseModel):
    customer_name: str
    phone: str
    email: str | None = None
    address: str | None = None


class CustomerUpdate(BaseModel):
    customer_name: str
    phone: str
    email: str | None = None
    address: str | None = None
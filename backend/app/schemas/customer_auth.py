
from pydantic import BaseModel, Field


class CustomerRegister(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=15)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    address: str | None = None


class CustomerLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

class CustomerProfileUpdate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=15)
    email: str = Field(min_length=5, max_length=254)
    address: str | None = Field(default=None, max_length=500)
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128
    )
from pydantic import BaseModel, Field


class AdminCreate(BaseModel):
    admin_name: str
    email: str
    password: str


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminProfileUpdate(BaseModel):
    admin_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128
    )
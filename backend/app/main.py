import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from backend.app.database.database import close_database_pool, init_database_pool
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers.admin import router as admin_router
from backend.app.routers.customer import router as customer_router
from backend.app.routers.vehicle import router as vehicle_router
from backend.app.routers.service import router as service_router
from backend.app.routers.technician import router as technician_router
from backend.app.routers.appointment import router as appointment_router
from backend.app.routers.parts import router as parts_router
from backend.app.routers.estimate import router as estimate_router
from backend.app.routers.invoice import router as invoice_router
from backend.app.routers.public_services import (
    router as public_services_router
)
from backend.app.routers.customer_auth import (
    router as customer_auth_router
)
from backend.app.routers.customer_portal import (
    router as customer_portal_router
)
from backend.app.routers.password_reset import (
    router as password_reset_router
)


from backend.app.routers.chatbot_ai import router as chatbot_ai_router
from backend.app.routers.admin_chatbot import router as admin_chatbot_router

IS_PRODUCTION = (
    os.getenv("APP_ENV", "development").strip().lower() == "production"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open the PostgreSQL pool before accepting requests.
    init_database_pool()
    try:
        yield
    finally:
        # Return and close pooled connections at application shutdown.
        close_database_pool()


app = FastAPI(
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
    lifespan=lifespan,
)

# CORS origins:
# Use CORS_ORIGINS in production as comma-separated frontend URLs.
# If it is not configured, allow the local development addresses.
local_origins = [
    "http://127.0.0.1:5503",
    "http://localhost:5503",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

allowed_origins = configured_origins or local_origins



app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


app.include_router(admin_router)
app.include_router(customer_router)
app.include_router(vehicle_router)
app.include_router(service_router)
app.include_router(technician_router)
app.include_router(appointment_router)
app.include_router(parts_router)
app.include_router(estimate_router)
app.include_router(invoice_router)
app.include_router(public_services_router)
app.include_router(customer_portal_router)
app.include_router(customer_auth_router)
app.include_router(password_reset_router)
app.include_router(chatbot_ai_router)
app.include_router(admin_chatbot_router)
@app.get("/")
def home():
    return {
        "message": "Vehicle Service Center API"
    }

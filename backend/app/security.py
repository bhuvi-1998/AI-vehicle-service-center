import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.database.database import get_connection


load_dotenv()

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(admin_id: int, email: str, role: str):

    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is missing from .env")

    payload = {
        "sub": str(admin_id),
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=ALGORITHM
    )


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="Authentication is not configured on the server."
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=[ALGORITHM]
        )

        admin_id = int(payload["sub"])

        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required."
            )

    except HTTPException:
        raise

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Your login has expired or is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT admin_id, admin_name, email, role
                FROM admins
                WHERE admin_id = %s
                """,
                (admin_id,)
            )

            admin = cursor.fetchone()

        if not admin or admin["role"] != "admin":
            raise HTTPException(
                status_code=401,
                detail="Admin account not found or inactive.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return admin

    finally:
        connection.close()



def get_current_customer(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in to access your customer account.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="Authentication is not configured on the server."
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=[ALGORITHM]
        )

        customer_id = int(payload["sub"])

        if payload.get("role") != "customer":
            raise HTTPException(
                status_code=403,
                detail="Customer access required."
            )

    except HTTPException:
        raise

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Your login has expired or is invalid.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    customer_id,
                    customer_name,
                    phone,
                    email,
                    address,
                    email_verified
                FROM customers
                WHERE customer_id = %s
                """,
                (customer_id,)
            )

            customer = cursor.fetchone()

    finally:
        connection.close()

    if not customer:
        raise HTTPException(
            status_code=401,
            detail="Customer account not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not customer["email_verified"]:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before accessing your account."
        )

    return customer

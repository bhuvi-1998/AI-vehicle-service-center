
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymysql.err import IntegrityError

from backend.app.database.database import get_connection
from backend.app.rate_limit import rate_limit
from backend.app.schemas.customer_auth import (
    CustomerRegister,
    CustomerLogin,
    CustomerProfileUpdate,

)
from backend.app.services.admin import (
    hash_password,
    verify_password,
    password_needs_rehash,
)
from backend.app.services.email_verification import (
    create_verification_token,
    send_verification_email,
)
from backend.app.security import (
    create_access_token,
    get_current_customer,
)


router = APIRouter(
    prefix="/customer-auth",
    tags=["Customer Authentication"],
)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class ResendVerificationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)


def clear_verification_token(token_hash: str) -> None:
    """Clear a verification token that could not be delivered."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET verification_token_hash = NULL,
                    verification_expires_at = NULL
                WHERE verification_token_hash = %s
                  AND email_verified = 0
                """,
                (token_hash,),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# CUSTOMER REGISTRATION
# =========================================================

@router.post(
    "/register",
    dependencies=[
        Depends(rate_limit(5, 3600, "customer-register"))
    ],
)
def register_customer(customer: CustomerRegister):
    customer_name = customer.customer_name.strip()
    phone = customer.phone.strip()
    email = customer.email.strip().lower()
    address = customer.address.strip() if customer.address else None

    if not customer_name or not phone or not email:
        raise HTTPException(
            status_code=422,
            detail="Name, phone, and email are required.",
        )

    raw_token, token_hash, expires_at = create_verification_token()
    stored_password_hash = hash_password(customer.password)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO customers
                    (
                        customer_name,
                        phone,
                        email,
                        address,
                        password_hash,
                        email_verified,
                        verification_token_hash,
                        verification_expires_at
                    )
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s)
                """,
                (
                    customer_name,
                    phone,
                    email,
                    address,
                    stored_password_hash,
                    token_hash,
                    expires_at,
                ),
            )

            customer_id = cursor.lastrowid

        connection.commit()

    except IntegrityError:
        connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="That phone number or email may already be registered.",
        ) from None

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    # The account remains unverified until the customer clicks
    # the valid link sent to their email address.
    try:
        send_verification_email(email, raw_token)

    except Exception:
        # Do not leave a usable token that was not delivered.
        try:
            clear_verification_token(token_hash)
        except Exception:
            pass

        raise HTTPException(
            status_code=503,
            detail=(
                "Your account was created, but the verification email "
                "could not be sent. Check the email configuration and "
                "request a new verification email."
            ),
        ) from None

    return {
        "message": (
            "Registration successful. Check your email and click "
            "Verify My Email before logging in."
        ),
        "customer_id": customer_id,
    }


# =========================================================
# VERIFY EMAIL — SINGLE-USE TOKEN
# =========================================================

@router.post(
    "/verify-email",
    dependencies=[
        Depends(rate_limit(10, 900, "customer-verify"))
    ],
)
def verify_customer_email(request: VerifyEmailRequest):
    token_hash = hashlib.sha256(
        request.token.encode("utf-8")
    ).hexdigest()

    connection = get_connection()
    verified = False

    try:
        with connection.cursor() as cursor:
            # A single conditional UPDATE consumes the token.
            # A previously used, expired, or invalid token cannot
            # change the account's verification status.
            cursor.execute(
                """
                UPDATE customers
                SET email_verified = 1,
                    verification_token_hash = NULL,
                    verification_expires_at = NULL
                WHERE verification_token_hash = %s
                  AND email_verified = 0
                  AND verification_expires_at > %s
                """,
                (token_hash, datetime.now()),
            )

            verified = cursor.rowcount == 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if not verified:
        raise HTTPException(
            status_code=400,
            detail=(
                "This verification link is invalid, expired, "
                "or has already been used. Request a new email."
            ),
        )

    return {
        "message": "Email verified successfully. You can now log in."
    }


# =========================================================
# RESEND VERIFICATION EMAIL
# =========================================================

@router.post(
    "/resend-verification",
    dependencies=[
        Depends(rate_limit(3, 900, "customer-resend"))
    ],
)
def resend_verification(request: ResendVerificationRequest):
    email = request.email.strip().lower()

    raw_token = None
    token_hash = None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, email_verified
                FROM customers
                WHERE email = %s
                """,
                (email,),
            )

            customer = cursor.fetchone()

            if customer and not customer["email_verified"]:
                raw_token, token_hash, expires_at = (
                    create_verification_token()
                )

                cursor.execute(
                    """
                    UPDATE customers
                    SET verification_token_hash = %s,
                        verification_expires_at = %s
                    WHERE customer_id = %s
                      AND email_verified = 0
                    """,
                    (
                        token_hash,
                        expires_at,
                        customer["customer_id"],
                    ),
                )

                if cursor.rowcount != 1:
                    raw_token = None
                    token_hash = None

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if raw_token and token_hash:
        try:
            send_verification_email(email, raw_token)

        except Exception:
            try:
                clear_verification_token(token_hash)
            except Exception:
                pass

            raise HTTPException(
                status_code=503,
                detail=(
                    "We could not send the verification email. "
                    "Please try again later."
                ),
            ) from None

    # Use the same normal response when an account is missing,
    # already verified, or successfully sent a new link.
    return {
        "message": (
            "If an unverified account exists for that email, "
            "a verification link has been sent."
        )
    }


# =========================================================
# CUSTOMER LOGIN
# =========================================================

@router.post(
    "/login",
    dependencies=[
        Depends(rate_limit(5, 900, "customer-login"))
    ],
)
def login_customer(credentials: CustomerLogin):
    email = credentials.email.strip().lower()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    customer_id,
                    customer_name,
                    email,
                    password_hash,
                    email_verified
                FROM customers
                WHERE email = %s
                """,
                (email,),
            )

            customer = cursor.fetchone()

    finally:
        connection.close()

    if (
        not customer
        or not customer["password_hash"]
        or not verify_password(
            credentials.password,
            customer["password_hash"],
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not customer["email_verified"]:
        raise HTTPException(
            status_code=403,
            detail=(
                "Please verify your email using the link we sent "
                "before logging in."
            ),
        )

    # Upgrade a legacy password hash after successful authentication.
    # The original hash condition avoids overwriting a hash changed
    # by another operation after this login retrieved the record.
    if password_needs_rehash(
        credentials.password,
        customer["password_hash"],
    ):
        new_password_hash = hash_password(credentials.password)

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE customers
                    SET password_hash = %s
                    WHERE customer_id = %s
                      AND password_hash = %s
                    """,
                    (
                        new_password_hash,
                        customer["customer_id"],
                        customer["password_hash"],
                    ),
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    access_token = create_access_token(
        customer["customer_id"],
        customer["email"],
        "customer",
    )

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "customer_id": customer["customer_id"],
        "customer_name": customer["customer_name"],
        "email": customer["email"],
        "role": "customer",
    }


# =========================================================
# CURRENT CUSTOMER PROFILE
# =========================================================

@router.get("/me")
def get_customer_profile(
    customer: dict = Depends(get_current_customer),
):
    return customer


# =========================================================
# UPDATE CUSTOMER PROFILE
# =========================================================

@router.put("/me")
def update_customer_profile(
    data: CustomerProfileUpdate,
    customer: dict = Depends(get_current_customer)
):
    customer_name = data.customer_name.strip()
    phone = data.phone.strip()
    email = data.email.strip().lower()
    address = data.address.strip() if data.address else None

    if len(customer_name) < 2:
        raise HTTPException(
            status_code=422,
            detail="Customer name must contain at least 2 characters."
        )

    if not phone or not email:
        raise HTTPException(
            status_code=422,
            detail="Phone number and email are required."
        )

    email_changed = email != customer["email"].strip().lower()

    # Hash a new password only when the customer provided one.
    new_password_hash = (
        hash_password(data.password)
        if data.password is not None
        else None
    )

    raw_token = None
    token_hash = None
    expires_at = None

    # A changed email must be verified again.
    if email_changed:
        raw_token, token_hash, expires_at = (
            create_verification_token()
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            updates = [
                "customer_name = %s",
                "phone = %s",
                "email = %s",
                "address = %s"
            ]

            values = [
                customer_name,
                phone,
                email,
                address
            ]

            if new_password_hash is not None:
                updates.append("password_hash = %s")
                values.append(new_password_hash)

            if email_changed:
                updates.extend([
                    "email_verified = 0",
                    "verification_token_hash = %s",
                    "verification_expires_at = %s"
                ])

                values.extend([
                    token_hash,
                    expires_at
                ])

            values.append(customer["customer_id"])

            query = f"""
                UPDATE customers
                SET {", ".join(updates)}
                WHERE customer_id = %s
            """

            cursor.execute(query, tuple(values))

        connection.commit()

    except IntegrityError:
        connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="That email address or phone number is already registered."
        ) from None

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if email_changed:
        try:
            send_verification_email(email, raw_token)

        except Exception:
            try:
                clear_verification_token(token_hash)
            except Exception:
                pass

            raise HTTPException(
                status_code=503,
                detail=(
                    "Your profile was saved, but the verification email "
                    "could not be sent. Please request a new verification "
                    "email before logging in."
                )
            ) from None

    return {
        "message": (
            "Profile updated. Please verify your new email address."
            if email_changed
            else "Customer profile updated successfully."
        ),
        "customer_id": customer["customer_id"],
        "customer_name": customer_name,
        "phone": phone,
        "email": email,
        "address": address,
        "email_verification_required": email_changed
    }
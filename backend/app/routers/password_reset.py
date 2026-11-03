import hashlib
import os
import secrets
import smtplib
import ssl

from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.database.database import get_connection
from backend.app.rate_limit import rate_limit
from backend.app.services.admin import hash_password


router = APIRouter(
    prefix="/password-reset",
    tags=["Password Recovery"]
)


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    account_type: Literal["admin", "customer"]


class PasswordResetComplete(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


def send_password_reset_email(
    recipient_email: str,
    token: str,
    account_type: str
):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv(
        "SMTP_APP_PASSWORD", ""
    ).replace(" ", "")
    sender_email = os.getenv(
        "EMAIL_FROM", smtp_username
    ).strip()

    if not smtp_username or not smtp_password or not sender_email:
        raise RuntimeError("Email settings are incomplete.")

    if account_type == "admin":
        base_url = os.getenv(
            "FRONTEND_ADMIN_BASE_URL",
            "http://127.0.0.1:5503/pages"
        ).rstrip("/")
    else:
        base_url = os.getenv(
            "FRONTEND_BASE_URL",
            "http://127.0.0.1:5503/customer-portal"
        ).rstrip("/")

    reset_link = f"{base_url}/forgot-password.html#token={token}"

    expiry_minutes = int(
        os.getenv("PASSWORD_RESET_TTL_MINUTES", "30")
    )

    message = EmailMessage()
    message["Subject"] = "Reset your VehicleCare password"
    message["From"] = sender_email
    message["To"] = recipient_email

    message.set_content(
        "We received a request to reset your VehicleCare password.\n\n"
        "Open this link to choose a new password:\n"
        f"{reset_link}\n\n"
        f"This link expires in {expiry_minutes} minutes and can be "
        "used only once.\n\n"
        "If you did not request a password reset, ignore this email."
    )

    message.add_alternative(
        f"""
        <html>
          <body style="font-family:Arial,sans-serif;color:#10233D">
            <h2>Reset your VehicleCare password</h2>
            <p>Use the button below to choose a new password.</p>
            <p>
              <a href="{reset_link}"
                 style="display:inline-block;padding:12px 20px;
                        background:#FFD700;color:#020B18;
                        text-decoration:none;border-radius:6px;
                        font-weight:bold">
                Reset My Password
              </a>
            </p>
            <p>
              This link expires in {expiry_minutes} minutes
              and can only be used once.
            </p>
            <p>If you did not request this, ignore this message.</p>
          </body>
        </html>
        """,
        subtype="html"
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.send_message(message)


@router.post(
    "/request",
    dependencies=[
        Depends(rate_limit(5, 900, "password-reset-request"))
    ]
)
def request_password_reset(request: PasswordResetRequest):
    email = request.email.strip().lower()
    account_type = request.account_type

    account = None
    raw_token = None
    token_hash = None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if account_type == "admin":
                cursor.execute(
                    """
                    SELECT admin_id AS account_id
                    FROM admins
                    WHERE email = %s
                    """,
                    (email,)
                )
            else:
                cursor.execute(
                    """
                    SELECT customer_id AS account_id
                    FROM customers
                    WHERE email = %s AND email_verified = 1
                    """,
                    (email,)
                )

            account = cursor.fetchone()

            if account:
                raw_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(
                    raw_token.encode("utf-8")
                ).hexdigest()

                expiry_minutes = int(
                    os.getenv("PASSWORD_RESET_TTL_MINUTES", "30")
                )

                # Invalidate previous unused reset links for this account.
                cursor.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used_at = %s
                    WHERE account_type = %s
                      AND account_id = %s
                      AND used_at IS NULL
                    """,
                    (
                        datetime.now(),
                        account_type,
                        account["account_id"]
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO password_reset_tokens (
                        account_type,
                        account_id,
                        token_hash,
                        expires_at
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        account_type,
                        account["account_id"],
                        token_hash,
                        datetime.now() + timedelta(
                            minutes=expiry_minutes
                        )
                    )
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    if account and raw_token and token_hash:
        try:
            send_password_reset_email(
                email,
                raw_token,
                account_type
            )

        except Exception as error:
            print(
                "Password-reset email delivery failed:",
                type(error).__name__
            )

            # An undelivered link must not remain usable.
            cleanup_connection = get_connection()

            try:
                with cleanup_connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE password_reset_tokens
                        SET used_at = %s
                        WHERE token_hash = %s
                          AND used_at IS NULL
                        """,
                        (datetime.now(), token_hash)
                    )

                cleanup_connection.commit()

            except Exception:
                cleanup_connection.rollback()
                raise

            finally:
                cleanup_connection.close()

    # Same response whether the email exists or not.
    return {
        "message": (
            "If an eligible account exists for that email, "
            "a password reset link will be sent. Check your inbox "
            "and spam folder."
        )
    }


@router.post(
    "/complete",
    dependencies=[
        Depends(rate_limit(10, 900, "password-reset-complete"))
    ]
)
def complete_password_reset(request: PasswordResetComplete):
    token_hash = hashlib.sha256(
        request.token.encode("utf-8")
    ).hexdigest()

    now = datetime.now()
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT reset_id, account_type, account_id
                FROM password_reset_tokens
                WHERE token_hash = %s
                  AND used_at IS NULL
                  AND expires_at > %s
                FOR UPDATE
                """,
                (token_hash, now)
            )

            reset_record = cursor.fetchone()

            if not reset_record:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This reset link is invalid, expired, "
                        "or already used. Request a new link."
                    )
                )

            password_hash = hash_password(request.new_password)

            if reset_record["account_type"] == "admin":
                cursor.execute(
                    """
                    UPDATE admins
                    SET password = %s
                    WHERE admin_id = %s
                    """,
                    (
                        password_hash,
                        reset_record["account_id"]
                    )
                )
            else:
                cursor.execute(
                    """
                    UPDATE customers
                    SET password_hash = %s
                    WHERE customer_id = %s
                      AND email_verified = 1
                    """,
                    (
                        password_hash,
                        reset_record["account_id"]
                    )
                )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=400,
                    detail="The account could not be updated."
                )

            # Consume all unused reset links for the account.
            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = %s
                WHERE account_type = %s
                  AND account_id = %s
                  AND used_at IS NULL
                """,
                (
                    now,
                    reset_record["account_type"],
                    reset_record["account_id"]
                )
            )

        connection.commit()

        return {
            "message": (
                "Password changed successfully. "
                "You can now log in with your new password."
            )
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


import hashlib
import os
import secrets
import smtplib
import ssl

from datetime import datetime, timedelta
from email.message import EmailMessage


def create_verification_token():
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    expiry_minutes = int(
        os.getenv("EMAIL_VERIFICATION_TTL_MINUTES", "30")
    )

    expires_at = datetime.now() + timedelta(
        minutes=expiry_minutes
    )

    return token, token_hash, expires_at


def send_verification_email(recipient_email, token):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_APP_PASSWORD", "").replace(" ", "")
    sender_email = os.getenv("EMAIL_FROM", smtp_username).strip()

    if not smtp_username or not smtp_password or not sender_email:
        raise RuntimeError("Email settings are incomplete.")

    base_url = os.getenv(
        "FRONTEND_BASE_URL",
        "http://127.0.0.1:5503/customer-portal"
    ).rstrip("/")

    # A URL fragment keeps the token out of the HTTP request URL
    # and normal local web-server access logs.
    verification_link = (
        f"{base_url}/verify-email.html#token={token}"
    )

    message = EmailMessage()
    message["Subject"] = "Verify your VehicleCare email address"
    message["From"] = sender_email
    message["To"] = recipient_email

    message.set_content(
        "Welcome to VehicleCare!\n\n"
        "Please verify your email address by opening this link:\n"
        f"{verification_link}\n\n"
        "This verification link expires in "
        f"{os.getenv('EMAIL_VERIFICATION_TTL_MINUTES', '30')} minutes "
        "and can be used only once.\n\n"
        "If you did not create a VehicleCare account, you can ignore "
        "this email."
    )

    message.add_alternative(
        f"""
        <html>
          <body style="font-family:Arial,sans-serif;color:#10233D">
            <h2>Welcome to VehicleCare</h2>
            <p>Please click the button below to verify your email address.</p>
            <p>
              <a href="{verification_link}"
                 style="display:inline-block;padding:12px 20px;
                        background:#FFD700;color:#020B18;
                        text-decoration:none;border-radius:6px;
                        font-weight:bold">
                Verify My Email
              </a>
            </p>
            <p>This link expires in
              {os.getenv('EMAIL_VERIFICATION_TTL_MINUTES', '30')} minutes
              and can be used only once.
            </p>
            <p>If you did not create an account, ignore this message.</p>
          </body>
        </html>
        """,
        subtype="html"
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20
    ) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

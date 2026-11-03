
from fastapi import APIRouter, HTTPException, Depends
from pymysql.err import IntegrityError

from backend.app.database.database import get_connection
from backend.app.schemas.admin import (
    AdminCreate,
    AdminLogin,
    AdminProfileUpdate,
)
from backend.app.services.admin import (
    hash_password,
    verify_password,
    password_needs_rehash,
)
from backend.app.security import (
    create_access_token,
    get_current_admin,
)


router = APIRouter(tags=["Admin Authentication"])


@router.post("/admins")
def create_admin(admin: AdminCreate):
    """
    Bootstrap the first admin account only.
    Once an admin exists, this public setup endpoint is disabled.
    """
    admin_name = admin.admin_name.strip()
    email = admin.email.strip().lower()

    if not admin_name or not email or not admin.password:
        raise HTTPException(
            status_code=422,
            detail="Admin name, email, and password are required.",
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM admins")
            result = cursor.fetchone()

            if result["total"] > 0:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Admin setup is disabled because an admin account "
                        "already exists."
                    ),
                )

            password_hash = hash_password(admin.password)

            cursor.execute(
                """
                INSERT INTO admins (admin_name, email, password, role)
                VALUES (%s, %s, %s, %s)
                """,
                (admin_name, email, password_hash, "admin"),
            )

            admin_id = cursor.lastrowid

        connection.commit()

        return {
            "message": "Admin account created successfully.",
            "admin_id": admin_id,
        }

    except HTTPException:
        connection.rollback()
        raise

    except IntegrityError:
        connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="An admin with this email already exists.",
        ) from None

    finally:
        connection.close()


@router.post("/admin/login")
def login_admin(admin: AdminLogin):
    email = admin.email.strip().lower()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT admin_id, admin_name, email, password, role
                FROM admins
                WHERE email = %s
                """,
                (email,),
            )
            saved_admin = cursor.fetchone()

    finally:
        connection.close()

    if (
        not saved_admin
        or not saved_admin["password"]
        or not verify_password(
            admin.password,
            saved_admin["password"],
        )
        or saved_admin["role"] != "admin"
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # Upgrade a legacy password hash after successful authentication.
    if password_needs_rehash(
        admin.password,
        saved_admin["password"],
    ):
        new_password_hash = hash_password(admin.password)
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE admins
                    SET password = %s
                    WHERE admin_id = %s
                    """,
                    (new_password_hash, saved_admin["admin_id"]),
                )

            connection.commit()

        finally:
            connection.close()

    token = create_access_token(
        saved_admin["admin_id"],
        saved_admin["email"],
        "admin",
    )

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "admin_id": saved_admin["admin_id"],
        "admin_name": saved_admin["admin_name"],
        "email": saved_admin["email"],
        "role": "admin",
    }

# =========================================================
# ADMIN PROFILE
# =========================================================

@router.get("/admin/me")
def get_admin_profile(
    admin: dict = Depends(get_current_admin)
):
    return admin


@router.put("/admin/me")
def update_admin_profile(
    data: AdminProfileUpdate,
    admin: dict = Depends(get_current_admin)
):
    admin_name = data.admin_name.strip()
    email = data.email.strip().lower()

    if len(admin_name) < 2 or not email:
        raise HTTPException(
            status_code=422,
            detail="Enter a valid admin name and email."
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT admin_id
                FROM admins
                WHERE email = %s AND admin_id != %s
                """,
                (email, admin["admin_id"])
            )

            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="This email is already used by another admin."
                )

            if data.password is not None:
                password_hash = hash_password(data.password)

                cursor.execute(
                    """
                    UPDATE admins
                    SET admin_name = %s,
                        email = %s,
                        password = %s
                    WHERE admin_id = %s
                    """,
                    (
                        admin_name,
                        email,
                        password_hash,
                        admin["admin_id"]
                    )
                )

            else:
                cursor.execute(
                    """
                    UPDATE admins
                    SET admin_name = %s,
                        email = %s
                    WHERE admin_id = %s
                    """,
                    (
                        admin_name,
                        email,
                        admin["admin_id"]
                    )
                )

        connection.commit()

        return {
            "message": "Admin profile updated successfully.",
            "admin_id": admin["admin_id"],
            "admin_name": admin_name,
            "email": email,
            "role": "admin"
        }

    except HTTPException:
        connection.rollback()
        raise

    except IntegrityError:
        connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="This email is already in use."
        ) from None

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
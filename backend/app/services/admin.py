import hashlib
import hmac
import secrets


CURRENT_ITERATIONS = 600_000
LEGACY_ITERATIONS = 100_000


def _derive_password_hash(
    password: str,
    salt: str,
    iterations: int
) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    ).hex()


def hash_password(password: str) -> str:
    """Create a salted hash for a new password."""
    salt = secrets.token_hex(16)
    password_hash = _derive_password_hash(
        password,
        salt,
        CURRENT_ITERATIONS
    )
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    """Verify current and older stored password hashes."""
    try:
        salt, stored_hash = stored_password.split(":", 1)

        if not salt or len(stored_hash) != 64:
            return False

        current_hash = _derive_password_hash(
            password, salt, CURRENT_ITERATIONS
        )

        if hmac.compare_digest(current_hash, stored_hash):
            return True

        legacy_hash = _derive_password_hash(
            password, salt, LEGACY_ITERATIONS
        )

        return hmac.compare_digest(legacy_hash, stored_hash)

    except (ValueError, TypeError, AttributeError):
        return False


def password_needs_rehash(
    password: str,
    stored_password: str
) -> bool:
    """Return True if a verified password uses the legacy hash setting."""
    try:
        salt, stored_hash = stored_password.split(":", 1)

        current_hash = _derive_password_hash(
            password, salt, CURRENT_ITERATIONS
        )

        return not hmac.compare_digest(current_hash, stored_hash)

    except (ValueError, TypeError, AttributeError):
        return False

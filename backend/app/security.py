import base64
import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    key_text = base64.urlsafe_b64encode(derived_key).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_text}${key_text}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        algorithm, iteration_text, salt_text, key_text = stored_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected_key = base64.urlsafe_b64decode(key_text.encode("ascii"))
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iteration_text),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(actual_key, expected_key)


def create_access_token() -> str:
    return secrets.token_urlsafe(32)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

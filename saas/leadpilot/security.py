"""Password hashing, signed session cookies and CSRF tokens (standard library only)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

PBKDF2_ROUNDS = 240_000
SESSION_MAX_AGE = 14 * 24 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
    return hmac.compare_digest(check.hex(), digest)


def _sign(payload: bytes, key: str) -> str:
    return hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()


def make_session(user_id: int, key: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"u": user_id, "t": int(time.time()),
                                                    "n": secrets.token_hex(8)}).encode())
    return f"{payload.decode()}.{_sign(payload, key)}"


def read_session(token: str, key: str) -> int | None:
    """Return the user id from a valid, unexpired cookie, else None."""
    try:
        payload, sig = token.rsplit(".", 1)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(_sign(payload.encode(), key), sig):
        return None
    data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    if time.time() - data["t"] > SESSION_MAX_AGE:
        return None
    return int(data["u"])


def csrf_token(session_token: str, key: str) -> str:
    return _sign(b"csrf:" + session_token.encode(), key)[:32]


def check_csrf(session_token: str, submitted: str, key: str) -> bool:
    return bool(submitted) and hmac.compare_digest(csrf_token(session_token, key), submitted)


def new_api_key() -> str:
    return "lp_" + secrets.token_urlsafe(24)


def verify_meta_signature(body: bytes, header: str, app_secret: str) -> bool:
    """Check Meta's X-Hub-Signature-256 header ('sha256=<hex>')."""
    if not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[7:])

"""JWT helpers — HS256, access 24h per PRD; refresh 7d with separate secret."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from jose import JWTError, jwt

from src.settings import get_settings


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_access_token(user_id: str, email: str, role: str) -> str:
    s = get_settings()
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "typ": "access",
        "iss": "auth-service",
        "iat": now,
        "exp": now + 86400,  # 24h
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    s = get_settings()
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "typ": "refresh",
        "iss": "auth-service",
        "iat": now,
        "exp": now + 7 * 86400,
    }
    return jwt.encode(payload, s.jwt_refresh_secret, algorithm="HS256")


def verify_access_token(token: str) -> dict[str, Any]:
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.jwt_secret,
            algorithms=["HS256"],
            issuer="auth-service",
        )
    except JWTError as e:
        raise ValueError("invalid access token") from e
    if payload.get("typ") != "access":
        raise ValueError("invalid token type")
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.jwt_refresh_secret,
            algorithms=["HS256"],
            issuer="auth-service",
        )
    except JWTError as e:
        raise ValueError("invalid refresh token") from e
    if payload.get("typ") != "refresh":
        raise ValueError("invalid token type")
    return payload

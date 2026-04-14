"""Auth routes — parameterized SQL only; NATS user.registered on register."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src import db
from src.events import publish
from src.jwt_utils import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_access_token,
    verify_refresh_token,
)
from src.passwords import hash_password, verify_password
from src.settings import get_settings

router = APIRouter(tags=["auth"])

REFRESH_DELTA = timedelta(days=7)


def normalize_role(raw: str | None) -> str:
    if raw == "admin":
        return "customer"
    return raw if isinstance(raw, str) and raw else "customer"


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str | None = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RefreshBody(BaseModel):
    refreshToken: str


class LogoutBody(BaseModel):
    refreshToken: str


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )
    raw = authorization[7:].strip()
    try:
        payload = verify_access_token(raw)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        ) from None
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return {
        "id": str(payload["sub"]),
        "email": payload["email"],
        "role": payload["role"],
    }


@router.get("/health")
async def auth_health():
    return {
        "status": "ok",
        "service": "auth-service",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@router.post("/register", status_code=201)
async def register(body: RegisterBody):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    role = normalize_role(body.role)
    async with db.pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            body.email,
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        pw_hash = hash_password(body.password)
        async with conn.transaction():
            uid = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                body.email,
                pw_hash,
                role,
            )
            uid_str = str(uid)
            refresh_raw = create_refresh_token(uid_str)
            th = hash_token(refresh_raw)
            expires_at = datetime.now(UTC) + REFRESH_DELTA
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                """,
                uid,
                th,
                expires_at,
            )

        urow = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE id = $1",
            uid,
        )

    await publish(
        "user.registered",
        {
            "user_id": uid_str,
            "email": urow["email"],
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    )

    access = create_access_token(uid_str, urow["email"], urow["role"])
    return {
        "accessToken": access,
        "refreshToken": refresh_raw,
        "user": {
            "id": uid_str,
            "email": urow["email"],
            "role": urow["role"],
        },
    }


@router.post("/login")
async def login(body: LoginBody):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, password_hash, role FROM users WHERE email = $1
            """,
            body.email,
        )
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        uid_str = str(row["id"])
        async with conn.transaction():
            refresh_raw = create_refresh_token(uid_str)
            th = hash_token(refresh_raw)
            expires_at = datetime.now(UTC) + REFRESH_DELTA
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                """,
                row["id"],
                th,
                expires_at,
            )

        access = create_access_token(uid_str, row["email"], row["role"])
        return {
            "accessToken": access,
            "refreshToken": refresh_raw,
            "user": {
                "id": uid_str,
                "email": row["email"],
                "role": row["role"],
            },
        }


@router.post("/refresh")
async def refresh_token(body: RefreshBody):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        payload = verify_refresh_token(body.refreshToken)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        ) from None
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    old_hash = hash_token(body.refreshToken)
    async with db.pool.acquire() as conn:
        rrow = await conn.fetchrow(
            """
            SELECT user_id, expires_at FROM refresh_tokens WHERE token_hash = $1
            """,
            old_hash,
        )
        if not rrow:
            raise HTTPException(
                status_code=401,
                detail="Refresh token revoked or unknown",
            )
        if str(rrow["user_id"]) != str(payload["sub"]):
            raise HTTPException(status_code=401, detail="Token mismatch")
        if rrow["expires_at"] < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        user = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE id = $1",
            rrow["user_id"],
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        uid_str = str(user["id"])
        new_refresh = create_refresh_token(uid_str)
        new_hash = hash_token(new_refresh)
        expires_at = datetime.now(UTC) + REFRESH_DELTA

        async with conn.transaction():
            await conn.execute(
                "DELETE FROM refresh_tokens WHERE token_hash = $1",
                old_hash,
            )
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                """,
                user["id"],
                new_hash,
                expires_at,
            )

        access = create_access_token(uid_str, user["email"], user["role"])
        return {"accessToken": access, "refreshToken": new_refresh}


@router.post("/logout")
async def logout(
    body: LogoutBody,
    user: Annotated[dict, Depends(get_current_user)],
):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        payload = verify_refresh_token(body.refreshToken)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    if str(payload["sub"]) != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Token does not belong to current user",
        )

    th = hash_token(body.refreshToken)
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id FROM refresh_tokens WHERE token_hash = $1",
            th,
        )
        if not row or str(row["user_id"]) != user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Refresh token not found for this user",
            )
        await conn.execute(
            "DELETE FROM refresh_tokens WHERE token_hash = $1",
            th,
        )
    return {"ok": True}


@router.post("/logout-all")
async def logout_all(user: Annotated[dict, Depends(get_current_user)]):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM refresh_tokens WHERE user_id = $1::uuid",
            user["id"],
        )
    return {"ok": True}


@router.get("/me")
async def me(user: Annotated[dict, Depends(get_current_user)]):
    if db.pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, role, created_at, updated_at FROM users WHERE id = $1::uuid
            """,
            user["id"],
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@router.get("/verify")
async def verify(user: Annotated[dict, Depends(get_current_user)]):
    return {
        "valid": True,
        "userId": user["id"],
        "email": user["email"],
        "role": user["role"],
    }

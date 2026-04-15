"""NATS — connect with retry; publish BaseEvent JSON (PRD event contract)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import nats
from nats.aio.client import Client as NatsClient

from src.settings import get_settings

logger = logging.getLogger(__name__)

BACKOFF_SEC = [1, 2, 4, 8, 16]

_nc: NatsClient | None = None


async def connect_nats() -> None:
    global _nc
    s = get_settings()
    if not s.nats_url:
        logger.warning("NATS_URL not set; NATS disabled")
        return

    max_attempts = len(BACKOFF_SEC) + 1
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            _nc = await nats.connect(servers=[s.nats_url])
            logger.info("NATS connected (auth-service)")
            return
        except Exception as e:
            last_err = e
            logger.warning(
                "NATS connect attempt %s/%s failed: %s",
                attempt + 1,
                max_attempts,
                e,
            )
            if attempt < len(BACKOFF_SEC):
                await asyncio.sleep(BACKOFF_SEC[attempt])

    logger.warning(
        "NATS unavailable after retries; continuing without NATS: %s",
        last_err,
    )


async def publish(subject: str, data: dict[str, Any]) -> None:
    if _nc is None:
        logger.warning("publish skipped (no NATS): %s", subject)
        return
    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    payload = {
        "event_id": str(uuid.uuid4()),
        "subject": subject,
        "service": "auth-service",
        "timestamp": ts,
        "data": data,
    }
    try:
        await _nc.publish(subject, json.dumps(payload).encode("utf-8"))
    except Exception as e:
        logger.warning("publish failed: %s", e)


async def drain_nats() -> None:
    global _nc
    if _nc is None:
        return
    try:
        await _nc.drain()
    except Exception as e:
        logger.warning("NATS drain: %s", e)
    _nc = None

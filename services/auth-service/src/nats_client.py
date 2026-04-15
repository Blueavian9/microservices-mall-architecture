import nats, json, asyncio
from .config import settings

_nc = None

async def get_nats():
    global _nc
    if _nc is None or not _nc.is_connected:
        _nc = await nats.connect(settings.nats_url)
    return _nc

async def publish(subject: str, data: dict):
    try:
        nc = await get_nats()
        await nc.publish(subject, json.dumps(data).encode())
    except Exception as e:
        print(f"[NATS] publish error: {e}")

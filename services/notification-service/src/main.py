import asyncio, json
import nats
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from .config import settings

app = FastAPI(title="notification-service")
Instrumentator().instrument(app).expose(app)

SUBJECTS = ["booking.created", "auth.user_registered"]

@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}

async def handle(msg):
    data = json.loads(msg.data.decode())
    print(f"[NOTIFY] subject={msg.subject} data={data}", flush=True)
    # TODO Phase 8+: plug in real email/SMS provider here

async def start_subscriber():
    nc = await nats.connect(settings.nats_url)
    for subject in SUBJECTS:
        await nc.subscribe(subject, cb=handle)
    print(f"[NOTIFY] subscribed to {SUBJECTS}", flush=True)

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_subscriber())

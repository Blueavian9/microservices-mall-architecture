import os, asyncio, json, logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.events import connect_nats, subscribe_all

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("notification-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(connect_nats())
    yield
    task.cancel()

app = FastAPI(title="notification-service", lifespan=lifespan)

@app.get("/notification/health")
def health():
    return {"status": "ok", "service": "notification-service"}

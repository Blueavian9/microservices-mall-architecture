import os, json, asyncio, logging
from nats.aio.client import Client as NATS
from src.email import send_booking_confirmation, send_welcome_email

log = logging.getLogger("notification-service.events")
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

async def connect_nats():
    nc = NATS()
    while True:
        try:
            await nc.connect(NATS_URL)
            log.info(f"Connected to NATS at {NATS_URL}")

            async def on_booking_created(msg):
                data = json.loads(msg.data.decode())
                log.info(f"[booking.created] {data}")
                await send_booking_confirmation(data)

            async def on_user_registered(msg):
                data = json.loads(msg.data.decode())
                log.info(f"[user.registered] {data}")
                await send_welcome_email(data)

            await nc.subscribe("booking.created", cb=on_booking_created)
            await nc.subscribe("user.registered", cb=on_user_registered)
            log.info("Subscribed to booking.created + user.registered")

            while True:
                await asyncio.sleep(1)

        except Exception as e:
            log.error(f"NATS connection error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

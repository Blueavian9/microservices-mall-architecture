import os, logging
import resend

log = logging.getLogger("notification-service.email")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@mall.local")

async def send_booking_confirmation(data: dict):
    if not RESEND_API_KEY:
        log.warning("email skipped — no API key (booking_confirmation)")
        return
    try:
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": data.get("email", "user@example.com"),
            "subject": "Booking Confirmed!",
            "html": f"<h1>Your booking is confirmed.</h1><pre>{data}</pre>"
        })
        log.info(f"Booking confirmation sent for {data.get('booking_id')}")
    except Exception as e:
        log.error(f"Failed to send booking confirmation: {e}")

async def send_welcome_email(data: dict):
    if not RESEND_API_KEY:
        log.warning("email skipped — no API key (welcome_email)")
        return
    try:
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": data.get("email", "user@example.com"),
            "subject": "Welcome to the Mall!",
            "html": f"<h1>Welcome, {data.get('username', 'friend')}!</h1>"
        })
        log.info(f"Welcome email sent for {data.get('username')}")
    except Exception as e:
        log.error(f"Failed to send welcome email: {e}")

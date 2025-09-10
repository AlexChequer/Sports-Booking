import os
import requests
from dotenv import load_dotenv

load_dotenv()


PAYMENT_URL = os.getenv("PAYMENT_URL", "http://sports-payment:8000")


def checkout(booking_id: int, amount: float, method: str, coupon: str | None = None):
    payload = {"booking_id": booking_id, "amount": amount, "method": method}
    if coupon:
        payload["coupon"] = coupon
    r = requests.post(f"{PAYMENT_URL}/checkout", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()
import os
import psycopg2
from fastapi import APIRouter
from app.services import agenda_client

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

@router.post("/callbacks/payment")
async def payment_callback(payment_id: int, booking_id: int, status: str, paid_amount: float | None = None, invoice_id: int | None = None, invoice_url: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT court_id, slot_id FROM bookings WHERE id=%s", (booking_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return {"ignored": True}

    if status == "APPROVED":
        cur.execute("UPDATE bookings SET status='CONFIRMED', paid_total=%s WHERE id=%s", (paid_amount, booking_id))
        agenda_client.mark_booked(court_id=row[0], slot_id=row[1], booking_id=booking_id)
    elif status == "DECLINED":
        cur.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (booking_id,))
        agenda_client.release_lock(f"{row[0]}-{row[1]}-{booking_id}")
    else:
        cur.execute("UPDATE bookings SET status='PENDING_PAYMENT' WHERE id=%s", (booking_id,))

    if invoice_id:
        cur.execute("UPDATE bookings SET invoice_id=%s, invoice_url=%s WHERE id=%s", (invoice_id, invoice_url, booking_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"ok": True}

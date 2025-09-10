import os
import psycopg2
from fastapi import APIRouter, HTTPException
from app.services import agenda_client, payment_client
from app.api.routes.quotes import calculate_quote
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

@router.post("/bookings")
async def create_booking(court_id: int, slot_id: int, extras: list[str] | None = None, notes: str | None = None):
    estimate = calculate_quote(court_id, slot_id, extras or [])
    lock = agenda_client.create_lock(court_id=court_id, slot_id=slot_id, booking_id=0)  # booking_id será o autoincremento

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO bookings (court_id, slot_id, status, estimate_total, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (court_id, slot_id, "CREATED", estimate["total"], notes),
    )
    booking_id = cur.fetchone()[0]

    # extras
    if extras:
        for e in extras:
            cur.execute(
                "INSERT INTO booking_extras (booking_id, type, qty, price) VALUES (%s, %s, %s, %s)",
                (booking_id, e, 1, float(estimate["extras"][0]["price"]) if estimate["extras"] else 0.0),
            )

    conn.commit()
    cur.close()
    conn.close()

    return {"booking_id": booking_id, "status": "CREATED", "estimate": estimate, "lock_id": lock["lock_id"]}

@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, court_id, slot_id, status, estimate_total, paid_total, notes FROM bookings WHERE id=%s", (booking_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, "booking not found")
    return {
        "id": row[0],
        "court_id": row[1],
        "slot_id": row[2],
        "status": row[3],
        "estimate_total": float(row[4]),
        "paid_total": float(row[5]) if row[5] else None,
        "notes": row[6],
    }

@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status FROM bookings WHERE id=%s", (booking_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(404, "booking not found")
    if row[0] == "CONFIRMED":
        cur.close()
        conn.close()
        raise HTTPException(400, "cannot cancel confirmed booking")
    cur.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (booking_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}

@router.get("/me/bookings")
async def list_bookings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, court_id, slot_id, status, estimate_total FROM bookings ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "court_id": r[1], "slot_id": r[2], "status": r[3], "estimate_total": float(r[4])}
        for r in rows
    ]

@router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: int, method: str, coupon: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT estimate_total FROM bookings WHERE id=%s", (booking_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(404, "booking not found")

    amount = float(row[0])
    pay = payment_client.checkout(booking_id=booking_id, amount=amount, method=method, coupon=coupon)

    cur.execute("UPDATE bookings SET status='PENDING_PAYMENT' WHERE id=%s", (booking_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {"payment_id": pay.get("payment_id"), "status": pay.get("status")}

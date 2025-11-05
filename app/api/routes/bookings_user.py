import os
import psycopg2

from fastapi import APIRouter, HTTPException, Depends

from pydantic import BaseModel
from typing import List, Optional

from app.services import agenda_client, payment_client
from app.api.routes.quotes import calculate_quote
from app.core.auth import verify_token
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ======= MODELS =======
class BookingCreate(BaseModel):
    court_id: int
    slot_id: int
    extras: List[str] = []
    # não tem mais notes; se o front mandar, será ignorado pelo parse manual abaixo

class BookingCheckout(BaseModel):
    method: str
    coupon: Optional[str] = None


# ======= ENDPOINTS =======
@router.post("/bookings")

async def create_booking(payload: BookingCreate):
    """
    JSON esperado:
    { "court_id": 1, "slot_id": 17, "extras": ["ball","vest"] }
    """
    court_id = payload.court_id
    slot_id = payload.slot_id

    # tolera 'notes' vindo do front sem quebrar (ignorado)
    extras = payload.extras or []

    estimate = calculate_quote(court_id, slot_id, extras)
    price_map = {e["type"]: float(e["price"]) for e in estimate.get("extras", [])}

    conn = get_conn()
    try:
        cur = conn.cursor()

        # 1) cria booking (sem coluna notes)
        cur.execute(
            """
            INSERT INTO bookings (court_id, slot_id, status, estimate_total)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (court_id, slot_id, "CREATED", float(estimate["total"])),
        )
        booking_id = cur.fetchone()[0]

        # 2) lock no Agenda usando booking_id real
        try:
            lock = agenda_client.create_lock(
                court_id=court_id, slot_id=slot_id, booking_id=booking_id
            )
            if not lock or not lock.get("lock_id"):
                raise RuntimeError("failed to lock slot")
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=409, detail=f"slot not available: {e}")

        # 3) extras

        for e in extras:
            cur.execute(
                """
                INSERT INTO booking_extras (booking_id, type, qty, price)
                VALUES (%s, %s, %s, %s)
                """,
                (booking_id, e, 1, price_map.get(e, 0.0)),
      


        conn.commit()
        cur.close()

        return {
            "booking_id": booking_id,
            "status": "CREATED",
            "estimate": estimate,
            "lock_id": lock["lock_id"],
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass



@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, payload=Depends(verify_token)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, court_id, slot_id, status, estimate_total, paid_total FROM bookings WHERE id=%s",
            (booking_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            raise HTTPException(404, "booking not found")
        return {
            "id": row[0],
            "court_id": row[1],
            "slot_id": row[2],
            "status": row[3],
            "estimate_total": float(row[4]),
            "paid_total": float(row[5]) if row[5] else None,
        }
    finally:
        conn.close()


@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: int, payload=Depends(verify_token)):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status FROM bookings WHERE id=%s", (booking_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "booking not found")
        if row[0] == "CONFIRMED":
            raise HTTPException(400, "cannot cancel confirmed booking")
        cur.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (booking_id,))
        conn.commit()
        cur.close()
        return {"ok": True}
    finally:
        conn.close()



@router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: int, payload: BookingCheckout):
    """
    JSON: { "method": "CARD" | "PIX" | "BOLETO", "coupon": "ABC" }
    """
    method = payload.method
    coupon = payload.coupon

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT estimate_total FROM bookings WHERE id=%s", (booking_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "booking not found")

        amount = float(row[0])
        pay = payment_client.checkout(
            booking_id=booking_id, amount=amount, method=method, coupon=coupon
        )

        cur.execute("UPDATE bookings SET status='PENDING_PAYMENT' WHERE id=%s", (booking_id,))
        conn.commit()
        cur.close()

        return {"payment_id": pay.get("payment_id"), "status": pay.get("status")}
    finally:
        conn.close()


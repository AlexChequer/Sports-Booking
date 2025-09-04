from fastapi import APIRouter, HTTPException
from app.services import agenda_client, payment_client
from app.api.routes.quotes import calculate_quote


router = APIRouter()


# Mock em memória
BOOKINGS: dict[int, dict] = {}
SEQ = 1


@router.post("/bookings")
async def create_booking(court_id: int, slot_id: int, extras: list[str] | None = None, notes: str | None = None):
    global SEQ
    booking_id = SEQ
    SEQ += 1


    estimate = calculate_quote(court_id, slot_id, extras or [])


    lock = agenda_client.create_lock(court_id=court_id, slot_id=slot_id, booking_id=booking_id)


    BOOKINGS[booking_id] = {
    "id": booking_id,
    "court_id": court_id,
    "slot_id": slot_id,
    "status": "CREATED",
    "extras": extras or [],
    "estimate_total": estimate["total"],
    "lock_id": lock["lock_id"],
    "notes": notes,
    }
    return {"booking_id": booking_id, "status": "CREATED", "estimate": estimate}


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int):
    b = BOOKINGS.get(booking_id)
    if not b:
        raise HTTPException(404, "booking not found")
    return b


@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: int):
    b = BOOKINGS.get(booking_id)
    if not b:
        raise HTTPException(404, "booking not found")
    if b["status"] == "CONFIRMED":
        raise HTTPException(400, "cannot cancel confirmed booking")
    if lock_id := b.get("lock_id"):
        agenda_client.release_lock(lock_id)
        b["lock_id"] = None
    b["status"] = "CANCELLED"
    return {"ok": True}


@router.get("/me/bookings")
async def list_bookings():
    return list(BOOKINGS.values())


@router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: int, method: str, coupon: str | None = None):
    b = BOOKINGS.get(booking_id)
    if not b:
        raise HTTPException(404, "booking not found")
    amount = float(b["estimate_total"]) # simples
    pay = payment_client.checkout(booking_id=booking_id, amount=amount, method=method, coupon=coupon)
    # status real será atualizado via callback
    b["status"] = "PENDING_PAYMENT"
    return {"payment_id": pay.get("payment_id"), "status": pay.get("status")}
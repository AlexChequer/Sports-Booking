from fastapi import APIRouter
from app.api.routes.bookings_user import BOOKINGS
from app.services import agenda_client


router = APIRouter()


@router.post("/callbacks/payment")
async def payment_callback(payment_id: int, booking_id: int, status: str, paid_amount: float | None = None, invoice_id: int | None = None, invoice_url: str | None = None):
    b = BOOKINGS.get(booking_id)
    if not b:
        return {"ignored": True}
    if status == "APPROVED":
        b["status"] = "CONFIRMED"
        agenda_client.mark_booked(court_id=b["court_id"], slot_id=b["slot_id"], booking_id=booking_id)
    elif status == "DECLINED":
        b["status"] = "CANCELLED"
        if lock_id := b.get("lock_id"):
            agenda_client.release_lock(lock_id)
            b["lock_id"] = None
    else:
        b["status"] = "PENDING_PAYMENT"
    if paid_amount is not None:
        b["paid_total"] = paid_amount
    if invoice_id:
        b["invoice_id"] = invoice_id
        b["invoice_url"] = invoice_url
    return {"ok": True}
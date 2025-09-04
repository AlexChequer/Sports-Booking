from fastapi import APIRouter


router = APIRouter()


EXTRA_PRICES = {"ball": 5.0, "vest": 8.0, "lights": 12.0}
BASE_PRICE = 50.0


@router.get("/quotes")
async def quote_endpoint(court_id: int, slot_id: int, extras: list[str] | None = None):
    return calculate_quote(court_id, slot_id, extras or [])


def calculate_quote(court_id: int, slot_id: int, extras: list[str]):
    extras_cost = sum(EXTRA_PRICES.get(e, 0.0) for e in extras)
    total = BASE_PRICE + extras_cost
    return {
    "subtotal": BASE_PRICE,
    "extras": [{"type": e, "price": EXTRA_PRICES.get(e, 0.0)} for e in extras],
    "total": total,
    }
from fastapi import FastAPI
from app.api.routes import health, bookings_user, quotes, callbacks


app = FastAPI(title="Sports-Booking")


app.include_router(health.router, tags=["health"])
app.include_router(bookings_user.router, tags=["bookings"])
app.include_router(quotes.router, tags=["quotes"])
app.include_router(callbacks.router, tags=["callbacks"])

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.bookings_user import router as bookings_router
from app.api.routes.callbacks import router as callbacks_router

app = FastAPI()
app.include_router(health_router)
app.include_router(quotes_router)
app.include_router(bookings_router)
app.include_router(callbacks_router)

client = TestClient(app)

# ---------- HEALTH ----------
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# ---------- QUOTES ----------
def test_quote_endpoint():
    response = client.get("/quotes", params={"court_id": 1, "slot_id": 2, "extras": ["ball", "vest"]})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 63.0
    assert len(data["extras"]) == 2

# ---------- BOOKINGS ----------
@patch("app.api.routes.bookings_user.get_conn")
@patch("app.services.agenda_client.create_lock")
@patch("app.api.routes.quotes.calculate_quote")
def test_create_booking(mock_quote, mock_lock, mock_conn):
    mock_quote.return_value = {"total": 60.0, "extras": [{"type": "ball", "price": 10.0}]}
    mock_lock.return_value = {"lock_id": "1-2-3"}
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [123]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post("/bookings", params={"court_id": 1, "slot_id": 2, "extras": ["ball"], "notes": "bring water"})
    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == 123
    assert data["status"] == "CREATED"
    assert data["lock_id"] == "1-2-3"

@patch("app.api.routes.bookings_user.get_conn")
def test_get_booking_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1, 2, 3, "CREATED", 50.0, 25.0, "note"]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.get("/bookings/1")
    assert response.status_code == 200
    assert response.json()["court_id"] == 2

@patch("app.api.routes.bookings_user.get_conn")
def test_get_booking_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.get("/bookings/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "booking not found"

@patch("app.api.routes.bookings_user.get_conn")
def test_cancel_booking_success(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ["CREATED"]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.delete("/bookings/1")
    assert response.status_code == 200
    assert response.json()["ok"]

@patch("app.api.routes.bookings_user.get_conn")
def test_cancel_booking_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.delete("/bookings/999")
    assert response.status_code == 404

@patch("app.api.routes.bookings_user.get_conn")
def test_cancel_booking_confirmed(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ["CONFIRMED"]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.delete("/bookings/1")
    assert response.status_code == 400
    assert response.json()["detail"] == "cannot cancel confirmed booking"

@patch("app.api.routes.bookings_user.get_conn")
def test_list_bookings(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(1, 2, 3, "CREATED", 50.0)]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.get("/me/bookings")
    assert response.status_code == 200
    assert response.json()[0]["status"] == "CREATED"

@patch("app.api.routes.bookings_user.get_conn")
@patch("app.services.payment_client.checkout")
def test_checkout_booking(mock_checkout, mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [100.0]
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_checkout.return_value = {"payment_id": "abc123", "status": "PENDING"}

    response = client.post("/bookings/1/checkout", params={"method": "pix"})
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "abc123"

# ---------- CALLBACK ----------
@patch("app.api.routes.callbacks.get_conn")
@patch("app.services.agenda_client.mark_booked")
@patch("app.services.agenda_client.release_lock")
def test_payment_callback_approved(mock_release, mock_mark, mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1, 2]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post("/callbacks/payment", params={
        "payment_id": 1,
        "booking_id": 1,
        "status": "APPROVED",
        "paid_amount": 100,
        "invoice_id": 10,
        "invoice_url": "url"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}

@patch("app.api.routes.callbacks.get_conn")
@patch("app.services.agenda_client.release_lock")
def test_payment_callback_declined(mock_release, mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1, 2]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post("/callbacks/payment", params={
        "payment_id": 1,
        "booking_id": 1,
        "status": "DECLINED"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}

@patch("app.api.routes.callbacks.get_conn")
def test_payment_callback_other(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1, 2]
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post("/callbacks/payment", params={
        "payment_id": 1,
        "booking_id": 1,
        "status": "OTHER"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}

@patch("app.api.routes.callbacks.get_conn")
def test_payment_callback_booking_not_found(mock_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post("/callbacks/payment", params={
        "payment_id": 1,
        "booking_id": 999,
        "status": "APPROVED"
    })
    assert response.status_code == 200
    assert response.json() == {"ignored": True}

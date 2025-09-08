
import pytest
from unittest.mock import patch, MagicMock
from app.services import agenda_client, payment_client

# ---------- AGENDA CLIENT ----------

@patch("app.services.agenda_client.requests.post")
def test_create_lock(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"lock_id": "1-2-3", "expires_at": "in+300"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = agenda_client.create_lock(1, 2, 3)
    assert result["lock_id"] == "1-2-3"
    mock_post.assert_called_once()

@patch("app.services.agenda_client.requests.post")
def test_release_lock(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"released": True}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = agenda_client.release_lock("1-2-3")
    assert result["released"] is True
    mock_post.assert_called_once()

@patch("app.services.agenda_client.requests.post")
def test_mark_booked(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = agenda_client.mark_booked(1, 2, 3)
    assert result["ok"] is True
    mock_post.assert_called_once()

@patch("app.services.agenda_client.requests.post")
def test_mark_released(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = agenda_client.mark_released(1, 2, 3)
    assert result["ok"] is True
    mock_post.assert_called_once()

# ---------- PAYMENT CLIENT ----------

@patch("app.services.payment_client.requests.post")
def test_checkout(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"payment_id": "abc123", "status": "PENDING"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = payment_client.checkout(1, 100.0, "pix", coupon="DISCOUNT10")
    assert result["payment_id"] == "abc123"
    assert result["status"] == "PENDING"
    mock_post.assert_called_once()

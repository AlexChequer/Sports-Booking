import os
import requests


AGENDA_URL = os.getenv("AGENDA_URL", "http://sports-agenda:8000")


def create_lock(court_id: int, slot_id: int, booking_id: int, ttl_seconds: int = 300):
    r = requests.post(f"{AGENDA_URL}/locks", params={
    "court_id": court_id,
    "slot_id": slot_id,
    "booking_id": booking_id,
    "ttl_seconds": ttl_seconds,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def release_lock(lock_id: int):
    r = requests.post(f"{AGENDA_URL}/locks/release", params={"lock_id": lock_id}, timeout=10)
    r.raise_for_status()
    return r.json()


def mark_booked(court_id: int, slot_id: int, booking_id: int):
    r = requests.post(f"{AGENDA_URL}/mark-booked", params={
    "court_id": court_id,
    "slot_id": slot_id,
    "booking_id": booking_id,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def mark_released(court_id: int, slot_id: int, booking_id: int):
    r = requests.post(f"{AGENDA_URL}/mark-released", params={
    "court_id": court_id,
    "slot_id": slot_id,
    "booking_id": booking_id,
    }, timeout=10)
    r.raise_for_status()
    return r.json()
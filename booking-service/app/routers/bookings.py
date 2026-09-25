import os
import httpx
ROOM_SERVICE_URL = os.getenv(
    ROOM_SERVICE_URL = "http://room-service:8001"
)

BILLING_SERVICE_URL = os.getenv(
    "BILLING_SERVICE_URL",
    "http://billing-service:8003"
)
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

import httpx

from ..database import get_db
from ..models import Booking
from ..schemas import BookingCreate, BookingResponse


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


ROOM_SERVICE_URL = "http://127.0.0.1:8001"

BILLING_SERVICE_URL = "http://127.0.0.1:8003"


@router.post("/", response_model=BookingResponse)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):

    try:

        response = httpx.get(
            f"{ROOM_SERVICE_URL}/rooms/by-number/{booking.room_number}",
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Room Service is unavailable"
        )


    if response.status_code == 404:

        raise HTTPException(
            status_code=404,
            detail="Room does not exist"
        )


    if response.status_code != 200:

        raise HTTPException(
            status_code=503,
            detail="Room Service returned an error"
        )


    room = response.json()


    if room["status"] != "available":

        raise HTTPException(
            status_code=400,
            detail="Room is not available"
        )


    new_booking = Booking(

        guest_name=booking.guest_name,

        guest_email=booking.guest_email,

        room_id=room["id"],

        room_number=room["room_number"],

        check_in=booking.check_in,

        check_out=booking.check_out,

        status="confirmed"
    )


    db.add(new_booking)

    db.commit()

    db.refresh(new_booking)


    return new_booking


@router.get("/", response_model=list[BookingResponse])
def get_bookings(
    db: Session = Depends(get_db)
):

    bookings = db.query(Booking).all()

    return bookings


@router.get("/room/{room_id}/active")
def get_active_booking_for_room(
    room_id: int,
    db: Session = Depends(get_db)
):

    booking = (
        db.query(Booking)
        .filter(
            Booking.room_id == room_id,
            Booking.status == "confirmed"
        )
        .first()
    )


    if not booking:

        raise HTTPException(
            status_code=404,
            detail="No active booking for this room"
        )


    return {
        "booking_id": booking.id,
        "guest_name": booking.guest_name,
        "guest_email": booking.guest_email,
        "room_id": booking.room_id,
        "room_number": booking.room_number,
        "check_in": booking.check_in,
        "check_out": booking.check_out,
        "status": booking.status
    }


@router.get("/internal/{booking_id}", response_model=BookingResponse)
def get_booking_internal(
    booking_id: int,
    db: Session = Depends(get_db)
):

    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )


    if not booking:

        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )


    return booking


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):

    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )


    if not booking:

        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )


    return booking


@router.get("/{booking_id}/payment-status")
def get_booking_payment_status(
    booking_id: int,
    db: Session = Depends(get_db)
):

    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )


    if not booking:

        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )


    try:

        response = httpx.get(
            f"{BILLING_SERVICE_URL}/billing/booking/{booking_id}/status",
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Billing Service is unavailable"
        )


    if response.status_code == 404:

        return {
            "booking_id": booking_id,
            "payment_status": "not_generated"
        }


    if response.status_code != 200:

        raise HTTPException(
            status_code=503,
            detail="Billing Service returned an error"
        )


    return response.json()
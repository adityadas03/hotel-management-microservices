import os
import requests

from fastapi import APIRouter, HTTPException

router = APIRouter()


ROOM_SERVICE_URL = os.getenv(
    "ROOM_SERVICE_URL",
    "http://room-service:8001"
)

BILLING_SERVICE_URL = os.getenv(
    "BILLING_SERVICE_URL",
    "http://billing-service:8003"
)


@router.post("/bookings")
def create_booking(booking: dict):

    room_number = booking.get("room_number")

    if room_number is None:
        raise HTTPException(
            status_code=400,
            detail="Room number is required"
        )

    # --------------------------------------------------
    # STEP 1: Check Room Service
    # --------------------------------------------------

    try:
        room_response = requests.get(
            f"{ROOM_SERVICE_URL}/rooms/{room_number}",
            timeout=5
        )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Room Service is unavailable"
        )

    if room_response.status_code != 200:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    room_data = room_response.json()

    if room_data.get("is_booked") is True:
        raise HTTPException(
            status_code=400,
            detail="Room is already booked"
        )

    # --------------------------------------------------
    # STEP 2: Book the Room
    # --------------------------------------------------

    try:
        update_response = requests.put(
            f"{ROOM_SERVICE_URL}/rooms/{room_number}/book",
            timeout=5
        )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Unable to communicate with Room Service"
        )

    if update_response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail="Unable to update room status"
        )

    # --------------------------------------------------
    # STEP 3: Prepare Booking Data
    # --------------------------------------------------

    booking_data = {
        "guest_name": booking.get("guest_name"),
        "guest_email": booking.get("guest_email"),
        "room_number": room_number,
        "check_in": booking.get("check_in"),
        "check_out": booking.get("check_out")
    }

    # --------------------------------------------------
    # STEP 4: Send Billing Request
    # --------------------------------------------------

    try:
        billing_response = requests.post(
            f"{BILLING_SERVICE_URL}/billing",
            json=booking_data,
            timeout=5
        )

    except requests.exceptions.RequestException:

        # Roll back room booking if Billing Service fails
        try:
            requests.put(
                f"{ROOM_SERVICE_URL}/rooms/{room_number}/release",
                timeout=5
            )
        except requests.exceptions.RequestException:
            pass

        raise HTTPException(
            status_code=503,
            detail="Billing Service is unavailable"
        )

    # --------------------------------------------------
    # STEP 5: Check Billing Response
    # --------------------------------------------------

    if billing_response.status_code not in [200, 201]:

        # Roll back room booking
        try:
            requests.put(
                f"{ROOM_SERVICE_URL}/rooms/{room_number}/release",
                timeout=5
            )
        except requests.exceptions.RequestException:
            pass

        raise HTTPException(
            status_code=500,
            detail="Unable to create billing record"
        )

    # --------------------------------------------------
    # STEP 6: Return Successful Booking
    # --------------------------------------------------

    return {
        "message": "Booking created successfully",
        "booking": booking_data,
        "billing": billing_response.json()
    }


@router.get("/")
def booking_service_status():

    return {
        "service": "Booking Service",
        "status": "running"
    }
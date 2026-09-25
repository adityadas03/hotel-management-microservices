import os
import httpx
ROOM_SERVICE_URL = os.getenv(
    "ROOM_SERVICE_URL",
    "http://127.0.0.1:8001"
)

BOOKING_SERVICE_URL = os.getenv(
    "BOOKING_SERVICE_URL",
    "http://127.0.0.1:8002"
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import httpx

from app.database import get_db
from app import models, schemas


router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)


# ---------------------------------------------------------
# SERVICE URLs
# ---------------------------------------------------------

BOOKING_SERVICE_URL = "http://booking-service:8002"
ROOM_SERVICE_URL = "http://room-service:8001"


# ---------------------------------------------------------
# 1. CREATE BILL
# ---------------------------------------------------------

@router.post("/", response_model=schemas.BillResponse)
def create_bill(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Check whether a bill already exists for this booking
    # -----------------------------------------------------

    existing_bill = (
        db.query(models.Bill)
        .filter(models.Bill.booking_id == bill.booking_id)
        .first()
    )

    if existing_bill:
        raise HTTPException(
            status_code=400,
            detail="A bill already exists for this booking."
        )


    # -----------------------------------------------------
    # Contact Booking Service
    # -----------------------------------------------------

    try:
        booking_response = httpx.get(
            f"{BOOKING_SERVICE_URL}/bookings/internal/{bill.booking_id}",
            timeout=5
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Booking Service is unavailable."
        )


    if booking_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Booking not found."
        )

    if booking_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unable to get booking information."
        )


    booking = booking_response.json()


    # -----------------------------------------------------
    # Get room number from booking
    # -----------------------------------------------------

    room_number = booking["room_number"]


    # -----------------------------------------------------
    # Contact Room Service
    # -----------------------------------------------------

    try:
        room_response = httpx.get(
            f"{ROOM_SERVICE_URL}/rooms/by-number/{room_number}",
            timeout=5
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Room Service is unavailable."
        )


    if room_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Room not found."
        )

    if room_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unable to get room information."
        )


    room = room_response.json()


    # -----------------------------------------------------
    # Calculate number of nights
    # -----------------------------------------------------

    try:
        check_in = datetime.strptime(
            booking["check_in"],
            "%Y-%m-%d"
        ).date()

        check_out = datetime.strptime(
            booking["check_out"],
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid booking date format."
        )


    nights = (check_out - check_in).days


    if nights <= 0:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date."
        )


    # -----------------------------------------------------
    # Calculate charges
    # -----------------------------------------------------

    price_per_night = float(room["price_per_night"])

    room_charge = price_per_night * nights

    additional_charge = float(bill.additional_charge)

    total_amount = room_charge + additional_charge


    # -----------------------------------------------------
    # Create Billing Database Record
    # -----------------------------------------------------

    new_bill = models.Bill(
        booking_id=bill.booking_id,
        room_charge=room_charge,
        additional_charge=additional_charge,
        total_amount=total_amount,
        payment_status="pending"
    )


    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)


    return new_bill


# ---------------------------------------------------------
# 2. GET ALL BILLS
# ---------------------------------------------------------

@router.get("/", response_model=list[schemas.BillResponse])
def get_all_bills(
    db: Session = Depends(get_db)
):

    bills = db.query(models.Bill).all()

    return bills


# ---------------------------------------------------------
# 3. GET PAYMENT STATUS FOR A BOOKING
# ---------------------------------------------------------

@router.get(
    "/booking/{booking_id}/status"
)
def get_payment_status(
    booking_id: int,
    db: Session = Depends(get_db)
):

    bill = (
        db.query(models.Bill)
        .filter(models.Bill.booking_id == booking_id)
        .first()
    )


    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found for this booking."
        )


    return {
        "booking_id": booking_id,
        "bill_id": bill.id,
        "payment_status": bill.payment_status,
        "total_amount": bill.total_amount
    }


# ---------------------------------------------------------
# 4. GET BILL DETAILS WITH BOOKING INFORMATION
# ---------------------------------------------------------

@router.get(
    "/{bill_id}/details"
)
def get_bill_details(
    bill_id: int,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Find bill
    # -----------------------------------------------------

    bill = (
        db.query(models.Bill)
        .filter(models.Bill.id == bill_id)
        .first()
    )


    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found."
        )


    # -----------------------------------------------------
    # Contact Booking Service
    # -----------------------------------------------------

    try:
        booking_response = httpx.get(
            f"{BOOKING_SERVICE_URL}/bookings/internal/{bill.booking_id}",
            timeout=5
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Booking Service is unavailable."
        )


    if booking_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Booking not found."
        )

    if booking_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unable to get booking information."
        )


    booking = booking_response.json()


    # -----------------------------------------------------
    # Return combined information
    # -----------------------------------------------------

    return {
        "bill": {
            "id": bill.id,
            "booking_id": bill.booking_id,
            "room_charge": bill.room_charge,
            "additional_charge": bill.additional_charge,
            "total_amount": bill.total_amount,
            "payment_status": bill.payment_status
        },

        "booking": booking
    }


# ---------------------------------------------------------
# 5. UPDATE PAYMENT STATUS
# ---------------------------------------------------------

@router.put(
    "/{bill_id}/payment",
    response_model=schemas.BillResponse
)
def update_payment(
    bill_id: int,
    db: Session = Depends(get_db)
):

    bill = (
        db.query(models.Bill)
        .filter(models.Bill.id == bill_id)
        .first()
    )


    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found."
        )


    # -----------------------------------------------------
    # Change payment status
    # -----------------------------------------------------

    if bill.payment_status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Bill is already marked as paid."
        )


    bill.payment_status = "paid"

    db.commit()
    db.refresh(bill)


    return bill


# ---------------------------------------------------------
# 6. GET SINGLE BILL
# ---------------------------------------------------------

@router.get(
    "/{bill_id}",
    response_model=schemas.BillResponse
)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):

    bill = (
        db.query(models.Bill)
        .filter(models.Bill.id == bill_id)
        .first()
    )


    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found."
        )


    return bill
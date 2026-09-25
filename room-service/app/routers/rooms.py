import os
import httpx
BOOKING_SERVICE_URL = os.getenv(
    "BOOKING_SERVICE_URL",
    "http://127.0.0.1:8002"
)
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

import httpx

from ..database import get_db
from ..models import Room
from ..schemas import RoomCreate, RoomResponse


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


BOOKING_SERVICE_URL = "http://127.0.0.1:8002"


# CREATE ROOM
@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):

    existing_room = (
        db.query(Room)
        .filter(Room.room_number == room.room_number)
        .first()
    )

    if existing_room:
        raise HTTPException(
            status_code=400,
            detail="Room number already exists"
        )

    new_room = Room(
        room_number=room.room_number,
        room_type=room.room_type,
        price_per_night=room.price_per_night,
        status=room.status
    )

    db.add(new_room)

    db.commit()

    db.refresh(new_room)

    return new_room


# GET ALL ROOMS
@router.get("/", response_model=list[RoomResponse])
def get_rooms(
    db: Session = Depends(get_db)
):

    rooms = db.query(Room).all()

    return rooms


# GET ROOM BY ROOM NUMBER
@router.get("/by-number/{room_number}", response_model=RoomResponse)
def get_room_by_number(
    room_number: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.room_number == room_number)
        .first()
    )

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return room


# CHECK ROOM AVAILABILITY
@router.get("/availability/{room_number}")
def check_room_availability(
    room_number: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.room_number == room_number)
        .first()
    )

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return {
        "room_number": room.room_number,
        "status": room.status,
        "available": room.status == "available"
    }


# ROOM SERVICE → BOOKING SERVICE
@router.get("/{room_id}/booking-summary")
def get_room_booking_summary(
    room_id: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    try:

        response = httpx.get(
            f"{BOOKING_SERVICE_URL}/bookings/room/{room_id}/active",
            timeout=5.0
        )

        if response.status_code == 404:

            return {
                "room_id": room.id,
                "room_number": room.room_number,
                "booking": None,
                "message": "No active booking"
            }

        if response.status_code != 200:

            raise HTTPException(
                status_code=503,
                detail="Booking Service unavailable"
            )

        booking_data = response.json()

        return {
            "room_id": room.id,
            "room_number": room.room_number,
            "booking": booking_data
        }

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Could not connect to Booking Service"
        )


# GET ROOM BY ID
@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:

        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    return room


# UPDATE ROOM
@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomCreate,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:

        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    room.room_number = room_data.room_number
    room.room_type = room_data.room_type
    room.price_per_night = room_data.price_per_night
    room.status = room_data.status

    db.commit()

    db.refresh(room)

    return room


# DELETE ROOM
@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db)
):

    room = (
        db.query(Room)
        .filter(Room.id == room_id)
        .first()
    )

    if not room:

        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    db.delete(room)

    db.commit()

    return {
        "message": "Room deleted successfully"
    }
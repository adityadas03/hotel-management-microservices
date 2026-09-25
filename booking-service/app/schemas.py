from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):

    guest_name: str

    guest_email: str

    room_number: int

    check_in: str

    check_out: str


class BookingResponse(BaseModel):

    id: int

    guest_name: str

    guest_email: str

    room_id: int

    room_number: int

    check_in: str

    check_out: str

    status: str

    model_config = ConfigDict(
        from_attributes=True
    )
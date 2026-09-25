from pydantic import BaseModel, Field, ConfigDict


class BillCreate(BaseModel):

    booking_id: int

    additional_charge: float = Field(
        default=0,
        ge=0
    )


class BillResponse(BaseModel):

    id: int

    booking_id: int

    room_charge: float

    additional_charge: float

    total_amount: float

    payment_status: str

    model_config = ConfigDict(
        from_attributes=True
    )
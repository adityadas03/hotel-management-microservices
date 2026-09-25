from pydantic import BaseModel, Field, ConfigDict


class RoomCreate(BaseModel):

    room_number: int

    room_type: str

    price_per_night: float = Field(gt=0)

    status: str = "available"


class RoomResponse(BaseModel):

    id: int

    room_number: int

    room_type: str

    price_per_night: float

    status: str

    model_config = ConfigDict(from_attributes=True)
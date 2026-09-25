from sqlalchemy import Column, Integer, String


from .database import Base


class Booking(Base):

    __tablename__ = "bookings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    guest_name = Column(
        String,
        nullable=False
    )

    guest_email = Column(
        String,
        nullable=False
    )

    room_id = Column(
        Integer,
        nullable=False
    )

    room_number = Column(
        Integer,
        nullable=False
    )

    check_in = Column(
        String,
        nullable=False
    )

    check_out = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="confirmed"
    )
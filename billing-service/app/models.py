from sqlalchemy import Column, Integer, Float, String


from .database import Base


class Bill(Base):

    __tablename__ = "bills"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    booking_id = Column(
        Integer,
        nullable=False
    )


    room_charge = Column(
        Float,
        nullable=False
    )


    additional_charge = Column(
        Float,
        default=0
    )


    total_amount = Column(
        Float,
        nullable=False
    )


    payment_status = Column(
        String,
        nullable=False,
        default="pending"
    )
from fastapi import FastAPI

from .database import Base, engine

from .routers.bookings import router as booking_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Hotel Booking Microservice",
    description="Booking Management Service using FastAPI and SQLite",
    version="1.0.0"
)


app.include_router(booking_router)


@app.get("/")
def root():

    return {
        "message": "Hotel Booking Microservice is running"
    }
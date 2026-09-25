from fastapi import FastAPI

from .database import Base, engine
from .routers.rooms import router as room_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Hotel Room Management Microservice",
    description="Room Management Service using FastAPI and SQLite",
    version="1.0.0"
)


app.include_router(room_router)


@app.get("/")
def root():

    return {
        "message": "Hotel Room Management Microservice is running"
    }
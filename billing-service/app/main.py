from fastapi import FastAPI

from .database import Base, engine

from .routers.billing import router as billing_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Hotel Billing Microservice",
    description="Billing Management Service using FastAPI and SQLite",
    version="1.0.0"
)


app.include_router(billing_router)


@app.get("/")
def root():

    return {
        "message": "Hotel Billing Microservice is running"
    }
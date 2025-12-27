from fastapi import FastAPI
from app.db.database import create_db_and_tables
from app.routers import exercises
# We import models here so SQLModel "knows" they exist before creating tables
from app.db import models 

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(exercises.router)

@app.get("/")
def root():
    return {"message": "Gym Tracker API is running"}
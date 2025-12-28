from fastapi import FastAPI
from app.db.database import create_db_and_tables
from app.routers import exercises, workouts
# We import models here so SQLModel "knows" they exist before creating tables
from app.db import models 

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(exercises.router)
app.include_router(workouts.router) # Add this line

@app.get("/")
def root():
    return {"message": "Gym Tracker API is running"}
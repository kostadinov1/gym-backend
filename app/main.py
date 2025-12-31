from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import create_db_and_tables
from app.routers import exercises, workouts, history, plans, auth
# We import models here so SQLModel "knows" they exist before creating tables
from app.db import models 

# Define the lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # This runs before the app starts accepting requests
    create_db_and_tables()
    print("✅ Database tables verified/created.")
    
    yield # The app runs while execution pauses here
    
    # --- SHUTDOWN LOGIC ---
    # This runs when you press Ctrl+C
    print("🛑 Shutting down Gym Tracker API...")

# Initialize FastAPI with the lifespan
app = FastAPI(lifespan=lifespan)

# Register Routers
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(history.router)
app.include_router(plans.router)


@app.get("/")
def root():
    return {"message": "Gym Tracker API is running"}
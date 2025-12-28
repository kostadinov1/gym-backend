from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# What a single set looks like when sent from the phone
class SessionSetCreate(BaseModel):
    exercise_id: uuid.UUID
    set_number: int
    reps: int
    weight: float
    is_completed: bool

# What the whole finished workout looks like
class SessionCreate(BaseModel):
    routine_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    sets: List[SessionSetCreate]

# What we return after saving
class SessionRead(BaseModel):
    id: uuid.UUID
    status: str
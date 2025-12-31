from pydantic import BaseModel, EmailStr
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str
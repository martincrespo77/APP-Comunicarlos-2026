from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ---- DTOs for User ----
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

# ---- DTOs for Message ----
class MessageCreate(BaseModel):
    sender_id: str
    receiver_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime
    read: bool

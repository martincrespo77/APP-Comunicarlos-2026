from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional

class User(Document):
    name: str
    email: str
    role: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

class Message(Document):
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False

    class Settings:
        name = "messages"

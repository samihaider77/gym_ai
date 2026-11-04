"""
User Domain Layer

Contains pure domain entities, interface abstractions, and business rules.
No framework imports (FastAPI, SQLAlchemy, Pydantic) belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class UserEntity:
    """
    Pure domain representation of a User entity.
    """
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    password_hash: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

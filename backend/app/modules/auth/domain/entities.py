"""
Auth Domain Layer

Contains pure domain entities and token abstractions.
"""
from dataclasses import dataclass


@dataclass
class TokenEntity:
    """
    Pure domain representation of an issued Authentication Token pair.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

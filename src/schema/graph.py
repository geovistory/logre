from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel

class Graph(BaseModel):
    """A Graph object."""

    uri: str = None
    label: Optional[str] = None
    comment: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the Graph instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Graph':
        """Create an Graph instance from a dictionary"""
        return cls(**data)
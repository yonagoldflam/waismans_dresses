from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SlotBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="Monday is 0 and Sunday is 6")
    start_time: time = Field(..., description="Slot start time")
    end_time: time = Field(..., description="Slot end time")
    max_capacity: int = Field(default=1, ge=1, description="Maximum simultaneous appointments")


class SlotCreate(SlotBase):
    """Payload used to create a weekly availability slot."""

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, value: time, info) -> time:
        """Ensure that the slot ends after it starts."""
        start_time = info.data.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be strictly after start_time")
        return value


class SlotResponse(SlotBase):
    """Slot data returned by the API."""

    id: UUID

    class Config:
        from_attributes = True

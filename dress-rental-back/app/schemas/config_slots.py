from datetime import time
from pydantic import BaseModel, Field, field_validator


class SlotBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0 = Monday, 6 = Sunday (Python datetime convention)")
    start_time: time = Field(..., description="When the slot starts (e.g., 10:00)")
    end_time: time = Field(..., description="When the slot ends (e.g., 11:00)")
    max_capacity: int = Field(default=1, ge=1,
                              description="How many appointments can be booked simultaneously in this slot")


class SlotCreate(SlotBase):
    """סכמה שהאדמין שולח כדי ליצור חלון זמן חדש במערכת"""

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: time, info) -> time:
        """ולידציה עסקית: מבטיחה ששעת הסיום היא אחרי שעת ההתחלה"""
        start_time = info.data.get("start_time")
        if start_time and v <= start_time:
            raise ValueError("end_time must be strictly after start_time")
        return v


class SlotResponse(SlotBase):
    """התשובה שחוזרת ל-UI של האדמין כדי להציג את הסלוטים הקיימים"""
    id: int

    class Config:
        from_attributes = True
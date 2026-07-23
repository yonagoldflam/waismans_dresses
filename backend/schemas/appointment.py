from datetime import date, time
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class AppointmentBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, examples=["Jane Doe"])
    customer_phone: str = Field(..., examples=["0501234567"])
    customer_email: EmailStr = Field(..., examples=["customer@example.com"])
    slot_date: date = Field(..., description="Appointment date in YYYY-MM-DD format")
    start_time: time = Field(..., description="Appointment start time in HH:MM format")

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Normalize and validate an Israeli or international phone number."""
        cleaned = re.sub(r"[\s\-]", "", value)
        if not re.match(r"^05\d{8}$|^\+?\d{9,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("slot_date")
    @classmethod
    def validate_future_date(cls, value: date) -> date:
        """Reject appointment dates before the current date."""
        if value < date.today():
            raise ValueError("Appointment date cannot be in the past")
        return value


class AppointmentCreate(AppointmentBase):
    """Payload used to create an appointment."""


class AppointmentResponse(AppointmentBase):
    """Appointment data returned by the API."""

    id: UUID
    status: str = Field(default="PENDING")

    class Config:
        from_attributes = True

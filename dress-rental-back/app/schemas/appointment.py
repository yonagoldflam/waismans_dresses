from datetime import date, time
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class AppointmentBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, examples=["ישראל ישראלי"])
    customer_phone: str = Field(..., examples=["0501234567"])
    customer_email: EmailStr = Field(..., examples=["customer@example.com"])
    slot_date: date = Field(..., description="The specific date for the appointment (YYYY-MM-DD)")
    start_time: time = Field(..., description="The start time of the appointment (HH:MM)")

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """ולידציה בסיסית לטלפון ישראלי/בינלאומי כדי למנוע זבל בבסיס הנתונים"""
        cleaned = re.sub(r"[\s\-]", "", v) # הסרת רווחים ומקפים
        if not re.match(r"^05\d{8}$|^\+?\d{9,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned

    @field_validator("slot_date")
    @classmethod
    def validate_date_not_past(cls, v: date) -> date:
        """מניעת קביעת תורים לעבר"""
        if v < date.today():
            raise ValueError("Appointment date cannot be in the past")
        return v


class AppointmentCreate(AppointmentBase):
    """סכמה שמייצגת את ה-Body שה-UI שולח בזמן קביעת תור חדש"""
    pass


class AppointmentResponse(AppointmentBase):
    """סכמה שמגדירה בדיוק מה חוזר ל-UI (למשל לפאנל האדמין) לאחר שליפה"""
    id: UUID  # ב-AWS DSQL נרצה להשתמש ב-UUIDs ל-Primary Keys של ישויות משתנות
    status: str = Field(default="PENDING")

    class Config:
        # מאפשר ל-Pydantic לקרוא גם ממילונים (dict) וגם מאובייקטים
        from_attributes = True

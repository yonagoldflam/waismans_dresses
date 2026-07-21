from pydantic import BaseModel, EmailStr
from datetime import datetime, date, time
from typing import List, Optional

class ReceptionTimeBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    slot_duration_minutes: int = 60

class ReceptionTimeCreate(ReceptionTimeBase):
    pass

class ReceptionTimeRead(ReceptionTimeBase):
    id: int

class AppointmentBase(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    appointment_time: datetime
    reception_time_id: int

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentRead(AppointmentBase):
    id: int
    created_at: datetime

class SlotAvailability(BaseModel):
    time: datetime
    is_available: bool

class DayAvailability(BaseModel):
    date: date
    slots: List[SlotAvailability]

class AdminAuth(BaseModel):
    password: str

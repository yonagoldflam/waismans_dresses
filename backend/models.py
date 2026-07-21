from datetime import datetime, date, time
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class ReceptionTime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date = Field(index=True)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=60)
    
    appointments: List["Appointment"] = Relationship(back_populates="reception_time")

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reception_time_id: int = Field(foreign_key="receptiontime.id")
    customer_name: str
    customer_email: str
    customer_phone: str
    appointment_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    reception_time: ReceptionTime = Relationship(back_populates="appointments")

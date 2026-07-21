from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta, date as date_type
from typing import List
from ..database import get_session
from ..models import ReceptionTime, Appointment
from ..schemas import AppointmentCreate, AppointmentRead, DayAvailability, SlotAvailability
from ..logger import logger

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/availability/{date}", response_model=DayAvailability)
async def get_availability(date: date_type, session: AsyncSession = Depends(get_session)):
    logger.info(f"Checking availability for date: {date}")
    
    # Get reception times for the day
    statement = select(ReceptionTime).where(ReceptionTime.date == date)
    result = await session.execute(statement)
    reception_times = result.scalars().all()
    
    if not reception_times:
        return DayAvailability(date=date, slots=[])

    # Get booked appointments for the day
    statement_appts = select(Appointment).join(ReceptionTime).where(ReceptionTime.date == date)
    result_appts = await session.execute(statement_appts)
    booked_appointments = result_appts.scalars().all()
    booked_times = {appt.appointment_time for appt in booked_appointments}

    slots = []
    for rt in reception_times:
        current_time = datetime.combine(rt.date, rt.start_time)
        end_time = datetime.combine(rt.date, rt.end_time)
        
        while current_time < end_time:
            slots.append(SlotAvailability(
                time=current_time,
                is_available=current_time not in booked_times
            ))
            current_time += timedelta(minutes=rt.slot_duration_minutes)
    
    return DayAvailability(date=date, slots=slots)

@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(appointment: AppointmentCreate, session: AsyncSession = Depends(get_session)):
    logger.info(f"Attempting to create appointment for {appointment.customer_email} at {appointment.appointment_time}")
    
    # Verify slot is still available
    # First, find if the reception_time_id exists and matches the date
    rt_statement = select(ReceptionTime).where(ReceptionTime.id == appointment.reception_time_id)
    rt_result = await session.execute(rt_statement)
    reception_time = rt_result.scalar_one_or_none()
    
    if not reception_time:
        logger.error(f"Reception time ID {appointment.reception_time_id} not found")
        raise HTTPException(status_code=404, detail="Reception time not found")

    # Check if already booked
    appt_statement = select(Appointment).where(Appointment.appointment_time == appointment.appointment_time)
    appt_result = await session.execute(appt_statement)
    if appt_result.scalar_one_or_none():
        logger.warning(f"Slot {appointment.appointment_time} already booked")
        raise HTTPException(status_code=400, detail="This slot is already booked")

    new_appointment = Appointment.from_orm(appointment)
    session.add(new_appointment)
    await session.commit()
    await session.refresh(new_appointment)
    
    logger.info(f"Appointment created successfully: {new_appointment.id}")
    return new_appointment

from datetime import date

from fastapi import HTTPException, status
from psycopg import AsyncConnection

from core.logger import logger
from db.repositories import AppointmentRepository, SlotRepository
from schemas.appointment import AppointmentCreate


class AppointmentService:
    @staticmethod
    async def get_available_slots(conn: AsyncConnection, target_date: date):
        """Return weekly slots that still have capacity on the requested date."""
        slots = await SlotRepository.get_slots_by_day_of_week(conn, target_date.weekday())
        if not slots:
            return []

        appointments = await AppointmentRepository.get_by_date(conn, target_date)
        available_slots = []
        for slot in slots:
            booked_count = sum(appointment["start_time"] == slot["start_time"] for appointment in appointments)
            remaining_capacity = slot["max_capacity"] - booked_count
            if remaining_capacity > 0:
                available_slots.append({
                    "slot_id": slot["id"],
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "slots_remaining": remaining_capacity,
                })
        return available_slots

    @staticmethod
    async def book_appointment(conn: AsyncConnection, appointment_data: AppointmentCreate):
        """Create an appointment when the requested slot is configured and available."""
        slot = await SlotRepository.get_slot_by_day_and_time(
            conn, appointment_data.slot_date.weekday(), appointment_data.start_time
        )
        if not slot:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected time slot is not available")

        booked_count = await AppointmentRepository.count_booked_slots(
            conn, appointment_data.slot_date, appointment_data.start_time
        )
        if booked_count >= slot["max_capacity"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This time slot is fully booked")

        logger.info("Creating appointment for %s", appointment_data.customer_name)
        return await AppointmentRepository.create(conn, appointment_data.model_dump())

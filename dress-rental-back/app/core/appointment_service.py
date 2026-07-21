from datetime import date
from psycopg import AsyncConnection
from app.db.repositories import AppointmentRepository, SlotRepository
from app.schemas.appointment import AppointmentCreate
from fastapi import HTTPException, status
from app.core.logger import logger


class AppointmentService:

    @staticmethod
    async def get_available_slots(conn: AsyncConnection, target_date: date):
        logger.info(f"Fetching available slots via Psycopg for date: {target_date}")

        day_of_week = target_date.weekday()
        slots = await SlotRepository.get_slots_by_day_of_week(conn, day_of_week)

        if not slots:
            logger.info(f"No slots configured for day of week: {day_of_week}")
            return []

        appointments = await AppointmentRepository.get_by_date(conn, target_date)

        available_list = []
        for slot in slots:
            # הגישה היא עכשיו כמילון (dict) כי אנחנו עובדים עם psycopg raw rows
            booked_count = sum(1 for app in appointments if app["start_time"] == slot["start_time"])
            slots_left = slot["max_capacity"] - booked_count

            if slots_left > 0:
                available_list.append({
                    "slot_id": slot["id"],
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "slots_remaining": slots_left
                })

        logger.info(f"Found {len(available_list)} available slots for {target_date}")
        return available_list

    @staticmethod
    async def book_appointment(conn: AsyncConnection, appointment_data: AppointmentCreate):
        logger.info(f"Attempting to book appointment for {appointment_data.customer_name} via Psycopg")

        day_of_week = appointment_data.slot_date.weekday()
        slot = await SlotRepository.get_slot_by_day_and_time(conn, day_of_week, appointment_data.start_time)

        if not slot:
            logger.warning("Booking failed: Slot is not configured.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected time slot is not available")

        booked_count = await AppointmentRepository.count_booked_slots(
            conn, appointment_data.slot_date, appointment_data.start_time
        )

        if booked_count >= slot["max_capacity"]:
            logger.warning(f"Booking failed: Slot at {appointment_data.start_time} is fully booked.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This time slot is fully booked")

        # הפיכת ה-Pydantic Model למילון עבור ה-Repository
        saved_appointment = await AppointmentRepository.create(conn, appointment_data.model_dump())
        logger.info(f"Successfully booked appointment ID: {saved_appointment['id']}")
        return saved_appointment
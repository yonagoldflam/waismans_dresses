from uuid import UUID

from fastapi import HTTPException, status
from psycopg import AsyncConnection

from core.logger import logger
from db.repositories import AppointmentRepository, SlotRepository
from schemas.config_slots import SlotCreate


class AdminService:
    @staticmethod
    async def get_all_appointments(conn: AsyncConnection, limit: int = 100, offset: int = 0):
        """Return a paginated list of appointments for the admin panel."""
        return await AppointmentRepository.get_all_paginated(conn, limit, offset)

    @staticmethod
    async def get_all_slots(conn: AsyncConnection):
        """Return every configured weekly availability slot."""
        return await SlotRepository.get_all(conn)

    @staticmethod
    async def create_available_slot(conn: AsyncConnection, slot_data: SlotCreate):
        """Create a slot unless another slot already starts at the same day and time."""
        existing_slot = await SlotRepository.get_slot_by_day_and_time(
            conn, slot_data.day_of_week, slot_data.start_time
        )
        if existing_slot:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A slot for this day and time already exists")

        logger.info("Creating availability slot for day %s", slot_data.day_of_week)
        return await SlotRepository.create(conn, slot_data.model_dump())

    @staticmethod
    async def delete_available_slot(conn: AsyncConnection, slot_id: UUID):
        """Delete an existing availability slot."""
        slot = await SlotRepository.get_by_id(conn, slot_id)
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

        await SlotRepository.delete(conn, slot_id)
        return {"detail": "Slot deleted successfully"}

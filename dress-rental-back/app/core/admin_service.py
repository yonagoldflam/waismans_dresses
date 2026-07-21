from psycopg import AsyncConnection
from app.db.repositories import AppointmentRepository, SlotRepository
from app.schemas.config_slots import SlotCreate
from fastapi import HTTPException, status
from app.core.logger import logger

class AdminService:

    @staticmethod
    async def get_all_appointments(conn: AsyncConnection, limit: int = 100, offset: int = 0):
        """
        שליפת כל התורים במערכת עבור פאנל הניהול
        """
        logger.info(f"Admin fetching appointments via Psycopg. Limit: {limit}, Offset: {offset}")
        appointments = await AppointmentRepository.get_all_paginated(conn, limit, offset)
        logger.info(f"Admin successfully fetched {len(appointments)} appointments")
        return appointments

    @staticmethod
    async def create_available_slot(conn: AsyncConnection, slot_data: SlotCreate):
        """
        הגדרת חלון זמן חדש (סלוט) שבו לקוחות יוכלו להזמין תורים
        """
        logger.info(f"Admin creating new slot for day {slot_data.day_of_week} at {slot_data.start_time}")

        # מניעת כפילויות של אותו חלון זמן באותו יום בשבוע
        existing_slot = await SlotRepository.get_slot_by_day_and_time(
            conn, slot_data.day_of_week, slot_data.start_time
        )
        if existing_slot:
            logger.warning(f"Admin slot creation failed: Slot for day {slot_data.day_of_week} at {slot_data.start_time} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A slot for this day and time already exists."
            )

        # הפיכת ה-Pydantic model למילון ושליחתו ל-Repository
        saved_slot = await SlotRepository.create(conn, slot_data.model_dump())
        logger.info(f"Admin successfully created slot ID: {saved_slot['id']}")
        return saved_slot

    @staticmethod
    async def delete_available_slot(conn: AsyncConnection, slot_id: int):
        """
        מחיקת חלון זמן מהמערכת (כדי למנוע תורים עתידיים בשעה הזו)
        """
        logger.info(f"Admin requesting deletion of slot ID: {slot_id}")

        # וידוא שחלון הזמן אכן קיים לפני המחיקה
        slot = await SlotRepository.get_by_id(conn, slot_id)
        if not slot:
            logger.warning(f"Admin slot deletion failed: Slot ID {slot_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found"
            )

        await SlotRepository.delete(conn, slot_id)
        logger.info(f"Admin successfully deleted slot ID: {slot_id}")
        return {"detail": "Slot deleted successfully"}
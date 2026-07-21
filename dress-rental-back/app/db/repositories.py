from datetime import date, time
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from app.core.logger import logger

class AppointmentRepository:
    @staticmethod
    async def get_by_date(conn: AsyncConnection, target_date: date) -> list[dict]:
        """שליפת כל התורים שאינם מבוטלים לתאריך מסוים"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, customer_name, customer_phone, customer_email, slot_date, start_time, status 
                FROM appointments 
                WHERE slot_date = %s AND status != 'CANCELED';
                """,
                (target_date,)
            )
            return await cur.fetchall()

    @staticmethod
    async def count_booked_slots(conn: AsyncConnection, target_date: date, start_time: time) -> int:
        """ספירת כמות התורים הפעילים לחלון זמן ספציפי"""
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM appointments 
                WHERE slot_date = %s AND start_time = %s AND status != 'CANCELED';
                """,
                (target_date, start_time)
            )
            result = await cur.fetchone()
            return result[0] if result else 0

    @staticmethod
    async def create(conn: AsyncConnection, data: dict) -> dict:
        """שמירת תור חדש והחזרת השורה שנוצרה"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO appointments (customer_name, customer_phone, customer_email, slot_date, start_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, customer_name, customer_phone, customer_email, slot_date, start_time, status;
                """,
                (data["customer_name"], data["customer_phone"], data["customer_email"], data["slot_date"], data["start_time"], "PENDING")
            )
            return await cur.fetchone()

    @staticmethod
    async def get_all_paginated(conn: AsyncConnection, limit: int, offset: int) -> list[dict]:
        """שליפת כל התורים עבור פאנל הניהול"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, customer_name, customer_phone, customer_email, slot_date, start_time, status
                FROM appointments
                ORDER BY slot_date DESC, start_time ASC
                LIMIT %s OFFSET %s;
                """,
                (limit, offset)
            )
            return await cur.fetchall()


class SlotRepository:
    @staticmethod
    async def get_slots_by_day_of_week(conn: AsyncConnection, day_of_week: int) -> list[dict]:
        """שליפת חלונות הזמן שהוגדרו ליום מסוים בשבוע"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, day_of_week, start_time, end_time, max_capacity 
                FROM available_slots 
                WHERE day_of_week = %s;
                """,
                (day_of_week,)
            )
            return await cur.fetchall()

    @staticmethod
    async def get_slot_by_day_and_time(conn: AsyncConnection, day_of_week: int, start_time: time) -> dict | None:
        """שליפת חלון זמן ספציפי לפי יום ושעה (למניעת כפילויות)"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, day_of_week, start_time, end_time, max_capacity 
                FROM available_slots 
                WHERE day_of_week = %s AND start_time = %s;
                """,
                (day_of_week, start_time)
            )
            return await cur.fetchone()

    @staticmethod
    async def get_by_id(conn: AsyncConnection, slot_id: int) -> dict | None:
        """שליפת חלון זמן לפי ID"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT id, day_of_week, start_time, end_time, max_capacity FROM available_slots WHERE id = %s;",
                (slot_id,)
            )
            return await cur.fetchone()

    @staticmethod
    async def create(conn: AsyncConnection, data: dict) -> dict:
        """יצירת חלון זמן חדש"""
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO available_slots (day_of_week, start_time, end_time, max_capacity)
                VALUES (%s, %s, %s, %s)
                RETURNING id, day_of_week, start_time, end_time, max_capacity;
                """,
                (data["day_of_week"], data["start_time"], data["end_time"], data["max_capacity"])
            )
            return await cur.fetchone()

    @staticmethod
    async def delete(conn: AsyncConnection, slot_id: int) -> None:
        """מחיקת חלון זמן"""
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM available_slots WHERE id = %s;", (slot_id,))

    @staticmethod
    async def create_tables_if_not_exists(conn: AsyncConnection):
        create_table_query = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
        -- 1. טבלת חלונות זמן (סלוטים)
        CREATE TABLE IF NOT EXISTS available_slots (
            id SERIAL PRIMARY KEY,
            day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            max_capacity INT NOT NULL DEFAULT 1 CHECK (max_capacity >= 1),
            UNIQUE (day_of_week, start_time)
        );
    
        -- 2. טבלת תורים
        CREATE TABLE IF NOT EXISTS appointments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            customer_name VARCHAR(100) NOT NULL,
            customer_phone VARCHAR(20) NOT NULL,
            customer_email VARCHAR(255) NOT NULL,
            slot_date DATE NOT NULL,
            start_time TIME NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELED'))
        );
    
        -- אינדקסים לביצועים מהירים בשאילתות של ה-Repository
        CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments (slot_date, start_time);
        CREATE INDEX IF NOT EXISTS idx_slots_day ON available_slots (day_of_week);
        """
        logger.info("Checking and creating database tables if needed...")
        try:
            async with conn.cursor() as cur:
                await cur.execute(create_table_query)
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"failed create tables error: {e}")


from datetime import date, time
from uuid import UUID, uuid4

from psycopg import AsyncConnection
from psycopg.rows import dict_row


class AppointmentRepository:
    @staticmethod
    async def get_by_date(conn: AsyncConnection, target_date: date) -> list[dict]:
        """Return non-cancelled appointments for a given date."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, customer_name, customer_phone, customer_email, slot_date, start_time, status "
                "FROM appointments WHERE slot_date = %s AND status != 'CANCELED';",
                (target_date,),
            )
            return await cursor.fetchall()

    @staticmethod
    async def count_booked_slots(conn: AsyncConnection, target_date: date, start_time: time) -> int:
        """Count active appointments at a particular date and time."""
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM appointments WHERE slot_date = %s AND start_time = %s AND status != 'CANCELED';",
                (target_date, start_time),
            )
            result = await cursor.fetchone()
            return result[0] if result else 0

    @staticmethod
    async def create(conn: AsyncConnection, data: dict) -> dict:
        """Insert and return a new appointment."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "INSERT INTO appointments (id, customer_name, customer_phone, customer_email, slot_date, start_time, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "RETURNING id, customer_name, customer_phone, customer_email, slot_date, start_time, status;",
                (uuid4(), data["customer_name"], data["customer_phone"], data["customer_email"], data["slot_date"], data["start_time"], "PENDING"),
            )
            return await cursor.fetchone()

    @staticmethod
    async def get_all_paginated(conn: AsyncConnection, limit: int, offset: int) -> list[dict]:
        """Return a page of appointments ordered by date and time."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, customer_name, customer_phone, customer_email, slot_date, start_time, status "
                "FROM appointments ORDER BY slot_date DESC, start_time ASC LIMIT %s OFFSET %s;",
                (limit, offset),
            )
            return await cursor.fetchall()


class SlotRepository:
    @staticmethod
    async def get_slots_by_day_of_week(conn: AsyncConnection, day_of_week: int) -> list[dict]:
        """Return slots configured for the requested weekday."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, day_of_week, start_time, end_time, max_capacity FROM available_slots WHERE day_of_week = %s;",
                (day_of_week,),
            )
            return await cursor.fetchall()

    @staticmethod
    async def get_slot_by_day_and_time(conn: AsyncConnection, day_of_week: int, start_time: time) -> dict | None:
        """Return a slot identified by its weekday and start time."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, day_of_week, start_time, end_time, max_capacity FROM available_slots "
                "WHERE day_of_week = %s AND start_time = %s;",
                (day_of_week, start_time),
            )
            return await cursor.fetchone()

    @staticmethod
    async def get_all(conn: AsyncConnection) -> list[dict]:
        """Return all configured slots ordered by weekday and time."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, day_of_week, start_time, end_time, max_capacity FROM available_slots "
                "ORDER BY day_of_week, start_time;"
            )
            return await cursor.fetchall()

    @staticmethod
    async def get_by_id(conn: AsyncConnection, slot_id: UUID) -> dict | None:
        """Return one slot by UUID."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "SELECT id, day_of_week, start_time, end_time, max_capacity FROM available_slots WHERE id = %s;",
                (slot_id,),
            )
            return await cursor.fetchone()

    @staticmethod
    async def create(conn: AsyncConnection, data: dict) -> dict:
        """Insert and return a new weekly availability slot."""
        async with conn.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                "INSERT INTO available_slots (id, day_of_week, start_time, end_time, max_capacity) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, day_of_week, start_time, end_time, max_capacity;",
                (uuid4(), data["day_of_week"], data["start_time"], data["end_time"], data["max_capacity"]),
            )
            return await cursor.fetchone()

    @staticmethod
    async def delete(conn: AsyncConnection, slot_id: UUID) -> None:
        """Delete a slot by UUID."""
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM available_slots WHERE id = %s;", (slot_id,))

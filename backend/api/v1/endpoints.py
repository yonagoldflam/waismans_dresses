from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from psycopg import AsyncConnection

from api.dependencies import verify_admin_token
from app_controller import app_controller
from core.admin_service import AdminService
from core.appointment_service import AppointmentService
from schemas.appointment import AppointmentCreate, AppointmentResponse
from schemas.config_slots import SlotCreate, SlotResponse

router = APIRouter()


@router.get("/appointments/available-slots", status_code=status.HTTP_200_OK)
async def get_available_slots(
    target_date: date = Query(..., description="Date to check in YYYY-MM-DD format"),
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection),
):
    """List available appointment times for a date."""
    return await AppointmentService.get_available_slots(conn, target_date)


@router.post("/appointments/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_data: AppointmentCreate,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection),
):
    """Create a customer appointment."""
    return await AppointmentService.book_appointment(conn, appointment_data)


@router.get("/admin/appointments", dependencies=[Depends(verify_admin_token)])
async def get_all_appointments(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection),
):
    """List appointments for the admin panel."""
    return await AdminService.get_all_appointments(conn, limit=limit, offset=offset)


@router.get("/admin/slots", response_model=list[SlotResponse], dependencies=[Depends(verify_admin_token)])
async def get_all_slots(conn: AsyncConnection = Depends(app_controller.dsql_session.connection)):
    """List configured weekly availability slots."""
    return await AdminService.get_all_slots(conn)


@router.post("/admin/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_admin_token)])
async def create_available_slot(
    slot_data: SlotCreate,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection),
):
    """Create a weekly availability slot."""
    return await AdminService.create_available_slot(conn, slot_data)


@router.delete("/admin/slots/{slot_id}", dependencies=[Depends(verify_admin_token)])
async def delete_available_slot(
    slot_id: UUID,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection),
):
    """Delete a weekly availability slot."""
    return await AdminService.delete_available_slot(conn, slot_id)

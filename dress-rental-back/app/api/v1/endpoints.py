from datetime import date
from fastapi import APIRouter, Depends, Query, status
from psycopg import AsyncConnection

# ייבוא ה-Services וה-Dependencies
from app.core.appointment_service import AppointmentService
from app.core.admin_service import AdminService
from app.api.dependencies import verify_admin_token


# ייבוא הסכמות של Pydantic לטובת Validation
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.schemas.config_slots import SlotCreate

from app.app_controller import app_controller

router = APIRouter()

# ==========================================
# 👥 ממשק ציבורי - לקוחות (Public Endpoints)
# ==========================================

@router.get("/appointments/available-slots", status_code=status.HTTP_200_OK)
async def get_available_slots(
    target_date: date = Query(..., description="The date to check for available slots (YYYY-MM-DD)"),
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    """
    הצגת שעות פנויות ללקוחות לתאריך ספציפי
    """
    return await AppointmentService.get_available_slots(conn, target_date)


@router.post("/appointments/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_data: AppointmentCreate,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    """
    קביעת תור חדש על ידי הלקוח (כולל בדיקת Capacity אסינכרונית)
    """
    return await AppointmentService.book_appointment(conn, appointment_data)


# ==========================================
# 👑 ממשק מנהל - מוגן בסיסמה (Admin Endpoints)
# ==========================================

@router.get(
    "/admin/appointments",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_token)]
)
async def get_all_appointments(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    """
    פאנל ניהול: צפייה בכל התורים שנקבעו במערכת (כולל דפדוף Pagination)
    """
    return await AdminService.get_all_appointments(conn, limit=limit, offset=offset)


@router.post(
    "/admin/slots",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_token)]
)
async def create_available_slot(
    slot_data: SlotCreate,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    """
    פאנל ניהול: הגדרת חלון זמן קבוע חדש (למשל: ימי שני, 10:00 עד 11:00, מקסימום 2 לקוחות)
    """
    return await AdminService.create_available_slot(conn, slot_data)

@router.post("/appointments/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_data: AppointmentCreate, # ולידציה אוטומטית לקלט של הלקוח
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    return await AppointmentService.book_appointment(conn, appointment_data)


@router.delete(
    "/admin/slots/{slot_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_token)]
)
async def delete_available_slot(
    slot_id: int,
    conn: AsyncConnection = Depends(app_controller.dsql_session.connection)
):
    """
    פאנל ניהול: מחיקת חלון זמן כדי שלא יהיה ניתן להזמין בו תורים יותר
    """
    return await AdminService.delete_available_slot(conn, slot_id)
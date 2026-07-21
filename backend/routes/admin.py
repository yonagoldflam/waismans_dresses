from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from ..database import get_session
from ..models import ReceptionTime, Appointment
from ..schemas import ReceptionTimeCreate, ReceptionTimeRead, AppointmentRead, AdminAuth
from ..config import settings
from ..logger import logger

router = APIRouter(prefix="/admin", tags=["Admin"])

async def verify_admin(x_admin_password: str = Header(None)):
    if x_admin_password != settings.ADMIN_PASSWORD:
        logger.warning("Unauthorized admin access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )

@router.post("/reception-times", response_model=ReceptionTimeRead, dependencies=[Depends(verify_admin)])
async def create_reception_time(rt: ReceptionTimeCreate, session: AsyncSession = Depends(get_session)):
    logger.info(f"Admin creating reception time for {rt.date}")
    new_rt = ReceptionTime.from_orm(rt)
    session.add(new_rt)
    await session.commit()
    await session.refresh(new_rt)
    return new_rt

@router.get("/reception-times", response_model=List[ReceptionTimeRead], dependencies=[Depends(verify_admin)])
async def list_reception_times(session: AsyncSession = Depends(get_session)):
    statement = select(ReceptionTime).order_by(ReceptionTime.date.desc())
    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/appointments", response_model=List[AppointmentRead], dependencies=[Depends(verify_admin)])
async def list_all_appointments(session: AsyncSession = Depends(get_session)):
    logger.info("Admin fetching all appointments")
    statement = select(Appointment).order_by(Appointment.appointment_time.desc())
    result = await session.execute(statement)
    return result.scalars().all()

@router.post("/verify")
async def verify_password(auth: AdminAuth):
    if auth.password == settings.ADMIN_PASSWORD:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Invalid password")

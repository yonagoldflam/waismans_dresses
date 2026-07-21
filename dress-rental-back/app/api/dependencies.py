import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.logger import logger
from app.config import config

# שליפת סיסמת האדמין מהקונפיגורציה (רצוי להזריק דרך Secrets ב-EKS)
ADMIN_SECRET_KEY = config.ADMIN_SECRET_KEY

# תשתית ה-Bearer Token של FastAPI
security_bearer = HTTPBearer()


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """
    מגן על ה-Endpoints של האדמין.
    בודק שהטוקן (הסיסמה) שנשלח מה-UI תואם בדיוק לסיסמה המוגדרת בקונפיגורציה.
    """
    provided_token = credentials.credentials

    if provided_token != ADMIN_SECRET_KEY:
        logger.warning("Unauthorized access attempt to Admin Panel - Invalid password provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
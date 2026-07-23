from urllib.parse import unquote

from fastapi import Header, HTTPException, status

from config import config
from core.logger import logger

ADMIN_SECRET_KEY = config.ADMIN_SECRET_KEY


async def verify_admin_token(x_admin_token: str | None = Header(default=None)):
    """Validate the URL-encoded admin token sent by the standalone frontend."""
    provided_token = unquote(x_admin_token or "")

    if provided_token != ADMIN_SECRET_KEY:
        logger.warning("Unauthorized admin access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )
    return True

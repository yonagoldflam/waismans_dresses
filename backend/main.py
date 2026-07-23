import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.endpoints import router as v1_router
from app_controller import app_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the database connection when the API starts and close it on shutdown."""
    await app_controller.dsql_session.init()
    yield
    await app_controller.dsql_session.close()


# The frontend runs as a separate application. Set FRONTEND_ORIGINS in production,
# for example: https://app.example.com,https://admin.example.com
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://18.197.154.189,http://localhost:3000,http://localhost:5500",
).split(",")

app = FastAPI(title="Dress Rental API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],
)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

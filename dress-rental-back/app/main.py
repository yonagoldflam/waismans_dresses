import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from app.api.v1.endpoints import router as v1_router
from app.app_controller import app_controller

@asynccontextmanager
async def lifespan(app: FastAPI):
    await app_controller.dsql_session.init()
    yield
    await app_controller.dsql_session.close()

app = FastAPI(title="Dress Rental API", version="1.0.0", lifespan=lifespan)
app.include_router(v1_router, prefix="/api/v1")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def booking_page():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

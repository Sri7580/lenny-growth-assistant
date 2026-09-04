import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.api import health

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("lenny-growth-assistant")

app = FastAPI(title="Lenny Growth Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "detail": str(exc)})


@app.on_event("startup")
async def on_startup():
    logger.info("Starting up — initializing database schema")
    await init_db()


app.include_router(health.router)


@app.get("/")
async def root():
    return {"service": "lenny-growth-assistant", "status": "running"}

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, reports, resources
from app.api import tasks, dashboard, feedback
from app.core.config import settings
from app.core.database import engine
from app.models import ngo_resource, user_report  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [
        "https://your-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(resources.router)
app.include_router(reports.router)

# Phase 4
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)
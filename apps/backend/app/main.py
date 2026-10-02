from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import CORS_ORIGINS
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Waypoint Driver API",
    version="1.0.0",
    description="Driver backend: frozen route-snapshot provider + append-only event ledger + offline sync/conflict API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Support both /api/driver/... and /api/v1/driver/...
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Waypoint Driver API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
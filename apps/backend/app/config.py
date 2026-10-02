"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── JWT ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "waypoint-driver-hackathon-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8h shift
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# ── Database ─────────────────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "waypoint_driver.db")

# ── MinIO / S3 (photo evidence) ─────────────────────────────────────────
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "waypoint-evidence")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# ── CORS ─────────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

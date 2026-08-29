from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI Resume Analyzer API",
    version="0.1.0",
    description="Backend API for the AI Resume Analyzer MVP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "AI Resume Analyzer API", "status": "running"}

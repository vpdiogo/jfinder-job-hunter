from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.evaluations import router as evaluations_router
from app.api.jobs import router as jobs_router
from app.api.profiles import router as profiles_router
from app.settings import settings

app = FastAPI(
    title="JFinder",
    description="Agentic job-hunting system",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(evaluations_router)
app.include_router(jobs_router)
app.include_router(profiles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }

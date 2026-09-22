from fastapi import FastAPI

from app.settings import settings

app = FastAPI(
    title="JFinder",
    description="Agentic job-hunting system",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }

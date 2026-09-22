from app.domain.enums import JobStatus
from app.domain.models import Application


class ApplicationService:
    """Manage deterministic application state transitions."""

    def create(self, job_url: str) -> Application:
        return Application(
            job_url=job_url,
            status=JobStatus.DISCOVERED,
        )

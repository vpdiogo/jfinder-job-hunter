from abc import ABC, abstractmethod

from app.domain.models import Job


class JobCollector(ABC):
    @abstractmethod
    def collect(self) -> list[Job]:
        """Collect job opportunities from a source."""
        raise NotImplementedError

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.settings import settings


class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    connect_args = (
        {"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {}
    )
    return create_engine(settings.database_url, connect_args=connect_args)


def create_database() -> None:
    from app.repositories import tables  # noqa: F401

    Base.metadata.create_all(get_engine())


def get_session() -> Generator[Session]:
    create_database()
    with Session(get_engine()) as session:
        yield session

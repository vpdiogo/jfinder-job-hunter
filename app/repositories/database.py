from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
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

    engine = get_engine()
    Base.metadata.create_all(engine)
    _upgrade_sqlite(engine)


def _upgrade_sqlite(engine: Engine) -> None:
    """Apply additive schema changes for the local SQLite development database."""
    if not engine.url.drivername.startswith("sqlite"):
        return

    additions = {
        "career_profiles": {
            "name": "VARCHAR(100)",
            "desired_seniority": "VARCHAR(50)",
            "work_modes": "JSON",
            "locations": "JSON",
            "timezones": "JSON",
            "salary_min": "FLOAT",
            "salary_max": "FLOAT",
            "languages": "JSON",
            "required_technologies": "JSON",
            "desired_technologies": "JSON",
        },
        "jobs": {
            "responsibilities": "JSON",
            "source": "VARCHAR(50)",
            "focus_profile_id": "INTEGER",
            "required_technologies": "JSON",
            "desired_technologies": "JSON",
            "seniority": "VARCHAR(50)",
            "work_mode": "VARCHAR(50)",
            "location": "VARCHAR(255)",
            "timezone": "VARCHAR(100)",
            "salary_min": "FLOAT",
            "salary_max": "FLOAT",
            "languages": "JSON",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
            if table == "career_profiles":
                connection.execute(
                    text("UPDATE career_profiles SET name = 'Perfil ' || id WHERE name IS NULL OR trim(name) = ''")
                )


def get_session() -> Generator[Session]:
    create_database()
    with Session(get_engine()) as session:
        yield session

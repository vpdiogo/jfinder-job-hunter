from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    CareerProfileInput,
    CareerProfileResponse,
    CareerProfileUpdate,
)
from app.repositories.database import get_session
from app.repositories.tables import CareerProfileRecord

router = APIRouter(prefix="/profiles", tags=["profiles"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post(
    "",
    response_model=CareerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    profile: CareerProfileInput,
    session: SessionDependency,
) -> CareerProfileResponse:
    record = CareerProfileRecord(**profile.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return _response(record)


@router.get("", response_model=list[CareerProfileResponse])
def list_profiles(session: SessionDependency) -> list[CareerProfileResponse]:
    records = session.scalars(
        select(CareerProfileRecord).order_by(CareerProfileRecord.id.desc())
    ).all()
    return [_response(record) for record in records]


@router.get("/{profile_id}", response_model=CareerProfileResponse)
def get_profile(
    profile_id: int,
    session: SessionDependency,
) -> CareerProfileResponse:
    return _response(_get_profile_or_404(session, profile_id))


@router.put("/{profile_id}", response_model=CareerProfileResponse)
def update_profile(
    profile_id: int,
    updates: CareerProfileUpdate,
    session: SessionDependency,
) -> CareerProfileResponse:
    record = _get_profile_or_404(session, profile_id)
    for field in updates.model_fields_set:
        setattr(record, field, getattr(updates, field))

    session.commit()
    session.refresh(record)
    return _response(record)


def _get_profile_or_404(
    session: Session,
    profile_id: int,
) -> CareerProfileRecord:
    record = session.get(CareerProfileRecord, profile_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return record


def _response(record: CareerProfileRecord) -> CareerProfileResponse:
    return CareerProfileResponse(
        id=record.id,
        skills=record.skills,
        target_titles=record.target_titles,
        desired_seniority=record.desired_seniority,
        work_modes=record.work_modes or [],
        locations=record.locations or [],
        timezones=record.timezones or [],
        salary_min=record.salary_min,
        salary_max=record.salary_max,
        languages=record.languages or [],
        required_technologies=record.required_technologies or [],
        desired_technologies=record.desired_technologies or [],
        created_at=record.created_at,
    )

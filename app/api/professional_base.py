from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApplicationProfileFromBaseRequest,
    CareerProfileResponse,
    ProfessionalBaseInput,
    ProfessionalBaseResponse,
)
from app.repositories.database import get_session
from app.repositories.tables import CareerProfileRecord, ProfessionalBaseRecord

router = APIRouter(prefix="/professional-base", tags=["professional-base"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=ProfessionalBaseResponse)
def get_professional_base(session: SessionDependency) -> ProfessionalBaseResponse:
    record = session.get(ProfessionalBaseRecord, 1)
    if record is None:
        raise HTTPException(status_code=404, detail="Professional base not found.")
    return _base_response(record)


@router.put("", response_model=ProfessionalBaseResponse)
def save_professional_base(
    payload: ProfessionalBaseInput,
    session: SessionDependency,
) -> ProfessionalBaseResponse:
    record = session.get(ProfessionalBaseRecord, 1)
    if record is None:
        record = ProfessionalBaseRecord(id=1, **payload.model_dump())
        session.add(record)
    else:
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        record = session.get(ProfessionalBaseRecord, 1)
        if record is None:
            raise
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
        session.commit()
    session.refresh(record)
    return _base_response(record)


@router.post(
    "/application-profiles",
    response_model=CareerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application_profile_from_base(
    payload: ApplicationProfileFromBaseRequest,
    session: SessionDependency,
) -> CareerProfileResponse:
    base = session.get(ProfessionalBaseRecord, 1)
    if base is None:
        raise HTTPException(status_code=409, detail="Create a professional base first.")
    record = CareerProfileRecord(
        **payload.model_dump(),
        professional_base_id=base.id,
        source_snapshot={
            "resume_content": base.resume_content,
            "links": base.links,
            "skills": base.skills,
            "experiences": base.experiences,
            "education": base.education,
            "languages": base.languages,
        },
    )
    session.add(record)
    session.flush()
    if record.name is None:
        record.name = f"Profile {record.id}"
    session.commit()
    session.refresh(record)
    return CareerProfileResponse(
        id=record.id, name=record.name, skills=record.skills,
        target_titles=record.target_titles, desired_seniority=record.desired_seniority,
        work_modes=record.work_modes or [], locations=record.locations or [],
        timezones=record.timezones or [], salary_min=record.salary_min,
        salary_max=record.salary_max, languages=record.languages or [],
        required_technologies=record.required_technologies or [],
        desired_technologies=record.desired_technologies or [], created_at=record.created_at,
    )


def _base_response(record: ProfessionalBaseRecord) -> ProfessionalBaseResponse:
    return ProfessionalBaseResponse(
        id=record.id, resume_content=record.resume_content, links=record.links or [],
        skills=record.skills or [], experiences=record.experiences or [],
        education=record.education or [], languages=record.languages or [],
        created_at=record.created_at, updated_at=record.updated_at,
    )

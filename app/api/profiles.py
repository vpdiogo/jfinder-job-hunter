from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    CareerProfileInput,
    CareerProfileResponse,
    CareerProfileUpdate,
    ResumeDraftResponse,
    ResumeExtractionConfirmationRequest,
    ResumeExtractionRequest,
    ResumeExtractionResponse,
)
from app.repositories.database import get_session
from app.repositories.tables import (
    CareerProfileRecord,
    ResumeExtractionRecord,
    utc_now,
)
from app.services.resume_parser import ResumeParser

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
    return _profile_response(record)


@router.get("", response_model=list[CareerProfileResponse])
def list_profiles(session: SessionDependency) -> list[CareerProfileResponse]:
    records = session.scalars(
        select(CareerProfileRecord).order_by(CareerProfileRecord.id.desc())
    ).all()
    return [_profile_response(record) for record in records]


@router.post(
    "/resume-extractions",
    response_model=ResumeExtractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def extract_resume(
    request: ResumeExtractionRequest,
    session: SessionDependency,
) -> ResumeExtractionResponse:
    draft = ResumeParser().extract(request.content)
    record = ResumeExtractionRecord(
        source_content=request.content,
        extracted_data=draft.as_dict(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _extraction_response(record)


@router.get(
    "/resume-extractions/{extraction_id}",
    response_model=ResumeExtractionResponse,
)
def get_resume_extraction(
    extraction_id: int,
    session: SessionDependency,
) -> ResumeExtractionResponse:
    return _extraction_response(_get_extraction_or_404(session, extraction_id))


@router.post(
    "/resume-extractions/{extraction_id}/confirm",
    response_model=CareerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_resume_extraction(
    extraction_id: int,
    request: ResumeExtractionConfirmationRequest,
    session: SessionDependency,
) -> CareerProfileResponse:
    extraction = _get_extraction_or_404(session, extraction_id)
    if extraction.confirmed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume extraction has already been confirmed.",
        )

    if request.profile_id is None:
        profile = CareerProfileRecord(**request.profile.model_dump())
        session.add(profile)
        session.flush()
    else:
        profile = _get_profile_or_404(session, request.profile_id)
        for field, value in request.profile.model_dump().items():
            setattr(profile, field, value)

    extraction.profile_id = profile.id
    extraction.confirmed_data = {
        "profile": request.profile.model_dump(mode="json"),
        "experiences": request.experiences,
        "education": request.education,
    }
    extraction.confirmed_at = utc_now()
    session.commit()
    session.refresh(profile)
    return _profile_response(profile)


@router.get("/{profile_id}", response_model=CareerProfileResponse)
def get_profile(
    profile_id: int,
    session: SessionDependency,
) -> CareerProfileResponse:
    return _profile_response(_get_profile_or_404(session, profile_id))


@router.put("/{profile_id}", response_model=CareerProfileResponse)
def update_profile(
    profile_id: int,
    updates: CareerProfileUpdate,
    session: SessionDependency,
) -> CareerProfileResponse:
    record = _get_profile_or_404(session, profile_id)
    salary_min = (
        updates.salary_min
        if "salary_min" in updates.model_fields_set
        else record.salary_min
    )
    salary_max = (
        updates.salary_max
        if "salary_max" in updates.model_fields_set
        else record.salary_max
    )
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="salary_min cannot be greater than salary_max.",
        )

    for field in updates.model_fields_set:
        setattr(record, field, getattr(updates, field))

    session.commit()
    session.refresh(record)
    return _profile_response(record)


def _get_profile_or_404(
    session: Session,
    profile_id: int,
) -> CareerProfileRecord:
    record = session.get(CareerProfileRecord, profile_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return record


def _get_extraction_or_404(
    session: Session,
    extraction_id: int,
) -> ResumeExtractionRecord:
    record = session.get(ResumeExtractionRecord, extraction_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Resume extraction not found.")
    return record


def _profile_response(record: CareerProfileRecord) -> CareerProfileResponse:
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


def _extraction_response(record: ResumeExtractionRecord) -> ResumeExtractionResponse:
    return ResumeExtractionResponse(
        id=record.id,
        source_content=record.source_content,
        draft=ResumeDraftResponse(**record.extracted_data),
        confirmed_profile_id=record.profile_id,
        confirmed_at=record.confirmed_at,
        created_at=record.created_at,
    )

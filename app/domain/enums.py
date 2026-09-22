from enum import StrEnum


class JobStatus(StrEnum):
    DISCOVERED = "discovered"
    EVALUATED = "evaluated"
    INTERESTED = "interested"
    APPLIED = "applied"
    RECRUITER = "recruiter"
    TECHNICAL = "technical"
    FINAL = "final"
    OFFER = "offer"
    REJECTED = "rejected"


class Recommendation(StrEnum):
    APPLY = "apply"
    REVIEW = "review"
    SKIP = "skip"

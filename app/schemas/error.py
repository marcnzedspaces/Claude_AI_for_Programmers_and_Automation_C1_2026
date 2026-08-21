from pydantic import Field

from app.schemas.common import StrictModel


class ValidationIssue(StrictModel):
    location: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=500)
    error_type: str = Field(min_length=1, max_length=100)


class ErrorDetail(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=500)
    request_id: str = Field(min_length=1, max_length=100)
    details: list[ValidationIssue] = Field(
        default_factory=list,
    )


class ErrorResponse(StrictModel):
    error: ErrorDetail

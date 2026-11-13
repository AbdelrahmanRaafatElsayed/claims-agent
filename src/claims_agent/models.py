from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ClaimStatus(StrEnum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"


class Claim(BaseModel):
    claim_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    diagnosis_code: str = Field(pattern=r"^[A-Z]\d{2}(\.[A-Z0-9]{1,4})?$")
    service_date: date
    submission_date: date
    billed_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    status: ClaimStatus

    @model_validator(mode="after")
    def submission_not_before_service(self):
        if self.submission_date < self.service_date:
            raise ValueError("submission_date cannot be before service_date")
        return self
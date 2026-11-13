import pytest
from pydantic import ValidationError

from claims_agent.models import Claim, ClaimStatus


def make_claim(**overrides):
    data = {
        "claim_id": "CLM-0001",
        "patient_id": "PAT-0001",
        "provider_id": "PRV-0001",
        "diagnosis_code": "C50.9",
        "service_date": "2026-01-10",
        "submission_date": "2026-01-12",
        "billed_amount": "1250.50",
        "status": "approved",
    }
    data.update(overrides)
    return Claim(**data)


def test_valid_claim_is_built_and_coerced():
    claim = make_claim()
    assert claim.status is ClaimStatus.APPROVED
    assert str(claim.billed_amount) == "1250.50"
    assert claim.service_date.year == 2026


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_non_positive_amount_rejected(amount):
    with pytest.raises(ValidationError):
        make_claim(billed_amount=amount)


@pytest.mark.parametrize("code", ["c50.9", "50.9", "C5", "C50.", "CANCER"])
def test_bad_diagnosis_code_rejected(code):
    with pytest.raises(ValidationError):
        make_claim(diagnosis_code=code)


def test_submission_before_service_rejected():
    with pytest.raises(ValidationError, match="submission_date"):
        make_claim(service_date="2026-02-01", submission_date="2026-01-15")


def test_unknown_status_rejected():
    with pytest.raises(ValidationError):
        make_claim(status="aproved")
import logging

import pytest
from pydantic import ValidationError

from claims_agent.errors import ClaimsAgentError, ClaimValidationError
from claims_agent.models import Claim
from claims_agent.parsing import parse_claim


def valid_raw(**overrides):
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
    return data


def test_valid_record_returns_claim():
    claim = parse_claim(valid_raw())
    assert isinstance(claim, Claim)
    assert claim.claim_id == "CLM-0001"


def test_invalid_record_carries_claim_id_and_problems():
    with pytest.raises(ClaimValidationError) as exc:
        parse_claim(valid_raw(billed_amount="-5"))
    assert exc.value.claim_id == "CLM-0001"
    assert any(p.startswith("billed_amount:") for p in exc.value.problems)


def test_missing_claim_id_is_labelled():
    with pytest.raises(ClaimValidationError) as exc:
        parse_claim({})
    assert exc.value.claim_id == "<missing>"


def test_original_pydantic_error_is_kept_as_cause():
    with pytest.raises(ClaimValidationError) as exc:
        parse_claim(valid_raw(status="aproved"))
    assert isinstance(exc.value.__cause__, ValidationError)


def test_caught_by_base_class():
    with pytest.raises(ClaimsAgentError):
        parse_claim(valid_raw(status="aproved"))


def test_rejection_is_logged_without_patient_data(caplog):
    with caplog.at_level(logging.WARNING, logger="claims_agent.parsing"):
        with pytest.raises(ClaimValidationError):
            parse_claim(valid_raw(patient_id="PAT-SECRET", billed_amount="-5"))
    assert "CLM-0001" in caplog.text
    assert "PAT-SECRET" not in caplog.text
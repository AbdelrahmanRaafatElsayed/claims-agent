"""Tests for the synthetic claims generator."""

from datetime import timedelta
from decimal import Decimal

import pytest

from claims_agent import generator_config as cfg
from claims_agent.generator import (
    generate_claims,
    in_spike,
    make_rng,
    scale_amount,
    spike_dates,
)
from claims_agent.parsing import parse_claim


@pytest.fixture(scope="module")
def full_dataset() -> list[dict]:
    """The full dataset, generated once and shared by the tests below."""
    return generate_claims(make_rng())


def test_same_seed_gives_identical_data(monkeypatch):
    monkeypatch.setattr(cfg, "N_CLAIMS", 2_000)
    assert generate_claims(make_rng(1)) == generate_claims(make_rng(1))


def test_different_seed_gives_different_data(monkeypatch):
    monkeypatch.setattr(cfg, "N_CLAIMS", 2_000)
    assert generate_claims(make_rng(1)) != generate_claims(make_rng(2))


def test_every_row_passes_the_validator(monkeypatch):
    monkeypatch.setattr(cfg, "N_CLAIMS", 3_000)
    for raw in generate_claims(make_rng()):
        parse_claim(raw)  # raises ClaimValidationError on any bad row


def test_ids_are_unique_and_follow_date_order(full_dataset):
    ids = [c["claim_id"] for c in full_dataset]
    assert len(set(ids)) == len(ids)
    dates = [c["service_date"] for c in full_dataset]
    assert dates == sorted(dates)  # no leakage: spike claims are not at the end


def test_oncology_share_is_close_to_config(full_dataset):
    onc = sum(c["diagnosis_code"].startswith("C") for c in full_dataset)
    assert abs(onc / len(full_dataset) - cfg.ONCOLOGY_SHARE) < 0.01


def test_oncology_claims_only_at_oncology_providers(full_dataset):
    for c in full_dataset:
        if c["diagnosis_code"].startswith("C"):
            assert c["provider_id"] in cfg.ONCOLOGY_PROVIDERS


def test_spike_volume_is_a_multiple_of_the_multiplier(full_dataset):
    total = sum(in_spike(c) for c in full_dataset)
    assert total >= 15  # the spike exists and is not trivially small
    assert total % cfg.SPIKE_VOLUME_MULTIPLIER == 0  # baseline x multiplier


def test_spike_dates_split_evenly_across_the_window():
    dates = spike_dates(22)
    assert len(dates) == 22
    assert all(cfg.SPIKE_START <= d <= cfg.SPIKE_END for d in dates)
    assert sum(d.month == cfg.SPIKE_START.month for d in dates) == 11
    assert sum(d.month == cfg.SPIKE_END.month for d in dates) == 11


def test_in_spike_window_boundaries():
    base = {
        "provider_id": cfg.SPIKE_PROVIDER,
        "diagnosis_code": "C50.9",
        "service_date": cfg.SPIKE_START.isoformat(),
    }
    before = (cfg.SPIKE_START - timedelta(days=1)).isoformat()
    after = (cfg.SPIKE_END + timedelta(days=1)).isoformat()
    assert in_spike(base)
    assert in_spike({**base, "service_date": cfg.SPIKE_END.isoformat()})
    assert not in_spike({**base, "service_date": before})
    assert not in_spike({**base, "service_date": after})
    assert not in_spike({**base, "provider_id": "P003"})
    assert not in_spike({**base, "diagnosis_code": "C18.9"})


def test_scale_amount_applies_the_multiplier():
    # pins the 1.4 setting: change the config and this test together
    assert scale_amount(Decimal("100.00")) == Decimal("140.00")
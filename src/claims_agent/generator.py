"""Synthetic claims generator (built in pieces)."""

import math
import random
from datetime import date, timedelta
from decimal import Decimal

from claims_agent import generator_config as cfg
from claims_agent.parsing import parse_claim


def make_rng(seed: int = cfg.SEED) -> random.Random:
    """Private random generator: same seed, same data."""
    return random.Random(seed)


def draw_amount(rng: random.Random, median: float, sigma: float) -> Decimal:
    """One log-normal billed amount in SAR, 2 decimals, never below 1."""
    value = rng.lognormvariate(math.log(median), sigma)
    return Decimal(f"{max(value, 1.0):.2f}")


def draw_oncology_amount(rng: random.Random) -> Decimal:
    """Most claims follow the log-normal; a small share are very expensive biologics."""
    if rng.random() < cfg.ONCOLOGY_TAIL_SHARE:
        low, high = cfg.ONCOLOGY_TAIL_RANGE
        return Decimal(f"{rng.uniform(low, high):.2f}")
    return draw_amount(rng, cfg.ONCOLOGY_MEDIAN, cfg.ONCOLOGY_SIGMA)


def draw_other_amount(rng: random.Random) -> Decimal:
    return draw_amount(rng, cfg.OTHER_MEDIAN, cfg.OTHER_SIGMA)


def pick_code(rng: random.Random, oncology: bool) -> str:
    """Weighted choice of an ICD-10 code."""
    table = cfg.ONCOLOGY_CODES if oncology else cfg.OTHER_CODES
    codes = [code for code, _ in table]
    weights = [weight for _, weight in table]
    return rng.choices(codes, weights=weights, k=1)[0]


def pick_status(rng: random.Random) -> str:
    statuses = list(cfg.STATUS_WEIGHTS)
    weights = list(cfg.STATUS_WEIGHTS.values())
    return rng.choices(statuses, weights=weights, k=1)[0]


def random_service_date(rng: random.Random) -> date:
    days_in_range = (cfg.END_DATE - cfg.START_DATE).days
    return cfg.START_DATE + timedelta(days=rng.randint(0, days_in_range))


def build_claim(rng, provider: str, code: str, service: date, amount: Decimal) -> dict:
    """Assemble one raw claim. The claim_id is assigned later, after sorting."""
    lag = rng.randint(0, cfg.MAX_SUBMISSION_LAG_DAYS)
    return {
        "claim_id": "",
        "patient_id": f"PT{rng.randint(1, cfg.N_PATIENTS):04d}",
        "provider_id": provider,
        "diagnosis_code": code,
        "service_date": service.isoformat(),
        "submission_date": (service + timedelta(days=lag)).isoformat(),
        "billed_amount": str(amount),
        "status": pick_status(rng),
    }


def make_claim(rng: random.Random) -> dict:
    """One ordinary claim."""
    oncology = rng.random() < cfg.ONCOLOGY_SHARE
    if oncology:
        provider = rng.choice(cfg.ONCOLOGY_PROVIDERS)
        amount = draw_oncology_amount(rng)
    else:
        provider = f"P{rng.randint(1, cfg.N_PROVIDERS):03d}"
        amount = draw_other_amount(rng)
    return build_claim(rng, provider, pick_code(rng, oncology),
                       random_service_date(rng), amount)


def scale_amount(amount: Decimal) -> Decimal:
    factor = Decimal(str(cfg.SPIKE_AMOUNT_MULTIPLIER))
    return (amount * factor).quantize(Decimal("0.01"))


def in_spike(claim: dict) -> bool:
    """True if a raw claim belongs to the spike group (provider, code, window)."""
    service = date.fromisoformat(claim["service_date"])
    return (
        claim["provider_id"] == cfg.SPIKE_PROVIDER
        and claim["diagnosis_code"].startswith(cfg.SPIKE_CODE_PREFIX)
        and cfg.SPIKE_START <= service <= cfg.SPIKE_END
    )


def spike_dates(count: int) -> list[date]:
    """Spread `count` dates evenly over the spike window (stratified, not random)."""
    days = (cfg.SPIKE_END - cfg.SPIKE_START).days + 1
    return [cfg.SPIKE_START + timedelta(days=int((i + 0.5) * days / count))
            for i in range(count)]


def make_spike_claim(rng: random.Random, service: date) -> dict:
    """An extra breast cancer claim at the spike provider on a given date."""
    amount = scale_amount(draw_oncology_amount(rng))
    return build_claim(rng, cfg.SPIKE_PROVIDER, "C50.9", service, amount)


def generate_claims(rng: random.Random) -> list[dict]:
    """Baseline claims, then the planted spike, then sort and number."""
    claims = [make_claim(rng) for _ in range(cfg.N_CLAIMS)]
    spiked = [c for c in claims if in_spike(c)]
    for c in spiked:  # existing spike-group claims get higher amounts
        c["billed_amount"] = str(scale_amount(Decimal(c["billed_amount"])))
    extra = round(len(spiked) * (cfg.SPIKE_VOLUME_MULTIPLIER - 1))
    claims.extend(make_spike_claim(rng, d) for d in spike_dates(extra))
    claims.sort(key=lambda c: (c["service_date"], c["patient_id"]))
    for number, c in enumerate(claims, start=1):  # numbering last: no leakage
        c["claim_id"] = f"CL{number:06d}"
    return claims



"""Entry point: generate claims, validate every row, write data/claims.csv."""

import csv
from pathlib import Path

from claims_agent.generator import generate_claims, make_rng
from claims_agent.parsing import parse_claim

OUTPUT_PATH = Path("data/claims.csv")
COLUMNS = [
    "claim_id", "patient_id", "provider_id", "diagnosis_code",
    "service_date", "submission_date", "billed_amount", "status",
]


def main() -> None:
    raw_claims = generate_claims(make_rng())
    for raw in raw_claims:  # fail fast: an invalid row raises ClaimValidationError
        parse_claim(raw)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(raw_claims)
    print(f"Wrote {len(raw_claims):,} validated claims to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
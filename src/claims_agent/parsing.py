import logging

from pydantic import ValidationError

from claims_agent.errors import ClaimValidationError
from claims_agent.models import Claim

logger = logging.getLogger(__name__)


def parse_claim(raw: dict) -> Claim:
    try:
        claim = Claim.model_validate(raw)
    except ValidationError as exc:
        problems = [
            f"{'.'.join(str(part) for part in err['loc']) or 'claim'}: {err['msg']}"
            for err in exc.errors()
        ]
        claim_id = str(raw.get("claim_id", "<missing>"))
        logger.warning("Rejected claim %s: %d problem(s)", claim_id, len(problems))
        raise ClaimValidationError(claim_id, problems) from exc
    logger.debug("Parsed claim %s", claim.claim_id)
    return claim
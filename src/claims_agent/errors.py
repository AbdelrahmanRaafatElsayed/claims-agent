class ClaimsAgentError(Exception):
    """Base class for every error this project raises on purpose."""


class ClaimValidationError(ClaimsAgentError):
    """A raw claim record failed validation."""

    def __init__(self, claim_id: str, problems: list[str]):
        self.claim_id = claim_id
        self.problems = problems
        super().__init__(f"Claim {claim_id} is invalid: " + "; ".join(problems))
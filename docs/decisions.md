# Decision notes

Each note: what I chose, what I rejected, why, and what it costs.

## 1. Validate claims once, at the boundary

**Chose:** I chose to validate where data comes in from outside: `parse_claim` and `build_dataset`. A row becomes a valid `Claim`, or it raises one `ClaimValidationError` that lists every problem.
**Rejected:** I rejected re-checking inside every function. I also rejected no validation, just trusting the data.
**Why:** Without a boundary, a claim with `billed_amount <= 0` or a submission date before the service date would reach a `SUM` and then the agent's answer, far from the bad row. With one boundary, the rules live in one place and the error names the claim.
**Cost:** Anything that skips the boundary is not checked, for example an insert straight into PostgreSQL. I added CHECK constraints for that, but now the same rules live in two places and can drift apart. Pydantic also checks shape, not truth: `C99.9` passes my ICD-10 pattern even though no such code exists.

## 2. Custom exceptions instead of a bare ValueError

**Chose:** I chose `ClaimsAgentError` as a base class and `ClaimValidationError` under it. The error carries the `claim_id` and the list of `problems`, and it keeps Pydantic's original error as its cause.
**Rejected:** I rejected a bare `ValueError`. I also rejected letting Pydantic's own `ValidationError` escape.
**Why:** A bare `ValueError` looks the same as an unrelated bug and holds no claim ID. With my own classes, callers catch `ClaimsAgentError` and nothing else, and one bad row gives one complete report. Wrapping Pydantic's error also keeps the rest of the code from depending on Pydantic.
**Cost:** More code to write and keep in step. Every new kind of failure needs its own class, or it falls back to the base one, which says less.

## 3. PostgreSQL installed in Ubuntu, not in Docker

**Chose:** I chose PostgreSQL 18 installed directly inside Ubuntu, with the database `claims` owned by an ordinary role.
**Rejected:** I rejected Docker Desktop with a Postgres container, which is what the plan said.
**Why:** My laptop has 4 GB of RAM, and Ubuntu sees about 1.6 GB of it. Docker Desktop would take memory that Postgres and VS Code need.
**Cost:** The database setup is not captured in one file. Someone who clones the repo has to install PostgreSQL by hand, and the README says how. Gate 1 on Dec 7 asks for Docker Compose, so I still have to solve this before then.

## 4. Plant one known anomaly in the synthetic data

**Chose:** I chose to plant one anomaly with a known size and place: breast cancer claims at one oncology provider in March and April 2026, with three times the claims and 40% higher amounts.
**Rejected:** I rejected random data with no ground truth. I also rejected real data, which is not public and which I must never take from my employer.
**Why:** With a known answer, I can mark the agent's finding right or wrong instead of guessing. Total oncology spend does not show the spike, so the agent has to look at provider, cancer type and month together.
**Cost:** The agent is tested on a pattern I designed, so passing proves less than finding one in real data. I spread the extra claims evenly, which real spikes never are.
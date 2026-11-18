"""Settings for the synthetic claims generator.

FACT = from a source. ESTIMATE = my assumption. VERIFY = check with real data.
"""

from datetime import date

SEED = 42  # same seed -> identical data on every run
N_CLAIMS = 50_000
N_PATIENTS = 3_000
N_PROVIDERS = 40
START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 6, 30)
MAX_SUBMISSION_LAG_DAYS = 30  # submission = service + 0..30 days

ONCOLOGY_SHARE = 0.05  # ESTIMATE: oncology share of claims by count

# (ICD-10 code, weight). ESTIMATE: weights follow Saudi Cancer Registry ranks.
ONCOLOGY_CODES = [
    ("C50.9", 40),  # breast
    ("C18.9", 18),  # colon
    ("C20", 7),     # rectum
    ("C85.9", 15),  # non-Hodgkin lymphoma
    ("C91.0", 6),   # acute lymphoblastic leukaemia
    ("C92.0", 6),   # acute myeloid leukaemia
    ("C34.9", 8),   # lung
]

# ESTIMATE: common non-oncology diagnoses
OTHER_CODES = [
    ("J06.9", 20),  # upper respiratory infection
    ("I10", 15),    # hypertension
    ("E11.9", 14),  # type 2 diabetes
    ("M54.5", 10),  # low back pain
    ("K29.7", 8),   # gastritis
    ("N39.0", 8),   # urinary tract infection
    ("J45.9", 7),   # asthma
    ("E78.5", 6),   # hyperlipidaemia
    ("R51", 6),     # headache
    ("L30.9", 6),   # dermatitis
]

STATUS_WEIGHTS = {"approved": 80, "denied": 12, "pending": 8}

# Billed amounts in SAR, log-normal: median and sigma (spread of the log)
ONCOLOGY_MEDIAN = 9_000  # FACT (clinic page, moderate reliability): 3,000-25,000
ONCOLOGY_SIGMA = 0.65
ONCOLOGY_TAIL_SHARE = 0.03  # biologic / dual-HER2 claims
ONCOLOGY_TAIL_RANGE = (40_000, 120_000)
OTHER_MEDIAN = 350  # ESTIMATE, no source
OTHER_SIGMA = 0.9

# The planted finding the agent must discover
SPIKE_PROVIDER = "P017"
SPIKE_START = date(2026, 3, 1)
SPIKE_END = date(2026, 4, 30)
SPIKE_CODE_PREFIX = "C50"
SPIKE_VOLUME_MULTIPLIER = 3
SPIKE_AMOUNT_MULTIPLIER = 1.4

assert sum(w for _, w in ONCOLOGY_CODES) == 100
assert sum(w for _, w in OTHER_CODES) == 100

# ESTIMATE: only 8 of the 40 providers treat cancer
ONCOLOGY_PROVIDERS = ["P003", "P008", "P012", "P017", "P021", "P027", "P033", "P038"]

assert SPIKE_PROVIDER in ONCOLOGY_PROVIDERS
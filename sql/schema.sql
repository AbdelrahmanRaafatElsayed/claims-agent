-- Claims table. Rebuild at any time: psql claims -f sql/schema.sql
DROP TABLE IF EXISTS claims;

CREATE TABLE claims (
    claim_id        TEXT          PRIMARY KEY,
    patient_id      TEXT          NOT NULL,
    provider_id     TEXT          NOT NULL,
    diagnosis_code  TEXT          NOT NULL
        CHECK (diagnosis_code ~ '^[A-Z][0-9]{2}(\.[A-Z0-9]{1,4})?$'),
    service_date    DATE          NOT NULL,
    submission_date DATE          NOT NULL,
    billed_amount   NUMERIC(12,2) NOT NULL CHECK (billed_amount > 0),
    status          TEXT          NOT NULL
        CHECK (status IN ('approved', 'denied', 'pending')),
    CONSTRAINT submission_not_before_service
        CHECK (submission_date >= service_date)
);
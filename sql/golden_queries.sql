\echo === Q01: total claims and total billed (SAR)
SELECT count(*) AS n_claims, sum(billed_amount) AS total_billed_sar
FROM claims;

\echo === Q02: denial rate, denied / all claims
SELECT round(100.0 * count(*) FILTER (WHERE status = 'denied') / count(*), 2) AS denied_pct
FROM claims;

\echo === Q03: top 5 diagnosis codes by total billed amount
SELECT diagnosis_code, count(*) AS n_claims, sum(billed_amount) AS total_billed_sar
FROM claims
GROUP BY diagnosis_code
ORDER BY total_billed_sar DESC
LIMIT 5;

\echo === Q04: denial rate, oncology vs non-oncology
SELECT CASE WHEN diagnosis_code LIKE 'C%' THEN 'oncology' ELSE 'non-oncology' END AS claim_group,
       count(*) AS n_claims,
       round(100.0 * count(*) FILTER (WHERE status = 'denied') / count(*), 2) AS denied_pct
FROM claims
GROUP BY 1
ORDER BY 1;

\echo === Q05: average billed amount per claim by cancer type
SELECT CASE diagnosis_code
         WHEN 'C50.9' THEN 'breast'
         WHEN 'C18.9' THEN 'colon'
         WHEN 'C20'   THEN 'rectum'
         WHEN 'C85.9' THEN 'lymphoma'
         WHEN 'C91.0' THEN 'leukaemia'
         WHEN 'C92.0' THEN 'leukaemia'
         WHEN 'C34.9' THEN 'lung'
       END AS cancer_type,
       count(*) AS n_claims,
       round(avg(billed_amount), 2) AS avg_billed_sar
FROM claims
WHERE diagnosis_code LIKE 'C%'
GROUP BY 1
ORDER BY avg_billed_sar DESC;

\echo === Q06: monthly oncology spend (SAR) and claim count
SELECT to_char(service_date, 'YYYY-MM') AS month,
       count(*) AS n_claims,
       sum(billed_amount) AS oncology_spend_sar
FROM claims
WHERE diagnosis_code LIKE 'C%'
GROUP BY 1
ORDER BY 1;

\echo === Q08: provider P017 breast cancer, spike months vs other months
SELECT CASE WHEN service_date BETWEEN '2026-03-01' AND '2026-04-30'
            THEN 'Mar-Apr 2026' ELSE 'other months' END AS period,
       count(*) AS n_claims,
       count(DISTINCT to_char(service_date, 'YYYY-MM')) AS n_months,
       round(count(*)::numeric
             / count(DISTINCT to_char(service_date, 'YYYY-MM')), 1) AS claims_per_month,
       round(avg(billed_amount), 2) AS avg_billed_sar
FROM claims
WHERE provider_id = 'P017' AND diagnosis_code LIKE 'C50%'
GROUP BY 1
ORDER BY 1;

\echo === Q07: anomaly scan, oncology provider x diagnosis, Nov 2025 - Jun 2026
WITH months AS (
    SELECT generate_series(date '2025-11-01', date '2026-06-01', interval '1 month')::date AS month
),
combos AS (
    SELECT DISTINCT provider_id, diagnosis_code
    FROM claims
    WHERE diagnosis_code LIKE 'C%'
),
monthly AS (
    SELECT k.provider_id, k.diagnosis_code, m.month, count(c.claim_id) AS n
    FROM combos k
    CROSS JOIN months m
    LEFT JOIN claims c
           ON c.provider_id = k.provider_id
          AND c.diagnosis_code = k.diagnosis_code
          AND date_trunc('month', c.service_date)::date = m.month
    GROUP BY k.provider_id, k.diagnosis_code, m.month
),
baseline AS (
    SELECT provider_id, diagnosis_code,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY n) AS median_n
    FROM monthly
    GROUP BY provider_id, diagnosis_code
)
SELECT mo.provider_id, mo.diagnosis_code, to_char(mo.month, 'YYYY-MM') AS month,
       mo.n, b.median_n,
       round(((mo.n - b.median_n) / sqrt(b.median_n))::numeric, 1) AS score
FROM monthly mo
JOIN baseline b USING (provider_id, diagnosis_code)
WHERE b.median_n >= 3
ORDER BY score DESC
LIMIT 5;
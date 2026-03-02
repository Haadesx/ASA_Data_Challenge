-- Build mart tables from stg.wwc_raw
-- Run after sql/wwc_analytic_schema.sql
-- Target: PostgreSQL 14+

BEGIN;

CREATE OR REPLACE FUNCTION mart.to_num(t TEXT)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN t IS NULL OR btrim(t) = '' THEN NULL
    WHEN btrim(t) ~ '^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$' THEN btrim(t)::NUMERIC
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION mart.to_int(t TEXT)
RETURNS BIGINT
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN t IS NULL OR btrim(t) = '' THEN NULL
    WHEN btrim(t) ~ '^[+-]?[0-9]+$' THEN btrim(t)::BIGINT
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION mart.to_bool(t TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN t IS NULL OR btrim(t) = '' THEN NULL
    WHEN lower(btrim(t)) IN ('true', 't', '1', 'yes', 'y') THEN TRUE
    WHEN lower(btrim(t)) IN ('false', 'f', '0', 'no', 'n') THEN FALSE
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION mart.to_date_safe(t TEXT)
RETURNS DATE
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN t IS NULL OR btrim(t) = '' THEN NULL
    WHEN btrim(t) ~ '^\d{4}-\d{2}-\d{2}$' THEN btrim(t)::DATE
    WHEN btrim(t) ~ '^\d{1,2}/\d{1,2}/\d{4}$' THEN to_date(btrim(t), 'MM/DD/YYYY')
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION mart.to_share(t TEXT)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN mart.to_num(t) IS NULL THEN NULL
    WHEN mart.to_num(t) > 1.0 AND mart.to_num(t) <= 100.0 THEN mart.to_num(t) / 100.0
    ELSE mart.to_num(t)
  END;
$$;

CREATE OR REPLACE FUNCTION mart.period_to_months(t TEXT)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$
  SELECT CASE
    WHEN t IS NULL OR btrim(t) = '' THEN NULL
    WHEN lower(btrim(t)) = 'posttest' THEN 0
    WHEN lower(btrim(t)) ~ '^\d+(\.\d+)?\s*day(s)?$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 1)) / 30.0
    WHEN lower(btrim(t)) ~ '^\d+(\.\d+)?\s*week(s)?$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 1)) / 4.345
    WHEN lower(btrim(t)) ~ '^\d+(\.\d+)?\s*month(s)?$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 1))
    WHEN lower(btrim(t)) ~ '^\d+(\.\d+)?\s*semester(s)?$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 1)) * 6.0
    WHEN lower(btrim(t)) ~ '^\d+(\.\d+)?\s*year(s)?$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 1)) * 12.0
    WHEN lower(btrim(t)) ~ '^year\s+\d+$'
      THEN mart.to_num(split_part(lower(btrim(t)), ' ', 2)) * 12.0
    ELSE NULL
  END;
$$;

TRUNCATE TABLE mart.fact_finding;
TRUNCATE TABLE mart.bridge_study_state;
TRUNCATE TABLE mart.dim_study;
TRUNCATE TABLE mart.dim_intervention;

INSERT INTO mart.dim_intervention (
  intervention_id,
  intervention_name,
  protocol,
  protocol_version,
  outcome_domain,
  effectiveness_rating,
  num_studies_meeting_standards,
  num_studies_eligible,
  sample_size_intervention,
  intervention_page_url
)
SELECT DISTINCT ON (intervention_id)
  intervention_id,
  COALESCE(NULLIF(r.i_intervention_name, ''), NULLIF(r.s_intervention_name, ''), NULLIF(r.f_intervention_name, '')) AS intervention_name,
  NULLIF(r.i_protocol, '') AS protocol,
  mart.to_int(r.i_protocol_version)::INT AS protocol_version,
  NULLIF(r.i_outcome_domain, '') AS outcome_domain,
  NULLIF(r.i_effectiveness_rating, '') AS effectiveness_rating,
  mart.to_int(r.i_numstudiesmeetingstandards)::INT AS num_studies_meeting_standards,
  mart.to_int(r.i_numstudieseligible)::INT AS num_studies_eligible,
  mart.to_int(COALESCE(r.payload ->> 'i_Sample_Size_Intervention', NULL)) AS sample_size_intervention,
  COALESCE(r.payload ->> 'i_Intervention_Page_URL', NULL) AS intervention_page_url
FROM stg.wwc_raw r
CROSS JOIN LATERAL (
  SELECT mart.to_int(COALESCE(NULLIF(r.i_interventionid, ''), NULLIF(r.s_interventionid, ''), NULLIF(r.f_interventionid, ''))) AS intervention_id
) k
WHERE k.intervention_id IS NOT NULL
ORDER BY intervention_id, COALESCE(NULLIF(r.i_intervention_name, ''), NULLIF(r.s_intervention_name, ''), NULLIF(r.f_intervention_name, '')) DESC;

INSERT INTO mart.dim_study (
  study_id,
  review_id,
  intervention_id,
  citation,
  publication,
  publication_date,
  posting_date,
  study_design_raw,
  study_design_std,
  study_rating,
  study_quality_score,
  standards_version,
  protocol,
  protocol_version,
  study_page_url
)
SELECT DISTINCT ON (study_id)
  study_id,
  mart.to_int(NULLIF(r.review_id, '')) AS review_id,
  mart.to_int(COALESCE(NULLIF(r.i_interventionid, ''), NULLIF(r.s_interventionid, ''), NULLIF(r.f_interventionid, ''))) AS intervention_id,
  NULLIF(r.s_citation, '') AS citation,
  NULLIF(r.s_publication, '') AS publication,
  mart.to_date_safe(NULLIF(r.s_publication_date, '')) AS publication_date,
  mart.to_date_safe(NULLIF(r.s_posting_date, '')) AS posting_date,
  NULLIF(r.s_study_design, '') AS study_design_raw,
  CASE
    WHEN lower(NULLIF(r.s_study_design, '')) IN ('randomized controlled trial', 'randomized controlled trial ')
      THEN 'Randomized Controlled Trial'
    WHEN lower(NULLIF(r.s_study_design, '')) = 'randomized controlled trial'
      THEN 'Randomized Controlled Trial'
    ELSE NULLIF(r.s_study_design, '')
  END AS study_design_std,
  NULLIF(r.s_study_rating, '') AS study_rating,
  CASE
    WHEN r.s_study_rating = 'Meets WWC standards without reservations' THEN 3
    WHEN r.s_study_rating = 'Meets WWC standards with reservations' THEN 2
    WHEN r.s_study_rating = 'Does not meet WWC standards' THEN 1
    ELSE 0
  END AS study_quality_score,
  NULLIF(r.s_standards_version, '') AS standards_version,
  NULLIF(r.s_protocol, '') AS protocol,
  mart.to_int(r.s_protocol_version)::INT AS protocol_version,
  NULLIF(r.s_study_page_url, '') AS study_page_url
FROM stg.wwc_raw r
CROSS JOIN LATERAL (
  SELECT mart.to_int(NULLIF(r.s_studyid, '')) AS study_id
) k
WHERE k.study_id IS NOT NULL
ORDER BY study_id, mart.to_date_safe(NULLIF(r.s_publication_date, '')) DESC NULLS LAST;

INSERT INTO mart.fact_finding (
  finding_id,
  review_id,
  study_id,
  intervention_id,
  outcome_measure_id,
  outcome_measure,
  outcome_domain,
  period_raw,
  period_months,
  sample_description,
  is_subgroup,
  outcome_sample_size,
  outcome_intervention_ss,
  outcome_comparison_ss,
  effect_size_study,
  effect_size_wwc,
  effect_size_final,
  effect_abs,
  improvement_index,
  p_value_study,
  p_value_wwc,
  is_statistically_significant,
  finding_rating,
  essa_rating,
  favorable_unfavorable_designation
)
SELECT
  mart.to_int(NULLIF(r.f_findingid, '')) AS finding_id,
  mart.to_int(NULLIF(r.review_id, '')) AS review_id,
  mart.to_int(NULLIF(r.s_studyid, '')) AS study_id,
  mart.to_int(COALESCE(NULLIF(r.i_interventionid, ''), NULLIF(r.s_interventionid, ''), NULLIF(r.f_interventionid, ''))) AS intervention_id,
  mart.to_int(NULLIF(r.f_outcome_measureid, '')) AS outcome_measure_id,
  NULLIF(r.f_outcome_measure, '') AS outcome_measure,
  NULLIF(r.f_outcome_domain, '') AS outcome_domain,
  NULLIF(r.f_period, '') AS period_raw,
  mart.period_to_months(NULLIF(r.f_period, '')) AS period_months,
  NULLIF(r.f_sample_description, '') AS sample_description,
  mart.to_bool(NULLIF(r.f_is_subgroup, '')) AS is_subgroup,
  mart.to_int(NULLIF(r.f_outcome_sample_size, '')) AS outcome_sample_size,
  mart.to_int(NULLIF(r.f_outcome_intervention_ss, '')) AS outcome_intervention_ss,
  mart.to_int(NULLIF(r.f_outcome_comparison_ss, '')) AS outcome_comparison_ss,
  mart.to_num(NULLIF(r.f_effect_size_study, '')) AS effect_size_study,
  mart.to_num(NULLIF(r.f_effect_size_wwc, '')) AS effect_size_wwc,
  COALESCE(mart.to_num(NULLIF(r.f_effect_size_wwc, '')), mart.to_num(NULLIF(r.f_effect_size_study, ''))) AS effect_size_final,
  ABS(COALESCE(mart.to_num(NULLIF(r.f_effect_size_wwc, '')), mart.to_num(NULLIF(r.f_effect_size_study, '')))) AS effect_abs,
  mart.to_num(NULLIF(r.f_improvement_index, '')) AS improvement_index,
  mart.to_num(NULLIF(r.f_p_value_study, '')) AS p_value_study,
  mart.to_num(NULLIF(r.f_p_value_wwc, '')) AS p_value_wwc,
  mart.to_bool(NULLIF(r.f_is_statistically_significant, '')) AS is_statistically_significant,
  NULLIF(r.f_finding_rating, '') AS finding_rating,
  NULLIF(r.f_essa_rating, '') AS essa_rating,
  NULLIF(r.f_favorableunfavorabledesignation, '') AS favorable_unfavorable_designation
FROM stg.wwc_raw r
WHERE mart.to_int(NULLIF(r.f_findingid, '')) IS NOT NULL
  AND mart.to_int(NULLIF(r.s_studyid, '')) IS NOT NULL;

-- Approximate inverse-variance weight when no study-level SE is provided.
UPDATE mart.fact_finding f
SET
  se_approx = CASE
    WHEN f.outcome_sample_size IS NOT NULL AND f.outcome_sample_size > 3
      THEN sqrt(4.0 / f.outcome_sample_size::NUMERIC)
    ELSE NULL
  END,
  weight_iv = CASE
    WHEN f.outcome_sample_size IS NOT NULL AND f.outcome_sample_size > 3
      THEN 1.0 / (4.0 / f.outcome_sample_size::NUMERIC)
    ELSE NULL
  END;

-- Winsorize tails within outcome domain to reduce leverage from extreme effects.
WITH pct AS (
  SELECT
    outcome_domain,
    percentile_cont(0.005) WITHIN GROUP (ORDER BY effect_size_final) AS p005,
    percentile_cont(0.995) WITHIN GROUP (ORDER BY effect_size_final) AS p995
  FROM mart.fact_finding
  WHERE effect_size_final IS NOT NULL
  GROUP BY 1
)
UPDATE mart.fact_finding f
SET
  effect_size_final = LEAST(GREATEST(f.effect_size_final, p.p005), p.p995),
  effect_abs = ABS(LEAST(GREATEST(f.effect_size_final, p.p005), p.p995)),
  is_outlier_effect = (f.effect_size_final < p.p005 OR f.effect_size_final > p.p995)
FROM pct p
WHERE f.outcome_domain = p.outcome_domain
  AND f.effect_size_final IS NOT NULL;

-- Expand study -> state mapping from JSON payload keys (if payload includes full source row).
WITH state_lookup AS (
  SELECT * FROM (VALUES
    ('s_Region_State_Alabama', 'AL'),
    ('s_Region_State_Alaska', 'AK'),
    ('s_Region_State_Arizona', 'AZ'),
    ('s_Region_State_Arkansas', 'AR'),
    ('s_Region_State_California', 'CA'),
    ('s_Region_State_Colorado', 'CO'),
    ('s_Region_State_Connecticut', 'CT'),
    ('s_Region_State_Delaware', 'DE'),
    ('s_Region_State_DC', 'DC'),
    ('s_Region_State_Florida', 'FL'),
    ('s_Region_State_Georgia', 'GA'),
    ('s_Region_State_Hawaii', 'HI'),
    ('s_Region_State_Idaho', 'ID'),
    ('s_Region_State_Illinois', 'IL'),
    ('s_Region_State_Indiana', 'IN'),
    ('s_Region_State_Iowa', 'IA'),
    ('s_Region_State_Kansas', 'KS'),
    ('s_Region_State_Kentucky', 'KY'),
    ('s_Region_State_Louisiana', 'LA'),
    ('s_Region_State_Maine', 'ME'),
    ('s_Region_State_Maryland', 'MD'),
    ('s_Region_State_Massachusetts', 'MA'),
    ('s_Region_State_Michigan', 'MI'),
    ('s_Region_State_Minnesota', 'MN'),
    ('s_Region_State_Mississippi', 'MS'),
    ('s_Region_State_Missouri', 'MO'),
    ('s_Region_State_Montana', 'MT'),
    ('s_Region_State_Nebraska', 'NE'),
    ('s_Region_State_Nevada', 'NV'),
    ('s_Region_State_New_Hampshire', 'NH'),
    ('s_Region_State_New_Jersey', 'NJ'),
    ('s_Region_State_New_Mexico', 'NM'),
    ('s_Region_State_New_York', 'NY'),
    ('s_Region_State_North_Carolina', 'NC'),
    ('s_Region_State_North_Dakota', 'ND'),
    ('s_Region_State_Ohio', 'OH'),
    ('s_Region_State_Oklahoma', 'OK'),
    ('s_Region_State_Oregon', 'OR'),
    ('s_Region_State_Pennsylvania', 'PA'),
    ('s_Region_State_Rhode_Island', 'RI'),
    ('s_Region_State_South_Carolina', 'SC'),
    ('s_Region_State_South_Dakota', 'SD'),
    ('s_Region_State_Tennessee', 'TN'),
    ('s_Region_State_Texas', 'TX'),
    ('s_Region_State_Utah', 'UT'),
    ('s_Region_State_Vermont', 'VT'),
    ('s_Region_State_Virginia', 'VA'),
    ('s_Region_State_Washington', 'WA'),
    ('s_Region_State_West_Virginia', 'WV'),
    ('s_Region_State_Wisconsin', 'WI'),
    ('s_Region_State_Wyoming', 'WY')
  ) AS t(state_col, state_abbr)
),
study_state AS (
  SELECT DISTINCT
    mart.to_int(r.s_studyid) AS study_id,
    l.state_abbr
  FROM stg.wwc_raw r
  JOIN state_lookup l
    ON lower(COALESCE(r.payload ->> l.state_col, 'false')) IN ('true', 't', '1', 'yes', 'y')
  WHERE mart.to_int(r.s_studyid) IS NOT NULL
),
weights AS (
  SELECT
    study_id,
    state_abbr,
    1.0 / COUNT(*) OVER (PARTITION BY study_id) AS state_weight
  FROM study_state
)
INSERT INTO mart.bridge_study_state (study_id, state_abbr, state_weight)
SELECT
  w.study_id,
  w.state_abbr,
  w.state_weight
FROM weights w
ON CONFLICT (study_id, state_abbr) DO UPDATE
SET state_weight = EXCLUDED.state_weight;

CREATE OR REPLACE VIEW mart.v_build_qc AS
SELECT
  (SELECT COUNT(*) FROM stg.wwc_raw) AS raw_rows,
  (SELECT COUNT(*) FROM mart.dim_intervention) AS dim_intervention_rows,
  (SELECT COUNT(*) FROM mart.dim_study) AS dim_study_rows,
  (SELECT COUNT(*) FROM mart.fact_finding) AS fact_finding_rows,
  (SELECT COUNT(*) FROM mart.bridge_study_state) AS bridge_state_rows,
  (SELECT COUNT(*) FROM mart.fact_finding WHERE effect_size_final IS NULL) AS missing_effect_size_rows,
  (SELECT COUNT(*) FROM mart.fact_finding WHERE weight_iv IS NULL) AS missing_weight_rows;

COMMIT;

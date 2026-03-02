-- WWC analytic schema for finding-level "what works for whom" modeling
-- Target: PostgreSQL 14+

CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS mart;

-- Raw landing table (typed as TEXT for robust ingestion).
CREATE TABLE IF NOT EXISTS stg.wwc_raw (
  review_id TEXT,
  i_interventionid TEXT,
  i_intervention_name TEXT,
  i_protocol TEXT,
  i_protocol_version TEXT,
  i_outcome_domain TEXT,
  i_numstudiesmeetingstandards TEXT,
  i_numstudieseligible TEXT,
  i_effectiveness_rating TEXT,
  s_studyid TEXT,
  s_intervention_name TEXT,
  s_protocol TEXT,
  s_protocol_version TEXT,
  s_standards_version TEXT,
  s_citation TEXT,
  s_study_design TEXT,
  s_study_rating TEXT,
  s_publication TEXT,
  s_publication_date TEXT,
  s_posting_date TEXT,
  s_study_page_url TEXT,
  s_interventionid TEXT,
  f_findingid TEXT,
  f_interventionid TEXT,
  f_intervention_name TEXT,
  f_outcome_measureid TEXT,
  f_outcome_measure TEXT,
  f_outcome_domain TEXT,
  f_period TEXT,
  f_sample_description TEXT,
  f_is_subgroup TEXT,
  f_outcome_sample_size TEXT,
  f_outcome_intervention_ss TEXT,
  f_outcome_comparison_ss TEXT,
  f_effect_size_study TEXT,
  f_effect_size_wwc TEXT,
  f_improvement_index TEXT,
  f_p_value_study TEXT,
  f_p_value_wwc TEXT,
  f_is_statistically_significant TEXT,
  f_finding_rating TEXT,
  f_essa_rating TEXT,
  f_l1_unit_of_analysis TEXT,
  f_favorableunfavorabledesignation TEXT,
  payload JSONB
);

-- Intervention dimension.
CREATE TABLE IF NOT EXISTS mart.dim_intervention (
  intervention_id BIGINT PRIMARY KEY,
  intervention_name TEXT,
  protocol TEXT,
  protocol_version INT,
  outcome_domain TEXT,
  effectiveness_rating TEXT,
  num_studies_meeting_standards INT,
  num_studies_eligible INT,
  sample_size_intervention BIGINT,
  intervention_page_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Study dimension.
CREATE TABLE IF NOT EXISTS mart.dim_study (
  study_id BIGINT PRIMARY KEY,
  review_id BIGINT,
  intervention_id BIGINT,
  citation TEXT,
  publication TEXT,
  publication_date DATE,
  posting_date DATE,
  study_design_raw TEXT,
  study_design_std TEXT,
  study_rating TEXT,
  study_quality_score SMALLINT,
  standards_version TEXT,
  protocol TEXT,
  protocol_version INT,
  study_page_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Finding-level fact table.
CREATE TABLE IF NOT EXISTS mart.fact_finding (
  finding_id BIGINT PRIMARY KEY,
  review_id BIGINT,
  study_id BIGINT NOT NULL REFERENCES mart.dim_study(study_id),
  intervention_id BIGINT REFERENCES mart.dim_intervention(intervention_id),
  outcome_measure_id BIGINT,
  outcome_measure TEXT,
  outcome_domain TEXT,
  period_raw TEXT,
  period_months NUMERIC(8,2),
  sample_description TEXT,
  is_subgroup BOOLEAN,
  outcome_sample_size BIGINT,
  outcome_intervention_ss BIGINT,
  outcome_comparison_ss BIGINT,
  effect_size_study NUMERIC,
  effect_size_wwc NUMERIC,
  effect_size_final NUMERIC,
  effect_abs NUMERIC,
  improvement_index NUMERIC,
  p_value_study NUMERIC,
  p_value_wwc NUMERIC,
  is_statistically_significant BOOLEAN,
  finding_rating TEXT,
  essa_rating TEXT,
  favorable_unfavorable_designation TEXT,
  se_approx NUMERIC,
  weight_iv NUMERIC,
  is_outlier_effect BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bridge table for state mapping from one-hot study flags.
CREATE TABLE IF NOT EXISTS mart.bridge_study_state (
  study_id BIGINT NOT NULL REFERENCES mart.dim_study(study_id),
  state_abbr CHAR(2) NOT NULL,
  state_weight NUMERIC(8,6) DEFAULT 1.0,
  PRIMARY KEY (study_id, state_abbr)
);

-- State-year external context table (NCES / ACS / SAIPE / RUCC).
CREATE TABLE IF NOT EXISTS mart.dim_context_state_year (
  state_abbr CHAR(2) NOT NULL,
  year INT NOT NULL,
  ccd_enrollment BIGINT,
  ccd_frpl_share NUMERIC,
  ccd_ell_share NUMERIC,
  ccd_swd_share NUMERIC,
  f33_pp_expenditure_real NUMERIC,
  f33_teacher_salary_real NUMERIC,
  saipe_child_poverty_rate NUMERIC,
  acs_median_income_real NUMERIC,
  acs_ba_share NUMERIC,
  acs_white_share NUMERIC,
  acs_black_share NUMERIC,
  acs_hispanic_share NUMERIC,
  rucc_rural_share NUMERIC,
  source_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (state_abbr, year)
);

-- Optional denormalized analytic view.
CREATE OR REPLACE VIEW mart.v_finding_analytic AS
SELECT
  f.finding_id,
  f.review_id,
  f.study_id,
  f.intervention_id,
  s.study_design_std,
  s.study_quality_score,
  EXTRACT(YEAR FROM COALESCE(s.publication_date, s.posting_date))::INT AS analysis_year,
  f.outcome_domain,
  f.outcome_measure,
  f.effect_size_final,
  f.se_approx,
  f.weight_iv,
  f.is_subgroup,
  f.is_statistically_significant,
  f.finding_rating,
  b.state_abbr,
  c.ccd_frpl_share,
  c.ccd_ell_share,
  c.ccd_swd_share,
  c.f33_pp_expenditure_real,
  c.saipe_child_poverty_rate,
  c.rucc_rural_share
FROM mart.fact_finding f
JOIN mart.dim_study s
  ON s.study_id = f.study_id
LEFT JOIN mart.bridge_study_state b
  ON b.study_id = f.study_id
LEFT JOIN mart.dim_context_state_year c
  ON c.state_abbr = b.state_abbr
 AND c.year = EXTRACT(YEAR FROM COALESCE(s.publication_date, s.posting_date))::INT;

CREATE INDEX IF NOT EXISTS idx_dim_study_intervention_id
  ON mart.dim_study (intervention_id);

CREATE INDEX IF NOT EXISTS idx_fact_finding_study_id
  ON mart.fact_finding (study_id);

CREATE INDEX IF NOT EXISTS idx_fact_finding_intervention_id
  ON mart.fact_finding (intervention_id);

CREATE INDEX IF NOT EXISTS idx_fact_finding_outcome_domain
  ON mart.fact_finding (outcome_domain);

CREATE INDEX IF NOT EXISTS idx_fact_finding_effect_size_final
  ON mart.fact_finding (effect_size_final);

CREATE INDEX IF NOT EXISTS idx_bridge_state_abbr
  ON mart.bridge_study_state (state_abbr);

CREATE INDEX IF NOT EXISTS idx_context_state_year_year
  ON mart.dim_context_state_year (year);


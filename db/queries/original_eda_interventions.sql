\pset pager off

-- Original WWC dataset EDA focused on interventions, outcomes, and evidence-quality signals.
-- Run with:
--   ./db/run_query.sh db/queries/original_eda_interventions.sql

\echo '== Base coverage =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT s_studyid) AS distinct_studies,
  COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> '') AS distinct_named_interventions,
  COUNT(*) FILTER (WHERE i_intervention_name IS NULL OR btrim(i_intervention_name) = '') AS missing_intervention_name_rows,
  COUNT(*) FILTER (WHERE f_effect_size_wwc IS NOT NULL AND btrim(f_effect_size_wwc) <> '') AS effect_size_rows,
  COUNT(*) FILTER (WHERE f_improvement_index IS NOT NULL AND btrim(f_improvement_index) <> '') AS improvement_index_rows,
  COUNT(*) FILTER (WHERE f_p_value_wwc IS NOT NULL AND btrim(f_p_value_wwc) <> '') AS p_value_rows,
  COUNT(*) FILTER (WHERE f_is_statistically_significant IS NOT NULL AND btrim(f_is_statistically_significant) <> '') AS significance_flag_rows,
  COUNT(*) FILTER (WHERE f_finding_rating IS NOT NULL AND btrim(f_finding_rating) <> '') AS finding_rating_rows,
  COUNT(*) FILTER (WHERE f_essa_rating IS NOT NULL AND btrim(f_essa_rating) <> '') AS essa_rating_rows
FROM raw.wwc_original;

\echo '== Publication year coverage =='
SELECT
  COUNT(*) AS rows_with_year,
  MIN(s_publication_date) AS min_publication_date,
  MAX(s_publication_date) AS max_publication_date,
  COUNT(DISTINCT s_publication_date) AS distinct_publication_dates
FROM raw.wwc_original
WHERE s_publication_date IS NOT NULL AND btrim(s_publication_date) <> '';

\echo '== Top interventions by support (named only, >= 10 rows) =='
SELECT
  i_intervention_name,
  COUNT(*) AS rows_n,
  COUNT(DISTINCT s_studyid) AS studies_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect_size_wwc,
  AVG(NULLIF(f_improvement_index, '')::numeric) AS mean_improvement_index,
  AVG(NULLIF(f_p_value_wwc, '')::numeric) AS mean_p_value_wwc
FROM raw.wwc_original
WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''
GROUP BY i_intervention_name
HAVING COUNT(*) >= 10
ORDER BY rows_n DESC, mean_effect_size_wwc DESC NULLS LAST
LIMIT 15;

\echo '== Outcome-domain coverage =='
SELECT
  COALESCE(NULLIF(btrim(i_outcome_domain), ''), 'missing') AS outcome_domain,
  COUNT(*) AS rows_n,
  COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> '') AS interventions_n,
  COUNT(DISTINCT s_studyid) AS studies_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect_size_wwc,
  AVG(NULLIF(f_improvement_index, '')::numeric) AS mean_improvement_index
FROM raw.wwc_original
GROUP BY 1
ORDER BY rows_n DESC, outcome_domain
LIMIT 15;

\echo '== Effect size distribution =='
SELECT
  effect_size_bin,
  rows_n,
  ROUND(mean_effect_size::numeric, 3) AS mean_effect_size,
  ROUND(min_effect_size::numeric, 3) AS min_effect_size,
  ROUND(max_effect_size::numeric, 3) AS max_effect_size
FROM (
  SELECT
    CASE
      WHEN es < 0 THEN 'negative'
      WHEN es < 0.10 THEN '0.00 to 0.09'
      WHEN es < 0.25 THEN '0.10 to 0.24'
      WHEN es < 0.50 THEN '0.25 to 0.49'
      WHEN es < 1.00 THEN '0.50 to 0.99'
      ELSE '1.00+'
    END AS effect_size_bin,
    CASE
      WHEN es < 0 THEN 1
      WHEN es < 0.10 THEN 2
      WHEN es < 0.25 THEN 3
      WHEN es < 0.50 THEN 4
      WHEN es < 1.00 THEN 5
      ELSE 6
    END AS sort_order,
    COUNT(*) AS rows_n,
    AVG(es) AS mean_effect_size,
    MIN(es) AS min_effect_size,
    MAX(es) AS max_effect_size
  FROM (
    SELECT NULLIF(f_effect_size_wwc, '')::numeric AS es
    FROM raw.wwc_original
    WHERE f_effect_size_wwc IS NOT NULL AND btrim(f_effect_size_wwc) <> ''
  ) x
  GROUP BY 1, 2
) b
ORDER BY sort_order;

\echo '== Improvement index distribution =='
SELECT
  improvement_index_bin,
  rows_n,
  ROUND(mean_improvement_index::numeric, 3) AS mean_improvement_index,
  ROUND(min_improvement_index::numeric, 3) AS min_improvement_index,
  ROUND(max_improvement_index::numeric, 3) AS max_improvement_index
FROM (
  SELECT
    CASE
      WHEN ii < 0 THEN 'negative'
      WHEN ii < 5 THEN '0 to 4.9'
      WHEN ii < 10 THEN '5 to 9.9'
      WHEN ii < 20 THEN '10 to 19.9'
      WHEN ii < 30 THEN '20 to 29.9'
      ELSE '30+'
    END AS improvement_index_bin,
    CASE
      WHEN ii < 0 THEN 1
      WHEN ii < 5 THEN 2
      WHEN ii < 10 THEN 3
      WHEN ii < 20 THEN 4
      WHEN ii < 30 THEN 5
      ELSE 6
    END AS sort_order,
    COUNT(*) AS rows_n,
    AVG(ii) AS mean_improvement_index,
    MIN(ii) AS min_improvement_index,
    MAX(ii) AS max_improvement_index
  FROM (
    SELECT NULLIF(f_improvement_index, '')::numeric AS ii
    FROM raw.wwc_original
    WHERE f_improvement_index IS NOT NULL AND btrim(f_improvement_index) <> ''
  ) x
  GROUP BY 1, 2
) b
ORDER BY sort_order;

\echo '== Quality / evidence signals =='
SELECT
  'f_is_statistically_significant' AS metric,
  f_is_statistically_significant AS value,
  COUNT(*) AS rows_n
FROM raw.wwc_original
WHERE f_is_statistically_significant IS NOT NULL AND btrim(f_is_statistically_significant) <> ''
GROUP BY 1, 2
UNION ALL
SELECT
  'f_finding_rating' AS metric,
  f_finding_rating AS value,
  COUNT(*) AS rows_n
FROM raw.wwc_original
WHERE f_finding_rating IS NOT NULL AND btrim(f_finding_rating) <> ''
GROUP BY 1, 2
UNION ALL
SELECT
  'f_essa_rating' AS metric,
  f_essa_rating AS value,
  COUNT(*) AS rows_n
FROM raw.wwc_original
WHERE f_essa_rating IS NOT NULL AND btrim(f_essa_rating) <> ''
GROUP BY 1, 2
UNION ALL
SELECT
  'i_effectiveness_rating' AS metric,
  i_effectiveness_rating AS value,
  COUNT(*) AS rows_n
FROM raw.wwc_original
WHERE i_effectiveness_rating IS NOT NULL AND btrim(i_effectiveness_rating) <> ''
GROUP BY 1, 2
ORDER BY metric, rows_n DESC, value;

\echo '== Small-support caveat: intervention rows with at least 10 studies =='
SELECT
  COUNT(*) AS interventions_with_10plus_studies,
  MIN(studies_n) AS min_studies_among_them,
  MAX(studies_n) AS max_studies_among_them
FROM (
  SELECT i_intervention_name, COUNT(DISTINCT s_studyid) AS studies_n
  FROM raw.wwc_original
  WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''
  GROUP BY i_intervention_name
  HAVING COUNT(DISTINCT s_studyid) >= 10
) t;

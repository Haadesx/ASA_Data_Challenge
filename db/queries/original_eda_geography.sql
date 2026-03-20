\pset pager off

-- Original WWC geography / urbanicity EDA.
-- Source table: raw.wwc_original only.
-- Run with:
--   ./db/run_query.sh db/queries/original_eda_geography.sql

\echo '== Base counts and metric coverage =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE NULLIF(f_effect_size_wwc, '') IS NOT NULL) AS effect_size_rows,
  COUNT(*) FILTER (WHERE NULLIF(f_improvement_index, '') IS NOT NULL) AS improvement_index_rows,
  COUNT(*) FILTER (WHERE NULLIF(f_p_value_wwc, '') IS NOT NULL) AS p_value_rows,
  COUNT(*) FILTER (WHERE NULLIF(f_is_statistically_significant, '') IS NOT NULL) AS significance_rows,
  COUNT(DISTINCT s_studyid) AS distinct_studies,
  COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> '') AS distinct_named_interventions
FROM raw.wwc_original;

\echo '== State coverage by assignment count =='
WITH state_counts AS (
  SELECT
    f_findingid,
    s_studyid,
    i_intervention_name,
    NULLIF(f_effect_size_wwc, '')::numeric AS effect_size_wwc,
    NULLIF(f_improvement_index, '')::numeric AS improvement_index,
    NULLIF(f_p_value_wwc, '')::numeric AS p_value_wwc,
    (CASE WHEN s_region_state_alabama = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_alaska = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_arizona = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_arkansas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_california = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_colorado = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_connecticut = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_delaware = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_dc = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_florida = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_georgia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_hawaii = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_idaho = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_illinois = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_indiana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_iowa = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_kansas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_kentucky = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_louisiana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_maine = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_maryland = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_massachusetts = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_michigan = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_minnesota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_mississippi = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_missouri = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_montana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_nebraska = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_nevada = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_hampshire = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_jersey = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_mexico = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_york = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_north_carolina = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_north_dakota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_ohio = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_oklahoma = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_oregon = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_pennsylvania = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_rhode_island = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_south_carolina = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_south_dakota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_tennessee = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_texas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_utah = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_vermont = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_virginia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_washington = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_west_virginia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_wisconsin = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_wyoming = '1.00' THEN 1 ELSE 0 END) AS state_tag_count
  FROM raw.wwc_original
)
SELECT
  state_tag_count,
  COUNT(*) AS findings,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_rows,
  ROUND(AVG(effect_size_wwc)::numeric, 3) AS mean_effect_size,
  ROUND(AVG(improvement_index)::numeric, 1) AS mean_improvement_index,
  ROUND(AVG(p_value_wwc)::numeric, 3) AS mean_p_value
FROM state_counts
GROUP BY state_tag_count
ORDER BY state_tag_count;

\echo '== Top states by finding assignments =='
WITH state_assignments AS (
  SELECT 'Alabama' AS state_name, COUNT(*) AS findings, COUNT(DISTINCT s_studyid) AS studies, COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> '') AS interventions, AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
  FROM raw.wwc_original WHERE s_region_state_alabama = '1.00'
  UNION ALL SELECT 'Alaska', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_alaska = '1.00'
  UNION ALL SELECT 'Arizona', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_arizona = '1.00'
  UNION ALL SELECT 'Arkansas', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_arkansas = '1.00'
  UNION ALL SELECT 'California', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_california = '1.00'
  UNION ALL SELECT 'Colorado', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_colorado = '1.00'
  UNION ALL SELECT 'Connecticut', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_connecticut = '1.00'
  UNION ALL SELECT 'Delaware', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_delaware = '1.00'
  UNION ALL SELECT 'District of Columbia', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_dc = '1.00'
  UNION ALL SELECT 'Florida', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_florida = '1.00'
  UNION ALL SELECT 'Georgia', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_georgia = '1.00'
  UNION ALL SELECT 'Hawaii', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_hawaii = '1.00'
  UNION ALL SELECT 'Idaho', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_idaho = '1.00'
  UNION ALL SELECT 'Illinois', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_illinois = '1.00'
  UNION ALL SELECT 'Indiana', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_indiana = '1.00'
  UNION ALL SELECT 'Iowa', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_iowa = '1.00'
  UNION ALL SELECT 'Kansas', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_kansas = '1.00'
  UNION ALL SELECT 'Kentucky', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_kentucky = '1.00'
  UNION ALL SELECT 'Louisiana', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_louisiana = '1.00'
  UNION ALL SELECT 'Maine', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_maine = '1.00'
  UNION ALL SELECT 'Maryland', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_maryland = '1.00'
  UNION ALL SELECT 'Massachusetts', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_massachusetts = '1.00'
  UNION ALL SELECT 'Michigan', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_michigan = '1.00'
  UNION ALL SELECT 'Minnesota', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_minnesota = '1.00'
  UNION ALL SELECT 'Mississippi', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_mississippi = '1.00'
  UNION ALL SELECT 'Missouri', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_missouri = '1.00'
  UNION ALL SELECT 'Montana', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_montana = '1.00'
  UNION ALL SELECT 'Nebraska', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_nebraska = '1.00'
  UNION ALL SELECT 'Nevada', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_nevada = '1.00'
  UNION ALL SELECT 'New Hampshire', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_new_hampshire = '1.00'
  UNION ALL SELECT 'New Jersey', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_new_jersey = '1.00'
  UNION ALL SELECT 'New Mexico', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_new_mexico = '1.00'
  UNION ALL SELECT 'New York', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_new_york = '1.00'
  UNION ALL SELECT 'North Carolina', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_north_carolina = '1.00'
  UNION ALL SELECT 'North Dakota', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_north_dakota = '1.00'
  UNION ALL SELECT 'Ohio', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_ohio = '1.00'
  UNION ALL SELECT 'Oklahoma', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_oklahoma = '1.00'
  UNION ALL SELECT 'Oregon', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_oregon = '1.00'
  UNION ALL SELECT 'Pennsylvania', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_pennsylvania = '1.00'
  UNION ALL SELECT 'Rhode Island', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_rhode_island = '1.00'
  UNION ALL SELECT 'South Carolina', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_south_carolina = '1.00'
  UNION ALL SELECT 'South Dakota', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_south_dakota = '1.00'
  UNION ALL SELECT 'Tennessee', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_tennessee = '1.00'
  UNION ALL SELECT 'Texas', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_texas = '1.00'
  UNION ALL SELECT 'Utah', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_utah = '1.00'
  UNION ALL SELECT 'Vermont', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_vermont = '1.00'
  UNION ALL SELECT 'Virginia', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_virginia = '1.00'
  UNION ALL SELECT 'Washington', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_washington = '1.00'
  UNION ALL SELECT 'West Virginia', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_west_virginia = '1.00'
  UNION ALL SELECT 'Wisconsin', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_wisconsin = '1.00'
  UNION ALL SELECT 'Wyoming', COUNT(*), COUNT(DISTINCT s_studyid), COUNT(DISTINCT i_intervention_name) FILTER (WHERE i_intervention_name IS NOT NULL AND btrim(i_intervention_name) <> ''), AVG(NULLIF(f_effect_size_wwc, '')::numeric) FROM raw.wwc_original WHERE s_region_state_wyoming = '1.00'
)
SELECT *
FROM state_assignments
WHERE findings > 0
ORDER BY findings DESC, state_name
LIMIT 15;

\echo '== State concentration among all state-tagged assignments =='
WITH state_assignments AS (
  SELECT 'Alabama' AS state_name, COUNT(*) AS findings FROM raw.wwc_original WHERE s_region_state_alabama = '1.00'
  UNION ALL SELECT 'Alaska', COUNT(*) FROM raw.wwc_original WHERE s_region_state_alaska = '1.00'
  UNION ALL SELECT 'Arizona', COUNT(*) FROM raw.wwc_original WHERE s_region_state_arizona = '1.00'
  UNION ALL SELECT 'Arkansas', COUNT(*) FROM raw.wwc_original WHERE s_region_state_arkansas = '1.00'
  UNION ALL SELECT 'California', COUNT(*) FROM raw.wwc_original WHERE s_region_state_california = '1.00'
  UNION ALL SELECT 'Colorado', COUNT(*) FROM raw.wwc_original WHERE s_region_state_colorado = '1.00'
  UNION ALL SELECT 'Connecticut', COUNT(*) FROM raw.wwc_original WHERE s_region_state_connecticut = '1.00'
  UNION ALL SELECT 'Delaware', COUNT(*) FROM raw.wwc_original WHERE s_region_state_delaware = '1.00'
  UNION ALL SELECT 'District of Columbia', COUNT(*) FROM raw.wwc_original WHERE s_region_state_dc = '1.00'
  UNION ALL SELECT 'Florida', COUNT(*) FROM raw.wwc_original WHERE s_region_state_florida = '1.00'
  UNION ALL SELECT 'Georgia', COUNT(*) FROM raw.wwc_original WHERE s_region_state_georgia = '1.00'
  UNION ALL SELECT 'Hawaii', COUNT(*) FROM raw.wwc_original WHERE s_region_state_hawaii = '1.00'
  UNION ALL SELECT 'Idaho', COUNT(*) FROM raw.wwc_original WHERE s_region_state_idaho = '1.00'
  UNION ALL SELECT 'Illinois', COUNT(*) FROM raw.wwc_original WHERE s_region_state_illinois = '1.00'
  UNION ALL SELECT 'Indiana', COUNT(*) FROM raw.wwc_original WHERE s_region_state_indiana = '1.00'
  UNION ALL SELECT 'Iowa', COUNT(*) FROM raw.wwc_original WHERE s_region_state_iowa = '1.00'
  UNION ALL SELECT 'Kansas', COUNT(*) FROM raw.wwc_original WHERE s_region_state_kansas = '1.00'
  UNION ALL SELECT 'Kentucky', COUNT(*) FROM raw.wwc_original WHERE s_region_state_kentucky = '1.00'
  UNION ALL SELECT 'Louisiana', COUNT(*) FROM raw.wwc_original WHERE s_region_state_louisiana = '1.00'
  UNION ALL SELECT 'Maine', COUNT(*) FROM raw.wwc_original WHERE s_region_state_maine = '1.00'
  UNION ALL SELECT 'Maryland', COUNT(*) FROM raw.wwc_original WHERE s_region_state_maryland = '1.00'
  UNION ALL SELECT 'Massachusetts', COUNT(*) FROM raw.wwc_original WHERE s_region_state_massachusetts = '1.00'
  UNION ALL SELECT 'Michigan', COUNT(*) FROM raw.wwc_original WHERE s_region_state_michigan = '1.00'
  UNION ALL SELECT 'Minnesota', COUNT(*) FROM raw.wwc_original WHERE s_region_state_minnesota = '1.00'
  UNION ALL SELECT 'Mississippi', COUNT(*) FROM raw.wwc_original WHERE s_region_state_mississippi = '1.00'
  UNION ALL SELECT 'Missouri', COUNT(*) FROM raw.wwc_original WHERE s_region_state_missouri = '1.00'
  UNION ALL SELECT 'Montana', COUNT(*) FROM raw.wwc_original WHERE s_region_state_montana = '1.00'
  UNION ALL SELECT 'Nebraska', COUNT(*) FROM raw.wwc_original WHERE s_region_state_nebraska = '1.00'
  UNION ALL SELECT 'Nevada', COUNT(*) FROM raw.wwc_original WHERE s_region_state_nevada = '1.00'
  UNION ALL SELECT 'New Hampshire', COUNT(*) FROM raw.wwc_original WHERE s_region_state_new_hampshire = '1.00'
  UNION ALL SELECT 'New Jersey', COUNT(*) FROM raw.wwc_original WHERE s_region_state_new_jersey = '1.00'
  UNION ALL SELECT 'New Mexico', COUNT(*) FROM raw.wwc_original WHERE s_region_state_new_mexico = '1.00'
  UNION ALL SELECT 'New York', COUNT(*) FROM raw.wwc_original WHERE s_region_state_new_york = '1.00'
  UNION ALL SELECT 'North Carolina', COUNT(*) FROM raw.wwc_original WHERE s_region_state_north_carolina = '1.00'
  UNION ALL SELECT 'North Dakota', COUNT(*) FROM raw.wwc_original WHERE s_region_state_north_dakota = '1.00'
  UNION ALL SELECT 'Ohio', COUNT(*) FROM raw.wwc_original WHERE s_region_state_ohio = '1.00'
  UNION ALL SELECT 'Oklahoma', COUNT(*) FROM raw.wwc_original WHERE s_region_state_oklahoma = '1.00'
  UNION ALL SELECT 'Oregon', COUNT(*) FROM raw.wwc_original WHERE s_region_state_oregon = '1.00'
  UNION ALL SELECT 'Pennsylvania', COUNT(*) FROM raw.wwc_original WHERE s_region_state_pennsylvania = '1.00'
  UNION ALL SELECT 'Rhode Island', COUNT(*) FROM raw.wwc_original WHERE s_region_state_rhode_island = '1.00'
  UNION ALL SELECT 'South Carolina', COUNT(*) FROM raw.wwc_original WHERE s_region_state_south_carolina = '1.00'
  UNION ALL SELECT 'South Dakota', COUNT(*) FROM raw.wwc_original WHERE s_region_state_south_dakota = '1.00'
  UNION ALL SELECT 'Tennessee', COUNT(*) FROM raw.wwc_original WHERE s_region_state_tennessee = '1.00'
  UNION ALL SELECT 'Texas', COUNT(*) FROM raw.wwc_original WHERE s_region_state_texas = '1.00'
  UNION ALL SELECT 'Utah', COUNT(*) FROM raw.wwc_original WHERE s_region_state_utah = '1.00'
  UNION ALL SELECT 'Vermont', COUNT(*) FROM raw.wwc_original WHERE s_region_state_vermont = '1.00'
  UNION ALL SELECT 'Virginia', COUNT(*) FROM raw.wwc_original WHERE s_region_state_virginia = '1.00'
  UNION ALL SELECT 'Washington', COUNT(*) FROM raw.wwc_original WHERE s_region_state_washington = '1.00'
  UNION ALL SELECT 'West Virginia', COUNT(*) FROM raw.wwc_original WHERE s_region_state_west_virginia = '1.00'
  UNION ALL SELECT 'Wisconsin', COUNT(*) FROM raw.wwc_original WHERE s_region_state_wisconsin = '1.00'
  UNION ALL SELECT 'Wyoming', COUNT(*) FROM raw.wwc_original WHERE s_region_state_wyoming = '1.00'
), totals AS (
  SELECT SUM(findings) AS total_assignments FROM state_assignments
)
SELECT
  ROUND(100.0 * SUM(findings) / MAX(total_assignments), 2) AS top4_share_pct,
  SUM(findings) AS top4_assignments,
  MAX(total_assignments) AS total_state_assignments
FROM (
  SELECT * FROM state_assignments ORDER BY findings DESC LIMIT 4
) top4
CROSS JOIN totals;

\echo '== Urbanicity coverage and overlap =='
WITH urbanicity_flags AS (
  SELECT
    f_findingid,
    NULLIF(f_effect_size_wwc, '')::numeric AS effect_size_wwc,
    NULLIF(f_improvement_index, '')::numeric AS improvement_index,
    (CASE WHEN s_urbanicity_rural = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_urbanicity_suburban = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_urbanicity_urban = '1.00' THEN 1 ELSE 0 END) AS urbanicity_tag_count,
    CASE
      WHEN s_urbanicity_rural = '1.00' AND s_urbanicity_suburban = '1.00' AND s_urbanicity_urban = '1.00' THEN 'rural_suburban_urban'
      WHEN s_urbanicity_rural = '1.00' AND s_urbanicity_suburban = '1.00' THEN 'rural_suburban'
      WHEN s_urbanicity_rural = '1.00' AND s_urbanicity_urban = '1.00' THEN 'rural_urban'
      WHEN s_urbanicity_suburban = '1.00' AND s_urbanicity_urban = '1.00' THEN 'suburban_urban'
      WHEN s_urbanicity_rural = '1.00' THEN 'rural_only'
      WHEN s_urbanicity_suburban = '1.00' THEN 'suburban_only'
      WHEN s_urbanicity_urban = '1.00' THEN 'urban_only'
      ELSE 'unlabeled'
    END AS urbanicity_group
  FROM raw.wwc_original
)
SELECT
  urbanicity_group,
  COUNT(*) AS findings,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_rows,
  ROUND(AVG(effect_size_wwc)::numeric, 3) AS mean_effect_size,
  ROUND(AVG(improvement_index)::numeric, 1) AS mean_improvement_index
FROM urbanicity_flags
GROUP BY urbanicity_group
ORDER BY findings DESC;

\echo '== Transportability-style signal: states with more multi-state rows vs mean effect =='
WITH state_rows AS (
  SELECT
    s_studyid,
    NULLIF(f_effect_size_wwc, '')::numeric AS effect_size_wwc,
    (CASE WHEN s_region_state_alabama = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_alaska = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_arizona = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_arkansas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_california = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_colorado = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_connecticut = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_delaware = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_dc = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_florida = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_georgia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_hawaii = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_idaho = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_illinois = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_indiana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_iowa = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_kansas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_kentucky = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_louisiana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_maine = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_maryland = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_massachusetts = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_michigan = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_minnesota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_mississippi = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_missouri = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_montana = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_nebraska = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_nevada = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_hampshire = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_jersey = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_mexico = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_new_york = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_north_carolina = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_north_dakota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_ohio = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_oklahoma = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_oregon = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_pennsylvania = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_rhode_island = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_south_carolina = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_south_dakota = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_tennessee = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_texas = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_utah = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_vermont = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_virginia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_washington = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_west_virginia = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_wisconsin = '1.00' THEN 1 ELSE 0 END
     + CASE WHEN s_region_state_wyoming = '1.00' THEN 1 ELSE 0 END) AS state_tag_count
  FROM raw.wwc_original
)
SELECT
  CASE
    WHEN state_tag_count = 0 THEN 'no_state_tag'
    WHEN state_tag_count = 1 THEN 'single_state'
    WHEN state_tag_count = 2 THEN 'two_states'
    ELSE 'three_plus_states'
  END AS state_span_group,
  COUNT(*) AS findings,
  ROUND(AVG(effect_size_wwc)::numeric, 3) AS mean_effect_size
FROM state_rows
GROUP BY 1
ORDER BY findings DESC;

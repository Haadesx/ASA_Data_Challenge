-- Load original WWC export and teammate aggregated data.
-- Runs once on first container initialization.
\copy raw.wwc_original FROM '/data/Interventions_Studies_And_Findings.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');
\copy raw.wwc_aggregated FROM '/data/asadata_aggregated.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"', NULL '');

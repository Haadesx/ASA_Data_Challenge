# ASA Data Challenge - WWC Analysis

This repository contains:
- WWC raw exports and aggregated teammate artifacts
- Data engineering and modeling scripts
- Data products (analysis-ready subsets)
- A professional data readiness dashboard
- In-depth project documentation

## Public Dashboard

- Landing page: `index.html`
- Dashboard file: `Urvi_Analysis/dashboard/data_readiness_dashboard.html`
- Documentation (formatted HTML): `Urvi_Analysis/WWC_Project_Documentation_InDepth.html`
- Methods and math report (formatted HTML): `Urvi_Analysis/Original_Multistate_Methods_Report.html`
- Data products index: `Urvi_Analysis/data_products/index.html`
- Outputs index: `outputs_ctx/index.html`

After GitHub Pages is enabled, public URL should be:

`https://haadesx.github.io/ASA_Data_Challenge/`

## Key Documentation

- `Urvi_Analysis/WWC_Project_Documentation_InDepth.md`
- `docs/wwc_end_to_end_documentation.md`
- `Urvi_Analysis/mentor_data_availability_plan.md`

## Docker SQL Environment

A Dockerized PostgreSQL setup is available for ad-hoc querying of both the original WWC export and teammate aggregated data.

- Setup guide: `db/README.md`
- Start script: `./db/start.sh`
- Compose file: `docker-compose.yml`
- Init SQL: `db/init/`
- Source-to-db column mappings: `db/column_mappings/`

## SQL Subagent

A reusable delegated-agent setup for SQL analysis lives at:

- `.claude/agents/wwc-postgres-analyst.md`
- `docs/data/wwc-postgres-schema.md`

Compatibility pointer:

- `docs/asa_sql_subagent.md`

Use the canonical agent spec when you want a subagent to run reproducible WWC SQL analysis against the Docker database.

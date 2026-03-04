# WWC Data Lapses and External Data Expansion Strategy

Date: 2026-03-02

## 0) What was added now (tangible update)

Created files:

- `data/context_state_year_saipe_extended.csv`
  - 1,632 rows (`51 states/DC x 1989-2024`)
  - pulled from Census SAIPE API (`SAEPOVRT0_17_PT`, `SAEMHI_PT`)
- `Urvi_Analysis/data_products/finding_context_saipe_1989_2024.csv`
  - finding-level join-ready context table with:
    - state-level SAIPE context where a state token is available
    - region-level fallback (`Northeast`, `Midwest`, `South`, `West`)
- `Urvi_Analysis/data_products/saipe_merge_coverage_summary_2026-03-02.csv`
  - key merge diagnostics

Coverage lift from this step:

- State-only SAIPE context coverage (all findings): **67.1%**
- State+region fallback coverage (all findings): **79.7%**
- State-only SAIPE context coverage (behavior subset): **46.2%**
- State+region fallback coverage (behavior subset): **73.7%**

## 1) What is missing right now (lapses)

Based on `Urvi_Analysis/data_products/combined_enriched_base.csv` (`n=13,023` findings):

- `s_Demographics_Sample_FRPL`: **32.3%** coverage
- `s_Demographics_Sample_ELL`: **39.3%** coverage
- `s_Urbanicity`: **66.9%** coverage
- `s_School_type`: **54.3%** coverage
- `s_Region_State`: **80.9%** coverage

Behavior/safety-relevant subset (`n=1,063` findings, keyword-based):

- FRPL coverage drops to **27.8%**
- ELL coverage drops to **22.5%**
- State coverage is **74.4%**
- Urbanicity coverage is **65.0%**

## 2) Why this matters (what these lapses cause)

- **Selection bias risk**: subgroup analyses are disproportionately based on studies that report FRPL/ELL.
- **Confounding risk**: without poverty/resource/safety context, intervention effects can proxy background state differences.
- **External validity limits**: weak context features make "what works for whom" claims less transportable.
- **Power loss in high-impact policy questions**: violence/discipline-focused work has the sparsest subgroup coverage.

## 3) Best external datasets to add next

## Priority A (high value, immediate)

1. NCES CCD public school files (state-year demographics)
- Link: https://nces.ed.gov/ccd/files.asp
- Adds: state-year FRPL, ELL, SWD context baselines
- Join: `state_abbr + analysis_year`
- Use: anchor subgroup models when study-level FRPL/ELL are missing

2. Census SAIPE child poverty
- Link: https://www.census.gov/programs-surveys/saipe/data/datasets.All.html
- Adds: state/year child poverty rate
- Join: `state_abbr + analysis_year`
- Use: poverty-adjusted heterogeneity and policy interpretation

3. Census ACS 5-year (state-level socioeconomic composition)
- Link: https://www.census.gov/data/developers/data-sets/acs-5year.html
- Adds: income, BA share, racial composition, unemployment proxies
- Join: `state_abbr + analysis_year`
- Use: macro context controls for transportability

## Priority B (for behavior/violence poster track)

1. CRDC data portal
- Link: https://ocrdata.ed.gov/
- Adds: discipline referrals, suspensions/expulsions, school climate/safety indicators
- Join: state-year (aggregate CRDC to state; map to nearest collection year)
- Use: test if intervention effects attenuate in high-discipline contexts

2. CDC YRBSS data
- Link: https://www.cdc.gov/yrbs/data/index.html
- Adds: state youth violence, bullying, weapon carrying, mental health prevalence
- Join: `state_abbr + nearest survey year`
- Use: construct "high-violence context" moderators for behavior outcomes

## Priority C (resource/economic context)

1. NCES F-33 school finance
- Link: https://nces.ed.gov/ccd/f33agency.asp
- Adds: per-pupil spending, revenue/fiscal capacity proxies
- Join: state + fiscal year mapped to analysis year
- Use: estimate whether effects differ by resource environment

2. BLS LAUS unemployment
- Link: https://www.bls.gov/lau/
- Adds: state labor market stress
- Join: `state_abbr + year`
- Use: recession stress control in time-varying models

## 4) Merge method (when and how)

1. Build canonical keys in WWC base:
- `state_abbr` from `s_Region_State`
- `analysis_year` from `s_Publication_Date`, fallback `s_Posting_Date`

2. Apply year harmonization:
- exact merge when available
- if missing, nearest-year mapping within ±2 years
- if still missing, clamp to context panel range for sensitivity-only runs

3. Model strategy:
- Stage 1: baseline WWC-only model
- Stage 2: add socioeconomic/resource context
- Stage 3: add safety/violence context (CRDC/YRBSS) for behavior outcomes

4. Validation outputs to publish:
- merge coverage table by dataset
- coefficient stability plot (baseline vs +context)
- subgroup ranking shifts after context controls

## 5) What we can claim after expansion

- Whether interventions that work in low-poverty/low-violence contexts fail to transport to high-poverty/high-violence contexts.
- Which interventions remain robust after controlling for background resource/safety differences.
- A policy-relevant targeting rule: "intervention X is most effective in context band Y".

## 6) Immediate execution checklist (next 7 days)

1. Rebuild context panel with complete CCD + SAIPE + ACS state-year coverage.
2. Add CRDC and YRBSS state-year context table for behavior outcomes.
3. Regenerate dashboard tabs:
- data coverage
- merge success rates
- heterogeneity by context bands
4. Re-run multivariate models and produce poster-ready figures.

"""
First-pass model formulas for WWC "what works for whom" analysis.

These formulas assume a denormalized dataframe similar to mart.v_finding_analytic
plus engineered columns described in docs/wwc_2026_schema_and_models.md.
"""

MODEL_A_FORMULA = (
    "effect_size_final ~ "
    "C(intervention_family) + frpl_share + ell_share + swd_share + minority_share + "
    "C(grade_band) + C(urbanicity) + C(study_design_std) + study_quality_score + "
    "publication_year_c + "
    "C(intervention_family):frpl_share + "
    "C(intervention_family):ell_share + "
    "C(intervention_family):swd_share"
)

MODEL_B_FORMULA = (
    "effect_size_final ~ "
    "C(intervention_family) + log_pp_exp + child_poverty_rate + teacher_salary_real + "
    "frpl_share + ell_share + C(study_design_std) + study_quality_score + publication_year_c + "
    "C(intervention_family):log_pp_exp + "
    "C(intervention_family):child_poverty_rate"
)

MODEL_C_TRANSPORT_FORMULA = (
    "effect_size_final ~ "
    "C(intervention_family) + acs_income_z + acs_ba_z + acs_white_share + acs_black_share + "
    "acs_hispanic_share + rucc_rural_share + frpl_share + ell_share + "
    "C(intervention_family):rucc_rural_share"
)

MODEL_C_COVERAGE_FORMULA = (
    "n_findings ~ C(subgroup) + C(state_abbr) + C(outcome_domain) + year_c"
)

# Recommended random intercept structure (if using mixed models):
RANDOM_EFFECTS = [
    "intervention_id",
    "study_id",
    "outcome_domain",
]

# Common weight variable for inverse-variance meta-regression:
WEIGHT_COLUMN = "weight_iv"


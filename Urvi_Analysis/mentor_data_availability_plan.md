# WWC Aggregated Data: Availability Assessment and Recommended Path

Source analyzed: `Urvi_Analysis/asadata_aggregated.csv`  
Row/column shape: `13,023 x 90`

## 1) What level is the data at?

The file is still fundamentally **finding-level** (`f_FindingID` unique in all rows), with nested context:
- Study-level fields (`s_*`) repeated across findings from the same study.
- Intervention-level fields (`i_*`) mostly sparse but present for a subset.

IDs and grain:
- Findings: `13,023`
- Studies: `1,601`
- Interventions: `1,035` (`s_interventionID`)

## 2) Geography granularity available

- **State-level**: available in `s_Region_State` (68.0% of rows, 63.1% of studies include at least one specific state).
- **County-level**: not available.
- **School-level**: no school IDs; only coarse school descriptors (`s_School_type`, `s_Urbanicity`) with partial coverage.

State support:
- States with >=30 finding rows: `45`
- States with >=100 finding rows: `37`

Top states by finding rows:
- Texas 1,812; California 1,796; New York 1,735; Pennsylvania 1,066; North Carolina 955.

## 3) Coverage and sparsity reality

High coverage (strong):
- Outcomes: `f_Effect_Size_WWC` 81.0%, `f_p_Value_WWC` 92.3%, `f_Outcome_Sample_Size` 99.9%
- Design/quality: `s_Study_Design` 99.9%, `s_Study_Rating` 100%
- Content/context: `s_Grade` 97.9%, `s_Topic` 93.0%, `s_Region_State` 80.9%

Moderate/low coverage (limits subgroup precision):
- `s_Urbanicity` 66.9%
- `s_School_type` 54.3%
- `s_Demographics_Sample_ELL` 39.3%
- `s_Demographics_Sample_FRPL` 32.3%
- `s_Disability` 16.1%
- `s_Demographics_Sample_Minority` 0.4%

## 4) Feasible analysis subsets

## 4.1 Predictive ML core (recommended primary)
Required:
- `f_Effect_Size_WWC`, `s_Study_Design`, `s_Study_Rating`, `s_Grade`, `s_Region_State`

Resulting sample:
- Rows: `8,412` (64.6%)
- Studies: `1,077`
- Interventions: `745`
- Outcome domains: `183`

This is large enough for predictive modeling with cross-validation and interaction terms.

## 4.2 CI-friendly core (recommended secondary)
Required:
- `f_Effect_Size_WWC`, `f_p_Value_WWC`, `f_Outcome_Sample_Size`, `s_Study_Design`, `s_Study_Rating`

Resulting sample:
- Rows: `10,329` (79.3%)
- Studies: `1,315`
- Interventions: `903`
- Outcome domains: `195`

This is the best subset for weighted/meta-regression and confidence intervals.

## 4.3 Demographic-rich subset (targeted only)
Required:
- ML core + `s_Demographics_Sample_FRPL` + `s_Demographics_Sample_ELL`

Resulting sample:
- Rows: `1,815` (13.9%)
- Studies: `260`
- Interventions: `186`
- Outcome domains: `100`

Useful for focused subgroup claims, not as the only analysis set.

## 5) Recommended strategy to mentor

1. Use **two-track analysis**:
- Track A: CI Core for robust effect estimation and inference.
- Track B: ML Core for predictive heterogeneity patterns.

2. Keep demographic-rich analysis as **sensitivity/targeted module**:
- Use it for “for whom” examples with clear caveats on sample size.

3. Scope geography to **state-level only**:
- Explicitly state county/school-ID analysis is not possible with this file.

4. Use interventions with sufficient support:
- In ML Core: 105 interventions have >=20 findings; 26 have >=50 findings.
- Set minimum support thresholds before ranking.

## 6) Immediate deliverables already generated

- Full column-level profile with level/constancy diagnostics:  
  `Urvi_Analysis/column_level_profile.csv`

This can be used to justify which variables enter each model and why.


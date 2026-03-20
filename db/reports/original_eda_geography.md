# Original WWC Geography and Urbanicity EDA

**Dataset:** `raw.wwc_original` in the local Dockerized PostgreSQL environment  
**Scope:** original export only, no teammate-aggregated table used  
**Focus:** state coverage, top states, concentration, multi-state prevalence, urbanicity overlap, and a descriptive transportability-style signal

## Executive Summary

The original WWC export is geographically concentrated and structurally overlapping. A small set of states carries a large share of the state-tagged evidence, and urbanicity flags are not mutually exclusive. The cleanest descriptive signal is that more geographic breadth does not correspond to stronger average effects in a monotonic way: single-state rows are stronger than 3+ state rows, while 2-state rows are in between.

## Dataset Coverage

- Total rows: `13023`
- Rows with effect size: `10553`
- Rows with improvement index: `12190`
- Rows with p-value: `12025`
- Rows with statistical-significance flag: `12905`
- Distinct studies: `1601`
- Distinct named interventions: `186`

## State Coverage

### State-tag distribution

Using only the actual state indicators in the original export, the row distribution is:

- `0` state tags: `4164` findings (`31.97%`)
- `1` state tag: `6545` findings (`50.26%`)
- `2` state tags: `789` findings (`6.06%`)
- `3+` state tags: `1525` findings (`11.71%`)

If you combine all rows with two or more state tags, multi-state prevalence is `2314` findings, or `17.77%` of the full export.

### Top states by finding assignments

The largest state contributors are:

- Texas: `1812` findings
- California: `1796` findings
- New York: `1735` findings
- Pennsylvania: `1066` findings
- North Carolina: `955` findings
- Illinois: `769` findings
- Florida: `731` findings
- Massachusetts: `720` findings
- District of Columbia: `651` findings
- Ohio: `613` findings
- Georgia: `604` findings
- Tennessee: `516` findings
- Washington: `505` findings
- Maryland: `469` findings
- Michigan: `434` findings

### Concentration

The top four states by assignment count are Texas, California, New York, and Pennsylvania.

- Top 4 state assignments: `6409`
- Total state assignments: `19768`
- Top 4 share: `32.42%`

That is the main concentration result: a small set of states dominates the geographic footprint.

## Urbanicity Coverage And Overlap

Urbanicity is also overlapping, not cleanly binary.

- `urban_only`: `4884` findings, mean effect size `0.213`, mean improvement index `7.3`
- `unlabeled`: `4308` findings, mean effect size `0.250`, mean improvement index `8.7`
- `rural_suburban_urban`: `1374` findings, mean effect size `0.162`, mean improvement index `5.9`
- `suburban_urban`: `719` findings, mean effect size `0.147`, mean improvement index `5.5`
- `rural_urban`: `660` findings, mean effect size `0.186`, mean improvement index `6.1`
- `suburban_only`: `584` findings, mean effect size `0.206`, mean improvement index `7.9`
- `rural_only`: `297` findings, mean effect size `0.205`, mean improvement index `7.5`
- `rural_suburban`: `197` findings, mean effect size `0.266`, mean improvement index `8.5`

The important structural point is that a substantial part of the sample is tagged with multiple urbanicity categories, and a very large slice is unlabeled.

## Transportability-Style Descriptive Signal

A simple descriptive check asks whether wider state coverage corresponds to larger effects.

- `single_state`: `6545` findings, mean effect size `0.185`
- `two_states`: `789` findings, mean effect size `0.217`
- `three_plus_states`: `1525` findings, mean effect size `0.156`
- `no_state_tag`: `4164` findings, mean effect size `0.281`

The cleanest interpretation is the non-monotonic part: single-state rows are stronger than 3+ state rows, and 2-state rows sit in between. That does not support a simple “more geographic breadth means larger effects” story. The no-state-tag group is large, so it should be treated as a coverage gap rather than a transportability benchmark.

## Interpretation

The original WWC geography signal is best summarized as:

- evidence is concentrated in a small number of states
- multi-state rows exist, but they are a minority
- urbanicity flags overlap enough that they should not be treated as mutually exclusive groups
- the strongest rural-only mean effect is based on a small slice, so it is a signal, not a conclusion
- more state breadth does not imply stronger effects in this dataset

That makes the dataset better suited to descriptive transportability questions than to a clean causal estimate of geography effects.

## Reproducibility

Run the saved SQL pack:

```bash
./db/run_query.sh db/queries/original_eda_geography.sql
```

The SQL pack was used to generate the numbers in this report.

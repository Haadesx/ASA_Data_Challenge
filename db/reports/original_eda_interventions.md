# Original WWC Intervention EDA

**Dataset:** `raw.wwc_original` in the local Dockerized PostgreSQL environment  
**Focus:** interventions, outcome domains, effect-size / improvement-index distributions, and evidence-quality signals

## Executive Summary

The original WWC export is large enough for useful descriptive EDA, but it is structurally sparse in the fields most people want to use for interpretation. The table has 13,023 rows and 1,601 distinct studies, but 9,965 rows do not have a usable intervention name. Outcome-domain tagging is also sparse: 9,965 rows have a missing outcome domain, which means more than three quarters of the rows cannot be cleanly grouped into outcome categories.

Among the named interventions that have at least 10 rows, support is concentrated in a small set of programs. The largest named interventions are `Success for All®` and `Head Start` with 136 rows each, followed by `READ 180®` with 103 rows, `Fraction Face-Off!` with 85 rows, and `Dual Enrollment Programs` with 80 rows.

Effect sizes are right-skewed but not trivial: 2,333 rows are negative, 2,601 fall in the 0.00 to 0.09 range, and 1,632 rows are at or above 0.50. Improvement index values show the same pattern, with 2,332 negative rows and 831 rows at 30 or above.

The most useful quality signal is that the dataset contains both WWC finding ratings and ESSA tiers, but ESSA coverage is sparse relative to the full table. The evidence base is also concentrated in a few interventions: only 4 interventions have 10 or more distinct studies.

## Base Coverage

From the full table:

- Total rows: 13,023
- Distinct studies: 1,601
- Distinct named interventions: 186
- Rows with missing intervention name: 9,965
- Rows with effect size: 10,553
- Rows with improvement index: 12,190
- Rows with p-value: 12,025
- Rows with statistical significance flag: 12,905
- Rows with finding rating: 10,259
- Rows with ESSA rating: 2,097

## Publication Date Coverage

- Rows with nonblank publication date: 13,023
- Distinct publication date values: 66
- Minimum publication date value: 1984
- Maximum publication date value: `N.D.`

That `N.D.` maximum is a data-quality signal: publication date is not fully normalized in the source table.

## Top Interventions by Support

Named interventions with at least 10 rows are concentrated in a small number of programs.

Top support counts:

- `Success for All®`: 136 rows, 9 studies, mean effect size 0.2610, mean improvement index 9.3235
- `Head Start`: 136 rows, 1 study, mean effect size 0.0104, mean improvement index 0.4412
- `READ 180®`: 103 rows, 10 studies, mean effect size 0.0927, mean improvement index 3.4563
- `Fraction Face-Off!`: 85 rows, 1 study, mean effect size 0.7494, mean improvement index 23.6706
- `Dual Enrollment Programs`: 80 rows, 5 studies, mean effect size 0.5462, mean improvement index 16.1750
- `Green Dot Public Schools`: 77 rows, 1 study, mean effect size 0.1873, mean improvement index 7.2763
- `National Board for Professional Teaching Standards (NBPTS) Certification`: 73 rows, 5 studies, mean effect size 0.0745, mean improvement index 2.9318
- `Leadership and Assistance for Science Education Reform (LASER)`: 72 rows, 1 study, mean effect size 0.0283, mean improvement index 1.1528
- `Leveled Literacy Intervention`: 62 rows, 2 studies, mean effect size 0.2987, mean improvement index 11.1452
- `Linked Learning Communities`: 62 rows, 4 studies, mean effect size 0.0925, mean improvement index 1.3065
- `Social Belonging`: 59 rows, 8 studies, mean effect size 0.0465, mean improvement index 1.7966
- `Caring School Community (CSC)`: 54 rows, 2 studies, mean effect size 0.1316, mean improvement index 5.4074
- `Sound Partners`: 51 rows, 7 studies, mean effect size 0.5488, mean improvement index 20.0784
- `Growth Mindset`: 51 rows, 6 studies, mean effect size 0.1050, mean improvement index 3.8824
- `SpellRead`: 48 rows, 2 studies, mean effect size 0.5273, mean improvement index 18.6042

A key interpretation issue: support volume and effect size do not move together. Some high-support interventions have modest effects, while some smaller cells have large effects.

## Outcome-Domain Coverage

The missing outcome-domain bucket is by far the largest single group.

Top outcome-domain groups:

- Missing: 9,965 rows, 1,244 studies, mean effect size 0.2039, mean improvement index 7.3017
- Alphabetics: 388 rows, 63 studies, mean effect size 0.4164, mean improvement index 13.9691
- General Mathematics Achievement: 366 rows, 72 studies, mean effect size 0.1631, mean improvement index 5.4678
- Comprehension: 319 rows, 98 studies, mean effect size 0.1753, mean improvement index 5.9434
- Reading achievement: 135 rows, 36 studies, mean effect size 0.2992, mean improvement index 11.0000
- Social-emotional development: 117 rows, 8 studies, mean effect size 0.0218, mean improvement index 0.6579
- Academic achievement: 110 rows, 34 studies, mean effect size 0.1410, mean improvement index 4.8091
- English language arts achievement: 95 rows, 14 studies, mean effect size 0.0947, mean improvement index 3.7468
- Reading Fluency: 95 rows, 38 studies, mean effect size 0.2249, mean improvement index 9.0538
- Science Achievement: 92 rows, 10 studies, mean effect size 0.0588, mean improvement index 2.4239
- Literacy Achievement: 83 rows, 27 studies, mean effect size 0.0837, mean improvement index 3.1605
- Access and enrollment: 78 rows, 17 studies, mean effect size 0.1875, mean improvement index 5.7051
- Knowledge, attitudes, & values: 74 rows, 14 studies, mean effect size 0.1920, mean improvement index 8.6757
- Oral language: 72 rows, 27 studies, mean effect size 0.1394, mean improvement index 6.0139
- Phonological processing: 63 rows, 21 studies, mean effect size 0.5801, mean improvement index 14.0952

The large missing bucket is the main reason domain-level comparisons should be interpreted as descriptive rather than exhaustive.

## Effect-Size Distribution

Effect sizes are broad and skewed toward modest positive values, with a meaningful negative tail.

- Negative: 2,333 rows, mean effect size -0.142
- 0.00 to 0.09: 2,601 rows, mean effect size 0.046
- 0.10 to 0.24: 2,271 rows, mean effect size 0.167
- 0.25 to 0.49: 1,716 rows, mean effect size 0.357
- 0.50 to 0.99: 1,185 rows, mean effect size 0.693
- 1.00+: 447 rows, mean effect size 1.504

This is not a narrow, normal-like distribution. The evidence base has a long right tail with some very large effects.

## Improvement-Index Distribution

Improvement index shows a parallel pattern.

- Negative: 2,332 rows, mean improvement index -5.673
- 0 to 4.9: 3,767 rows, mean improvement index 1.764
- 5 to 9.9: 2,237 rows, mean improvement index 6.818
- 10 to 19.9: 2,053 rows, mean improvement index 13.841
- 20 to 29.9: 970 rows, mean improvement index 23.952
- 30+: 831 rows, mean improvement index 37.640

## Quality and Evidence Signals

The dataset has usable evidence-quality fields, but coverage varies a lot.

- `f_finding_rating`: 7,280 rows are `Meets WWC standards without reservations`; 2,979 rows are `Meets WWC standards with reservations`
- `f_essa_rating`: 1,283 rows are `Evidence Tier 3`, 507 are `Evidence Tier 1`, and 307 are `Evidence Tier 2`
- `f_is_statistically_significant`: 8,608 `False`, 4,297 `True`
- `i_effectiveness_rating`: 926 `No Discernible Effects`, 879 `Potentially Positive Effects`, 796 `Positive Effects`, 393 `Mixed Effects`, 35 `Not Measured`, 25 `Potentially Negative Effects`, 4 `N/A`

## Small-Support Caveat

Only 4 interventions have at least 10 distinct studies.

That matters because the intervention-level evidence base is concentrated in a small number of heavily studied programs, while many other interventions are thinly supported.

## Main Caveats

- Intervention names are missing for 9,965 rows.
- Outcome-domain tagging is missing for 9,965 rows.
- Publication date is not cleanly normalized and includes `N.D.` values.
- Only 4 interventions have 10 or more studies, so intervention-level comparisons are often thin.
- The dataset is best treated as descriptive evidence synthesis, not a causal design.

## Reproducibility

Run the query pack:

```bash
./db/run_query.sh db/queries/original_eda_interventions.sql
```

The report reflects the exact outputs from that query pack.

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression


REGION_BUCKET_COLUMNS = {
    "s_Region_State_Midwest",
    "s_Region_State_Northeast",
    "s_Region_State_South",
    "s_Region_State_West",
}

STATE_COL_TO_ABBR = {
    "s_Region_State_Alabama": "AL",
    "s_Region_State_Alaska": "AK",
    "s_Region_State_Arizona": "AZ",
    "s_Region_State_Arkansas": "AR",
    "s_Region_State_California": "CA",
    "s_Region_State_Colorado": "CO",
    "s_Region_State_Connecticut": "CT",
    "s_Region_State_Delaware": "DE",
    "s_Region_State_DC": "DC",
    "s_Region_State_Florida": "FL",
    "s_Region_State_Georgia": "GA",
    "s_Region_State_Hawaii": "HI",
    "s_Region_State_Idaho": "ID",
    "s_Region_State_Illinois": "IL",
    "s_Region_State_Indiana": "IN",
    "s_Region_State_Iowa": "IA",
    "s_Region_State_Kansas": "KS",
    "s_Region_State_Kentucky": "KY",
    "s_Region_State_Louisiana": "LA",
    "s_Region_State_Maine": "ME",
    "s_Region_State_Maryland": "MD",
    "s_Region_State_Massachusetts": "MA",
    "s_Region_State_Michigan": "MI",
    "s_Region_State_Minnesota": "MN",
    "s_Region_State_Mississippi": "MS",
    "s_Region_State_Missouri": "MO",
    "s_Region_State_Montana": "MT",
    "s_Region_State_Nebraska": "NE",
    "s_Region_State_Nevada": "NV",
    "s_Region_State_New_Hampshire": "NH",
    "s_Region_State_New_Jersey": "NJ",
    "s_Region_State_New_Mexico": "NM",
    "s_Region_State_New_York": "NY",
    "s_Region_State_North_Carolina": "NC",
    "s_Region_State_North_Dakota": "ND",
    "s_Region_State_Ohio": "OH",
    "s_Region_State_Oklahoma": "OK",
    "s_Region_State_Oregon": "OR",
    "s_Region_State_Pennsylvania": "PA",
    "s_Region_State_Rhode_Island": "RI",
    "s_Region_State_South_Carolina": "SC",
    "s_Region_State_South_Dakota": "SD",
    "s_Region_State_Tennessee": "TN",
    "s_Region_State_Texas": "TX",
    "s_Region_State_Utah": "UT",
    "s_Region_State_Vermont": "VT",
    "s_Region_State_Virginia": "VA",
    "s_Region_State_Washington": "WA",
    "s_Region_State_West_Virginia": "WV",
    "s_Region_State_Wisconsin": "WI",
    "s_Region_State_Wyoming": "WY",
}


def configure_plotting() -> None:
    sns.set_theme(style="whitegrid", context="talk", palette="colorblind")
    plt.rcParams["figure.facecolor"] = "#F8FAFC"
    plt.rcParams["axes.facecolor"] = "#F8FAFC"
    plt.rcParams["savefig.facecolor"] = "#F8FAFC"
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.titleweight"] = "bold"


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def coalesce_columns(df: pd.DataFrame, cols: Iterable[str]) -> pd.Series:
    out = pd.Series([pd.NA] * len(df), index=df.index, dtype="object")
    for col in cols:
        if col not in df.columns:
            continue
        candidate = df[col].replace("", pd.NA)
        mask = out.isna()
        out.loc[mask] = candidate.loc[mask]
    return out


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def to_bool(series: pd.Series) -> pd.Series:
    lookup = {
        "true": True,
        "t": True,
        "1": True,
        "1.0": True,
        "yes": True,
        "y": True,
        "false": False,
        "f": False,
        "0": False,
        "0.0": False,
        "no": False,
        "n": False,
    }
    s = series.astype("string").str.strip().str.lower()
    return s.map(lookup).astype("boolean")


def to_share(series: pd.Series) -> pd.Series:
    s = to_numeric(series)
    return pd.Series(np.where((s > 1.0) & (s <= 100.0), s / 100.0, s), index=series.index)


def parse_period_to_months(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.lower()
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    out[s == "posttest"] = 0.0
    out[s == "0 days"] = 0.0
    out[s == "0 weeks"] = 0.0
    out[s == "0 months"] = 0.0
    out[s == "0 years"] = 0.0

    pattern = r"^\s*(\d+(\.\d+)?)\s*(day|days|week|weeks|month|months|semester|semesters|year|years)\s*$"
    m = s.str.extract(pattern)
    val = pd.to_numeric(m[0], errors="coerce")
    unit = m[2]
    out.loc[unit.isin(["day", "days"])] = val[unit.isin(["day", "days"])] / 30.0
    out.loc[unit.isin(["week", "weeks"])] = val[unit.isin(["week", "weeks"])] / 4.345
    out.loc[unit.isin(["month", "months"])] = val[unit.isin(["month", "months"])]
    out.loc[unit.isin(["semester", "semesters"])] = val[unit.isin(["semester", "semesters"])] * 6.0
    out.loc[unit.isin(["year", "years"])] = val[unit.isin(["year", "years"])] * 12.0

    year_n = s.str.extract(r"^year\s+(\d+)$")
    year_v = pd.to_numeric(year_n[0], errors="coerce")
    out = out.fillna(year_v * 12.0)
    return out


def standardize_study_design(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.lower()
    mapping = {
        "randomized controlled trial": "Randomized Controlled Trial",
        "quasi-experimental design": "Quasi-Experimental Design",
        "single case design": "Single Case Design",
        "regression discontinuity design": "Regression Discontinuity Design",
    }
    return s.map(mapping).fillna(series)


def derive_grade_band(df: pd.DataFrame, prefix: str = "s_") -> pd.Series:
    pk = to_bool(df.get(f"{prefix}Grade_PK", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    k = to_bool(df.get(f"{prefix}Grade_K", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    elem = pd.Series(False, index=df.index)
    mid = pd.Series(False, index=df.index)
    hs = pd.Series(False, index=df.index)

    for g in [1, 2, 3, 4, 5]:
        elem = elem | to_bool(df.get(f"{prefix}Grade_{g}", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    for g in [6, 7, 8]:
        mid = mid | to_bool(df.get(f"{prefix}Grade_{g}", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    for g in [9, 10, 11, 12]:
        hs = hs | to_bool(df.get(f"{prefix}Grade_{g}", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)

    ps = to_bool(df.get(f"{prefix}Grade_PS", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    out = np.select(
        [pk | k, elem, mid, hs, ps],
        ["Early Childhood", "Elementary", "Middle", "High School", "Postsecondary"],
        default="Mixed/Unknown",
    )
    return pd.Series(out, index=df.index)


def derive_urbanicity(df: pd.DataFrame, prefix: str = "s_") -> pd.Series:
    urban = to_bool(df.get(f"{prefix}Urbanicity_Urban", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    suburban = to_bool(df.get(f"{prefix}Urbanicity_Suburban", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    rural = to_bool(df.get(f"{prefix}Urbanicity_Rural", pd.Series(index=df.index, dtype="object"))).fillna(False).astype(bool)
    out = np.select([urban, suburban, rural], ["Urban", "Suburban", "Rural"], default="Mixed/Unknown")
    return pd.Series(out, index=df.index)


def derive_intervention_family(df: pd.DataFrame) -> pd.Series:
    name = coalesce_columns(df, ["i_Intervention_Name", "s_Intervention_Name", "f_Intervention_Name"]).astype("string")
    out = pd.Series("Other", index=df.index, dtype="string")

    flag_map = [
        ("i_Program_Type_Curriculum", "Curriculum"),
        ("i_Program_Type_Supplement", "Supplement"),
        ("i_Program_Type_Practice", "Practice"),
        ("i_Program_Type_Policy", "Policy"),
        ("i_Program_Type_Teacher_level", "Teacher-Level"),
        ("i_Program_Type_School_level", "School-Level"),
    ]
    for col, label in flag_map:
        if col in df.columns:
            out = np.where(to_bool(df[col]).fillna(False).astype(bool), label, out)
            out = pd.Series(out, index=df.index, dtype="string")

    lowered = name.str.lower().fillna("")
    keyword_rules = [
        (r"\btutor|tutoring\b", "Tutoring"),
        (r"\btechnology|computer|digital|online\b", "Technology-Assisted"),
        (r"\bcoaching|professional development|teacher training\b", "Teacher Support"),
        (r"\bbehavior|social emotional|sel\b", "Behavior/SEL"),
        (r"\bcollege|postsecondary\b", "College Access"),
    ]
    for pattern, label in keyword_rules:
        out = np.where((out == "Other") & lowered.str.contains(pattern, regex=True), label, out)
        out = pd.Series(out, index=df.index, dtype="string")
    return out.fillna("Other")


def winsorize_by_group(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    lower_q: float = 0.005,
    upper_q: float = 0.995,
) -> pd.Series:
    out = df[value_col].copy()
    bounds = (
        df[[group_col, value_col]]
        .dropna()
        .groupby(group_col)[value_col]
        .quantile([lower_q, upper_q])
        .unstack()
        .rename(columns={lower_q: "lo", upper_q: "hi"})
    )
    for g, row in bounds.iterrows():
        mask = df[group_col] == g
        out.loc[mask] = out.loc[mask].clip(lower=row["lo"], upper=row["hi"])
    return out


def study_state_bridge(raw: pd.DataFrame) -> pd.DataFrame:
    state_cols = [
        c for c in raw.columns if c.startswith("s_Region_State_") and c not in REGION_BUCKET_COLUMNS and c in STATE_COL_TO_ABBR
    ]
    if not state_cols or "s_StudyID" not in raw.columns:
        return pd.DataFrame(columns=["study_id", "state_abbr", "state_weight"])
    s = raw[["s_StudyID"] + state_cols].copy()
    s["study_id"] = to_numeric(s["s_StudyID"]).astype("Int64")
    for c in state_cols:
        s[c] = to_bool(s[c]).fillna(False).astype(bool)
    long = s.melt(id_vars=["study_id"], value_vars=state_cols, var_name="state_col", value_name="flag")
    long = long[long["flag"] & long["study_id"].notna()].copy()
    if long.empty:
        return pd.DataFrame(columns=["study_id", "state_abbr", "state_weight"])
    long["state_abbr"] = long["state_col"].map(STATE_COL_TO_ABBR)
    long = long.dropna(subset=["state_abbr"]).drop_duplicates(subset=["study_id", "state_abbr"])
    c = long.groupby("study_id")["state_abbr"].transform("count")
    long["state_weight"] = 1.0 / c
    long["study_id"] = long["study_id"].astype("int64")
    return long[["study_id", "state_abbr", "state_weight"]]


def _proxy_context_features(df: pd.DataFrame, context_label: str) -> pd.DataFrame:
    out = df.copy()
    frpl_med = out["frpl_share"].dropna().median() if out["frpl_share"].notna().any() else 0.5
    ell_med = out["ell_share"].dropna().median() if out["ell_share"].notna().any() else 0.1
    swd_med = out["swd_share"].dropna().median() if out["swd_share"].notna().any() else 0.12
    frpl = out["frpl_share"].fillna(frpl_med)
    ell = out["ell_share"].fillna(ell_med)
    swd = out["swd_share"].fillna(swd_med)
    child_poverty = out.get("saipe_child_poverty_rate", pd.Series(np.nan, index=out.index)).fillna(frpl.clip(0, 1))
    pp_exp = out.get("f33_pp_expenditure_real", pd.Series(np.nan, index=out.index))
    pp_exp = pp_exp.fillna((12000 * (1.10 - 0.45 * frpl)).clip(lower=3500, upper=24000))
    teacher_salary = out.get("f33_teacher_salary_real", pd.Series(np.nan, index=out.index))
    teacher_salary = teacher_salary.fillna((34000 + 1.7 * pp_exp).clip(lower=30000, upper=95000))
    acs_income = out.get("acs_median_income_real", pd.Series(np.nan, index=out.index))
    acs_income = acs_income.fillna((45000 + 30000 * (1 - child_poverty)).clip(lower=25000, upper=110000))
    acs_ba = out.get("acs_ba_share", pd.Series(np.nan, index=out.index))
    acs_ba = acs_ba.fillna((0.12 + 0.45 * (1 - child_poverty)).clip(lower=0.05, upper=0.8))

    rucc = out.get("rucc_rural_share", pd.Series(np.nan, index=out.index))
    rucc_fallback = pd.Series(
        np.select(
            [out["urbanicity"] == "Rural", out["urbanicity"] == "Suburban", out["urbanicity"] == "Urban"],
            [0.9, 0.35, 0.05],
            default=0.3,
        ),
        index=out.index,
    )
    rucc = rucc.fillna(rucc_fallback)

    out["child_poverty_rate"] = child_poverty.clip(0, 1)
    out["f33_pp_expenditure_real"] = pp_exp
    out["log_pp_exp"] = np.log(np.maximum(pp_exp, 1))
    out["teacher_salary_real"] = teacher_salary
    out["acs_median_income_real"] = acs_income
    out["acs_ba_share"] = acs_ba.clip(0, 1)
    out["rucc_rural_share"] = rucc.clip(0, 1)
    out["context_source"] = context_label
    return out


def prepare_analytic_dataset(wwc_csv: str | Path, context_csv: str | Path | None = None) -> pd.DataFrame:
    raw = pd.read_csv(wwc_csv, encoding="utf-8-sig", low_memory=False)
    df = raw.copy()

    df["study_id"] = to_numeric(df["s_StudyID"]).astype("Int64")
    df["finding_id"] = to_numeric(df["f_FindingID"]).astype("Int64")
    intervention = coalesce_columns(df, ["i_InterventionID", "s_interventionID", "f_InterventionID"])
    df["intervention_id"] = to_numeric(intervention).astype("Int64")
    df = df[df["study_id"].notna() & df["finding_id"].notna()].copy()

    df["effect_size_study"] = to_numeric(df["f_Effect_Size_Study"])
    df["effect_size_wwc"] = to_numeric(df["f_Effect_Size_WWC"])
    df["effect_size_final"] = df["effect_size_wwc"].fillna(df["effect_size_study"])
    df["effect_size_final"] = winsorize_by_group(df, "effect_size_final", "f_Outcome_Domain")
    df["effect_abs"] = df["effect_size_final"].abs()
    df["outcome_sample_size"] = to_numeric(df["f_Outcome_Sample_Size"])
    df["is_subgroup"] = to_bool(df["f_Is_Subgroup"]).fillna(False)
    df["is_statistically_significant"] = to_bool(df["f_Is_Statistically_Significant"])
    df["period_months"] = parse_period_to_months(df["f_Period"])
    df["publication_date"] = pd.to_datetime(df["s_Publication_Date"], errors="coerce", format="mixed")
    posting = pd.to_datetime(df["s_Posting_Date"], errors="coerce", format="mixed")
    df["publication_year"] = df["publication_date"].dt.year.fillna(posting.dt.year).fillna(0)
    df["study_design_std"] = standardize_study_design(df["s_Study_Design"]).fillna("Unknown")
    df["study_quality_score"] = df["s_Study_Rating"].map(
        {
            "Meets WWC standards without reservations": 3,
            "Meets WWC standards with reservations": 2,
            "Does not meet WWC standards": 1,
        }
    ).fillna(0)

    df["frpl_share"] = to_share(df.get("s_Demographics_Sample_FRPL", pd.Series(index=df.index, dtype="float64")))
    df["ell_share"] = to_share(df.get("s_Demographics_Sample_ELL", pd.Series(index=df.index, dtype="float64")))
    df["swd_share"] = to_share(df.get("s_Demographics_Sample_SWD", pd.Series(index=df.index, dtype="float64")))
    df["minority_share"] = to_share(df.get("s_Demographics_Sample_Minority", pd.Series(index=df.index, dtype="float64")))
    nonminority = to_share(df.get("s_Demographics_Sample_Nonminority", pd.Series(index=df.index, dtype="float64")))
    df["minority_share"] = df["minority_share"].fillna((1 - nonminority).where(nonminority.notna()))

    df["urbanicity"] = derive_urbanicity(df, prefix="s_")
    df["grade_band"] = derive_grade_band(df, prefix="s_")
    df["intervention_family"] = derive_intervention_family(df)

    se = np.sqrt(4.0 / np.maximum(df["outcome_sample_size"].fillna(0), 4))
    se = pd.Series(se, index=df.index).replace([np.inf, -np.inf], np.nan)
    df["se_approx"] = se
    df["weight_iv"] = 1.0 / (se**2)

    bridge = study_state_bridge(raw)
    if not bridge.empty:
        df = df.merge(bridge, on="study_id", how="left")
    else:
        df["state_abbr"] = pd.NA
        df["state_weight"] = 1.0
    df["state_weight"] = df["state_weight"].fillna(1.0)

    context_label = "proxy_from_wwc"
    if context_csv:
        context = pd.read_csv(context_csv)
        context.columns = [c.strip() for c in context.columns]
        if "state_abbr" not in context.columns or "year" not in context.columns:
            raise ValueError("context_csv must include columns: state_abbr, year")
        context["state_abbr"] = context["state_abbr"].astype("string").str.strip().str.upper()
        context["year"] = to_numeric(context["year"]).astype("Int64")
        df = df.merge(
            context,
            left_on=["state_abbr", "publication_year"],
            right_on=["state_abbr", "year"],
            how="left",
            suffixes=("", "_ctx"),
        )

        if "ccd_frpl_share" in df.columns:
            df["frpl_share"] = to_share(df["ccd_frpl_share"]).fillna(df["frpl_share"])
        if "ccd_ell_share" in df.columns:
            df["ell_share"] = to_share(df["ccd_ell_share"]).fillna(df["ell_share"])
        if "ccd_swd_share" in df.columns:
            df["swd_share"] = to_share(df["ccd_swd_share"]).fillna(df["swd_share"])
        if "saipe_child_poverty_rate" in df.columns:
            df["child_poverty_rate"] = to_share(df["saipe_child_poverty_rate"])
        if "f33_pp_expenditure_real" in df.columns:
            df["f33_pp_expenditure_real"] = to_numeric(df["f33_pp_expenditure_real"])
        if "f33_teacher_salary_real" in df.columns:
            df["f33_teacher_salary_real"] = to_numeric(df["f33_teacher_salary_real"])
        if "acs_median_income_real" in df.columns:
            df["acs_median_income_real"] = to_numeric(df["acs_median_income_real"])
        if "acs_ba_share" in df.columns:
            df["acs_ba_share"] = to_share(df["acs_ba_share"])
        if "rucc_rural_share" in df.columns:
            df["rucc_rural_share"] = to_share(df["rucc_rural_share"])
        context_label = "merged_external_with_proxy_fallback"

    df = _proxy_context_features(df, context_label=context_label)

    df["analysis_weight"] = df["weight_iv"].fillna(1.0) * df["state_weight"].fillna(1.0)
    pub_med = df["publication_year"].median()
    if pd.isna(pub_med):
        pub_med = 0
    df["publication_year_c"] = df["publication_year"] - pub_med
    df["state_abbr"] = df["state_abbr"].astype("string").fillna("NA")

    for col in [
        "frpl_share",
        "ell_share",
        "swd_share",
        "minority_share",
        "child_poverty_rate",
        "rucc_rural_share",
        "acs_ba_share",
    ]:
        if col in df.columns:
            df[col] = pd.Series(df[col], index=df.index).clip(lower=0, upper=1)

    return df


def build_design_matrix(
    df: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    interactions: list[tuple[str, str]] | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    interactions = interactions or []
    passthrough = [
        "study_id",
        "finding_id",
        "intervention_id",
        "f_Outcome_Domain",
        "state_abbr",
        "is_subgroup",
        "frpl_share",
        "ell_share",
        "swd_share",
        "child_poverty_rate",
        "log_pp_exp",
        "intervention_family",
        "grade_band",
        "urbanicity",
    ]
    required = ["effect_size_final", "analysis_weight"] + numeric_cols + categorical_cols
    required = list(dict.fromkeys(required + [c for c in passthrough if c in df.columns]))
    work = df[required].copy()
    work = work[work["effect_size_final"].notna()].copy()

    for col in numeric_cols:
        work[col] = to_numeric(work[col])
        non_null = work[col].dropna()
        med = non_null.median() if not non_null.empty else np.nan
        if pd.isna(med):
            med = 0.0
        work[col] = work[col].fillna(med)
    for col in categorical_cols:
        work[col] = work[col].astype("string").fillna("Unknown")

    x_num = work[numeric_cols].copy()
    x_cat = pd.get_dummies(work[categorical_cols], prefix=categorical_cols, drop_first=True, dtype=float)
    X = pd.concat([x_num, x_cat], axis=1)

    for left, right in interactions:
        if left in categorical_cols and right in numeric_cols:
            pref = f"{left}_"
            for col in [c for c in X.columns if c.startswith(pref)]:
                X[f"{col}:x:{right}"] = X[col] * X[right]
        elif left in numeric_cols and right in numeric_cols:
            X[f"{left}:x:{right}"] = X[left] * X[right]

    y = work["effect_size_final"].astype(float)
    w = work["analysis_weight"].fillna(1.0).astype(float)
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = y.replace([np.inf, -np.inf], np.nan)
    valid = y.notna()
    X = X.loc[valid]
    w = w.loc[valid]
    work = work.loc[valid]
    y = y.loc[valid]
    return X, y, w, work


def fit_weighted_linear(
    X: pd.DataFrame,
    y: pd.Series,
    w: pd.Series,
) -> dict[str, object]:
    model = LinearRegression()
    model.fit(X.values, y.values, sample_weight=w.values)
    pred = pd.Series(model.predict(X.values), index=y.index, name="predicted_effect")
    resid = y - pred
    wsum = np.sum(w)
    ybar = np.sum(w * y) / wsum
    sst = np.sum(w * (y - ybar) ** 2)
    sse = np.sum(w * (resid) ** 2)
    weighted_r2 = 1 - (sse / sst) if sst > 0 else np.nan

    coef = pd.Series(model.coef_, index=X.columns, name="coefficient")
    coef = pd.concat([pd.Series({"intercept": model.intercept_}), coef])
    coef.name = "coefficient"
    return {
        "model": model,
        "pred": pred,
        "resid": resid,
        "coef": coef.sort_values(key=np.abs, ascending=False),
        "weighted_r2": float(weighted_r2),
    }


def write_json(path: str | Path, payload: dict) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    d = df[[value_col, weight_col]].dropna()
    if d.empty:
        return np.nan
    return float(np.average(d[value_col], weights=d[weight_col]))


def decile_bins(series: pd.Series) -> pd.Series:
    s = series.copy()
    if s.nunique(dropna=True) < 10:
        return pd.cut(s, bins=5, labels=False, include_lowest=True)
    return pd.qcut(s, q=10, labels=False, duplicates="drop")

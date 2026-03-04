#!/usr/bin/env python3
from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px


RAW_INPUT = Path("WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv")
OUT_DATA = Path("Urvi_Analysis/data_products")
OUT_DASH = Path("Urvi_Analysis/dashboard")
STATE_PROFILE_DIR = OUT_DASH / "state_profiles_original"

REGION_BUCKETS = {"Midwest", "Northeast", "South", "West", "U S  Region", "U.S. Region"}

STATE_NAME_TO_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District Of Columbia": "DC",
    "District of Columbia": "DC",
    "DC": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
ABBR_TO_STATE = {v: k for k, v in STATE_NAME_TO_ABBR.items() if len(v) == 2}
ABBR_TO_STATE["DC"] = "District of Columbia"


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_DASH.mkdir(parents=True, exist_ok=True)
    STATE_PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def boolish(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    return s.isin({"1", "1.0", "true", "t", "yes", "y"})


def normalize_state_from_col(col: str) -> str | None:
    raw = col.replace("s_Region_State_", "").replace("_", " ").strip()
    if raw in REGION_BUCKETS:
        return None
    if raw == "DC":
        return "DC"
    return STATE_NAME_TO_ABBR.get(raw.title())


def parse_state_tokens(df: pd.DataFrame) -> pd.DataFrame:
    state_cols = [c for c in df.columns if c.startswith("s_Region_State_")]
    mapped_pairs = [(c, normalize_state_from_col(c)) for c in state_cols]
    mapped_pairs = [(c, a) for c, a in mapped_pairs if a]
    use_cols = [c for c, _ in mapped_pairs]
    abbrs = [a for _, a in mapped_pairs]

    flags = pd.DataFrame(index=df.index)
    for c in use_cols:
        flags[c] = boolish(df[c])

    tokens = []
    for row in flags.itertuples(index=False, name=None):
        vals = [abbrs[i] for i, v in enumerate(row) if v]
        tokens.append(sorted(set(vals)))

    out = df.copy()
    out["state_tokens"] = tokens
    out["state_count"] = out["state_tokens"].apply(len)
    out["has_state"] = out["state_count"] > 0
    out["is_multistate"] = out["state_count"] >= 2
    return out


def split_tokens(series: pd.Series) -> pd.Series:
    return (
        series.dropna()
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
        .replace("", np.nan)
        .dropna()
    )


def safe_pct_positive(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return float("nan")
    return float((s > 0).mean() * 100.0)


def describe_scope(
    exp: pd.DataFrame,
    scope_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    exp = exp.copy()
    exp["effect_size_num"] = pd.to_numeric(exp["f_Effect_Size_WWC"], errors="coerce")
    exp["improvement_num"] = pd.to_numeric(exp["f_Improvement_Index"], errors="coerce")
    exp["outcome_sample_num"] = pd.to_numeric(exp["f_Outcome_Sample_Size"], errors="coerce")
    exp["outcome_sample_weighted"] = exp["outcome_sample_num"] * exp["row_weight"]

    state_summary = (
        exp.groupby("state_abbr", as_index=False)
        .agg(
            findings_n=("f_FindingID", "nunique"),
            studies_n=("s_StudyID", "nunique"),
            interventions_n=("i_InterventionID", "nunique"),
            weighted_finding_contribution=("row_weight", "sum"),
            weighted_outcome_sample=("outcome_sample_weighted", "sum"),
            mean_effect_size_wwc=("effect_size_num", "mean"),
            median_effect_size_wwc=("effect_size_num", "median"),
            pct_positive_effect_size=("effect_size_num", safe_pct_positive),
            mean_improvement_index=("improvement_num", "mean"),
            single_state_rows=("is_multistate", lambda s: int((~s).sum())),
            multistate_rows=("is_multistate", lambda s: int(s.sum())),
        )
        .sort_values("findings_n", ascending=False)
        .reset_index(drop=True)
    )
    total_contrib = state_summary["weighted_finding_contribution"].sum()
    if total_contrib > 0:
        state_summary["contribution_share_pct"] = state_summary["weighted_finding_contribution"] / total_contrib * 100.0
    else:
        state_summary["contribution_share_pct"] = np.nan
    state_summary["state_name"] = state_summary["state_abbr"].map(ABBR_TO_STATE)

    state_iv = (
        exp.groupby(["state_abbr", "i_InterventionID", "i_Intervention_Name"], as_index=False)
        .agg(
            findings_n=("f_FindingID", "nunique"),
            studies_n=("s_StudyID", "nunique"),
            weighted_outcome_sample=("outcome_sample_weighted", "sum"),
            mean_effect_size_wwc=("effect_size_num", "mean"),
            median_effect_size_wwc=("effect_size_num", "median"),
            pct_positive_effect_size=("effect_size_num", safe_pct_positive),
            mean_improvement_index=("improvement_num", "mean"),
        )
    )
    state_iv["intervention_name"] = state_iv["i_Intervention_Name"].fillna("Unknown intervention")

    study_cols = ["state_abbr", "s_StudyID", "s_Study_Design", "s_Study_Rating", "s_Study_Page_URL"]
    state_study = (
        exp[study_cols + ["f_FindingID", "i_InterventionID", "effect_size_num", "improvement_num", "outcome_sample_weighted"]]
        .groupby(study_cols, as_index=False)
        .agg(
            findings_n=("f_FindingID", "nunique"),
            interventions_n=("i_InterventionID", "nunique"),
            weighted_outcome_sample=("outcome_sample_weighted", "sum"),
            mean_effect_size_wwc=("effect_size_num", "mean"),
            mean_improvement_index=("improvement_num", "mean"),
        )
    )

    topic_cols = [c for c in exp.columns if c.startswith("s_Topic_")]
    topic_rows = []
    for c in topic_cols:
        m = boolish(exp[c])
        if not m.any():
            continue
        t = exp.loc[m, ["state_abbr", "f_FindingID"]].copy()
        t["topic"] = c.replace("s_Topic_", "").replace("_", " ")
        topic_rows.append(t)
    if topic_rows:
        topic_long = pd.concat(topic_rows, ignore_index=True)
        state_topic = (
            topic_long.groupby(["state_abbr", "topic"], as_index=False)["f_FindingID"]
            .nunique()
            .rename(columns={"f_FindingID": "findings_n"})
        )
    else:
        state_topic = pd.DataFrame(columns=["state_abbr", "topic", "findings_n"])

    if "f_Outcome_Domain" in exp.columns:
        outcome_long = exp[["state_abbr", "f_FindingID", "f_Outcome_Domain"]].dropna().copy()
        state_outcome = (
            outcome_long.groupby(["state_abbr", "f_Outcome_Domain"], as_index=False)["f_FindingID"]
            .nunique()
            .rename(columns={"f_FindingID": "findings_n"})
        )
    else:
        state_outcome = pd.DataFrame(columns=["state_abbr", "f_Outcome_Domain", "findings_n"])

    grade_cols = [c for c in exp.columns if c.startswith("s_Grade_")]
    grade_rows = []
    for c in grade_cols:
        m = boolish(exp[c])
        if not m.any():
            continue
        g = exp.loc[m, ["state_abbr", "f_FindingID"]].copy()
        g["grade_bucket"] = c.replace("s_Grade_", "").replace("_", " ")
        grade_rows.append(g)
    if grade_rows:
        grade_long = pd.concat(grade_rows, ignore_index=True)
        state_grade = (
            grade_long.groupby(["state_abbr", "grade_bucket"], as_index=False)["f_FindingID"]
            .nunique()
            .rename(columns={"f_FindingID": "findings_n"})
        )
    else:
        state_grade = pd.DataFrame(columns=["state_abbr", "grade_bucket", "findings_n"])

    state_summary.to_csv(OUT_DATA / f"state_summary_{scope_key}_original.csv", index=False)
    state_iv.to_csv(OUT_DATA / f"state_interventions_{scope_key}_original.csv", index=False)
    state_study.to_csv(OUT_DATA / f"state_studies_{scope_key}_original.csv", index=False)
    state_topic.to_csv(OUT_DATA / f"state_topics_{scope_key}_original.csv", index=False)
    state_outcome.to_csv(OUT_DATA / f"state_outcomes_{scope_key}_original.csv", index=False)
    state_grade.to_csv(OUT_DATA / f"state_grades_{scope_key}_original.csv", index=False)

    return state_summary, state_iv, state_study, state_topic, state_outcome, state_grade


def map_html(df: pd.DataFrame, metric: str, title: str, midpoint_zero: bool = False) -> str:
    kwargs = {}
    if midpoint_zero:
        kwargs["color_continuous_scale"] = "RdBu"
        kwargs["color_continuous_midpoint"] = 0.0
    else:
        kwargs["color_continuous_scale"] = "Turbo"

    fig = px.choropleth(
        df,
        locations="state_abbr",
        locationmode="USA-states",
        color=metric,
        hover_name="state_name",
        hover_data={
            "findings_n": ":,.0f",
            "studies_n": ":,.0f",
            "interventions_n": ":,.0f",
            "contribution_share_pct": ":.2f",
            "mean_effect_size_wwc": ":.3f",
            "pct_positive_effect_size": ":.2f",
            "mean_improvement_index": ":.2f",
        },
        scope="usa",
        title=title,
        **kwargs,
    )
    fig.update_layout(template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    return fig.to_html(full_html=False, include_plotlyjs=False)


def bar_html(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> str:
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        color=color,
        title=title,
        template="plotly_white",
    )
    fig.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    return fig.to_html(full_html=False, include_plotlyjs=False)


def write_state_profile_pages(
    scope_key: str,
    state_summary: pd.DataFrame,
    state_iv: pd.DataFrame,
    state_study: pd.DataFrame,
    state_topic: pd.DataFrame,
    state_outcome: pd.DataFrame,
    state_grade: pd.DataFrame,
) -> None:
    for abbr in sorted(state_summary["state_abbr"].dropna().unique()):
        srow = state_summary[state_summary["state_abbr"] == abbr]
        if srow.empty:
            continue
        summary = srow.iloc[0]
        iv = state_iv[state_iv["state_abbr"] == abbr].sort_values("findings_n", ascending=False).head(20).copy()
        studies = state_study[state_study["state_abbr"] == abbr].sort_values("findings_n", ascending=False).head(25).copy()
        topic = state_topic[state_topic["state_abbr"] == abbr].sort_values("findings_n", ascending=False).head(15).copy()
        outcome = state_outcome[state_outcome["state_abbr"] == abbr].sort_values("findings_n", ascending=False).head(15).copy()
        grade = state_grade[state_grade["state_abbr"] == abbr].sort_values("findings_n", ascending=False).head(15).copy()

        if not iv.empty:
            iv_plot = bar_html(
                iv.sort_values("findings_n"),
                x="findings_n",
                y="intervention_name",
                title=f"{abbr}: Top Interventions by Findings",
                color="mean_effect_size_wwc",
            )
        else:
            iv_plot = "<p>No intervention rows for this state.</p>"

        topic_plot = bar_html(topic.sort_values("findings_n"), x="findings_n", y="topic", title=f"{abbr}: Top Topics") if not topic.empty else "<p>No topic rows.</p>"
        outcome_plot = (
            bar_html(outcome.sort_values("findings_n"), x="findings_n", y="f_Outcome_Domain", title=f"{abbr}: Top Outcome Domains")
            if not outcome.empty
            else "<p>No outcome domain rows.</p>"
        )
        grade_plot = (
            bar_html(grade.sort_values("findings_n"), x="findings_n", y="grade_bucket", title=f"{abbr}: Top Grade Buckets")
            if not grade.empty
            else "<p>No grade rows.</p>"
        )

        studies_disp = studies.copy()
        if "s_Study_Page_URL" in studies_disp.columns:
            studies_disp["s_Study_Page_URL"] = studies_disp["s_Study_Page_URL"].fillna("").apply(
                lambda u: f"<a href='{u}' target='_blank'>link</a>" if isinstance(u, str) and u.startswith("http") else ""
            )
        for c in ["mean_effect_size_wwc", "mean_improvement_index", "weighted_outcome_sample"]:
            if c in studies_disp.columns:
                studies_disp[c] = studies_disp[c].round(3)
        studies_html = studies_disp[
            [
                "s_StudyID",
                "findings_n",
                "interventions_n",
                "s_Study_Design",
                "s_Study_Rating",
                "mean_effect_size_wwc",
                "mean_improvement_index",
                "weighted_outcome_sample",
                "s_Study_Page_URL",
            ]
        ].to_html(index=False, border=0, escape=False)

        html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{abbr} Profile ({scope_key})</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
    .wrap {{ max-width: 1450px; margin: 0 auto; padding: 20px; }}
    .card {{ background: #fff; border: 1px solid #dbe2ea; border-radius: 12px; padding: 14px; margin-bottom: 14px; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; }}
    .kpi {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; }}
    .kpi .l {{ font-size: 12px; color: #475569; }}
    .kpi .v {{ font-size: 20px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 7px; text-align: left; }}
    th {{ font-size: 12px; text-transform: uppercase; color: #475569; }}
    @media (max-width: 1100px) {{ .grid2 {{ grid-template-columns: 1fr; }} .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{summary["state_name"]} ({abbr}) - Original WWC EDA [{scope_key}]</h1>
      <p><a href="../original_full_state_eda_dashboard.html">Back to National EDA</a></p>
      <div class="kpis">
        <div class="kpi"><div class="l">Findings</div><div class="v">{int(summary["findings_n"]):,}</div></div>
        <div class="kpi"><div class="l">Studies</div><div class="v">{int(summary["studies_n"]):,}</div></div>
        <div class="kpi"><div class="l">Interventions</div><div class="v">{int(summary["interventions_n"]):,}</div></div>
        <div class="kpi"><div class="l">Contribution %</div><div class="v">{summary["contribution_share_pct"]:.2f}%</div></div>
        <div class="kpi"><div class="l">Mean Effect</div><div class="v">{summary["mean_effect_size_wwc"]:.3f}</div></div>
        <div class="kpi"><div class="l">% Positive</div><div class="v">{summary["pct_positive_effect_size"]:.2f}%</div></div>
        <div class="kpi"><div class="l">Mean Improvement</div><div class="v">{summary["mean_improvement_index"]:.2f}</div></div>
      </div>
    </div>

    <div class="card">{iv_plot}</div>
    <div class="grid2">
      <div class="card">{topic_plot}</div>
      <div class="card">{outcome_plot}</div>
    </div>
    <div class="card">{grade_plot}</div>
    <div class="card">
      <h2>Top Studies</h2>
      {studies_html}
    </div>
  </div>
</body>
</html>"""

        out = STATE_PROFILE_DIR / f"{abbr}_{scope_key}.html"
        out.write_text(html, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    raw = pd.read_csv(RAW_INPUT, encoding="utf-8-sig", low_memory=False)
    raw = parse_state_tokens(raw)
    raw = raw[raw["has_state"]].copy()

    # Narrow to a stable set for repeated EDA outputs.
    keep_cols = [
        "f_FindingID",
        "s_StudyID",
        "i_InterventionID",
        "i_Intervention_Name",
        "f_Effect_Size_WWC",
        "f_Improvement_Index",
        "f_Outcome_Sample_Size",
        "s_Study_Design",
        "s_Study_Rating",
        "s_Study_Page_URL",
        "f_Outcome_Domain",
        "is_multistate",
        "state_tokens",
        "state_count",
    ]
    keep_cols += [c for c in raw.columns if c.startswith("s_Topic_")]
    keep_cols += [c for c in raw.columns if c.startswith("s_Grade_")]
    keep_cols = [c for c in keep_cols if c in raw.columns]
    base = raw[keep_cols].copy()
    base_exp = base.explode("state_tokens").rename(columns={"state_tokens": "state_abbr"})
    base_exp["row_weight"] = 1.0 / base_exp["state_count"]

    all_scope = base_exp.copy()
    ms_scope = base_exp[base_exp["is_multistate"]].copy()

    all_state, all_iv, all_study, all_topic, all_outcome, all_grade = describe_scope(all_scope, "all_rows")
    ms_state, ms_iv, ms_study, ms_topic, ms_outcome, ms_grade = describe_scope(ms_scope, "multistate_only")

    write_state_profile_pages("all_rows", all_state, all_iv, all_study, all_topic, all_outcome, all_grade)
    write_state_profile_pages("multistate_only", ms_state, ms_iv, ms_study, ms_topic, ms_outcome, ms_grade)

    all_disp = all_state.copy()
    ms_disp = ms_state.copy()
    for df in [all_disp, ms_disp]:
        for c in [
            "mean_effect_size_wwc",
            "median_effect_size_wwc",
            "pct_positive_effect_size",
            "mean_improvement_index",
            "contribution_share_pct",
            "weighted_outcome_sample",
            "weighted_finding_contribution",
        ]:
            if c in df.columns:
                df[c] = df[c].round(3)
        df["all_profile"] = df["state_abbr"].apply(lambda a: f"<a href='state_profiles_original/{a}_all_rows.html'>{a} all</a>")
        df["ms_profile"] = df["state_abbr"].apply(lambda a: f"<a href='state_profiles_original/{a}_multistate_only.html'>{a} multi</a>")

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_findings = int(base["f_FindingID"].nunique())
    total_studies = int(base["s_StudyID"].nunique())
    total_interventions = int(base["i_InterventionID"].nunique())
    ms_findings = int(base[base["is_multistate"]]["f_FindingID"].nunique())
    ms_share = (ms_findings / total_findings * 100.0) if total_findings else 0.0

    maps = {
        "all_findings": map_html(all_state, "findings_n", "All Rows: Findings by State"),
        "all_effect": map_html(all_state, "mean_effect_size_wwc", "All Rows: Mean Effect Size by State", midpoint_zero=True),
        "all_positive": map_html(all_state, "pct_positive_effect_size", "All Rows: % Positive Findings by State"),
        "ms_findings": map_html(ms_state, "findings_n", "Multi-State Only: Findings by State"),
        "ms_effect": map_html(ms_state, "mean_effect_size_wwc", "Multi-State Only: Mean Effect Size by State", midpoint_zero=True),
        "ms_positive": map_html(ms_state, "pct_positive_effect_size", "Multi-State Only: % Positive Findings by State"),
    }

    all_table = all_disp.sort_values("findings_n", ascending=False)[
        [
            "state_abbr",
            "state_name",
            "findings_n",
            "studies_n",
            "interventions_n",
            "contribution_share_pct",
            "mean_effect_size_wwc",
            "pct_positive_effect_size",
            "mean_improvement_index",
            "all_profile",
            "ms_profile",
        ]
    ].to_html(index=False, border=0, escape=False)
    ms_table = ms_disp.sort_values("findings_n", ascending=False)[
        [
            "state_abbr",
            "state_name",
            "findings_n",
            "studies_n",
            "interventions_n",
            "contribution_share_pct",
            "mean_effect_size_wwc",
            "pct_positive_effect_size",
            "mean_improvement_index",
            "all_profile",
            "ms_profile",
        ]
    ].to_html(index=False, border=0, escape=False)

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Original WWC Full State EDA</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f5f8fc; color: #0f172a; }}
    .wrap {{ max-width: 1550px; margin: 0 auto; padding: 20px; }}
    .hero {{ background: linear-gradient(120deg,#0f172a 0%,#1d4ed8 50%,#0891b2 100%); color: #fff; border-radius: 14px; padding: 20px; }}
    .kpis {{ margin-top: 12px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }}
    .kpi {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 10px; }}
    .kpi .l {{ font-size: 12px; color: #cbd5e1; }}
    .kpi .v {{ font-size: 22px; font-weight: 700; color: #fff; }}
    .card {{ background: #fff; border: 1px solid #dbe2ea; border-radius: 12px; padding: 14px; margin-top: 14px; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 7px; text-align: left; }}
    th {{ font-size: 12px; text-transform: uppercase; color: #475569; }}
    @media (max-width: 1200px) {{ .grid2, .grid3 {{ grid-template-columns: 1fr; }} .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Original WWC Full State EDA</h1>
      <p>Generated {generated}. Uses only the original export file. Includes all rows and a multi-state-only lens to reduce signal blur.</p>
      <div class="kpis">
        <div class="kpi"><div class="l">Findings (state-coded)</div><div class="v">{total_findings:,}</div></div>
        <div class="kpi"><div class="l">Studies</div><div class="v">{total_studies:,}</div></div>
        <div class="kpi"><div class="l">Interventions</div><div class="v">{total_interventions:,}</div></div>
        <div class="kpi"><div class="l">Multi-state findings</div><div class="v">{ms_findings:,}</div></div>
        <div class="kpi"><div class="l">Multi-state share</div><div class="v">{ms_share:.2f}%</div></div>
      </div>
    </section>

    <section class="card">
      <h2>All Rows Maps</h2>
      <div class="grid3">
        <div>{maps["all_findings"]}</div>
        <div>{maps["all_effect"]}</div>
        <div>{maps["all_positive"]}</div>
      </div>
    </section>

    <section class="card">
      <h2>Multi-State Only Maps</h2>
      <div class="grid3">
        <div>{maps["ms_findings"]}</div>
        <div>{maps["ms_effect"]}</div>
        <div>{maps["ms_positive"]}</div>
      </div>
    </section>

    <section class="grid2">
      <div class="card">
        <h2>State Breakdown (All Rows)</h2>
        {all_table}
      </div>
      <div class="card">
        <h2>State Breakdown (Multi-State Only)</h2>
        {ms_table}
      </div>
    </section>
  </div>
</body>
</html>"""

    (OUT_DASH / "original_full_state_eda_dashboard.html").write_text(html, encoding="utf-8")

    summary_txt = (
        "Original WWC full state EDA generated.\n"
        f"- Dashboard: {OUT_DASH / 'original_full_state_eda_dashboard.html'}\n"
        f"- State profile dir: {STATE_PROFILE_DIR}\n"
        f"- state_summary_all_rows_original.csv\n"
        f"- state_summary_multistate_only_original.csv\n"
        f"- state_interventions_all_rows_original.csv\n"
        f"- state_interventions_multistate_only_original.csv\n"
        f"- state_studies_all_rows_original.csv\n"
        f"- state_studies_multistate_only_original.csv\n"
        f"- state_topics_all_rows_original.csv\n"
        f"- state_topics_multistate_only_original.csv\n"
        f"- state_outcomes_all_rows_original.csv\n"
        f"- state_outcomes_multistate_only_original.csv\n"
        f"- state_grades_all_rows_original.csv\n"
        f"- state_grades_multistate_only_original.csv\n"
    )
    (OUT_DASH / "original_state_eda_README.txt").write_text(summary_txt, encoding="utf-8")
    print(summary_txt)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


AGG_INPUT = Path("Urvi_Analysis/asadata_aggregated.csv")
ORIG_INPUT = Path("WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv")
DATA_OUT = Path("Urvi_Analysis/data_products")
DASH_OUT = Path("Urvi_Analysis/dashboard")

REGION_BUCKETS = {"Midwest", "Northeast", "South", "West"}

STATE_NAME_TO_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
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
VALID_ABBR = set(STATE_NAME_TO_ABBR.values())
ABBR_TO_STATE = {v: k for k, v in STATE_NAME_TO_ABBR.items() if k != "DC"}
ABBR_TO_STATE["DC"] = "District of Columbia"

SUBSET_SPECS = [
    {
        "id": "predictive_modeling_core",
        "description": "Primary ML subset for heterogeneity prediction",
        "required_non_null": [
            "f_Effect_Size_WWC",
            "s_Study_Design",
            "s_Study_Rating",
            "s_Grade",
        ],
        "required_true": ["state_specific_available"],
    },
    {
        "id": "inference_ci_core",
        "description": "Primary inferential subset for confidence intervals/meta-regression",
        "required_non_null": [
            "f_Effect_Size_WWC",
            "f_p_Value_WWC",
            "f_Outcome_Sample_Size",
            "s_Study_Design",
            "s_Study_Rating",
        ],
        "required_true": [],
    },
    {
        "id": "geography_context_core",
        "description": "Subset for state+school-context analyses",
        "required_non_null": [
            "f_Effect_Size_WWC",
            "s_Study_Design",
            "s_Study_Rating",
        ],
        "required_true": ["state_specific_available", "urbanicity_available", "school_type_available"],
    },
    {
        "id": "demographic_strict_subset",
        "description": "Strict demographic subset (FRPL + ELL available)",
        "required_non_null": [
            "f_Effect_Size_WWC",
            "s_Study_Design",
            "s_Study_Rating",
            "s_Grade",
            "s_Demographics_Sample_FRPL",
            "s_Demographics_Sample_ELL",
        ],
        "required_true": ["state_specific_available"],
    },
]


def ensure_dirs() -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    DASH_OUT.mkdir(parents=True, exist_ok=True)


def to_boolish(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    return s.isin({"true", "t", "1", "1.0", "yes", "y"})


def normalize_state_token(token: str) -> str | None:
    t = token.strip()
    if not t or t in REGION_BUCKETS:
        return None
    if len(t) == 2 and t.upper() in VALID_ABBR:
        return t.upper()
    return STATE_NAME_TO_ABBR.get(t)


def parse_agg_state_tokens(series: pd.Series) -> pd.Series:
    def parse(v: object) -> list[str]:
        if pd.isna(v):
            return []
        out = []
        for tok in [t.strip() for t in str(v).split(";") if t.strip()]:
            abbr = normalize_state_token(tok)
            if abbr:
                out.append(abbr)
        return out

    return series.apply(parse)


def parse_orig_state_tokens(orig_df: pd.DataFrame) -> pd.Series:
    state_cols = [
        c
        for c in orig_df.columns
        if c.startswith("s_Region_State_")
        and c not in {"s_Region_State_Midwest", "s_Region_State_Northeast", "s_Region_State_South", "s_Region_State_West"}
    ]

    col_to_abbr: dict[str, str] = {}
    for c in state_cols:
        key = c.replace("s_Region_State_", "").replace("_", " ")
        key = key.replace("DC", "District of Columbia")
        key = key.title()
        mapped = STATE_NAME_TO_ABBR.get(key)
        if mapped:
            col_to_abbr[c] = mapped

    tokens = []
    for _, row in orig_df[state_cols].iterrows():
        states = []
        for c in state_cols:
            if c in col_to_abbr and to_boolish(pd.Series([row[c]])).iloc[0]:
                states.append(col_to_abbr[c])
        tokens.append(sorted(set(states)))
    return pd.Series(tokens, index=orig_df.index)


def combine_tokens(a: pd.Series, b: pd.Series) -> pd.Series:
    return pd.Series([sorted(set(x + y)) for x, y in zip(a, b)], index=a.index)


def readiness_status(rows: int, studies: int, interventions: int) -> str:
    if rows >= 5000 and studies >= 500 and interventions >= 200:
        return "GO"
    if rows >= 2000 and studies >= 250 and interventions >= 100:
        return "GO (Cautious)"
    return "NO-GO"


def status_css(s: str) -> str:
    if s == "GO":
        return "ok"
    if "Cautious" in s:
        return "warn"
    return "bad"


def apply_subset(df: pd.DataFrame, spec: dict) -> pd.Series:
    m = pd.Series(True, index=df.index)
    if spec["required_non_null"]:
        m &= df[spec["required_non_null"]].notna().all(axis=1)
    for c in spec["required_true"]:
        m &= df[c].fillna(False).astype(bool)
    return m


def build_enriched_base() -> tuple[pd.DataFrame, dict]:
    agg = pd.read_csv(AGG_INPUT, encoding="utf-8-sig", low_memory=False)
    orig = pd.read_csv(ORIG_INPUT, encoding="utf-8-sig", low_memory=False)

    common = set(agg.columns) & set(orig.columns)
    extra_cols = [c for c in orig.columns if c not in common]
    orig_extra = orig[["f_FindingID"] + extra_cols].copy()
    df = agg.merge(orig_extra, on="f_FindingID", how="left")

    # Derived fields combining aggregate + original detail.
    agg_states = parse_agg_state_tokens(df["s_Region_State"])
    orig_states = parse_orig_state_tokens(orig)
    combined_states = combine_tokens(agg_states, orig_states)
    df["state_tokens"] = combined_states
    df["state_specific_available"] = df["state_tokens"].apply(lambda x: len(x) > 0)
    df["state_specific_count"] = df["state_tokens"].apply(len)

    urban_cols = [c for c in orig.columns if c.startswith("s_Urbanicity_")]
    school_cols = [c for c in orig.columns if c.startswith("s_School_type_")]
    grade_cols = [c for c in orig.columns if c.startswith("s_Grade_")]
    topic_cols = [c for c in orig.columns if c.startswith("s_Topic_")]
    race_share_cols = [c for c in orig.columns if c.startswith("s_Race_")]

    if urban_cols:
        u = pd.Series(False, index=orig.index)
        for c in urban_cols:
            u |= to_boolish(orig[c])
        df["urbanicity_available"] = u.values | df["s_Urbanicity"].notna().values
    else:
        df["urbanicity_available"] = df["s_Urbanicity"].notna()

    if school_cols:
        s = pd.Series(False, index=orig.index)
        for c in school_cols:
            s |= to_boolish(orig[c])
        df["school_type_available"] = s.values | df["s_School_type"].notna().values
    else:
        df["school_type_available"] = df["s_School_type"].notna()

    g = pd.Series(0, index=orig.index, dtype=float)
    for c in grade_cols:
        g += to_boolish(orig[c]).astype(int)
    df["grade_flag_count"] = g.values

    t = pd.Series(0, index=orig.index, dtype=float)
    for c in topic_cols:
        t += to_boolish(orig[c]).astype(int)
    df["topic_flag_count"] = t.values

    demo_cols = [
        "s_Demographics_Sample_FRPL",
        "s_Demographics_Sample_ELL",
        "s_Demographics_Sample_Minority",
        "s_Demographics_Sample_Nonminority",
    ]
    demo_cols = [c for c in demo_cols if c in df.columns]
    race_signal = orig[race_share_cols].notna().any(axis=1) if race_share_cols else pd.Series(False, index=orig.index)
    demo_signal = df[demo_cols].notna().any(axis=1) if demo_cols else pd.Series(False, index=df.index)
    df["demographic_signal_available"] = demo_signal.values | race_signal.values

    meta = {
        "agg_rows": int(len(agg)),
        "orig_rows": int(len(orig)),
        "agg_cols": int(agg.shape[1]),
        "orig_cols": int(orig.shape[1]),
        "extra_orig_cols": int(len(extra_cols)),
        "state_one_hot_cols": int(len([c for c in orig.columns if c.startswith("s_Region_State_")])),
        "grade_one_hot_cols": int(len(grade_cols)),
        "topic_one_hot_cols": int(len(topic_cols)),
    }
    return df, meta


def plot_template() -> dict:
    return {
        "template": "plotly_white",
        "font_family": "IBM Plex Sans, Segoe UI, Arial, sans-serif",
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#ffffff",
    }


def build_figures(
    subset_summary: pd.DataFrame,
    required_cov: pd.DataFrame,
    state_summary: pd.DataFrame,
    topic_summary: pd.DataFrame,
    coverage_df: pd.DataFrame,
    iv_support: pd.DataFrame,
) -> dict[str, str]:
    fig1 = px.bar(
        subset_summary,
        x="subset",
        y="rows",
        color="status",
        text="rows",
        color_discrete_map={"GO": "#16a34a", "GO (Cautious)": "#f59e0b", "NO-GO": "#ef4444"},
        title="Subset Readiness by Row Count",
    )
    fig1.update_layout(**plot_template(), xaxis_title="", yaxis_title="Rows")

    heat = required_cov.pivot(index="subset", columns="field", values="coverage").fillna(0)
    fig2 = go.Figure(
        data=go.Heatmap(
            z=heat.values,
            x=heat.columns.tolist(),
            y=heat.index.tolist(),
            colorscale=[[0.0, "#fee2e2"], [0.5, "#fde68a"], [1.0, "#14b8a6"]],
            zmin=0,
            zmax=1,
            text=np.round(heat.values * 100, 1),
            texttemplate="%{text}%",
            textfont={"size": 11},
        )
    )
    fig2.update_layout(**plot_template(), title="Coverage of Required Fields")

    fig3 = px.choropleth(
        state_summary,
        locations="state_abbr",
        locationmode="USA-states",
        color="finding_rows",
        hover_name="state_name",
        scope="usa",
        color_continuous_scale="Turbo",
        title="Evidence Density Across U.S. States",
    )
    fig3.update_layout(**plot_template())

    top_topic = topic_summary.head(15).sort_values("count")
    fig4 = go.Figure(
        go.Bar(
            x=top_topic["count"],
            y=top_topic["topic"],
            orientation="h",
            marker_color="#7c3aed",
            text=top_topic["count"],
            textposition="outside",
        )
    )
    fig4.update_layout(**plot_template(), title="Top Topic Signals", xaxis_title="Count", yaxis_title="")

    bins = [0.0, 0.05, 0.2, 0.5, 0.8, 0.95, 1.0001]
    labels = ["0-5%", "5-20%", "20-50%", "50-80%", "80-95%", "95-100%"]
    cbin = pd.cut(coverage_df["coverage"], bins=bins, labels=labels, include_lowest=True)
    dist = cbin.value_counts().reindex(labels).fillna(0)
    fig5 = go.Figure(
        go.Bar(
            x=dist.index.tolist(),
            y=dist.values.tolist(),
            marker_color=["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#14b8a6"],
            text=dist.values.tolist(),
            textposition="outside",
        )
    )
    fig5.update_layout(**plot_template(), title="Column Coverage Distribution", xaxis_title="Coverage bin", yaxis_title="Columns")

    fig6 = px.histogram(
        iv_support,
        x="finding_rows",
        nbins=35,
        color_discrete_sequence=["#0ea5e9"],
        title="Intervention Support in Predictive Core",
    )
    fig6.add_vline(x=20, line_color="#a16207", line_dash="dash", annotation_text="20-row min threshold")
    fig6.update_layout(**plot_template(), xaxis_title="Finding rows per intervention", yaxis_title="Count")

    return {
        "subset": fig1.to_html(full_html=False, include_plotlyjs="cdn"),
        "req_heat": fig2.to_html(full_html=False, include_plotlyjs=False),
        "state_map": fig3.to_html(full_html=False, include_plotlyjs=False),
        "topics": fig4.to_html(full_html=False, include_plotlyjs=False),
        "cov_dist": fig5.to_html(full_html=False, include_plotlyjs=False),
        "iv_hist": fig6.to_html(full_html=False, include_plotlyjs=False),
    }


def make_html_table(df: pd.DataFrame, cols: list[str], with_classes: str = "tbl") -> str:
    return df[cols].to_html(index=False, border=0, classes=with_classes, escape=False)


def build_dashboard(
    base: pd.DataFrame,
    subset_summary: pd.DataFrame,
    required_cov: pd.DataFrame,
    coverage_df: pd.DataFrame,
    state_summary: pd.DataFrame,
    topic_summary: pd.DataFrame,
    iv_support: pd.DataFrame,
    meta: dict,
) -> str:
    figs = build_figures(subset_summary, required_cov, state_summary, topic_summary, coverage_df, iv_support)

    rows = len(base)
    findings = base["f_FindingID"].nunique()
    studies = base["s_StudyID"].nunique()
    interventions = base["s_interventionID"].nunique()
    state_share = float(base["state_specific_available"].mean())
    demo_share = float(base["demographic_signal_available"].mean())

    ss = subset_summary.set_index("subset")
    decision = "Proceed: Two-Track Modeling"
    if not (ss.loc["predictive_modeling_core", "status"].startswith("GO") and ss.loc["inference_ci_core", "status"].startswith("GO")):
        decision = "Proceed with Caution"

    readiness_score = (
        100
        * (
            0.35 * ss.loc["predictive_modeling_core", "row_share"]
            + 0.35 * ss.loc["inference_ci_core", "row_share"]
            + 0.20 * state_share
            + 0.10 * demo_share
        )
    )
    readiness_score = float(np.clip(readiness_score, 0, 100))

    action_matrix = pd.DataFrame(
        [
            ["Predictive heterogeneity ML", "predictive_modeling_core", ss.loc["predictive_modeling_core", "status"]],
            ["Inference with CI/meta-regression", "inference_ci_core", ss.loc["inference_ci_core", "status"]],
            ["State-context modeling", "geography_context_core", ss.loc["geography_context_core", "status"]],
            ["Strict demographic subgroup modeling", "demographic_strict_subset", ss.loc["demographic_strict_subset", "status"]],
            ["County-level modeling", "N/A", "NO-GO"],
            ["School-ID level claims", "N/A", "NO-GO"],
        ],
        columns=["analysis", "recommended_subset", "status"],
    )
    action_matrix["status"] = action_matrix["status"].map(lambda s: f"<span class='pill {status_css(s)}'>{s}</span>")

    subset_disp = subset_summary.copy()
    subset_disp["row_share"] = (subset_disp["row_share"] * 100).round(1).astype(str) + "%"
    subset_disp["status"] = subset_disp["status"].map(lambda s: f"<span class='pill {status_css(s)}'>{s}</span>")

    cov_disp = coverage_df.head(25).copy()
    cov_disp["coverage_pct"] = (cov_disp["coverage"] * 100).round(1).astype(str) + "%"

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WWC Research Readiness Dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
    :root {{
      --bg: #f4f7ff;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --line: #dbe4f0;
      --ok: #16a34a;
      --warn: #f59e0b;
      --bad: #ef4444;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(1200px 500px at -10% -20%, #bfdbfe 0%, transparent 70%),
        radial-gradient(1200px 500px at 110% -10%, #ddd6fe 0%, transparent 70%),
        var(--bg);
    }}
    .wrap {{ max-width: 1440px; margin: 0 auto; padding: 22px 22px 40px; }}
    .hero {{
      background: linear-gradient(120deg, #0f172a 0%, #1d4ed8 50%, #7c3aed 100%);
      color: #fff;
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 12px 28px rgba(15, 23, 42, 0.25);
    }}
    .hero h1 {{ margin: 0; font-size: 29px; }}
    .hero .sub {{ margin-top: 6px; color: #dbeafe; font-size: 14px; }}
    .hero-grid {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 14px;
      align-items: center;
    }}
    .decision {{
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.24);
      border-radius: 12px;
      padding: 12px 14px;
    }}
    .decision .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.7px; color: #dbeafe; }}
    .decision .value {{ margin-top: 4px; font-size: 24px; font-weight: 700; }}
    .score {{ text-align: right; font-family: "IBM Plex Mono", monospace; font-size: 30px; font-weight: 600; }}
    .score small {{ display: block; font-family: "IBM Plex Sans"; font-size: 12px; color: #dbeafe; }}

    .kpis {{
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(6, minmax(140px,1fr));
      gap: 12px;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
    }}
    .kpi .label {{ font-size: 12px; color: var(--muted); }}
    .kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
    .kpi .bar {{ margin-top: 10px; height: 6px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }}
    .kpi .bar > span {{ display: block; height: 100%; }}

    .grid2 {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; margin-top: 14px; }}
    .grid2eq {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
    }}
    .card h2 {{ margin: 0 0 10px; font-size: 16px; }}
    .muted {{ color: var(--muted); font-size: 13px; }}
    .list {{ margin: 0; padding-left: 18px; }}
    .list li {{ margin: 7px 0; }}
    .tbl {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .tbl th,.tbl td {{
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
      padding: 8px;
      vertical-align: top;
    }}
    .tbl th {{
      font-size: 12px;
      color: #334155;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}
    .pill {{
      font-size: 12px;
      font-weight: 700;
      border-radius: 999px;
      padding: 4px 8px;
      border: 1px solid transparent;
      display: inline-block;
    }}
    .pill.ok {{ color: #065f46; background: #dcfce7; border-color: #bbf7d0; }}
    .pill.warn {{ color: #92400e; background: #fef3c7; border-color: #fde68a; }}
    .pill.bad {{ color: #991b1b; background: #fee2e2; border-color: #fecaca; }}

    @media (max-width: 1100px) {{
      .hero-grid, .grid2, .grid2eq {{ grid-template-columns: 1fr; }}
      .kpis {{ grid-template-columns: repeat(2, minmax(140px,1fr)); }}
      .score {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>WWC Research Readiness Dashboard</h1>
      <div class="sub">Using both aggregated + original WWC export | Generated: {generated}</div>
      <div class="hero-grid">
        <div class="decision">
          <div class="label">Executive Decision</div>
          <div class="value">{decision}</div>
          <div class="sub">Primary recommendation: <strong>Inference CI Core</strong> + <strong>Predictive Modeling Core</strong>.</div>
        </div>
        <div class="score">
          {readiness_score:.1f}/100
          <small>Composite Readiness Score</small>
        </div>
      </div>
    </section>

    <section class="kpis">
      <div class="kpi"><div class="label">Rows</div><div class="value">{rows:,}</div><div class="bar"><span style="width:100%;background:#1d4ed8"></span></div></div>
      <div class="kpi"><div class="label">Findings</div><div class="value">{findings:,}</div><div class="bar"><span style="width:100%;background:#7c3aed"></span></div></div>
      <div class="kpi"><div class="label">Studies</div><div class="value">{studies:,}</div><div class="bar"><span style="width:{min(studies/1600,1)*100:.1f}%;background:#0ea5e9"></span></div></div>
      <div class="kpi"><div class="label">Interventions</div><div class="value">{interventions:,}</div><div class="bar"><span style="width:{min(interventions/1200,1)*100:.1f}%;background:#14b8a6"></span></div></div>
      <div class="kpi"><div class="label">Specific-State Coverage</div><div class="value">{state_share*100:.1f}%</div><div class="bar"><span style="width:{state_share*100:.1f}%;background:#22c55e"></span></div></div>
      <div class="kpi"><div class="label">Demographic Signal</div><div class="value">{demo_share*100:.1f}%</div><div class="bar"><span style="width:{demo_share*100:.1f}%;background:#f59e0b"></span></div></div>
    </section>

    <section class="grid2">
      <div class="card">
        <h2>Why This Uses Both Files</h2>
        <ul class="list">
          <li>Aggregated file gives curated fields and cleaner grouped labels.</li>
          <li>Original WWC export contributes <strong>{meta["extra_orig_cols"]}</strong> additional columns with one-hot detail.</li>
          <li>Added original-detail structure: state flags ({meta["state_one_hot_cols"]}), grade flags ({meta["grade_one_hot_cols"]}), topic flags ({meta["topic_one_hot_cols"]}).</li>
          <li>Derived features now use both sources: <code>state_specific_available</code>, <code>urbanicity_available</code>, <code>school_type_available</code>, <code>demographic_signal_available</code>.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Can We Do This?</h2>
        {make_html_table(action_matrix, ["analysis", "recommended_subset", "status"])}
      </div>
    </section>

    <section class="grid2eq">
      <div class="card">{figs["subset"]}</div>
      <div class="card">{figs["req_heat"]}</div>
    </section>

    <section class="grid2eq">
      <div class="card">{figs["state_map"]}</div>
      <div class="card">{figs["topics"]}</div>
    </section>

    <section class="grid2eq">
      <div class="card">{figs["cov_dist"]}</div>
      <div class="card">{figs["iv_hist"]}</div>
    </section>

    <section class="grid2">
      <div class="card">
        <h2>Subset Readiness Table</h2>
        {make_html_table(subset_disp, ["subset", "rows", "row_share", "studies", "interventions", "outcome_domains", "status"])}
      </div>
      <div class="card">
        <h2>Top Coverage Fields</h2>
        {make_html_table(cov_disp, ["column", "coverage_pct", "n_unique", "non_null"])}
        <p class="muted">Coverage is measured on the enriched base table (aggregated + original features).</p>
      </div>
    </section>
  </div>
</body>
</html>"""


def main() -> None:
    ensure_dirs()
    base, meta = build_enriched_base()

    # Save enriched base for traceability.
    base.to_csv(DATA_OUT / "combined_enriched_base.csv", index=False)

    # Build subsets with improved names.
    subset_rows = []
    subsets: dict[str, pd.DataFrame] = {}
    for spec in SUBSET_SPECS:
        mask = apply_subset(base, spec)
        sub = base.loc[mask].copy()
        subsets[spec["id"]] = sub
        sub.to_csv(DATA_OUT / f"{spec['id']}.csv", index=False)
        subset_rows.append(
            {
                "subset": spec["id"],
                "description": spec["description"],
                "required_non_null": ", ".join(spec["required_non_null"]),
                "required_true": ", ".join(spec["required_true"]) if spec["required_true"] else "",
                "rows": int(len(sub)),
                "row_share": len(sub) / len(base) if len(base) else np.nan,
                "studies": int(sub["s_StudyID"].nunique()),
                "interventions": int(sub["s_interventionID"].nunique()),
                "outcome_domains": int(sub["f_Outcome_Domain"].nunique()),
            }
        )
    subset_summary = pd.DataFrame(subset_rows)
    subset_summary["status"] = subset_summary.apply(
        lambda r: readiness_status(int(r["rows"]), int(r["studies"]), int(r["interventions"])),
        axis=1,
    )
    subset_summary.to_csv(DATA_OUT / "subset_readiness_summary.csv", index=False)

    # Backward-compatible aliases for prior file names.
    subsets["predictive_modeling_core"].to_csv(DATA_OUT / "ml_core.csv", index=False)
    subsets["inference_ci_core"].to_csv(DATA_OUT / "ci_core.csv", index=False)
    subsets["demographic_strict_subset"].to_csv(DATA_OUT / "ml_demo.csv", index=False)

    # Coverage summary for all fields.
    cov_rows = []
    n = len(base)
    for c in base.columns:
        nn = int(base[c].notna().sum())
        try:
            nun = int(base[c].nunique(dropna=True))
        except TypeError:
            nun = int(base[c].astype(str).nunique(dropna=True))
        cov_rows.append({"column": c, "non_null": nn, "coverage": nn / n if n else np.nan, "n_unique": nun})
    coverage_df = pd.DataFrame(cov_rows).sort_values("coverage", ascending=False)
    coverage_df.to_csv(DATA_OUT / "column_coverage_summary.csv", index=False)

    # Required field coverage matrix.
    req_rows = []
    for spec in SUBSET_SPECS:
        for field in spec["required_non_null"]:
            req_rows.append({"subset": spec["id"], "field": field, "coverage": float(base[field].notna().mean())})
        for field in spec["required_true"]:
            req_rows.append({"subset": spec["id"], "field": field, "coverage": float(base[field].fillna(False).astype(bool).mean())})
    required_cov = pd.DataFrame(req_rows)
    required_cov.to_csv(DATA_OUT / "required_column_coverage_matrix.csv", index=False)

    # State summary using combined tokens.
    state_exp = base["state_tokens"].explode().dropna()
    state_summary = (
        state_exp.value_counts()
        .rename_axis("state_abbr")
        .reset_index(name="finding_rows")
        .sort_values("finding_rows", ascending=False)
    )
    state_summary["state_name"] = state_summary["state_abbr"].map(ABBR_TO_STATE)
    state_summary.to_csv(DATA_OUT / "state_coverage_summary.csv", index=False)

    # Topic summary (prefer aggregate topic string; fallback topic flags already embedded in base).
    topic_tokens = (
        base["s_Topic"]
        .dropna()
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
    )
    topic_summary = topic_tokens.value_counts().rename_axis("topic").reset_index(name="count")
    topic_summary.to_csv(DATA_OUT / "topic_coverage_summary.csv", index=False)

    # Intervention support in predictive core.
    iv_support = (
        subsets["predictive_modeling_core"]
        .groupby("s_interventionID")
        .size()
        .reset_index(name="finding_rows")
        .sort_values("finding_rows", ascending=False)
    )
    iv_support.to_csv(DATA_OUT / "predictive_core_intervention_support.csv", index=False)
    iv_support.to_csv(DATA_OUT / "ml_core_intervention_support.csv", index=False)

    # Dashboard.
    html = build_dashboard(
        base=base,
        subset_summary=subset_summary,
        required_cov=required_cov,
        coverage_df=coverage_df,
        state_summary=state_summary,
        topic_summary=topic_summary,
        iv_support=iv_support,
        meta=meta,
    )
    out_html = DASH_OUT / "data_readiness_dashboard.html"
    out_html.write_text(html, encoding="utf-8")

    summary = (
        "Generated files (new subset names + compatibility aliases):\n"
        f"- {DATA_OUT / 'combined_enriched_base.csv'}\n"
        f"- {DATA_OUT / 'predictive_modeling_core.csv'}\n"
        f"- {DATA_OUT / 'inference_ci_core.csv'}\n"
        f"- {DATA_OUT / 'geography_context_core.csv'}\n"
        f"- {DATA_OUT / 'demographic_strict_subset.csv'}\n"
        f"- {DATA_OUT / 'ml_core.csv'} (alias)\n"
        f"- {DATA_OUT / 'ci_core.csv'} (alias)\n"
        f"- {DATA_OUT / 'ml_demo.csv'} (alias)\n"
        f"- {DATA_OUT / 'subset_readiness_summary.csv'}\n"
        f"- {DATA_OUT / 'column_coverage_summary.csv'}\n"
        f"- {DATA_OUT / 'required_column_coverage_matrix.csv'}\n"
        f"- {DATA_OUT / 'state_coverage_summary.csv'}\n"
        f"- {DATA_OUT / 'topic_coverage_summary.csv'}\n"
        f"- {DATA_OUT / 'predictive_core_intervention_support.csv'}\n"
        f"- {out_html}\n"
    )
    (DASH_OUT / "README.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()

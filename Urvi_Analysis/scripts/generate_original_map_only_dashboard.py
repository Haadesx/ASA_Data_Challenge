#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px


ALL_ROWS = Path("Urvi_Analysis/data_products/state_summary_all_rows_original.csv")
MS_ROWS = Path("Urvi_Analysis/data_products/state_summary_multistate_only_original.csv")
OUT_HTML = Path("Urvi_Analysis/dashboard/original_map_only_dashboard.html")


def map_html(
    df: pd.DataFrame,
    metric: str,
    title: str,
    include_plotlyjs: str | bool,
    midpoint_zero: bool = False,
    range_color: tuple[float, float] | None = None,
) -> str:
    kwargs = {}
    if midpoint_zero:
        kwargs["color_continuous_scale"] = "RdBu"
        kwargs["color_continuous_midpoint"] = 0.0
    else:
        kwargs["color_continuous_scale"] = "Turbo"
    if range_color is not None:
        kwargs["range_color"] = range_color

    fig = px.choropleth(
        df,
        locations="state_abbr",
        locationmode="USA-states",
        color=metric,
        scope="usa",
        hover_name="state_name",
        hover_data={
            "findings_n": ":,.0f",
            "studies_n": ":,.0f",
            "interventions_n": ":,.0f",
            "contribution_share_pct": ":.2f",
            "mean_effect_size_wwc": ":.3f",
            "pct_positive_effect_size": ":.2f",
            "mean_improvement_index": ":.2f",
            "weighted_outcome_sample": ":,.1f",
            "weighted_finding_contribution": ":,.1f",
        },
        title=title,
        **kwargs,
    )
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font_family="IBM Plex Sans, Arial, sans-serif",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig.to_html(full_html=False, include_plotlyjs=include_plotlyjs)


def build_scope_maps(df: pd.DataFrame, scope_label: str, first_include_plotlyjs: str | bool) -> tuple[list[str], bool]:
    cards = []
    metrics = [
        ("findings_n", f"{scope_label}: Findings Count", False, None),
        ("studies_n", f"{scope_label}: Studies Count", False, None),
        ("interventions_n", f"{scope_label}: Interventions Count", False, None),
        ("contribution_share_pct", f"{scope_label}: Contribution Share (%)", False, None),
        ("mean_effect_size_wwc", f"{scope_label}: Mean WWC Effect Size", True, None),
        ("pct_positive_effect_size", f"{scope_label}: % Positive Findings", False, (0, 100)),
        ("mean_improvement_index", f"{scope_label}: Mean Improvement Index", True, None),
        ("weighted_outcome_sample", f"{scope_label}: Weighted Outcome Sample", False, None),
    ]

    include_js = first_include_plotlyjs
    first_done = False
    for metric, title, midpoint_zero, rng in metrics:
        html = map_html(
            df=df,
            metric=metric,
            title=title,
            include_plotlyjs=include_js if not first_done else False,
            midpoint_zero=midpoint_zero,
            range_color=rng,
        )
        cards.append(html)
        if not first_done:
            first_done = True
    return cards, True


def main() -> None:
    all_df = pd.read_csv(ALL_ROWS)
    ms_df = pd.read_csv(MS_ROWS)

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_findings = int(all_df["findings_n"].sum())
    total_studies = int(all_df["studies_n"].sum())
    total_interventions = int(all_df["interventions_n"].sum())
    ms_findings = int(ms_df["findings_n"].sum())

    all_cards, _ = build_scope_maps(all_df, "All State-Coded Rows", "cdn")
    ms_cards, _ = build_scope_maps(ms_df, "Multi-State Rows Only", False)

    all_block = "\n".join([f"<div class='card'>{c}</div>" for c in all_cards])
    ms_block = "\n".join([f"<div class='card'>{c}</div>" for c in ms_cards])

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Original WWC Map-Only EDA</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f5f8fc; color: #0f172a; }}
    .wrap {{ max-width: 1700px; margin: 0 auto; padding: 20px; }}
    .hero {{ background: linear-gradient(120deg,#0f172a 0%,#1d4ed8 50%,#0891b2 100%); color: #fff; border-radius: 14px; padding: 20px; }}
    .kpis {{ margin-top: 12px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
    .kpi {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 10px; }}
    .kpi .l {{ font-size: 12px; color: #cbd5e1; }}
    .kpi .v {{ font-size: 22px; font-weight: 700; color: #fff; }}
    .section {{ margin-top: 16px; }}
    .section h2 {{ margin: 0 0 10px 0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .card {{ background: #fff; border: 1px solid #dbe2ea; border-radius: 12px; padding: 10px; }}
    .note {{ margin-top: 8px; color: #334155; font-size: 14px; }}
    @media (max-width: 1200px) {{ .grid {{ grid-template-columns: 1fr; }} .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Original WWC Map-Only EDA (USA)</h1>
      <div>Generated {generated}. No tables, map-first visualization only.</div>
      <div class="kpis">
        <div class="kpi"><div class="l">Findings (sum across states)</div><div class="v">{total_findings:,}</div></div>
        <div class="kpi"><div class="l">Studies (sum across states)</div><div class="v">{total_studies:,}</div></div>
        <div class="kpi"><div class="l">Interventions (sum across states)</div><div class="v">{total_interventions:,}</div></div>
        <div class="kpi"><div class="l">Multi-state Findings (sum)</div><div class="v">{ms_findings:,}</div></div>
      </div>
      <div class="note">Use the first block for overall signal and the second block to inspect de-blurred multi-state behavior.</div>
    </section>

    <section class="section">
      <h2>All State-Coded Rows</h2>
      <div class="grid">
        {all_block}
      </div>
    </section>

    <section class="section">
      <h2>Multi-State Rows Only</h2>
      <div class="grid">
        {ms_block}
      </div>
    </section>
  </div>
</body>
</html>"""

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px

RAW_INPUT = Path('WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv')
OUT_HTML = Path('Urvi_Analysis/dashboard/texas_dashboard.html')

EXTERNAL_SOURCES = [
    {
        'name': 'NCES CCD',
        'url': 'https://nces.ed.gov/ccd/index.asp',
        'desc': 'Base school and district registry with NCES IDs, enrollment, staffing, and district structure.'
    },
    {
        'name': 'NCES EDGE Locale',
        'url': 'https://nces.ed.gov/programs/edge/Geographic/LocaleBoundaries',
        'desc': 'Official urban/suburban/town/rural geography for school and district matching.'
    },
    {
        'name': 'TEA District Type',
        'url': 'https://tea.texas.gov/acctres/analyze/years.html',
        'desc': 'Texas district-type classification for major urban, suburban, and rural framing.'
    },
    {
        'name': 'TEA Snapshot',
        'url': 'https://tea.texas.gov/perfreport/snapshot/index.html',
        'desc': 'District demographics, finance, staffing, and performance context.'
    },
    {
        'name': 'TEA TAPR',
        'url': 'https://tea.texas.gov/perfreport/tapr/index.html',
        'desc': 'District and campus subgroup outcomes and accountability reporting.'
    },
    {
        'name': 'TEA Accountability Data',
        'url': 'https://tea.texas.gov/texas-schools/accountability/academic-accountability/performance-reporting/accountability-data-resources',
        'desc': 'STAAR and accountability downloads for Texas district or campus-level context.'
    },
    {
        'name': 'Census SAIPE',
        'url': 'https://www.census.gov/data/datasets/2024/demo/saipe/2024-school-districts.html',
        'desc': 'School-district child poverty estimates for a stronger “for whom” layer.'
    },
    {
        'name': 'ACS 5-year',
        'url': 'https://www.census.gov/data/developers/data-sets/acs-5year.html',
        'desc': 'Income, internet access, language, commuting, and neighborhood demographics.'
    },
    {
        'name': 'FCC Broadband Map',
        'url': 'https://broadbandmap.fcc.gov/home',
        'desc': 'Broadband access context for Texas digital divide analyses.'
    },
    {
        'name': 'Texas Broadband Office',
        'url': 'https://comptroller.texas.gov/programs/broadband/outreach/maps/',
        'desc': 'Texas-specific broadband layers and mapping tools.'
    },
]


def boolish(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    return s.isin({'1', '1.0', 'true', 't', 'yes', 'y'})


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce')


def pct_positive(series: pd.Series) -> float:
    s = to_num(series).dropna()
    if s.empty:
        return float('nan')
    return float((s > 0).mean() * 100.0)


def summarize_subset(df: pd.DataFrame, label: str) -> dict:
    eff = to_num(df['f_Effect_Size_WWC'])
    imp = to_num(df['f_Improvement_Index'])
    return {
        'label': label,
        'rows_n': int(len(df)),
        'findings_n': int(df['f_FindingID'].nunique()),
        'studies_n': int(df['s_StudyID'].nunique()),
        'interventions_n': int(df['i_InterventionID'].nunique()),
        'mean_effect_size_wwc': float(eff.mean()),
        'pct_positive_effect_size': pct_positive(df['f_Effect_Size_WWC']),
        'mean_improvement_index': float(imp.mean()),
    }


def summarize_interventions(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    out = (
        df.assign(
            effect_size_num=to_num(df['f_Effect_Size_WWC']),
            improvement_num=to_num(df['f_Improvement_Index']),
        )
        .groupby(['i_InterventionID', 'i_Intervention_Name'], as_index=False)
        .agg(
            findings_n=('f_FindingID', 'nunique'),
            studies_n=('s_StudyID', 'nunique'),
            mean_effect_size_wwc=('effect_size_num', 'mean'),
            pct_positive_effect_size=('effect_size_num', pct_positive),
            mean_improvement_index=('improvement_num', 'mean'),
        )
        .sort_values('findings_n', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    out['intervention_name'] = out['i_Intervention_Name'].fillna('Unknown intervention')
    return out


def summarize_boolean_prefix(df: pd.DataFrame, prefix: str, label_col: str, top_n: int = 10) -> pd.DataFrame:
    rows = []
    for col in [c for c in df.columns if c.startswith(prefix)]:
        mask = boolish(df[col])
        if not mask.any():
            continue
        tmp = df.loc[mask, ['f_FindingID', 'f_Effect_Size_WWC']].copy()
        tmp[label_col] = col.replace(prefix, '').replace('_', ' ')
        rows.append(tmp)
    if not rows:
        return pd.DataFrame(columns=[label_col, 'findings_n', 'mean_effect_size_wwc'])
    out = (
        pd.concat(rows, ignore_index=True)
        .assign(effect_size_num=lambda x: to_num(x['f_Effect_Size_WWC']))
        .groupby(label_col, as_index=False)
        .agg(
            findings_n=('f_FindingID', 'nunique'),
            mean_effect_size_wwc=('effect_size_num', 'mean'),
        )
        .sort_values('findings_n', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return out


def summarize_outcomes(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    out = (
        df[['f_FindingID', 'f_Outcome_Domain', 'f_Effect_Size_WWC']]
        .dropna(subset=['f_Outcome_Domain'])
        .assign(effect_size_num=lambda x: to_num(x['f_Effect_Size_WWC']))
        .groupby('f_Outcome_Domain', as_index=False)
        .agg(
            findings_n=('f_FindingID', 'nunique'),
            mean_effect_size_wwc=('effect_size_num', 'mean'),
        )
        .sort_values('findings_n', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return out


def summarize_studies(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    out = (
        df.assign(
            effect_size_num=to_num(df['f_Effect_Size_WWC']),
            improvement_num=to_num(df['f_Improvement_Index']),
        )
        .groupby(['s_StudyID', 's_Study_Design', 's_Study_Rating', 's_Study_Page_URL'], as_index=False)
        .agg(
            findings_n=('f_FindingID', 'nunique'),
            interventions_n=('i_InterventionID', 'nunique'),
            mean_effect_size_wwc=('effect_size_num', 'mean'),
            mean_improvement_index=('improvement_num', 'mean'),
        )
        .sort_values('findings_n', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return out


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None, orientation: str = 'h') -> str:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        title=title,
        template='plotly_white',
    )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family='IBM Plex Sans, Segoe UI, Arial, sans-serif', color='#0f172a'),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})


def plot_grouped(summary_df: pd.DataFrame, value_cols: list[str], title: str) -> str:
    long = summary_df.melt(id_vars='label', value_vars=value_cols, var_name='metric', value_name='value')
    fig = px.bar(long, x='label', y='value', color='metric', barmode='group', title=title, template='plotly_white')
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family='IBM Plex Sans, Segoe UI, Arial, sans-serif', color='#0f172a'),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})


def plot_heatmap(summary_df: pd.DataFrame) -> str:
    heat = summary_df.set_index('label')[['findings_n', 'studies_n', 'interventions_n', 'mean_effect_size_wwc', 'pct_positive_effect_size', 'mean_improvement_index']]
    fig = px.imshow(
        heat,
        text_auto='.3g',
        aspect='auto',
        color_continuous_scale=['#eff6ff', '#93c5fd', '#1d4ed8'],
        title='Texas lens comparison',
    )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family='IBM Plex Sans, Segoe UI, Arial, sans-serif', color='#0f172a'),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})


def table_html(df: pd.DataFrame, linkify_study: bool = False) -> str:
    disp = df.copy()
    for col in ['mean_effect_size_wwc', 'pct_positive_effect_size', 'mean_improvement_index']:
        if col in disp.columns:
            disp[col] = disp[col].round(3)
    if linkify_study and 's_Study_Page_URL' in disp.columns:
        disp['s_Study_Page_URL'] = disp['s_Study_Page_URL'].fillna('').apply(
            lambda u: f"<a href='https://ies.ed.gov{u}' target='_blank'>study</a>" if isinstance(u, str) and u.startswith('/') else ''
        )
    return disp.to_html(index=False, border=0, escape=False)


def source_cards_html() -> str:
    return ''.join(
        f"<a class='source' href='{src['url']}' target='_blank'><strong>{src['name']}</strong><span>{src['desc']}</span></a>"
        for src in EXTERNAL_SOURCES
    )


def section_block(df: pd.DataFrame, label: str, note: str, slug: str) -> str:
    summary = summarize_subset(df, label)
    iv = summarize_interventions(df)
    outcomes = summarize_outcomes(df)
    topics = summarize_boolean_prefix(df, 's_Topic_', 'topic')
    grades = summarize_boolean_prefix(df, 's_Grade_', 'grade_bucket')
    studies = summarize_studies(df)

    iv_plot = plot_bar(iv.sort_values('findings_n'), 'findings_n', 'intervention_name', f'{label}: Top interventions', 'mean_effect_size_wwc') if not iv.empty else '<div class="empty-state">No intervention rows.</div>'
    outcome_plot = plot_bar(outcomes.sort_values('findings_n'), 'findings_n', 'f_Outcome_Domain', f'{label}: Top outcome domains', 'mean_effect_size_wwc') if not outcomes.empty else '<div class="empty-state">No outcome rows.</div>'
    topic_plot = plot_bar(topics.sort_values('findings_n'), 'findings_n', 'topic', f'{label}: Top topics', 'mean_effect_size_wwc') if not topics.empty else '<div class="empty-state">No topic rows.</div>'
    grade_plot = plot_bar(grades.sort_values('findings_n'), 'findings_n', 'grade_bucket', f'{label}: Top grade buckets', 'mean_effect_size_wwc') if not grades.empty else '<div class="empty-state">No grade rows.</div>'

    kpis = f"""
    <div class='kpis'>
      <div class='kpi'><div class='label'>Findings</div><div class='value'>{summary['findings_n']:,}</div></div>
      <div class='kpi'><div class='label'>Studies</div><div class='value'>{summary['studies_n']:,}</div></div>
      <div class='kpi'><div class='label'>Interventions</div><div class='value'>{summary['interventions_n']:,}</div></div>
      <div class='kpi'><div class='label'>Mean effect</div><div class='value'>{summary['mean_effect_size_wwc']:.3f}</div></div>
      <div class='kpi'><div class='label'>% positive</div><div class='value'>{summary['pct_positive_effect_size']:.1f}%</div></div>
      <div class='kpi'><div class='label'>Improvement index</div><div class='value'>{summary['mean_improvement_index']:.2f}</div></div>
    </div>
    """

    studies_table = table_html(
        studies[[
            's_StudyID', 'findings_n', 'interventions_n', 's_Study_Design', 's_Study_Rating',
            'mean_effect_size_wwc', 'mean_improvement_index', 's_Study_Page_URL'
        ]],
        linkify_study=True,
    ) if not studies.empty else '<div class="empty-state">No studies in this subset.</div>'

    return f"""
    <section id='{slug}' class='tab-content'>
      <div class='card'>
        <h2>{label}</h2>
        <div class='section-note'>{note}</div>
        {kpis}
      </div>
      <div class='grid2'>
        <div class='card'><div class='chart'>{iv_plot}</div></div>
        <div class='card'><div class='chart'>{outcome_plot}</div></div>
      </div>
      <div class='grid2'>
        <div class='card'><div class='chart'>{topic_plot}</div></div>
        <div class='card'><div class='chart'>{grade_plot}</div></div>
      </div>
      <div class='card'>
        <h2>Top Studies in {label}</h2>
        <div class='table-wrap'>{studies_table}</div>
      </div>
    </section>
    """


def main() -> None:
    df = pd.read_csv(RAW_INPUT, encoding='utf-8-sig', low_memory=False)

    texas = df[boolish(df['s_Region_State_Texas'])].copy()
    texas_urban = texas[boolish(texas['s_Urbanicity_Urban'])].copy()
    texas_rural = texas[boolish(texas['s_Urbanicity_Rural'])].copy()
    texas_suburban = texas[boolish(texas['s_Urbanicity_Suburban'])].copy()
    any_tag = texas[boolish(texas['s_Urbanicity_Urban']) | boolish(texas['s_Urbanicity_Rural']) | boolish(texas['s_Urbanicity_Suburban'])].copy()
    both_ru = texas[boolish(texas['s_Urbanicity_Urban']) & boolish(texas['s_Urbanicity_Rural'])].copy()

    summary_df = pd.DataFrame([
        summarize_subset(texas, 'All Texas'),
        summarize_subset(texas_urban, 'Urban Texas'),
        summarize_subset(texas_rural, 'Rural Texas'),
    ])

    hero = summarize_subset(texas, 'All Texas')
    comparison_heatmap = plot_heatmap(summary_df)
    volume_plot = plot_grouped(summary_df, ['findings_n', 'studies_n', 'interventions_n'], 'Texas support volume by lens')
    effect_plot = plot_grouped(summary_df, ['mean_effect_size_wwc', 'pct_positive_effect_size', 'mean_improvement_index'], 'Texas effectiveness metrics by lens')

    summary_table = summary_df.copy()
    for c in ['mean_effect_size_wwc', 'pct_positive_effect_size', 'mean_improvement_index']:
        summary_table[c] = summary_table[c].round(3)

    all_block = section_block(
        texas,
        'All Texas',
        'Every original WWC row coded to Texas. This is the full Texas lens before urbanicity splitting.',
        'all',
    )
    urban_block = section_block(
        texas_urban,
        'Urban Texas',
        'Original-only subset using `s_Urbanicity_Urban = 1`. This is not mutually exclusive with Rural Texas because some studies carry multiple urbanicity tags.',
        'urban',
    )
    rural_block = section_block(
        texas_rural,
        'Rural Texas',
        'Original-only subset using `s_Urbanicity_Rural = 1`. This is not mutually exclusive with Urban Texas because some studies carry multiple urbanicity tags.',
        'rural',
    )

    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    coverage_pct = len(any_tag) / len(texas) * 100.0 if len(texas) else 0.0

    html = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Texas WWC Dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
    :root {{ --bg:#f4f7ff; --card:#fff; --text:#0f172a; --muted:#475569; --line:#dbe4f0; --line2:#e7edf5; --brand:#1d4ed8; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif; color: var(--text); background: radial-gradient(1000px 500px at -8% -20%, #c7d2fe 0%, transparent 60%), radial-gradient(900px 480px at 108% -18%, #bfdbfe 0%, transparent 55%), var(--bg); }}
    .wrap {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
    .hero {{ background: linear-gradient(120deg, #0f172a 0%, #1d4ed8 56%, #0891b2 100%); color: #fff; border-radius: 18px; padding: 22px; box-shadow: 0 12px 28px rgba(15, 23, 42, 0.23); }}
    .hero-top {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .hero h1 {{ margin: 0; font-size: 32px; }}
    .hero .sub {{ margin-top: 8px; color: #dbeafe; font-size: 14px; max-width: 1100px; line-height: 1.5; }}
    .hero-badge {{ background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22); border-radius: 999px; padding: 8px 12px; font-size: 12px; white-space: nowrap; }}
    .kpis {{ margin-top: 16px; display: grid; grid-template-columns: repeat(6, minmax(140px, 1fr)); gap: 10px; }}
    .kpi {{ background: rgba(255,255,255,0.13); border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; padding: 12px; }}
    .kpi .label {{ font-size: 12px; color: #dbeafe; text-transform: uppercase; letter-spacing: 0.4px; }}
    .kpi .value {{ margin-top: 4px; font-size: 24px; font-weight: 700; line-height: 1.1; }}
    .nav {{ margin-top: 14px; background: rgba(255,255,255,0.72); border: 1px solid var(--line); border-radius: 14px; padding: 10px; backdrop-filter: blur(6px); box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05); }}
    .nav button {{ border: 1px solid var(--line); background: #fff; color: var(--text); padding: 10px 14px; border-radius: 999px; font: inherit; font-weight: 600; cursor: pointer; margin: 4px 6px 4px 0; transition: all .16s ease; }}
    .nav button:hover {{ border-color: #93c5fd; background: #eff6ff; }}
    .nav button.active {{ background: var(--brand); color: #fff; border-color: var(--brand); box-shadow: 0 8px 16px rgba(29,78,216,0.2); }}
    .tab-content {{ display: none; margin-top: 16px; animation: fadein .16s ease; }}
    .tab-content.active {{ display: block; }}
    @keyframes fadein {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 16px; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05); }}
    .card h2 {{ margin: 0 0 10px; font-size: 16px; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }}
    .table-wrap {{ width: 100%; overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }}
    table {{ width: 100%; min-width: 980px; border-collapse: separate; border-spacing: 0; font-size: 13px; background: #fff; }}
    th, td {{ border-bottom: 1px solid var(--line2); padding: 8px; text-align: left; vertical-align: top; }}
    th {{ position: sticky; top: 0; z-index: 1; font-size: 11px; text-transform: uppercase; letter-spacing: .3px; color: var(--muted); background: #f2f6fc; }}
    tbody tr:nth-child(even) td {{ background: #fcfdff; }}
    td:not(:first-child), th:not(:first-child) {{ white-space: nowrap; }}
    .chart {{ min-height: 420px; }}
    .section-note {{ color: var(--muted); font-size: 13px; line-height: 1.55; }}
    .pillrow {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
    .pill {{ display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 12px; font-weight: 600; }}
    .source-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 10px; }}
    .source {{ display: block; background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 14px; color: var(--text); text-decoration: none; box-shadow: 0 4px 12px rgba(15,23,42,0.04); }}
    .source:hover {{ border-color: #93c5fd; background: #f8fbff; }}
    .source strong {{ display: block; margin-bottom: 6px; color: var(--brand); }}
    .source span {{ color: var(--muted); font-size: 13px; line-height: 1.4; }}
    .empty-state {{ color: var(--muted); padding: 14px; border: 1px dashed #cbd5e1; border-radius: 12px; background: #fafcff; }}
    .plotly-graph-div {{ min-height: 420px !important; width: 100% !important; }}
    @media (max-width: 1200px) {{ .kpis {{ grid-template-columns: repeat(2, minmax(140px, 1fr)); }} .grid2, .source-grid {{ grid-template-columns: 1fr; }} .hero-top {{ flex-direction: column; }} }}
  </style>
  <script src='https://cdn.plot.ly/plotly-2.32.0.min.js'></script>
</head>
<body>
  <div class='wrap'>
    <section class='hero'>
      <div class='hero-top'>
        <div>
          <h1>Texas WWC Dashboard</h1>
          <div class='sub'>Original-only Texas deep dive built directly from the WWC export. Rural and Urban Texas are now split only from the original study-level fields <code>s_Urbanicity_Rural</code> and <code>s_Urbanicity_Urban</code>, so this page no longer depends on the enriched-base urbanicity layer.</div>
        </div>
        <div class='hero-badge'>Original WWC only · Texas-specific · Reproducible split</div>
      </div>
      <div class='kpis'>
        <div class='kpi'><div class='label'>TX findings</div><div class='value'>{hero['findings_n']:,}</div></div>
        <div class='kpi'><div class='label'>TX studies</div><div class='value'>{hero['studies_n']:,}</div></div>
        <div class='kpi'><div class='label'>TX interventions</div><div class='value'>{hero['interventions_n']:,}</div></div>
        <div class='kpi'><div class='label'>Tagged rows</div><div class='value'>{len(any_tag):,}</div></div>
        <div class='kpi'><div class='label'>Urban rows</div><div class='value'>{len(texas_urban):,}</div></div>
        <div class='kpi'><div class='label'>Rural rows</div><div class='value'>{len(texas_rural):,}</div></div>
      </div>
    </section>

    <section class='nav'>
      <button class='tablink active' onclick="openTab(event, 'overview')">Overview</button>
      <button class='tablink' onclick="openTab(event, 'all')">All Texas</button>
      <button class='tablink' onclick="openTab(event, 'urban')">Urban Texas</button>
      <button class='tablink' onclick="openTab(event, 'rural')">Rural Texas</button>
    </section>

    <section id='overview' class='tab-content active'>
      <div class='grid2'>
        <div class='card'><h2>Texas Lens Comparison</h2><div class='chart'>{comparison_heatmap}</div></div>
        <div class='card'><h2>Support Volume by Lens</h2><div class='chart'>{volume_plot}</div></div>
      </div>
      <div class='grid2'>
        <div class='card'><h2>Effectiveness Metrics by Lens</h2><div class='chart'>{effect_plot}</div></div>
        <div class='card'>
          <h2>Interpretation Notes</h2>
          <div class='section-note'>
            <ul>
              <li>Generated {generated} from the original WWC export only.</li>
              <li>Texas-coded rows in the original file: {len(texas):,}.</li>
              <li>Rows with at least one original study urbanicity tag: {len(any_tag):,} ({coverage_pct:.1f}% of Texas rows).</li>
              <li>Urban-tagged Texas rows: {len(texas_urban):,}.</li>
              <li>Rural-tagged Texas rows: {len(texas_rural):,}.</li>
              <li>Suburban-tagged Texas rows: {len(texas_suburban):,}.</li>
              <li>Rows tagged both rural and urban: {len(both_ru):,}.</li>
              <li>The Urban Texas and Rural Texas tabs are not exclusive partitions because the original WWC export allows multiple urbanicity tags on the same row.</li>
            </ul>
          </div>
          <div class='pillrow'>
            <span class='pill'>All Texas rows: {len(texas):,}</span>
            <span class='pill'>Urban coverage: {len(texas_urban):,}</span>
            <span class='pill'>Rural coverage: {len(texas_rural):,}</span>
            <span class='pill'>Overlap: {len(both_ru):,}</span>
          </div>
        </div>
      </div>
      <div class='card'>
        <h2>Texas Summary Table</h2>
        <div class='table-wrap'>{table_html(summary_table[['label','rows_n','findings_n','studies_n','interventions_n','mean_effect_size_wwc','pct_positive_effect_size','mean_improvement_index']])}</div>
      </div>
      <div class='card'>
        <h2>External Datasets To Merge Next</h2>
        <div class='section-note'>These are the strongest official sources for taking the Texas WWC slices into a more causal or policy-facing design.</div>
        <div class='source-grid'>{source_cards_html()}</div>
      </div>
    </section>

    {all_block}
    {urban_block}
    {rural_block}
  </div>
  <script>
    function openTab(evt, tabName) {{
      const tabs = document.getElementsByClassName('tab-content');
      for (let i = 0; i < tabs.length; i++) tabs[i].classList.remove('active');
      const links = document.getElementsByClassName('tablink');
      for (let i = 0; i < links.length; i++) links[i].classList.remove('active');
      document.getElementById(tabName).classList.add('active');
      evt.currentTarget.classList.add('active');
      window.dispatchEvent(new Event('resize'));
    }}
  </script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding='utf-8')
    print(f'Wrote {OUT_HTML}')


if __name__ == '__main__':
    main()

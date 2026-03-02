#!/usr/bin/env python3
from pathlib import Path
import html
import mistune

ROOT=Path('/Volumes/Auxilary/Side_Projects/ASA_Data_Challange')
md=ROOT/'Urvi_Analysis'/'WWC_Project_Documentation_InDepth.md'
out=ROOT/'Urvi_Analysis'/'WWC_Project_Documentation_InDepth.html'
text=md.read_text(encoding='utf-8')
rendered=mistune.html(text)
page=f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WWC In-Depth Documentation</title>
  <style>
    :root {{ --bg:#f6f8ff; --card:#ffffff; --line:#dbe4f0; --text:#0f172a; --muted:#475569; --link:#1d4ed8; }}
    body {{ margin:0; font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif; color:var(--text); background:radial-gradient(900px 400px at -10% -20%,#bfdbfe 0%,transparent 70%), radial-gradient(900px 400px at 110% -10%,#ddd6fe 0%,transparent 70%), var(--bg); }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 22px; }}
    .top {{ background: linear-gradient(120deg,#0f172a 0%,#1d4ed8 55%,#7c3aed 100%); color:white; border-radius:14px; padding:18px; box-shadow: 0 8px 24px rgba(15,23,42,.2); }}
    .top h1 {{ margin:0; font-size: 28px; }}
    .top p {{ margin:6px 0 0; color:#dbeafe; }}
    .card {{ margin-top:14px; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px; box-shadow:0 3px 10px rgba(15,23,42,.05); }}
    .nav a {{ color:white; font-weight:600; text-decoration:none; margin-right:14px; }}
    .nav a:hover {{ text-decoration: underline; }}
    h1,h2,h3,h4 {{ color:#0b2340; line-height:1.3; }}
    h2 {{ margin-top:26px; border-top:1px solid #e2e8f0; padding-top:16px; }}
    p,li {{ line-height:1.6; font-size:15px; }}
    code {{ background:#eef2ff; padding:2px 6px; border-radius:6px; font-family: ui-monospace, Menlo, monospace; font-size: 90%; }}
    pre {{ background:#0b1220; color:#e2e8f0; padding:14px; border-radius:10px; overflow:auto; }}
    a {{ color:var(--link); text-decoration:none; }}
    a:hover {{ text-decoration: underline; }}
    table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
    th,td {{ border:1px solid #dbe4f0; padding:8px; text-align:left; font-size:14px; }}
    th {{ background:#eff6ff; }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="top">
      <div class="nav"><a href="../index.html">Home</a><a href="./dashboard/data_readiness_dashboard.html">Dashboard</a></div>
      <h1>WWC Project Documentation (In-Depth)</h1>
      <p>Formatted HTML version for public viewing on GitHub Pages.</p>
    </section>
    <section class="card">{rendered}</section>
  </div>
</body>
</html>'''
out.write_text(page,encoding='utf-8')
print('wrote',out)

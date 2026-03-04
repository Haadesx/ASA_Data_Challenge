#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RAW_INPUT = Path("WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv")
OUT_DATA = Path("Urvi_Analysis/data_products")
OUT_FIG = Path("Urvi_Analysis/dashboard/figures")

TARGET_STATES = ["NY", "NJ", "CA", "TX"]
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
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def boolish(series: pd.Series) -> pd.Series:
    # Original WWC state flags are mostly 1/NaN; keep robust parsing for mixed encodings.
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
    mapped = [(c, normalize_state_from_col(c)) for c in state_cols]
    mapped = [(c, a) for c, a in mapped if a]
    use_cols = [c for c, _ in mapped]
    abbrs = [a for _, a in mapped]

    flags = pd.DataFrame(index=df.index)
    for c in use_cols:
        flags[c] = boolish(df[c])

    tokens = []
    for row in flags.itertuples(index=False, name=None):
        st = [abbrs[i] for i, v in enumerate(row) if v]
        tokens.append(sorted(st))

    out = df.copy()
    out["state_tokens"] = tokens
    out["state_count"] = out["state_tokens"].apply(len)
    out["is_multistate"] = out["state_count"] >= 2
    return out


def summary_for_state(df_state: pd.DataFrame, abbr: str) -> dict[str, float]:
    effect = pd.to_numeric(df_state["f_Effect_Size_WWC"], errors="coerce")
    improvement = pd.to_numeric(df_state["f_Improvement_Index"], errors="coerce")
    return {
        "state_abbr": abbr,
        "state_name": ABBR_TO_STATE.get(abbr, abbr),
        "findings_n": int(df_state["f_FindingID"].nunique()),
        "studies_n": int(df_state["s_StudyID"].nunique()),
        "interventions_n": int(df_state["i_InterventionID"].nunique()),
        "mean_effect_size_wwc": float(effect.mean()) if effect.notna().any() else float("nan"),
        "median_effect_size_wwc": float(effect.median()) if effect.notna().any() else float("nan"),
        "pct_positive_effect_size": float((effect.dropna() > 0).mean() * 100) if effect.notna().any() else float("nan"),
        "mean_improvement_index": float(improvement.mean()) if improvement.notna().any() else float("nan"),
    }


def plot_combo_effects(combo_df: pd.DataFrame) -> None:
    top = combo_df.sort_values("findings_n", ascending=False).head(20).copy()
    top = top.sort_values("mean_effect_size_wwc", ascending=True)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 9), dpi=220)
    bars = ax.barh(
        top["state_combo"],
        top["mean_effect_size_wwc"],
        color=sns.color_palette("viridis", n_colors=len(top)),
        edgecolor="#0f172a",
        linewidth=0.4,
    )
    ax.axvline(0, color="#334155", linewidth=1.0, linestyle="--")
    ax.set_title("Multi-State Study Combinations: Mean WWC Effect Size (Top 20 by Findings)")
    ax.set_xlabel("Mean WWC effect size")
    ax.set_ylabel("State combination")

    for bar, n in zip(bars, top["findings_n"]):
        x = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        pad = 0.01 if x >= 0 else -0.01
        ha = "left" if x >= 0 else "right"
        ax.text(x + pad, y, f"n={int(n)}", va="center", ha=ha, fontsize=8, color="#111827")

    fig.tight_layout()
    fig.savefig(OUT_FIG / "multistate_combinations_effect_size.png")
    plt.close(fig)


def plot_state_intervention_panels(intervention_long: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    for abbr in TARGET_STATES:
        part = intervention_long[intervention_long["state_abbr"] == abbr].copy()
        part = part.sort_values("findings_n", ascending=False).head(15)
        if part.empty:
            continue
        part = part.sort_values("mean_effect_size_wwc", ascending=True)

        fig, ax = plt.subplots(figsize=(12, 7), dpi=220)
        norm = plt.Normalize(0, 100)
        colors = plt.cm.turbo(norm(part["pct_positive_effect_size"].fillna(0)))
        bars = ax.barh(
            part["intervention_name"],
            part["mean_effect_size_wwc"],
            color=colors,
            edgecolor="#1f2937",
            linewidth=0.4,
        )
        ax.axvline(0, color="#334155", linewidth=1.0, linestyle="--")
        ax.set_title(f"{abbr} (Multi-State Rows Only): Intervention Mean Effect Size")
        ax.set_xlabel("Mean WWC effect size")
        ax.set_ylabel("Intervention")

        for bar, n in zip(bars, part["findings_n"]):
            x = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2
            pad = 0.01 if x >= 0 else -0.01
            ha = "left" if x >= 0 else "right"
            ax.text(x + pad, y, f"n={int(n)}", va="center", ha=ha, fontsize=8, color="#111827")

        sm = plt.cm.ScalarMappable(cmap="turbo", norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_label("% positive findings (effect size > 0)")

        fig.tight_layout()
        fig.savefig(OUT_FIG / f"multistate_{abbr.lower()}_intervention_effect.png")
        plt.close(fig)


def plot_target_state_summary(state_summary: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    order = state_summary.sort_values("mean_effect_size_wwc", ascending=False)["state_abbr"]

    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=220)
    ax2 = ax1.twinx()

    x = range(len(order))
    effect = state_summary.set_index("state_abbr").loc[order, "mean_effect_size_wwc"]
    pct = state_summary.set_index("state_abbr").loc[order, "pct_positive_effect_size"]

    ax1.bar(x, effect, color="#2563eb", alpha=0.88, label="Mean effect size")
    ax2.plot(x, pct, color="#dc2626", marker="o", linewidth=2, label="% positive findings")
    ax1.axhline(0, color="#334155", linewidth=1.0, linestyle="--")

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(order)
    ax1.set_ylabel("Mean WWC effect size")
    ax2.set_ylabel("% positive findings")
    ax1.set_title("NY/NJ/CA/TX Multi-State Signal Comparison")

    fig.tight_layout()
    fig.savefig(OUT_FIG / "multistate_target_states_summary.png")
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    raw = pd.read_csv(RAW_INPUT, encoding="utf-8-sig", low_memory=False)
    raw = parse_state_tokens(raw)

    multi = raw[raw["is_multistate"]].copy()
    multi["effect_size_num"] = pd.to_numeric(multi["f_Effect_Size_WWC"], errors="coerce")
    multi["improvement_num"] = pd.to_numeric(multi["f_Improvement_Index"], errors="coerce")

    # Combination-level aggregation for multi-state studies.
    combo = multi.copy()
    combo["state_combo"] = combo["state_tokens"].apply(lambda x: " | ".join(x))
    combo_summary = (
        combo.groupby("state_combo", as_index=False)
        .agg(
            findings_n=("f_FindingID", "nunique"),
            studies_n=("s_StudyID", "nunique"),
            interventions_n=("i_InterventionID", "nunique"),
            mean_effect_size_wwc=("effect_size_num", "mean"),
            median_effect_size_wwc=("effect_size_num", "median"),
            pct_positive_effect_size=("effect_size_num", lambda s: 100.0 * float((s.dropna() > 0).mean()) if s.notna().any() else float("nan")),
            mean_improvement_index=("improvement_num", "mean"),
        )
        .sort_values("findings_n", ascending=False)
    )
    combo_summary.to_csv(OUT_DATA / "multistate_combo_summary_original.csv", index=False)
    plot_combo_effects(combo_summary)

    # Target state summaries from multi-state rows only.
    state_rows = []
    state_iv_rows = []
    for abbr in TARGET_STATES:
        part = multi[multi["state_tokens"].apply(lambda t: abbr in t)].copy()
        state_rows.append(summary_for_state(part, abbr))

        iv = (
            part.groupby(["i_InterventionID", "i_Intervention_Name"], as_index=False)
            .agg(
                findings_n=("f_FindingID", "nunique"),
                studies_n=("s_StudyID", "nunique"),
                mean_effect_size_wwc=("effect_size_num", "mean"),
                median_effect_size_wwc=("effect_size_num", "median"),
                pct_positive_effect_size=(
                    "effect_size_num",
                    lambda s: 100.0 * float((s.dropna() > 0).mean()) if s.notna().any() else float("nan"),
                ),
                mean_improvement_index=("improvement_num", "mean"),
            )
            .sort_values("findings_n", ascending=False)
        )
        iv["state_abbr"] = abbr
        iv["state_name"] = ABBR_TO_STATE.get(abbr, abbr)
        iv["intervention_name"] = iv["i_Intervention_Name"].fillna("Unknown intervention")
        state_iv_rows.append(iv)

    state_summary = pd.DataFrame(state_rows)
    state_summary.to_csv(OUT_DATA / "multistate_target_state_summary_original.csv", index=False)
    plot_target_state_summary(state_summary)

    intervention_long = pd.concat(state_iv_rows, ignore_index=True)
    intervention_long.to_csv(OUT_DATA / "multistate_target_state_interventions_original.csv", index=False)
    plot_state_intervention_panels(intervention_long)

    # Keep a transparent row-level extraction for future causal workflow.
    subset = multi[multi["state_tokens"].apply(lambda t: any(s in t for s in TARGET_STATES))].copy()
    subset.to_csv(OUT_DATA / "multistate_rows_for_ny_nj_ca_tx_original.csv", index=False)

    print("Generated:")
    print(f"- {OUT_DATA / 'multistate_combo_summary_original.csv'}")
    print(f"- {OUT_DATA / 'multistate_target_state_summary_original.csv'}")
    print(f"- {OUT_DATA / 'multistate_target_state_interventions_original.csv'}")
    print(f"- {OUT_DATA / 'multistate_rows_for_ny_nj_ca_tx_original.csv'}")
    print(f"- {OUT_FIG / 'multistate_combinations_effect_size.png'}")
    print(f"- {OUT_FIG / 'multistate_target_states_summary.png'}")
    for abbr in TARGET_STATES:
        print(f"- {OUT_FIG / f'multistate_{abbr.lower()}_intervention_effect.png'}")


if __name__ == "__main__":
    main()

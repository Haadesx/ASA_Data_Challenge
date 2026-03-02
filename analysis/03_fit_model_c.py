#!/usr/bin/env python3
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from _utils import (
    build_design_matrix,
    configure_plotting,
    ensure_dir,
    fit_weighted_linear,
    prepare_analytic_dataset,
    weighted_mean,
    write_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Model C: evidence equity + transportability.")
    p.add_argument(
        "--wwc-csv",
        default="WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv",
        help="Path to WWC merged CSV.",
    )
    p.add_argument("--context-csv", default=None, help="Optional state-year context CSV.")
    p.add_argument("--outdir", default="outputs/model_c", help="Output directory.")
    return p.parse_args()


def subgroup_label(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [
                (df["frpl_share"] >= 0.6) & (df["ell_share"] >= 0.15),
                (df["frpl_share"] >= 0.6),
                (df["ell_share"] >= 0.15),
                (df["swd_share"] >= 0.13),
            ],
            ["High Poverty + High EL", "High Poverty", "High EL", "High SWD"],
            default="General/Mixed",
        ),
        index=df.index,
    )


def main() -> None:
    args = parse_args()
    outdir = ensure_dir(args.outdir)
    configure_plotting()

    df = prepare_analytic_dataset(args.wwc_csv, args.context_csv)
    df["subgroup_label"] = subgroup_label(df)
    df["acs_income_z"] = (df["acs_median_income_real"] - df["acs_median_income_real"].mean()) / df[
        "acs_median_income_real"
    ].std(ddof=0)
    df["acs_ba_z"] = (df["acs_ba_share"] - df["acs_ba_share"].mean()) / df["acs_ba_share"].std(ddof=0)

    numeric = [
        "acs_income_z",
        "acs_ba_z",
        "rucc_rural_share",
        "frpl_share",
        "ell_share",
        "child_poverty_rate",
        "study_quality_score",
        "publication_year_c",
    ]
    categorical = ["intervention_family", "state_abbr", "study_design_std"]
    interactions = [("intervention_family", "rucc_rural_share")]
    X, y, w, work = build_design_matrix(df, numeric, categorical, interactions)
    fit = fit_weighted_linear(X, y, w)
    work = work.assign(predicted_effect=fit["pred"].values, residual=fit["resid"].values)
    coef = fit["coef"].rename_axis("feature").reset_index()
    coef.to_csv(outdir / "coefficients.csv", index=False)
    work.to_csv(outdir / "finding_predictions.csv", index=False)

    write_json(
        outdir / "metrics.json",
        {
            "model": "C_transportability",
            "rows": int(len(work)),
            "features": int(X.shape[1]),
            "weighted_r2": fit["weighted_r2"],
            "context_source_values": sorted(df["context_source"].dropna().unique().tolist()),
        },
    )

    coverage = (
        df.groupby(["subgroup_label", "f_Outcome_Domain"], dropna=False)["finding_id"]
        .count()
        .rename("n_findings")
        .reset_index()
    )
    top_domains = coverage.groupby("f_Outcome_Domain")["n_findings"].sum().sort_values(ascending=False).head(14).index
    cov_plot = coverage[coverage["f_Outcome_Domain"].isin(top_domains)].copy()
    pivot = cov_plot.pivot(index="subgroup_label", columns="f_Outcome_Domain", values="n_findings").fillna(0)
    pivot = pivot.astype(float)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot = pivot[pivot.sum(axis=0).sort_values(ascending=False).index]
    pivot.to_csv(outdir / "coverage_heatmap_table.csv")

    plt.figure(figsize=(14, 7))
    sns.heatmap(pivot, cmap="YlGnBu", linewidths=0.3)
    plt.title("Evidence Coverage: Findings by Subgroup and Outcome Domain")
    plt.xlabel("Outcome Domain")
    plt.ylabel("Subgroup")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(outdir / "coverage_heatmap.png", dpi=220)
    plt.close()

    work2 = work.copy()
    work2["subgroup_label"] = subgroup_label(work2)
    risk = (
        work2.groupby(["state_abbr", "subgroup_label"], dropna=False)
        .agg(
            n_findings=("finding_id", "count"),
            avg_abs_resid=("residual", lambda s: float(np.mean(np.abs(s)))),
            avg_pred=("predicted_effect", "mean"),
            avg_poverty=("child_poverty_rate", "mean"),
        )
        .reset_index()
    )
    risk["transport_risk"] = risk["avg_abs_resid"] * (1.0 / np.sqrt(risk["n_findings"].clip(lower=1))) * (
        1 + risk["avg_poverty"].fillna(risk["avg_poverty"].median())
    )
    risk["n_findings"] = pd.to_numeric(risk["n_findings"], errors="coerce").astype(float)
    risk["avg_pred"] = pd.to_numeric(risk["avg_pred"], errors="coerce")
    risk["transport_risk"] = pd.to_numeric(risk["transport_risk"], errors="coerce")
    risk["avg_poverty"] = pd.to_numeric(risk["avg_poverty"], errors="coerce")
    risk = risk.sort_values("transport_risk", ascending=False)
    risk.to_csv(outdir / "transport_risk_by_state_subgroup.csv", index=False)

    top_risk = risk[(risk["state_abbr"] != "NA") & (risk["n_findings"] >= 5)].head(25)
    plt.figure(figsize=(12, 10))
    sns.barplot(data=top_risk, x="transport_risk", y=top_risk["state_abbr"] + " | " + top_risk["subgroup_label"], color="#2563EB")
    plt.title("Highest Transport Risk Segments (High Need, Low Evidence)")
    plt.xlabel("Transport Risk Index")
    plt.ylabel("State | Subgroup")
    plt.tight_layout()
    plt.savefig(outdir / "transport_risk_top25.png", dpi=220)
    plt.close()

    scatter = risk[(risk["state_abbr"] != "NA") & (risk["n_findings"] >= 8)].copy()
    plt.figure(figsize=(11, 8))
    sns.scatterplot(
        data=scatter,
        x="avg_pred",
        y="transport_risk",
        hue="avg_poverty",
        size="n_findings",
        sizes=(20, 350),
        palette="rocket_r",
        alpha=0.85,
    )
    plt.axvline(0, color="#111827", linestyle="--", linewidth=1.0)
    plt.title("Predicted Impact vs Transport Risk")
    plt.xlabel("Average Predicted Effect")
    plt.ylabel("Transport Risk Index")
    plt.tight_layout()
    plt.savefig(outdir / "impact_vs_transport_risk.png", dpi=220)
    plt.close()

    equity_rank = (
        work2.groupby(["intervention_family", "subgroup_label"], dropna=False)
        .apply(lambda d: weighted_mean(d, "predicted_effect", "analysis_weight"))
        .rename("avg_pred_effect")
        .reset_index()
        .sort_values(["subgroup_label", "avg_pred_effect"], ascending=[True, False])
    )
    equity_rank.to_csv(outdir / "intervention_rank_by_subgroup.csv", index=False)


if __name__ == "__main__":
    main()

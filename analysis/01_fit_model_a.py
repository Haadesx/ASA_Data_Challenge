#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
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
    p = argparse.ArgumentParser(description="Model A: subgroup heterogeneity (what works for whom).")
    p.add_argument(
        "--wwc-csv",
        default="WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv",
        help="Path to WWC merged CSV.",
    )
    p.add_argument("--context-csv", default=None, help="Optional state-year context CSV.")
    p.add_argument("--outdir", default="outputs/model_a", help="Output directory.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    outdir = ensure_dir(args.outdir)
    configure_plotting()

    df = prepare_analytic_dataset(args.wwc_csv, args.context_csv)
    numeric = [
        "frpl_share",
        "ell_share",
        "swd_share",
        "minority_share",
        "study_quality_score",
        "publication_year_c",
    ]
    categorical = ["intervention_family", "grade_band", "urbanicity", "study_design_std"]
    interactions = [
        ("intervention_family", "frpl_share"),
        ("intervention_family", "ell_share"),
        ("intervention_family", "swd_share"),
    ]

    X, y, w, work = build_design_matrix(df, numeric, categorical, interactions)
    fit = fit_weighted_linear(X, y, w)
    work = work.assign(predicted_effect=fit["pred"].values, residual=fit["resid"].values)
    coef = fit["coef"].rename_axis("feature").reset_index()

    coef.to_csv(outdir / "coefficients.csv", index=False)
    work.to_csv(outdir / "finding_predictions.csv", index=False)
    write_json(
        outdir / "metrics.json",
        {
            "model": "A_subgroup_heterogeneity",
            "rows": int(len(work)),
            "features": int(X.shape[1]),
            "weighted_r2": fit["weighted_r2"],
            "context_source_values": sorted(df["context_source"].dropna().unique().tolist()),
        },
    )

    coef_plot = coef[coef["feature"] != "intercept"].copy()
    coef_plot["abs_coef"] = coef_plot["coefficient"].abs()
    coef_plot = coef_plot.nlargest(30, "abs_coef").sort_values("coefficient")

    plt.figure(figsize=(12, 10))
    sns.barplot(data=coef_plot, y="feature", x="coefficient", palette="vlag")
    plt.axvline(0, color="#111827", linewidth=1.2)
    plt.title("Model A: Top Coefficients (Weighted Linear Model)")
    plt.xlabel("Coefficient")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(outdir / "coef_top30.png", dpi=220)
    plt.close()

    h = work.copy()
    h["frpl_band"] = pd.qcut(h["frpl_share"].rank(method="first"), q=3, labels=["Low FRPL", "Mid FRPL", "High FRPL"])
    top_families = h["intervention_family"].value_counts().head(12).index
    h = h[h["intervention_family"].isin(top_families)]
    heat = (
        h.groupby(["intervention_family", "frpl_band"], dropna=False)
        .apply(lambda d: weighted_mean(d, "predicted_effect", "analysis_weight"))
        .rename("predicted_effect")
        .reset_index()
    )
    pivot = heat.pivot(index="intervention_family", columns="frpl_band", values="predicted_effect").sort_index()

    plt.figure(figsize=(11, 7))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0, linewidths=0.3)
    plt.title("Predicted Effect by Intervention Family and FRPL Band")
    plt.xlabel("FRPL Band")
    plt.ylabel("Intervention Family")
    plt.tight_layout()
    plt.savefig(outdir / "heterogeneity_heatmap_frpl.png", dpi=220)
    plt.close()

    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        data=work.sample(min(5000, len(work)), random_state=42),
        x="effect_size_final",
        y="predicted_effect",
        hue="is_subgroup",
        alpha=0.45,
        s=28,
    )
    min_v = min(work["effect_size_final"].min(), work["predicted_effect"].min())
    max_v = max(work["effect_size_final"].max(), work["predicted_effect"].max())
    plt.plot([min_v, max_v], [min_v, max_v], color="#1f2937", linestyle="--", linewidth=1.2)
    plt.title("Observed vs Predicted Effects (Model A)")
    plt.xlabel("Observed Effect Size")
    plt.ylabel("Predicted Effect Size")
    plt.tight_layout()
    plt.savefig(outdir / "observed_vs_predicted.png", dpi=220)
    plt.close()

    ranking = (
        h.groupby(["intervention_family", "frpl_band"], dropna=False)
        .apply(lambda d: weighted_mean(d, "predicted_effect", "analysis_weight"))
        .rename("avg_pred_effect")
        .reset_index()
        .sort_values(["frpl_band", "avg_pred_effect"], ascending=[True, False])
    )
    ranking.to_csv(outdir / "intervention_rank_by_frpl_band.csv", index=False)


if __name__ == "__main__":
    main()


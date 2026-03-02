#!/usr/bin/env python3
from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _utils import (
    build_design_matrix,
    configure_plotting,
    decile_bins,
    ensure_dir,
    fit_weighted_linear,
    prepare_analytic_dataset,
    weighted_mean,
    write_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Model B: resource moderation.")
    p.add_argument(
        "--wwc-csv",
        default="WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv",
        help="Path to WWC merged CSV.",
    )
    p.add_argument("--context-csv", default=None, help="Optional state-year context CSV.")
    p.add_argument("--outdir", default="outputs/model_b", help="Output directory.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    outdir = ensure_dir(args.outdir)
    configure_plotting()

    df = prepare_analytic_dataset(args.wwc_csv, args.context_csv)
    numeric = [
        "log_pp_exp",
        "child_poverty_rate",
        "teacher_salary_real",
        "frpl_share",
        "ell_share",
        "study_quality_score",
        "publication_year_c",
    ]
    categorical = ["intervention_family", "study_design_std", "state_abbr"]
    interactions = [
        ("intervention_family", "log_pp_exp"),
        ("intervention_family", "child_poverty_rate"),
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
            "model": "B_resource_moderation",
            "rows": int(len(work)),
            "features": int(X.shape[1]),
            "weighted_r2": fit["weighted_r2"],
            "context_source_values": sorted(df["context_source"].dropna().unique().tolist()),
        },
    )

    coeff_focus = coef[
        coef["feature"].str.contains("log_pp_exp|child_poverty_rate|teacher_salary_real|:x:", regex=True, na=False)
    ].copy()
    coeff_focus["abs_coef"] = coeff_focus["coefficient"].abs()
    coeff_focus = coeff_focus.nlargest(30, "abs_coef").sort_values("coefficient")

    plt.figure(figsize=(12, 10))
    sns.barplot(data=coeff_focus, y="feature", x="coefficient", palette="coolwarm")
    plt.axvline(0, color="#111827", linewidth=1.2)
    plt.title("Resource Moderators and Interactions (Model B)")
    plt.xlabel("Coefficient")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(outdir / "coef_resource_terms.png", dpi=220)
    plt.close()

    top_fam = work["intervention_family"].value_counts().head(4).index
    m = work[work["intervention_family"].isin(top_fam)].copy()
    m["pp_exp_group"] = pd.qcut(m["log_pp_exp"], q=2, labels=["Lower Spending", "Higher Spending"], duplicates="drop")
    m["poverty_decile"] = decile_bins(m["child_poverty_rate"])
    line = (
        m.groupby(["intervention_family", "pp_exp_group", "poverty_decile"], dropna=False)
        .apply(lambda d: weighted_mean(d, "predicted_effect", "analysis_weight"))
        .rename("avg_pred_effect")
        .reset_index()
    )

    g = sns.relplot(
        data=line,
        x="poverty_decile",
        y="avg_pred_effect",
        hue="pp_exp_group",
        col="intervention_family",
        kind="line",
        marker="o",
        col_wrap=2,
        height=4,
        aspect=1.3,
        facet_kws={"sharey": True, "sharex": True},
    )
    g.set_axis_labels("Child Poverty Decile (0=lowest)", "Predicted Effect")
    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle("Resource Moderation Curves by Intervention Family")
    g.savefig(outdir / "moderation_curves.png", dpi=220)
    plt.close(g.fig)

    state = (
        work.groupby("state_abbr", dropna=False)
        .agg(
            findings=("finding_id", "count"),
            avg_effect=("effect_size_final", lambda s: s.mean()),
            avg_log_pp_exp=("log_pp_exp", "mean"),
            avg_poverty=("child_poverty_rate", "mean"),
        )
        .reset_index()
    )
    state = state[(state["state_abbr"] != "NA") & (state["findings"] >= 20)].copy()
    state["findings"] = pd.to_numeric(state["findings"], errors="coerce").astype(float)
    state["avg_log_pp_exp"] = pd.to_numeric(state["avg_log_pp_exp"], errors="coerce")
    state["avg_effect"] = pd.to_numeric(state["avg_effect"], errors="coerce")
    state["avg_poverty"] = pd.to_numeric(state["avg_poverty"], errors="coerce")
    state.to_csv(outdir / "state_resource_summary.csv", index=False)

    plt.figure(figsize=(11, 8))
    sns.scatterplot(
        data=state,
        x="avg_log_pp_exp",
        y="avg_effect",
        size="findings",
        hue="avg_poverty",
        sizes=(40, 400),
        palette="mako_r",
        alpha=0.85,
    )
    for _, r in state.sort_values("findings", ascending=False).head(12).iterrows():
        plt.text(r["avg_log_pp_exp"], r["avg_effect"], r["state_abbr"], fontsize=9)
    plt.title("State-Level Effectiveness vs Resource Level")
    plt.xlabel("Average log(Per-Pupil Expenditure)")
    plt.ylabel("Average Effect Size")
    plt.tight_layout()
    plt.savefig(outdir / "state_resource_bubble.png", dpi=220)
    plt.close()


if __name__ == "__main__":
    main()

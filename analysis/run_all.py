#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run all WWC model scripts and generate visual outputs.")
    p.add_argument(
        "--wwc-csv",
        default="WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv",
        help="Path to WWC merged CSV.",
    )
    p.add_argument("--context-csv", default=None, help="Optional merged context CSV.")
    p.add_argument("--outroot", default="outputs", help="Output root directory.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    outroot = Path(args.outroot)
    outroot.mkdir(parents=True, exist_ok=True)
    scripts = [
        ("analysis/01_fit_model_a.py", outroot / "model_a"),
        ("analysis/02_fit_model_b.py", outroot / "model_b"),
        ("analysis/03_fit_model_c.py", outroot / "model_c"),
    ]
    for script, outdir in scripts:
        cmd = [sys.executable, script, "--wwc-csv", args.wwc_csv, "--outdir", str(outdir)]
        if args.context_csv:
            cmd.extend(["--context-csv", args.context_csv])
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()


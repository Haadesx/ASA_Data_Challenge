#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests


ACS_VARS = [
    "NAME",
    "B19013_001E",  # median household income
    "B15003_001E",  # pop 25+
    "B15003_022E",  # bachelor's
    "B15003_023E",  # master's
    "B15003_024E",  # professional school
    "B15003_025E",  # doctorate
    "B03002_001E",  # total
    "B03002_003E",  # white non-hispanic
    "B03002_004E",  # black non-hispanic
    "B03002_012E",  # hispanic (any race)
]

FIPS_TO_ABBR = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}


def get_json(url: str) -> list[list[str]]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_acs_state_year(year: int) -> pd.DataFrame:
    vars_q = ",".join(ACS_VARS)
    url = f"https://api.census.gov/data/{year}/acs/acs5?get={vars_q}&for=state:*"
    rows = get_json(url)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["year"] = year
    df["state_abbr"] = df["state"].map(FIPS_TO_ABBR)
    df = df[df["state_abbr"].notna()].copy()

    for c in ACS_VARS:
        if c == "NAME":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    edu_total = df["B15003_001E"]
    edu_ba_plus = df["B15003_022E"] + df["B15003_023E"] + df["B15003_024E"] + df["B15003_025E"]
    race_total = df["B03002_001E"]

    out = pd.DataFrame(
        {
            "state_abbr": df["state_abbr"],
            "year": df["year"],
            "acs_median_income_real": df["B19013_001E"],
            "acs_ba_share": np.where(edu_total > 0, edu_ba_plus / edu_total, np.nan),
            "acs_white_share": np.where(race_total > 0, df["B03002_003E"] / race_total, np.nan),
            "acs_black_share": np.where(race_total > 0, df["B03002_004E"] / race_total, np.nan),
            "acs_hispanic_share": np.where(race_total > 0, df["B03002_012E"] / race_total, np.nan),
        }
    )
    return out


def fetch_saipe_state_year(year: int) -> pd.DataFrame:
    url = (
        "https://api.census.gov/data/timeseries/poverty/saipe"
        f"?get=NAME,SAEPOVRT5_17R_PT,SAEMHI_PT&for=state:*&time={year}"
    )
    rows = get_json(url)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["state_abbr"] = df["state"].map(FIPS_TO_ABBR)
    df = df[df["state_abbr"].notna()].copy()
    df["year"] = pd.to_numeric(df["time"], errors="coerce").astype("Int64")
    df["saipe_child_poverty_rate"] = pd.to_numeric(df["SAEPOVRT5_17R_PT"], errors="coerce") / 100.0
    df["saipe_median_income"] = pd.to_numeric(df["SAEMHI_PT"], errors="coerce")
    return df[["state_abbr", "year", "saipe_child_poverty_rate", "saipe_median_income"]]


def fetch_rucc_state_share() -> pd.DataFrame:
    url = "https://www.ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=39528"
    long = pd.read_csv(url, encoding="latin1")
    wide = long.pivot_table(index=["FIPS", "State", "County_Name"], columns="Attribute", values="Value", aggfunc="first").reset_index()
    wide["RUCC_2023"] = pd.to_numeric(wide.get("RUCC_2023"), errors="coerce")
    wide["Population_2020"] = pd.to_numeric(wide.get("Population_2020"), errors="coerce")
    wide = wide[wide["State"].isin(FIPS_TO_ABBR.values())].copy()
    wide["is_rural_county"] = wide["RUCC_2023"] >= 7
    wide["rural_pop"] = np.where(wide["is_rural_county"], wide["Population_2020"], 0.0)

    state = (
        wide.groupby("State", as_index=False)
        .agg(total_pop=("Population_2020", "sum"), rural_pop=("rural_pop", "sum"))
        .rename(columns={"State": "state_abbr"})
    )
    state["rucc_rural_share"] = np.where(state["total_pop"] > 0, state["rural_pop"] / state["total_pop"], np.nan)
    return state[["state_abbr", "rucc_rural_share"]]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build state-year context CSV from ACS + SAIPE + RUCC.")
    p.add_argument("--year-start", type=int, default=2009, help="First ACS year (>=2009 recommended).")
    p.add_argument("--year-end", type=int, default=2024, help="Last year to fetch.")
    p.add_argument(
        "--out-csv",
        default="data/context_state_year_acs_saipe_rucc.csv",
        help="Output merged context CSV path.",
    )
    p.add_argument(
        "--out-meta",
        default="data/context_state_year_acs_saipe_rucc.meta.json",
        help="Output metadata JSON path.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.year_start > args.year_end:
        raise ValueError("year-start must be <= year-end")

    years = list(range(args.year_start, args.year_end + 1))
    acs_parts: list[pd.DataFrame] = []
    saipe_parts: list[pd.DataFrame] = []

    for y in years:
        try:
            acs_parts.append(fetch_acs_state_year(y))
        except Exception as exc:
            print(f"ACS fetch failed for {y}: {exc}")
        try:
            saipe_parts.append(fetch_saipe_state_year(y))
        except Exception as exc:
            print(f"SAIPE fetch failed for {y}: {exc}")

    if not acs_parts:
        raise RuntimeError("No ACS data fetched.")

    acs = pd.concat(acs_parts, ignore_index=True)
    if saipe_parts:
        saipe = pd.concat(saipe_parts, ignore_index=True)
    else:
        saipe = pd.DataFrame(columns=["state_abbr", "year", "saipe_child_poverty_rate", "saipe_median_income"])
    rucc = fetch_rucc_state_share()

    merged = acs.merge(saipe, on=["state_abbr", "year"], how="left")
    merged = merged.merge(rucc, on="state_abbr", how="left")

    merged["ccd_frpl_share"] = merged["saipe_child_poverty_rate"].clip(0, 1)
    merged["ccd_ell_share"] = np.nan
    merged["ccd_swd_share"] = np.nan
    merged["f33_pp_expenditure_real"] = np.nan
    merged["f33_teacher_salary_real"] = np.nan
    merged["year"] = pd.to_numeric(merged["year"], errors="coerce").astype("Int64")
    merged = merged.sort_values(["state_abbr", "year"]).reset_index(drop=True)

    out_cols = [
        "state_abbr",
        "year",
        "ccd_frpl_share",
        "ccd_ell_share",
        "ccd_swd_share",
        "f33_pp_expenditure_real",
        "f33_teacher_salary_real",
        "saipe_child_poverty_rate",
        "acs_median_income_real",
        "acs_ba_share",
        "acs_white_share",
        "acs_black_share",
        "acs_hispanic_share",
        "rucc_rural_share",
    ]
    out = merged[out_cols].copy()

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)

    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "year_start": args.year_start,
        "year_end": args.year_end,
        "rows": int(len(out)),
        "sources": {
            "acs5_api": "https://api.census.gov/data/{year}/acs/acs5",
            "saipe_api": "https://api.census.gov/data/timeseries/poverty/saipe",
            "rucc_csv": "https://www.ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=39528",
        },
        "notes": [
            "FRPL share proxied using SAIPE child poverty rate when NCES CCD FRPL is unavailable.",
            "F-33 finance columns are null placeholders and can be replaced later with NCES F-33.",
            "RUCC rural share is constant across years (derived from 2023 RUCC and 2020 county population).",
        ],
    }
    out_meta = Path(args.out_meta)
    out_meta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote {len(out)} rows to {out_csv}")
    print(f"Wrote metadata to {out_meta}")


if __name__ == "__main__":
    main()


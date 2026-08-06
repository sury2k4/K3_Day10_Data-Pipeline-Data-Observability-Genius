from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


from pathlib import Path

from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    total_rows = len(df)
    null_paper_ids = int(df["paper_id"].isnull().sum()) if "paper_id" in df.columns else total_rows
    duplicate_paper_ids = int(df["paper_id"].duplicated().sum()) if "paper_id" in df.columns else total_rows
    null_titles = int(df["title"].isnull().sum()) if "title" in df.columns else total_rows
    
    blank_summaries = int((df["summary_chars"] == 0).sum()) if "summary_chars" in df.columns else 0
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0

    checks = {
        "non_empty_dataset": total_rows > 0,
        "no_null_paper_ids": null_paper_ids == 0,
        "unique_paper_ids": duplicate_paper_ids == 0,
        "no_null_titles": null_titles == 0,
        "no_blank_summaries": blank_summaries == 0,
        "freshness_threshold": stale_rows == 0,
    }

    all_passed = all(checks.values())
    report = {
        "report_name": report_name,
        "total_rows": total_rows,
        "metrics": {
            "null_paper_ids": null_paper_ids,
            "duplicate_paper_ids": duplicate_paper_ids,
            "null_titles": null_titles,
            "blank_summaries": blank_summaries,
            "stale_rows": stale_rows,
        },
        "checks": checks,
        "passed": all_passed,
    }

    out_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(out_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    total_rows = len(df)
    if total_rows == 0:
        report = {
            "latest_published": "N/A",
            "oldest_published": "N/A",
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
        }
    else:
        published_dates = df["published"].dropna().tolist()
        latest_pub = max(published_dates) if published_dates else "N/A"
        oldest_pub = min(published_dates) if published_dates else "N/A"
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
        is_fresh = (stale_rows == 0)

        report = {
            "latest_published": str(latest_pub),
            "oldest_published": str(oldest_pub),
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "is_fresh": is_fresh,
        }

    out_p = Path(report_path)
    write_json(out_p, report)
    return report


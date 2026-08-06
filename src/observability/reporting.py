from __future__ import annotations

from typing import Any


from pathlib import Path

from core.utils import write_text


def generate_phase1_report(
    report_path: Path | str,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    hit_rate = metrics.get("retrieval_hit_rate", 0.0) * 100
    token_f1 = metrics.get("mean_token_f1", 0.0) * 100
    judge_acc = metrics.get("judge_accuracy", 0.0) * 100
    judge_score = metrics.get("mean_judge_score", 0.0)
    samples = metrics.get("samples", 0)

    quality_passed = quality.get("passed", False)
    freshness_status = "FRESH" if freshness.get("is_fresh", False) else "STALE"

    md_content = f"""# Data Pipeline Baseline Report (Phase 1)

## Executive Summary
This report presents the baseline data pipeline performance, dataset metadata, data quality check results, and RAG retrieval evaluation.

## 1. Data Ingestion Summary
- **Source API:** {source_summary.get("source_api", "Crossref API")}
- **Query:** `{source_summary.get("source_query", "N/A")}`
- **Total Raw Records:** {source_summary.get("raw_count", 0)}
- **Total Cleaned Records:** {source_summary.get("clean_count", 0)}

## 2. Evaluation Metrics (Baseline)
- **Evaluation Samples:** {samples}
- **Retrieval Hit Rate:** {hit_rate:.2f}%
- **Mean Token F1 Score:** {token_f1:.2f}%
- **LLM Judge Accuracy:** {judge_acc:.2f}%
- **Mean Judge Score (1-5):** {judge_score:.2f}

## 3. Data Observability & Quality Signals
- **Data Quality Status:** {"✅ PASSED" if quality_passed else "❌ FAILED"}
- **Dataset Freshness Status:** `{freshness_status}`
- **Latest Published Paper:** {freshness.get("latest_published", "N/A")}
- **Oldest Published Paper:** {freshness.get("oldest_published", "N/A")}
- **Stale Row Count:** {freshness.get("stale_rows", 0)}

### Data Quality Checks Breakdown
| Check Name | Status |
| --- | --- |
| Non-empty dataset | {"PASS" if quality.get("checks", {}).get("non_empty_dataset") else "FAIL"} |
| No null paper_ids | {"PASS" if quality.get("checks", {}).get("no_null_paper_ids") else "FAIL"} |
| Unique paper_ids | {"PASS" if quality.get("checks", {}).get("unique_paper_ids") else "FAIL"} |
| No null titles | {"PASS" if quality.get("checks", {}).get("no_null_titles") else "FAIL"} |
| No blank summaries | {"PASS" if quality.get("checks", {}).get("no_blank_summaries") else "FAIL"} |
| Freshness threshold | {"PASS" if quality.get("checks", {}).get("freshness_threshold") else "FAIL"} |
"""
    write_text(Path(report_path), md_content)


def generate_corruption_report(
    report_path: Path | str,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    b_hit = baseline_metrics.get("retrieval_hit_rate", 0.0) * 100
    c_hit = corrupted_metrics.get("retrieval_hit_rate", 0.0) * 100
    r_hit = repaired_metrics.get("retrieval_hit_rate", 0.0) * 100

    b_f1 = baseline_metrics.get("mean_token_f1", 0.0) * 100
    c_f1 = corrupted_metrics.get("mean_token_f1", 0.0) * 100
    r_f1 = repaired_metrics.get("mean_token_f1", 0.0) * 100

    b_acc = baseline_metrics.get("judge_accuracy", 0.0) * 100
    c_acc = corrupted_metrics.get("judge_accuracy", 0.0) * 100
    r_acc = repaired_metrics.get("judge_accuracy", 0.0) * 100

    b_score = baseline_metrics.get("mean_judge_score", 0.0)
    c_score = corrupted_metrics.get("mean_judge_score", 0.0)
    r_score = repaired_metrics.get("mean_judge_score", 0.0)

    md_content = f"""# Data Corruption & Repair Impact Analysis Report

## Executive Summary
This report analyzes the impact of controlled data corruption on RAG agent accuracy and demonstrates the effectiveness of automated data pipeline repair from reliable raw sources.

## 1. Metrics Comparison Across States

| State | Retrieval Hit Rate | Mean Token F1 | Judge Accuracy | Mean Judge Score (1-5) |
| --- | :---: | :---: | :---: | :---: |
| **Baseline** | {b_hit:.2f}% | {b_f1:.2f}% | {b_acc:.2f}% | {b_score:.2f} |
| **Corrupted** | {c_hit:.2f}% | {c_f1:.2f}% | {c_acc:.2f}% | {c_score:.2f} |
| **Repaired** | {r_hit:.2f}% | {r_f1:.2f}% | {r_acc:.2f}% | {r_score:.2f} |

### Key Observations & Delta
- **Impact of Corruption:** Retrieval Hit Rate dropped by **{b_hit - c_hit:.2f}%** and Token F1 dropped by **{b_f1 - c_f1:.2f}%**.
- **Recovery after Repair:** Retrieval Hit Rate recovered by **+{r_hit - c_hit:.2f}%** and Token F1 recovered by **+{r_f1 - c_f1:.2f}%**.

## 2. Observability & Data Quality Signals

| Metric / Indicator | Corrupted State | Repaired State |
| --- | :---: | :---: |
| **Quality Check Passed** | {"✅ YES" if corrupted_quality.get("passed") else "❌ NO"} | {"✅ YES" if repaired_quality.get("passed") else "❌ NO"} |
| **Dataset Freshness** | {"FRESH" if corrupted_freshness.get("is_fresh") else "STALE"} | {"FRESH" if repaired_freshness.get("is_fresh") else "STALE"} |
| **Stale Row Count** | {corrupted_freshness.get("stale_rows", 0)} | {repaired_freshness.get("stale_rows", 0)} |
| **Blank Summaries** | {corrupted_quality.get("metrics", {}).get("blank_summaries", 0)} | {repaired_quality.get("metrics", {}).get("blank_summaries", 0)} |
| **Duplicate IDs** | {corrupted_quality.get("metrics", {}).get("duplicate_paper_ids", 0)} | {repaired_quality.get("metrics", {}).get("duplicate_paper_ids", 0)} |

## 3. Conclusion
1. **Bad Data Degrades Agent Performance:** Injecting noise, blanking summaries, truncating titles, and making dates stale severely hinders vector similarity retrieval and LLM context precision.
2. **Automated Pipeline Repair Restores Accuracy:** Re-ingesting raw, reliable metadata and re-running cleaning/deduplication fully restores Agent retrieval hit rate and response quality.
"""
    write_text(Path(report_path), md_content)


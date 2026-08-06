from __future__ import annotations


import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("[INFO] Starting Data Corruption & Automated Repair Pipeline...")
    settings = load_settings()

    # 1. Read baseline dataset & metrics
    print("[INFO] Loading baseline clean dataset & metrics...")
    if not settings.paths.clean_csv.exists() or not settings.paths.baseline_metrics.exists():
        raise RuntimeError("Baseline clean CSV or metrics missing. Please run phase1 pipeline first!")
    
    baseline_df = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # 2. Corrupt data
    print("[INFO] Simulating controlled data corruption (dropping records, blanking summaries, injecting noise)...")
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"       Corrupted DataFrame contains {len(corrupted_df)} rows.")

    # 3. Build Corrupted Index & Evaluate
    print("[INFO] Building Chroma Vector Index (Corrupted)...")
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    print("[INFO] Evaluating Corrupted Pipeline Performance on Baseline Test Set...")
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"       Corrupted Retrieval Hit Rate: {corrupted_eval.summary['retrieval_hit_rate']*100:.2f}%")

    # 4. Corrupted Quality & Freshness
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.quality_dir / "freshness_corrupted.json")

    # 5. Repair Data from Raw Source
    print("[INFO] Repairing Data Pipeline by re-ingesting raw records & re-running cleaning...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"       Repaired DataFrame contains {len(repaired_df)} rows.")

    # 6. Build Repaired Index & Evaluate
    print("[INFO] Building Chroma Vector Index (Repaired)...")
    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    print("[INFO] Evaluating Repaired Pipeline Performance...")
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"       Repaired Retrieval Hit Rate: {repaired_eval.summary['retrieval_hit_rate']*100:.2f}%")

    # 7. Repaired Quality & Freshness
    repaired_quality = run_data_quality_checks(repaired_df, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.quality_dir / "freshness_repaired.json")

    # 8. Generate Comparison Report
    print("[INFO] Generating Markdown Corruption vs Repair Comparison Report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print(f"[SUCCESS] Data Corruption & Repair Flow completed! Report saved to: {settings.paths.comparison_report}")



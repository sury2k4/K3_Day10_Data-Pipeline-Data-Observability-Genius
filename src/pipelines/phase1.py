from __future__ import annotations


from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("[INFO] Starting Phase 1 Baseline Pipeline...")
    # 1. Load settings
    settings = load_settings()

    # 2. Fetch raw records
    print("[INFO] Ingesting raw paper records from source...")
    raw_records = fetch_source_records(settings)
    print(f"       Loaded {len(raw_records)} raw records.")

    # 3. Clean data
    print("[INFO] Cleaning data and creating embedding text...")
    clean_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    print(f"       Cleaned DataFrame contains {len(clean_df)} rows.")

    # 4. Build Chroma Vector Index
    print("[INFO] Building MiniLM Embeddings & Chroma Vector Store (Baseline)...")
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"       Indexed {len(index.documents)} documents into collection '{index.collection_name}'.")

    # 5. Build evaluation test set
    print("[INFO] Building Evaluation Test Set...")
    test_set = build_test_set(clean_df, settings.paths.eval_testset)
    print(f"       Created test set with {len(test_set)} question items.")

    # 6. Evaluate pipeline
    print("[INFO] Evaluating Baseline Pipeline Performance...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"       Retrieval Hit Rate: {eval_bundle.summary['retrieval_hit_rate']*100:.2f}%")
    print(f"       Mean Token F1: {eval_bundle.summary['mean_token_f1']*100:.2f}%")

    # 7. Data Quality & Freshness
    print("[INFO] Running Data Quality & Freshness Monitoring...")
    quality_report = run_data_quality_checks(clean_df, settings, report_name="baseline")
    freshness_report = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    # 8. Generate Phase 1 Report
    print("[INFO] Generating Markdown Phase 1 Baseline Report...")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_count": len(raw_records),
        "clean_count": len(clean_df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )

    print(f"[SUCCESS] Phase 1 Baseline Pipeline completed! Report saved to: {settings.paths.baseline_report}")



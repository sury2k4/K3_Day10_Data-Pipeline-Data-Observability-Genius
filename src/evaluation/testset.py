from __future__ import annotations

from typing import Any

import pandas as pd


from pathlib import Path

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    if df.empty:
        raise ValueError("DataFrame is empty. Cannot build test set.")

    records = df.to_dict(orient="records")
    test_items: list[dict[str, Any]] = []

    # Select representative samples (up to 6 papers)
    sample_records = records[: min(6, len(records))]

    for idx, row in enumerate(sample_records, start=1):
        paper_id = row["paper_id"]
        title = row["title"]
        summary = row["summary"]
        authors = row["authors_joined"]
        pub_date = row["published"]
        categories = row["categories_joined"]

        # Type 1: Summary / core finding
        test_items.append(
            {
                "id": f"eval_sum_{idx}",
                "question_type": "summary",
                "question": f"What is the main topic or abstract of the paper '{title}'?",
                "ground_truth": summary if summary else title,
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # Type 2: Authors lookup
        test_items.append(
            {
                "id": f"eval_author_{idx}",
                "question_type": "authors",
                "question": f"Who are the authors of paper '{title}'?",
                "ground_truth": f"The authors of '{title}' are {authors}.",
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # Type 3: Published date lookup
        test_items.append(
            {
                "id": f"eval_date_{idx}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": f"The paper '{title}' was published on {pub_date}.",
                "ground_truth_doc_ids": [paper_id],
            }
        )

        # Type 4: Categories query
        test_items.append(
            {
                "id": f"eval_cat_{idx}",
                "question_type": "categories",
                "question": f"What categories or subjects does the paper '{title}' belong to?",
                "ground_truth": f"The paper belongs to: {categories}.",
                "ground_truth_doc_ids": [paper_id],
            }
        )

    out_p = Path(output_path)
    write_json(out_p, test_items)
    return test_items


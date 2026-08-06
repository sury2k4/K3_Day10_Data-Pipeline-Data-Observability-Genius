from __future__ import annotations

import pandas as pd


from pathlib import Path

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    c_df = df.copy()
    logs: list[dict[str, str]] = []

    # 1. Drop latest records
    if len(c_df) > 5:
        dropped_ids = c_df.iloc[:2]["paper_id"].tolist()
        c_df = c_df.iloc[2:].reset_index(drop=True)
        logs.append({"action": "drop_latest_records", "details": f"Dropped paper_ids: {dropped_ids}"})

    # 2. Blank summary for select rows
    if len(c_df) > 0:
        c_df.loc[0, "summary"] = ""
        c_df.loc[0, "summary_chars"] = 0
        logs.append({"action": "blank_summary", "details": f"Blanked summary for paper_id: {c_df.loc[0, 'paper_id']}"})

    # 3. Inject noise into text & truncate title
    if len(c_df) > 1:
        c_df.loc[1, "title"] = c_df.loc[1, "title"][:10] + " [CORRUPTED TRUNCATED]"
        c_df.loc[1, "summary"] = "NOISE RANDOM BAD DATA " * 5
        c_df.loc[1, "summary_chars"] = len(c_df.loc[1, "summary"])
        logs.append({"action": "inject_noise_and_truncate_title", "details": f"Corrupted paper_id: {c_df.loc[1, 'paper_id']}"})

    # 4. Make date stale
    if len(c_df) > 2:
        c_df.loc[2, "published"] = "2010-01-01"
        c_df.loc[2, "age_days"] = 5000
        logs.append({"action": "make_date_stale", "details": f"Set published date to 2010-01-01 for paper_id: {c_df.loc[2, 'paper_id']}"})

    # 5. Add duplicate rows
    if len(c_df) > 3:
        dup_row = c_df.iloc[[3]].copy()
        c_df = pd.concat([c_df, dup_row], ignore_index=True)
        logs.append({"action": "add_duplicate_row", "details": f"Duplicated row for paper_id: {dup_row.iloc[0]['paper_id']}"})

    # 6. Rebuild text_for_embedding with corrupted text
    rebuilt_texts = []
    for _, row in c_df.iterrows():
        summary_val = row["summary"] if row["summary"] else "No summary available."
        text = (
            f"Title: {row['title']}\n"
            f"Summary: {summary_val}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}"
        )
        rebuilt_texts.append(text)

    c_df["text_for_embedding"] = rebuilt_texts

    write_json(Path(output_log_path), {"corruptions": logs, "total_corrupted_rows": len(c_df)})
    return c_df


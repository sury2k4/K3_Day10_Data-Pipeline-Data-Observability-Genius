from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


from core.utils import compact_join, normalize_whitespace


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    rows = []
    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        if not title:
            continue

        authors_list = [normalize_whitespace(a) for a in r.authors if normalize_whitespace(a)]
        categories_list = [normalize_whitespace(c) for c in r.categories if normalize_whitespace(c)]

        authors_joined = compact_join(authors_list, sep=", ") or "Unknown Author"
        categories_joined = compact_join(categories_list, sep=", ") or "General"
        primary_category = r.primary_category or (categories_list[0] if categories_list else "General")

        try:
            pub_dt = datetime.strptime(r.published[:10], "%Y-%m-%d")
        except Exception:
            pub_dt = datetime(2024, 1, 1)

        run_dt_naive = run_date.replace(tzinfo=None) if run_date.tzinfo else run_date
        age_days = max(0, (run_dt_naive - pub_dt).days)

        summary_chars = len(summary)
        text_for_embedding = (
            f"Title: {title}\n"
            f"Summary: {summary if summary else 'No summary available.'}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}"
        )

        rows.append(
            {
                "paper_id": r.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors_list,
                "categories": categories_list,
                "primary_category": primary_category,
                "published": r.published[:10],
                "updated": r.updated[:10],
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Drop duplicates by paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first").reset_index(drop=True)
    # Sort by published date descending
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df


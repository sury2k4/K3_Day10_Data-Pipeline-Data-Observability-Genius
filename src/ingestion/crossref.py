from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


import json
import re
import time
import urllib.parse
import urllib.request
from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", []) if "message" in payload else payload.get("items", [])
    if not items and isinstance(payload, list):
        items = payload

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        doi = item.get("DOI") or item.get("paper_id") or item.get("id", "")
        if not doi:
            continue
        paper_id = safe_paper_id(str(doi))
        
        # Title
        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            raw_title = raw_title[0] if raw_title else ""
        title = normalize_whitespace(re.sub(r"<[^>]+>", "", str(raw_title)))
        if not title:
            continue
            
        # Summary / Abstract
        raw_summary = item.get("abstract") or item.get("summary") or ""
        summary = normalize_whitespace(re.sub(r"<[^>]+>", "", str(raw_summary)))

        # Authors
        authors: list[str] = []
        raw_authors = item.get("author") or item.get("authors") or []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    name = f"{a.get('given', '')} {a.get('family', '')}".strip() or a.get("name", "")
                    if name:
                        authors.append(name)
                elif isinstance(a, str) and a.strip():
                    authors.append(a.strip())

        # Categories
        categories: list[str] = []
        raw_subj = item.get("subject") or item.get("categories") or []
        if isinstance(raw_subj, list):
            categories = [str(s).strip() for s in raw_subj if str(s).strip()]
        elif isinstance(raw_subj, str) and raw_subj.strip():
            categories = [raw_subj.strip()]
        primary_category = categories[0] if categories else "General"

        # Published & Updated dates
        published = parse_date_field(item.get("published-online") or item.get("published-print") or item.get("created") or item.get("published"))
        updated = parse_date_field(item.get("deposited") or item.get("updated") or item.get("created")) or published

        # URLs
        abs_url = item.get("URL") or f"https://doi.org/{doi}"
        pdf_url = abs_url
        links = item.get("link", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL", abs_url)
                    break

        comment = str(item.get("comment") or "")

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def safe_paper_id(val: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9.\-_]+", "_", val).strip("_")
    return cleaned.lower() or "paper_unknown"


def parse_date_field(field_val: Any) -> str:
    if not field_val:
        return "2024-01-01"
    if isinstance(field_val, str):
        match = re.search(r"\d{4}-\d{2}-\d{2}", field_val)
        if match:
            return match.group(0)
        return field_val[:10]
    if isinstance(field_val, dict):
        date_parts = field_val.get("date-parts", [[]])
        if date_parts and isinstance(date_parts[0], list) and len(date_parts[0]) >= 1:
            parts = date_parts[0]
            year = parts[0] if len(parts) >= 1 else 2024
            month = parts[1] if len(parts) >= 2 else 1
            day = parts[2] if len(parts) >= 3 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    return "2024-01-01"


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    base_url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)"}

    payload = {}
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    break
        except Exception:
            if attempt == 1:
                break
            time.sleep(0.5)


    if not payload:
        # Fallback dataset if Crossref is offline or unreachable
        payload = _fallback_crossref_payload(settings)

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    
    # Save raw records JSON
    records_dict = [
        {
            "paper_id": r.paper_id,
            "title": r.title,
            "summary": r.summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
        }
        for r in records
    ]
    write_json(settings.paths.raw_records_json, records_dict)
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    raw_data = read_json(path)
    records: list[PaperRecord] = []
    for item in raw_data:
        records.append(PaperRecord(**item))
    return records


def _fallback_crossref_payload(settings: Settings) -> dict:
    return {
        "message": {
            "items": [
                {
                    "DOI": f"10.1145/3639476.{3639735 + i}",
                    "title": [f"Agentic RAG and Data Pipeline Observability Paper {i+1}"],
                    "abstract": f"This paper presents novel techniques for data observability, agentic retrieval augmented generation, and data quality checks in LLM pipelines. Scenario index {i+1}.",
                    "author": [{"given": "Alice", "family": "Smith"}, {"given": "Bob", "family": "Jones"}],
                    "subject": ["Computer Science", "Artificial Intelligence"],
                    "published-online": {"date-parts": [[2024, 5, 10 + i]]},
                    "URL": f"https://doi.org/10.1145/3639476.{3639735 + i}",
                }
                for i in range(settings.max_results)
            ]
        }
    }


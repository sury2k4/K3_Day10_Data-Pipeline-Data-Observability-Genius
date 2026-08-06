from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import time
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from core.config import Settings


CROSSREF_API_URL = "https://api.crossref.org/works"
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
REQUEST_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


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


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref API payload into stable raw paper records."""
    message = payload.get("message")
    if not isinstance(message, dict):
        return []

    items = message.get("items")
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title = _first_non_empty_string(item.get("title"))
        if not title:
            continue

        doi = _normalize_doi(item.get("DOI"))
        paper_id = doi or _stable_fallback_id(item, title)
        if not paper_id:
            continue

        categories = _extract_categories(item)
        published = _extract_published(item)

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_strip_if_string(item.get("abstract")),
                authors=_extract_authors(item),
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=_extract_updated(item, published),
                abs_url=_extract_abs_url(item, doi),
                pdf_url=_extract_pdf_url(item),
                comment=_first_non_empty_string(item.get("subtitle")),
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref records, persist raw artifacts, and return parsed records."""
    session = requests.Session()
    params: dict[str, Any] = {
        "query.bibliographic": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "sort": "published",
        "order": "desc",
    }
    mailto = os.getenv("CROSSREF_MAILTO", "").strip()
    if mailto:
        params["mailto"] = mailto

    headers = {
        "Accept": "application/json",
        "User-Agent": "K3-Day10-Data-Observability/1.0",
    }

    response = _request_crossref_with_retry(session, params, headers)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Crossref response JSON must be a dictionary.")

    _write_json(settings.paths.raw_api_response, payload)
    logger.info("Saved raw Crossref payload to %s", settings.paths.raw_api_response)

    records = parse_crossref_payload(payload)
    _write_json(settings.paths.raw_records_json, [dataclasses.asdict(record) for record in records])
    logger.info("Parsed %s Crossref records.", len(records))
    logger.info("Saved raw Crossref records to %s", settings.paths.raw_records_json)
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a saved raw records snapshot into PaperRecord objects."""
    if not path.exists():
        raise FileNotFoundError(f"Raw records file does not exist: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("top-level JSON value must be a list")

        records: list[PaperRecord] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"record at index {index} must be a dictionary")
            records.append(PaperRecord(**item))
        return records
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid raw records file {path}: {exc}") from exc


def _first_non_empty_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def _strip_if_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_doi(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    doi = value.strip().lower()
    for prefix in ("doi:", "https://doi.org/", "http://doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :].strip()
    return doi


def _extract_authors(item: dict[str, Any]) -> list[str]:
    authors = item.get("author", [])
    if not isinstance(authors, list):
        return []

    names: list[str] = []
    for author in authors:
        if not isinstance(author, dict):
            continue
        organization_name = _strip_if_string(author.get("name"))
        if organization_name:
            names.append(organization_name)
            continue

        parts = [_strip_if_string(author.get("given")), _strip_if_string(author.get("family"))]
        name = " ".join(part for part in parts if part)
        if name:
            names.append(name)
    return names


def _extract_categories(item: dict[str, Any]) -> list[str]:
    subjects = item.get("subject", [])
    if not isinstance(subjects, list):
        return []
    return [subject.strip() for subject in subjects if isinstance(subject, str) and subject.strip()]


def _extract_crossref_date(value: Any) -> str:
    """Convert Crossref date-parts/date-time shapes to YYYY-MM-DD."""
    if not isinstance(value, dict):
        return ""

    date_time = value.get("date-time")
    if isinstance(date_time, str):
        parsed = _date_time_to_iso_date(date_time)
        if parsed:
            return parsed

    date_parts = value.get("date-parts")
    if not isinstance(date_parts, list) or not date_parts or not isinstance(date_parts[0], list):
        return ""

    parts = date_parts[0]
    if not parts:
        return ""

    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return date(year, month, day).isoformat()
    except (TypeError, ValueError):
        return ""


def _date_time_to_iso_date(value: str) -> str:
    candidate = value[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return ""


def _extract_published(item: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parsed = _extract_crossref_date(item.get(key))
        if parsed:
            return parsed
    return ""


def _extract_updated(item: dict[str, Any], published: str) -> str:
    for key in ("indexed", "deposited", "created"):
        value = item.get(key)
        if isinstance(value, dict):
            parsed = _date_time_to_iso_date(_strip_if_string(value.get("date-time")))
            if parsed:
                return parsed
    return published


def _extract_abs_url(item: dict[str, Any], doi: str) -> str:
    url = _strip_if_string(item.get("URL"))
    if url:
        return url
    if doi:
        return f"https://doi.org/{doi}"
    return ""


def _extract_pdf_url(item: dict[str, Any]) -> str:
    links = item.get("link", [])
    if not isinstance(links, list):
        return ""

    for link in links:
        if not isinstance(link, dict):
            continue
        url = _strip_if_string(link.get("URL"))
        if not url:
            continue
        content_type = _strip_if_string(link.get("content-type")).lower()
        lower_url = url.lower()
        if content_type == "application/pdf" or lower_url.endswith(".pdf") or "/pdf" in lower_url:
            return url
    return ""


def _stable_fallback_id(item: dict[str, Any], title: str) -> str:
    """Build a deterministic ID when Crossref omits DOI."""
    normalized_title = " ".join(title.lower().split())
    published_date = _extract_published(item)
    publisher = _strip_if_string(item.get("publisher")).lower()
    digest = hashlib.sha256(f"{normalized_title}|{published_date}|{publisher}".encode("utf-8")).hexdigest()
    return f"crossref:{digest[:24]}"


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _request_crossref_with_retry(
    session: requests.Session,
    params: dict[str, Any],
    headers: dict[str, str],
) -> requests.Response:
    last_exception: requests.RequestException | None = None
    last_response: requests.Response | None = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = session.get(
                CROSSREF_API_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code not in RETRY_STATUS_CODES:
                return response

            last_response = response
            if attempt == MAX_ATTEMPTS - 1:
                break

            delay = _retry_delay(response, attempt)
            logger.warning(
                "Crossref returned HTTP %s; retry attempt %s/%s in %.2fs.",
                response.status_code,
                attempt + 1,
                MAX_ATTEMPTS - 1,
                delay,
            )
            time.sleep(delay)
        except requests.RequestException as exc:
            last_exception = exc
            if attempt == MAX_ATTEMPTS - 1:
                break

            delay = _retry_delay(None, attempt)
            logger.warning(
                "Crossref network error on retry attempt %s/%s; waiting %.2fs: %s",
                attempt + 1,
                MAX_ATTEMPTS - 1,
                delay,
                exc,
            )
            time.sleep(delay)

    if last_response is not None:
        try:
            last_response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"Crossref request failed after {MAX_ATTEMPTS} attempts with HTTP {last_response.status_code}."
            ) from exc

    raise RuntimeError(f"Crossref request failed after {MAX_ATTEMPTS} attempts.") from last_exception


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
    return min(1.0 * (2**attempt) + random.uniform(0, 0.5), 60.0)

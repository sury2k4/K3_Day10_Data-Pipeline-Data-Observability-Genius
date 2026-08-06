from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingestion.crossref import PaperRecord, fetch_source_records, load_raw_records, parse_crossref_payload


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _valid_payload() -> dict:
    return {
        "message": {
            "items": [
                {
                    "DOI": "https://doi.org/10.1234/ABC",
                    "title": ["A Useful RAG Paper"],
                    "abstract": "  <jats:p>Useful abstract.</jats:p>  ",
                    "author": [
                        {"given": "John", "family": "Smith"},
                        {"given": "Jane", "family": "Doe"},
                    ],
                    "subject": ["Information Retrieval", "Machine Learning"],
                    "published-online": {"date-parts": [[2026, 8, 6]]},
                    "indexed": {"date-time": "2026-08-07T12:00:00Z"},
                    "URL": "https://doi.org/10.1234/abc",
                    "link": [{"content-type": "application/pdf", "URL": "https://example.org/paper.pdf"}],
                    "subtitle": ["Short subtitle"],
                }
            ]
        }
    }


def _settings(tmp_path):
    return SimpleNamespace(
        source_query="agentic rag",
        source_filter="from-pub-date:2026-01-01,has-abstract:true",
        max_results=2,
        paths=SimpleNamespace(
            raw_api_response=tmp_path / "raw" / "crossref_response.json",
            raw_records_json=tmp_path / "raw" / "crossref_records.json",
        ),
    )


def test_parse_valid_payload_maps_all_fields() -> None:
    records = parse_crossref_payload(_valid_payload())

    assert records == [
        PaperRecord(
            paper_id="10.1234/abc",
            title="A Useful RAG Paper",
            summary="<jats:p>Useful abstract.</jats:p>",
            authors=["John Smith", "Jane Doe"],
            categories=["Information Retrieval", "Machine Learning"],
            primary_category="Information Retrieval",
            published="2026-08-06",
            updated="2026-08-07",
            abs_url="https://doi.org/10.1234/abc",
            pdf_url="https://example.org/paper.pdf",
            comment="Short subtitle",
        )
    ]


def test_parse_missing_optional_fields() -> None:
    payload = {"message": {"items": [{"DOI": "10.5555/example", "title": ["Only Title"]}]}}

    record = parse_crossref_payload(payload)[0]

    assert record.summary == ""
    assert record.authors == []
    assert record.categories == []
    assert record.primary_category == ""
    assert record.published == ""
    assert record.pdf_url == ""
    assert record.comment == ""


def test_fallback_id_is_stable_without_doi() -> None:
    payload = {
        "message": {
            "items": [
                {
                    "title": ["No DOI Paper"],
                    "published": {"date-parts": [[2026]]},
                    "publisher": "Example Publisher",
                }
            ]
        }
    }

    record_1 = parse_crossref_payload(payload)[0]
    record_2 = parse_crossref_payload(payload)[0]

    assert record_1.paper_id == record_2.paper_id
    assert record_1.paper_id.startswith("crossref:")


def test_parse_skips_record_without_title() -> None:
    payload = {"message": {"items": [{"DOI": "10.5555/missing-title", "title": ["  "]}]}}

    assert parse_crossref_payload(payload) == []


@patch("ingestion.crossref.time.sleep")
@patch("ingestion.crossref.requests.Session")
def test_fetch_retries_429(mock_session_cls: MagicMock, mock_sleep: MagicMock, tmp_path) -> None:
    session = mock_session_cls.return_value
    session.get.side_effect = [FakeResponse(429, headers={"Retry-After": "0"}), FakeResponse(200, _valid_payload())]

    records = fetch_source_records(_settings(tmp_path))

    assert len(records) == 1
    assert session.get.call_count == 2
    mock_sleep.assert_called_once_with(0.0)


@patch("ingestion.crossref.time.sleep")
@patch("ingestion.crossref.random.uniform", return_value=0)
@patch("ingestion.crossref.requests.Session")
def test_fetch_retries_503(mock_session_cls: MagicMock, mock_uniform: MagicMock, mock_sleep: MagicMock, tmp_path) -> None:
    session = mock_session_cls.return_value
    session.get.side_effect = [FakeResponse(503), FakeResponse(503), FakeResponse(200, _valid_payload())]

    records = fetch_source_records(_settings(tmp_path))

    assert len(records) == 1
    assert session.get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("ingestion.crossref.requests.Session")
def test_fetch_does_not_retry_400(mock_session_cls: MagicMock, tmp_path) -> None:
    session = mock_session_cls.return_value
    session.get.return_value = FakeResponse(400)

    with pytest.raises(requests.HTTPError):
        fetch_source_records(_settings(tmp_path))

    assert session.get.call_count == 1


@patch("ingestion.crossref.requests.Session")
def test_fetch_saves_artifacts(mock_session_cls: MagicMock, tmp_path) -> None:
    settings = _settings(tmp_path)
    session = mock_session_cls.return_value
    session.get.return_value = FakeResponse(200, _valid_payload())

    fetch_source_records(settings)

    assert settings.paths.raw_api_response.exists()
    assert settings.paths.raw_records_json.exists()
    assert isinstance(json.loads(settings.paths.raw_api_response.read_text(encoding="utf-8")), dict)
    assert isinstance(json.loads(settings.paths.raw_records_json.read_text(encoding="utf-8")), list)


def test_load_raw_records(tmp_path) -> None:
    path = tmp_path / "records.json"
    record = parse_crossref_payload(_valid_payload())[0]
    path.write_text(json.dumps([record.__dict__]), encoding="utf-8")

    records = load_raw_records(path)

    assert records == [record]
    assert isinstance(records[0], PaperRecord)

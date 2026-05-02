import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_SUBMISSIONS = {
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "form": ["10-K", "10-Q", "10-K"],
            "accessionNumber": ["0000320193-24-000123", "0000320193-24-000099", "0000320193-23-000050"],
            "filingDate": ["2024-11-01", "2024-08-01", "2023-11-03"],
            "primaryDocument": ["aapl-20240928.htm", "aapl-20240629.htm", "aapl-20230930.htm"],
        }
    },
}

MOCK_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}


def _make_mock(json_data):
    m = MagicMock()
    m.json.return_value = json_data
    return m


@patch("app.services.filing_service.edgar_client")
@patch("app.services.company_service.edgar_client")
def test_latest_filing_10k(mock_company_client, mock_filing_client):
    efts_resp = _make_mock({"hits": {"hits": []}})
    tickers_resp = _make_mock(MOCK_TICKERS)
    submissions_resp = _make_mock(MOCK_SUBMISSIONS)

    mock_company_client.get = AsyncMock(side_effect=[efts_resp, tickers_resp])
    mock_filing_client.get = AsyncMock(return_value=submissions_resp)

    resp = client.get("/filings/latest?company=Apple+Inc.&form_type=10-K")
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["company"] == "Apple Inc."
    assert data["form_type"] == "10-K"
    assert data["filed_date"] == "2024-11-01"
    assert "aapl-20240928.htm" in data["document_url"]


@patch("app.services.filing_service.edgar_client")
@patch("app.services.company_service.edgar_client")
def test_latest_filing_not_found(mock_company_client, mock_filing_client):
    efts_resp = _make_mock({"hits": {"hits": []}})
    tickers_resp = _make_mock(MOCK_TICKERS)
    submissions_resp = _make_mock({
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "form": ["10-K"],
                "accessionNumber": ["0000320193-24-000123"],
                "filingDate": ["2024-11-01"],
                "primaryDocument": ["doc.htm"],
            }
        },
    })

    mock_company_client.get = AsyncMock(side_effect=[efts_resp, tickers_resp])
    mock_filing_client.get = AsyncMock(return_value=submissions_resp)

    resp = client.get("/filings/latest?company=Apple&form_type=8-K")
    assert resp.status_code == 404, resp.json()


def test_invalid_form_type():
    resp = client.get("/filings/latest?company=Apple&form_type=INVALID")
    assert resp.status_code == 400


def test_missing_company_param():
    resp = client.get("/filings/latest")
    assert resp.status_code == 422

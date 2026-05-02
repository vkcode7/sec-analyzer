import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.services.company_service.edgar_client")
def test_search_returns_results(mock_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "0000320193:something",
                    "_source": {"entity_name": "Apple Inc.", "file_num": "0-12345"},
                }
            ]
        }
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    resp = client.get("/companies/search?q=apple")
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Apple Inc."
    assert data[0]["cik"] == "0000320193"


def test_search_empty_query():
    resp = client.get("/companies/search?q=")
    assert resp.status_code == 400


def test_search_missing_query():
    resp = client.get("/companies/search")
    assert resp.status_code == 422


@patch("app.services.company_service.edgar_client")
def test_search_falls_back_to_tickers(mock_client):
    """When EFTS returns empty hits, falls back to company_tickers.json"""
    efts_response = MagicMock()
    efts_response.json.return_value = {"hits": {"hits": []}}

    tickers_response = MagicMock()
    tickers_response.json.return_value = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }

    mock_client.get = AsyncMock(side_effect=[efts_response, tickers_response])

    resp = client.get("/companies/search?q=apple")
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert any(c["ticker"] == "AAPL" for c in data)

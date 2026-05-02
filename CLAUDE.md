# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

All commands must use the `fenv` virtualenv located at `sec-analyzer/fenv/`:

```bash
# Run the server
fenv/bin/uvicorn app.main:app --reload

# Run all tests
fenv/bin/pytest tests/ -v

# Run a single test
fenv/bin/pytest tests/test_companies.py::test_search_returns_results -v

# Install dependencies
fenv/bin/pip install -r requirements.txt
fenv/bin/pip install -r requirements-dev.txt
```

The project runs on **Python 3.9**. Use `Optional[X]` instead of `X | None` — the `X | None` union syntax requires Python 3.10+, and Pydantic v2 on 3.9 does not support it even with `from __future__ import annotations`.

## Architecture

Request flow: `routers/` → `services/` → `edgar_client.py` → SEC EDGAR APIs

- **`app/main.py`** — FastAPI app with `lifespan` context manager that calls `edgar_client.start()`/`stop()` to manage the shared `httpx.AsyncClient`.
- **`app/services/edgar_client.py`** — Singleton `EdgarClient` with `asyncio.Semaphore` rate limiting (8 req/sec). All HTTP calls go through its `.get()` method. Tests patch `app.services.<module>.edgar_client` directly.
- **`app/services/company_service.py`** — `search_companies()` tries EFTS full-text search first, falls back to filtering `company_tickers.json`. `resolve_cik()` is used by the filing service to turn a name/CIK string into a zero-padded 10-digit CIK.
- **`app/services/filing_service.py`** — Fetches `submissions/CIK{cik}.json`, finds the most recent filing of the requested form type, and builds the document URL from the `primaryDocument` field (or falls back to fetching the index page).
- **`app/config.py`** — `Settings` (Pydantic `BaseSettings`) with SEC API base URLs and rate limit. Override via env vars or `.env` file.

## SEC EDGAR APIs

| Purpose | URL |
|---|---|
| Company search | `https://efts.sec.gov/LATEST/search-index?q=&entity={name}` |
| Ticker/CIK map | `https://www.sec.gov/files/company_tickers.json` |
| Filing history | `https://data.sec.gov/submissions/CIK{10-digit-cik}.json` |
| Filing archive | `https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{filename}` |

Rate limit: 10 req/sec. The `User-Agent` header (`SECAnalyzer admin@example.com`) is required on all requests.

## Testing Approach

Tests use `fastapi.testclient.TestClient` (sync) with `unittest.mock.patch` to replace the `edgar_client` singleton in each service module. Mock responses use `MagicMock` (not `AsyncMock`) for the response object itself, with `AsyncMock` only on the `.get()` method.

## Testing via Browser UI (uses swagger)

From the project directory:
```bash
cd /Users/vk/repo/sec-analyzer
fenv/bin/uvicorn app.main:app --reload
```
Then open your browser to:
- Interactive API docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

The Swagger UI lets you expand each endpoint, click "Try it out", fill in
parameters, and execute real requests against the live SEC EDGAR APIs
directly from the browser. No curl needed.

Quick tests to try:
  1. GET /companies/search → set q to Apple
  2. GET /filings/latest → set company to Apple Inc. and form_type to 10-K
  3. GET /health → should return {"status": "ok"}


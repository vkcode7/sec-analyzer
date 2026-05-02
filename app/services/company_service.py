from app.models.company import Company
from app.services.edgar_client import edgar_client
from app.config import settings


async def search_companies(query: str) -> list[Company]:
    """Search companies by name using EDGAR full-text search, falling back to tickers JSON."""
    try:
        url = (
            f"{settings.sec_efts_url}/LATEST/search-index"
            f"?q=&entity={query}"
            f"&hits.hits._source=period_of_report,entity_name,file_num,biz_location,inc_states"
        )
        resp = await edgar_client.get(url)
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        seen_ciks: set[str] = set()
        results: list[Company] = []
        for hit in hits:
            src = hit.get("_source", {})
            entity_name = src.get("entity_name", "")
            file_num = src.get("file_num", "")
            # CIK is embedded in _id field like "0000320193"
            cik = hit.get("_id", "").split(":")[0] if ":" in hit.get("_id", "") else ""
            if not cik:
                continue
            if cik in seen_ciks:
                continue
            seen_ciks.add(cik)
            results.append(Company(cik=cik, name=entity_name))
        if results:
            return results
    except Exception:
        pass

    # Fallback: filter company_tickers.json
    return await _search_tickers_json(query)


async def _search_tickers_json(query: str) -> list[Company]:
    url = f"{settings.sec_www_url}/files/company_tickers.json"
    resp = await edgar_client.get(url)
    data = resp.json()
    query_lower = query.lower()
    results: list[Company] = []
    for entry in data.values():
        name: str = entry.get("title", "")
        if query_lower in name.lower():
            cik = str(entry.get("cik_str", "")).zfill(10)
            ticker = entry.get("ticker", "")
            results.append(Company(cik=cik, name=name, ticker=ticker))
        if len(results) >= 20:
            break
    return results


async def resolve_cik(name_or_cik: str) -> tuple[str, str]:
    """Return (cik_10digit, company_name). Accepts CIK number or company name."""
    # If it looks like a CIK (all digits), pad and return
    stripped = name_or_cik.strip()
    if stripped.isdigit():
        return stripped.zfill(10), stripped

    companies = await search_companies(stripped)
    if not companies:
        # Try tickers.json direct ticker match
        companies = await _search_tickers_json(stripped)
    if not companies:
        raise ValueError(f"Company not found: {name_or_cik}")
    best = companies[0]
    return best.cik.zfill(10), best.name

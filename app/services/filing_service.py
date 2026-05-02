import re
from typing import Optional
from app.models.filing import Filing
from app.services.edgar_client import edgar_client
from app.services.company_service import resolve_cik
from app.config import settings


async def get_latest_filing(company: str, form_type: str = "10-K") -> Filing:
    cik, company_name = await resolve_cik(company)
    cik_int = str(int(cik))  # remove leading zeros for archive URLs

    submissions_url = f"{settings.sec_base_url}/submissions/CIK{cik}.json"
    resp = await edgar_client.get(submissions_url)
    data = resp.json()

    company_name = data.get("name", company_name)

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    dates = filings.get("filingDate", [])
    primary_docs = filings.get("primaryDocument", [])

    best_idx = None
    best_date = ""
    for i, form in enumerate(forms):
        if form == form_type:
            filing_date = dates[i] if i < len(dates) else ""
            if filing_date > best_date:
                best_date = filing_date
                best_idx = i

    if best_idx is None:
        raise ValueError(f"No {form_type} filing found for {company_name}")

    accession = accessions[best_idx]
    primary_doc = primary_docs[best_idx] if best_idx < len(primary_docs) else ""
    accession_nodash = accession.replace("-", "")

    doc_url = await _resolve_document_url(cik_int, accession_nodash, primary_doc)

    return Filing(
        company=company_name,
        cik=cik,
        form_type=form_type,
        filed_date=best_date,
        document_url=doc_url,
    )


async def _resolve_document_url(cik: str, accession_nodash: str, primary_doc: str) -> Optional[str]:
    base = f"{settings.sec_www_url}/Archives/edgar/data/{cik}/{accession_nodash}"

    if primary_doc:
        return f"{base}/{primary_doc}"

    index_url = f"{base}/{accession_nodash}-index.htm"
    try:
        resp = await edgar_client.get(index_url)
        text = resp.text
        htm_matches = re.findall(r'href="([^"]+\.htm)"', text, re.IGNORECASE)
        pdf_matches = re.findall(r'href="([^"]+\.pdf)"', text, re.IGNORECASE)
        candidates = htm_matches or pdf_matches
        if candidates:
            first = candidates[0]
            if first.startswith("http"):
                return first
            if first.startswith("/"):
                return f"{settings.sec_www_url}{first}"
            return f"{base}/{first}"
    except Exception:
        pass

    return f"{base}/{accession_nodash}-index.htm"

from fastapi import APIRouter, Query, HTTPException
from app.models.filing import Filing
from app.services.filing_service import get_latest_filing
from typing import Literal

router = APIRouter(prefix="/filings", tags=["filings"])

SUPPORTED_FORMS = {"10-K", "10-Q", "8-K"}


@router.get("/latest", response_model=Filing)
async def latest_filing(
    company: str = Query(..., description="Company name or CIK"),
    form_type: str = Query("10-K", description="SEC form type (10-K, 10-Q, 8-K)"),
):
    if form_type not in SUPPORTED_FORMS:
        raise HTTPException(
            status_code=400,
            detail=f"form_type must be one of {sorted(SUPPORTED_FORMS)}",
        )
    try:
        return await get_latest_filing(company, form_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

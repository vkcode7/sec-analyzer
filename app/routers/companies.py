from fastapi import APIRouter, Query, HTTPException
from app.models.company import Company
from app.services.company_service import search_companies

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/search", response_model=list[Company])
async def search(q: str = Query(..., description="Company name to search")):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty")
    try:
        return await search_companies(q)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

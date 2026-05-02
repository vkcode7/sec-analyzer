from typing import Optional
from pydantic import BaseModel


class Filing(BaseModel):
    company: str
    cik: str
    form_type: str
    filed_date: str
    document_url: Optional[str] = None

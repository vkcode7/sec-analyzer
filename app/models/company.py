from typing import Optional
from pydantic import BaseModel


class Company(BaseModel):
    cik: str
    name: str
    ticker: Optional[str] = None

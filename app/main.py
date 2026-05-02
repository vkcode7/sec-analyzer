from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.edgar_client import edgar_client
from app.routers import companies, filings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await edgar_client.start()
    yield
    await edgar_client.stop()


app = FastAPI(
    title="SEC Financial Statements Analyzer",
    description="REST API for searching SEC EDGAR filings",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(companies.router)
app.include_router(filings.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

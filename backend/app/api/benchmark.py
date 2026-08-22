from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from scripts.benchmark import run_benchmark

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

class BenchmarkRequest(BaseModel):
    queries: Optional[list[str]] = None

@router.post("/run")
async def run_benchmark_endpoint(req: BenchmarkRequest = None):
    queries = req.queries if req and req.queries else None
    result = await run_benchmark(queries)
    return result

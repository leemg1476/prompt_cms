from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.prompts import WorkerRunResult
from app.services.worker_service import run_worker_once

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.post("/run-once", response_model=WorkerRunResult)
def trigger_worker_run(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> WorkerRunResult:
    return run_worker_once(db, limit=limit)

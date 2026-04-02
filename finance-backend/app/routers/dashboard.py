from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import require_any_role
from app.models.user import User
from app.schemas.transaction import TransactionResponse
from app.services.dashboard_service import (
    get_by_category,
    get_monthly_trends,
    get_recent_transactions,
    get_summary,
    get_weekly_trends,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_summary(db)


@router.get("/by-category")
def by_category(
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_by_category(db)


@router.get("/trends/monthly")
def monthly_trends(
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_monthly_trends(db)


@router.get("/trends/weekly")
def weekly_trends(
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_weekly_trends(db)


@router.get("/recent", response_model=list[TransactionResponse])
def recent(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_recent_transactions(db, limit=limit)

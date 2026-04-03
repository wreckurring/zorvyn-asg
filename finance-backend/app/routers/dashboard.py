from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import require_admin, require_any_role
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.budget import BudgetStatus
from app.schemas.dashboard import (
    AnomalyRecord,
    CategoryBreakdown,
    InsightsResponse,
    SummaryResponse,
    TrendPeriod,
)
from app.schemas.transaction import TransactionResponse
from app.services.budget_service import get_budget_status
from app.services.dashboard_service import (
    get_anomalies,
    get_by_category,
    get_categories,
    get_insights,
    get_monthly_trends,
    get_recent_transactions,
    get_summary,
    get_weekly_trends,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=SummaryResponse)
def summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from must not be after date_to")
    return get_summary(db, date_from=date_from, date_to=date_to)


@router.get("/by-category", response_model=list[CategoryBreakdown])
def by_category(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from must not be after date_to")
    return get_by_category(db, date_from=date_from, date_to=date_to)


@router.get("/categories", response_model=list[str])
def categories(
    type: TransactionType | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_categories(db, type=type)


@router.get("/trends/monthly", response_model=list[TrendPeriod])
def monthly_trends(db: Session = Depends(get_db), _: User = Depends(require_any_role)):
    return get_monthly_trends(db)


@router.get("/trends/weekly", response_model=list[TrendPeriod])
def weekly_trends(db: Session = Depends(get_db), _: User = Depends(require_any_role)):
    return get_weekly_trends(db)


@router.get("/recent", response_model=list[TransactionResponse])
def recent(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_recent_transactions(db, limit=limit)


@router.get("/anomalies", response_model=list[AnomalyRecord])
def anomalies(
    z_threshold: float = Query(2.0, ge=1.0, le=4.0, description="Z-score cutoff (default 2.0 = top ~2.5% of spend per category)"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_anomalies(db, z_threshold=z_threshold)


@router.get("/insights", response_model=InsightsResponse)
def insights(db: Session = Depends(get_db), _: User = Depends(require_any_role)):
    return get_insights(db)


@router.get("/budget-status", response_model=list[BudgetStatus])
def budget_status(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Month in YYYY-MM format"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    return get_budget_status(db, month=month)

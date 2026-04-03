from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import get_current_user, require_admin, require_analyst_or_admin
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetResponse
from app.services.budget_service import (
    create_budget,
    delete_budget,
    get_budget_by_category_month,
    get_budget_by_id,
    get_budgets,
    update_budget_limit,
)

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetResponse])
def list_budgets(
    month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_budgets(db, month=month)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    if get_budget_by_category_month(db, data.category, data.month):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A budget for '{data.category}' in {data.month} already exists",
        )
    return create_budget(db, data, created_by=current_user.id)


@router.patch("/{budget_id}", response_model=BudgetResponse)
def update(
    budget_id: int,
    monthly_limit: float,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    budget = get_budget_by_id(db, budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    if monthly_limit <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="monthly_limit must be greater than zero")
    return update_budget_limit(db, budget, monthly_limit)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    budget_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    budget = get_budget_by_id(db, budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    delete_budget(db, budget)

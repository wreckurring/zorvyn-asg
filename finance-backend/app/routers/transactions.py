from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import require_admin, require_analyst_or_admin, require_any_role
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    get_transactions,
    soft_delete_transaction,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    type: TransactionType | None = Query(None),
    category: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    return get_transactions(db, type=type, category=category, date_from=date_from, date_to=date_to, skip=skip, limit=limit)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return create_transaction(db, data, created_by=current_user.id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return update_transaction(db, txn, data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    soft_delete_transaction(db, txn)

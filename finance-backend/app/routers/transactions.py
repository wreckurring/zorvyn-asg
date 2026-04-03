import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import require_admin, require_analyst_or_admin, require_any_role
from app.models.audit_log import AuditAction
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.audit_service import record
from app.services.transaction_service import (
    create_transaction,
    get_all_transactions_for_export,
    get_transaction_by_id,
    get_transaction_stats,
    get_transactions,
    soft_delete_transaction,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/export")
def export_csv(
    type: TransactionType | None = Query(None),
    category: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must not be after date_to",
        )

    rows = get_all_transactions_for_export(db, type=type, category=category, date_from=date_from, date_to=date_to)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "type", "category", "amount", "notes", "created_by", "created_at"])
    for t in rows:
        writer.writerow([t.id, t.date, t.type.value, t.category, t.amount, t.notes or "", t.created_by, t.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/stats")
def stats(
    type: TransactionType | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must not be after date_to",
        )
    return get_transaction_stats(db, type=type, date_from=date_from, date_to=date_to)


@router.get("", response_model=PaginatedTransactions)
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
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must not be after date_to",
        )
    total, results = get_transactions(
        db, type=type, category=category, date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )
    return PaginatedTransactions(total=total, skip=skip, limit=limit, results=results)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    txn = create_transaction(db, data, created_by=current_user.id)
    record(db, current_user.id, AuditAction.create, "transaction", txn.id, f"category={txn.category} amount={txn.amount}")
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    updated = update_transaction(db, txn, data)
    changed = ", ".join(f"{k}={v}" for k, v in data.model_dump(exclude_unset=True).items())
    record(db, current_user.id, AuditAction.update, "transaction", transaction_id, changed)
    return updated


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    txn = get_transaction_by_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    soft_delete_transaction(db, txn)
    record(db, current_user.id, AuditAction.delete, "transaction", transaction_id)

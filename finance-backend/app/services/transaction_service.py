from datetime import date

from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def _build_transaction_query(
    db: Session,
    type: TransactionType | None,
    category: str | None,
    date_from: date | None,
    date_to: date | None,
):
    query = db.query(Transaction).filter(Transaction.is_deleted == False)
    if type:
        query = query.filter(Transaction.type == type)
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category}%"))
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    return query


def get_transactions(
    db: Session,
    type: TransactionType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, list[Transaction]]:
    query = _build_transaction_query(db, type, category, date_from, date_to)
    total = query.count()
    results = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return total, results


def get_all_transactions_for_export(
    db: Session,
    type: TransactionType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Transaction]:
    return (
        _build_transaction_query(db, type, category, date_from, date_to)
        .order_by(Transaction.date.desc())
        .all()
    )


def get_transaction_by_id(db: Session, transaction_id: int) -> Transaction | None:
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.is_deleted == False)
        .first()
    )


def create_transaction(db: Session, data: TransactionCreate, created_by: int) -> Transaction:
    txn = Transaction(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by=created_by,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def update_transaction(db: Session, txn: Transaction, data: TransactionUpdate) -> Transaction:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


def soft_delete_transaction(db: Session, txn: Transaction) -> Transaction:
    txn.is_deleted = True
    db.commit()
    db.refresh(txn)
    return txn

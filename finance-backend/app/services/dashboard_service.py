from collections import defaultdict
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType


def get_summary(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    query = db.query(Transaction.type, func.sum(Transaction.amount)).filter(Transaction.is_deleted == False)

    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)

    rows = query.group_by(Transaction.type).all()
    totals = {row[0]: row[1] for row in rows}
    income = totals.get(TransactionType.income, 0.0)
    expenses = totals.get(TransactionType.expense, 0.0)

    return {
        "total_income": income,
        "total_expenses": expenses,
        "net_balance": income - expenses,
    }


def get_by_category(db: Session) -> list[dict]:
    rows = (
        db.query(Transaction.category, Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
        .group_by(Transaction.category, Transaction.type)
        .order_by(Transaction.category)
        .all()
    )

    return [{"category": row[0], "type": row[1], "total": row[2]} for row in rows]


def _group_by_period(rows) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for period, txn_type, total in rows:
        if txn_type == TransactionType.income:
            grouped[period]["income"] = total
        else:
            grouped[period]["expenses"] = total
    return [{"period": p, **v} for p, v in sorted(grouped.items())]


def get_monthly_trends(db: Session) -> list[dict]:
    label = func.to_char(Transaction.date, "YYYY-MM").label("period")
    rows = (
        db.query(label, Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
        .group_by("period", Transaction.type)
        .order_by("period")
        .all()
    )
    return _group_by_period(rows)


def get_weekly_trends(db: Session) -> list[dict]:
    label = func.to_char(Transaction.date, "IYYY-IW").label("period")
    rows = (
        db.query(label, Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
        .group_by("period", Transaction.type)
        .order_by("period")
        .all()
    )
    return _group_by_period(rows)


def get_recent_transactions(db: Session, limit: int = 10) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.is_deleted == False)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

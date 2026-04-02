from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType


def get_summary(db: Session) -> dict:
    rows = (
        db.query(Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
        .group_by(Transaction.type)
        .all()
    )

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

    return [
        {"category": row[0], "type": row[1], "total": row[2]}
        for row in rows
    ]


def get_monthly_trends(db: Session) -> list[dict]:
    month_label = func.to_char(Transaction.date, "YYYY-MM").label("month")

    rows = (
        db.query(month_label, Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
        .group_by("month", Transaction.type)
        .order_by("month")
        .all()
    )

    grouped: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for month, txn_type, total in rows:
        if txn_type == TransactionType.income:
            grouped[month]["income"] = total
        else:
            grouped[month]["expenses"] = total

    return [
        {"month": month, **values}
        for month, values in sorted(grouped.items())
    ]


def get_recent_transactions(db: Session, limit: int = 10) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.is_deleted == False)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

from collections import defaultdict
from datetime import date, timedelta
from math import sqrt
from typing import Optional

from sqlalchemy import distinct, func
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


def get_by_category(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    query = (
        db.query(Transaction.category, Transaction.type, func.sum(Transaction.amount))
        .filter(Transaction.is_deleted == False)
    )

    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)

    rows = query.group_by(Transaction.category, Transaction.type).order_by(Transaction.category).all()
    return [{"category": row[0], "type": row[1], "total": row[2]} for row in rows]


def get_categories(db: Session, type: Optional[TransactionType] = None) -> list[str]:
    query = db.query(distinct(Transaction.category)).filter(Transaction.is_deleted == False)
    if type:
        query = query.filter(Transaction.type == type)
    rows = query.order_by(Transaction.category).all()
    return [row[0] for row in rows]


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


def get_anomalies(db: Session, z_threshold: float = 2.0) -> list[dict]:
    stats_rows = (
        db.query(
            Transaction.category,
            func.avg(Transaction.amount).label("avg"),
            func.stddev_pop(Transaction.amount).label("std"),
            func.count(Transaction.id).label("cnt"),
        )
        .filter(Transaction.is_deleted == False)
        .group_by(Transaction.category)
        .having(func.count(Transaction.id) >= 3)
        .all()
    )

    anomalies = []
    for stat in stats_rows:
        if stat.std is None or stat.std == 0:
            continue
        cutoff = stat.avg + z_threshold * stat.std
        flagged = (
            db.query(Transaction)
            .filter(
                Transaction.is_deleted == False,
                Transaction.category == stat.category,
                Transaction.amount > cutoff,
            )
            .all()
        )
        for txn in flagged:
            z_score = (txn.amount - stat.avg) / stat.std
            anomalies.append({
                "transaction_id": txn.id,
                "date": txn.date,
                "category": txn.category,
                "type": txn.type,
                "amount": txn.amount,
                "category_avg": round(stat.avg, 2),
                "category_std": round(stat.std, 2),
                "z_score": round(z_score, 2),
            })

    return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)


def get_insights(db: Session) -> dict:
    today = date.today()
    current_month = today.strftime("%Y-%m")
    current_month_start = today.replace(day=1)

    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
    prev_month_end = current_month_start - timedelta(days=1)

    overall = get_summary(db)
    current = get_summary(db, date_from=current_month_start)
    previous = get_summary(db, date_from=prev_month_start, date_to=prev_month_end)

    savings_rate = 0.0
    if overall["total_income"] > 0:
        savings_rate = round((overall["net_balance"] / overall["total_income"]) * 100, 1)

    expense_categories = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
        .filter(Transaction.is_deleted == False, Transaction.type == TransactionType.expense)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .first()
    )
    top_expense_category = expense_categories[0] if expense_categories else None

    mom_change_pct = None
    if previous["total_expenses"] > 0:
        mom_change_pct = round(
            ((current["total_expenses"] - previous["total_expenses"]) / previous["total_expenses"]) * 100, 1
        )

    total_txn_count = db.query(func.count(Transaction.id)).filter(Transaction.is_deleted == False).scalar()

    avg_transaction = (
        db.query(func.avg(Transaction.amount)).filter(Transaction.is_deleted == False).scalar()
    )

    largest_txn = (
        db.query(Transaction)
        .filter(Transaction.is_deleted == False)
        .order_by(Transaction.amount.desc())
        .first()
    )

    days_with_data = (
        db.query(func.count(func.distinct(Transaction.date)))
        .filter(Transaction.is_deleted == False)
        .scalar()
    ) or 1
    avg_daily_expense = round(overall["total_expenses"] / days_with_data, 2) if days_with_data else 0.0

    return {
        "savings_rate_pct": savings_rate,
        "top_expense_category": top_expense_category,
        "month_over_month_expense_change_pct": mom_change_pct,
        "current_month_net": current["net_balance"],
        "avg_transaction_amount": round(avg_transaction, 2) if avg_transaction else 0.0,
        "avg_daily_expense": avg_daily_expense,
        "total_transactions": total_txn_count,
        "largest_transaction_id": largest_txn.id if largest_txn else None,
        "largest_transaction_amount": largest_txn.amount if largest_txn else None,
    }

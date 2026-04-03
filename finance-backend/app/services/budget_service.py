from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import BudgetCreate, BudgetStatus


def get_budgets(db: Session, month: str | None = None) -> list[Budget]:
    query = db.query(Budget)
    if month:
        query = query.filter(Budget.month == month)
    return query.order_by(Budget.month.desc(), Budget.category).all()


def get_budget_by_id(db: Session, budget_id: int) -> Budget | None:
    return db.query(Budget).filter(Budget.id == budget_id).first()


def get_budget_by_category_month(db: Session, category: str, month: str) -> Budget | None:
    return db.query(Budget).filter(Budget.category == category, Budget.month == month).first()


def create_budget(db: Session, data: BudgetCreate, created_by: int) -> Budget:
    budget = Budget(
        category=data.category,
        monthly_limit=data.monthly_limit,
        month=data.month,
        created_by=created_by,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def update_budget_limit(db: Session, budget: Budget, monthly_limit: float) -> Budget:
    budget.monthly_limit = monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget: Budget) -> None:
    db.delete(budget)
    db.commit()


def get_budget_status(db: Session, month: str) -> list[BudgetStatus]:
    budgets = get_budgets(db, month=month)

    actuals_rows = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.expense,
            func.to_char(Transaction.date, "YYYY-MM") == month,
        )
        .group_by(Transaction.category)
        .all()
    )
    actuals = {row[0]: row[1] for row in actuals_rows}

    result = []
    seen_categories = set()

    for b in budgets:
        actual = actuals.get(b.category, 0.0)
        variance = b.monthly_limit - actual
        utilization = round((actual / b.monthly_limit) * 100, 1) if b.monthly_limit > 0 else 0.0
        status = "over_budget" if actual > b.monthly_limit else "under_budget"
        seen_categories.add(b.category)
        result.append(BudgetStatus(
            category=b.category,
            month=month,
            budget=b.monthly_limit,
            actual=actual,
            variance=variance,
            utilization_pct=utilization,
            status=status,
        ))

    for category, actual in actuals.items():
        if category not in seen_categories:
            result.append(BudgetStatus(
                category=category,
                month=month,
                budget=0.0,
                actual=actual,
                variance=-actual,
                utilization_pct=0.0,
                status="no_budget",
            ))

    return sorted(result, key=lambda x: x.actual, reverse=True)

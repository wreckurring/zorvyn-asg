from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel

from app.models.transaction import TransactionType


class SummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float


class CategoryBreakdown(BaseModel):
    category: str
    type: TransactionType
    total: float


class TrendPeriod(BaseModel):
    period: str
    income: float
    expenses: float


class TransactionStat(BaseModel):
    category: str
    type: TransactionType
    count: int
    total: float
    avg: float
    min: float
    max: float


class AnomalyRecord(BaseModel):
    transaction_id: int
    date: date
    category: str
    type: TransactionType
    amount: float
    category_avg: float
    category_std: float
    z_score: float


class InsightsResponse(BaseModel):
    savings_rate_pct: float
    top_expense_category: Optional[str]
    month_over_month_expense_change_pct: Optional[float]
    current_month_net: float
    avg_transaction_amount: float
    avg_daily_expense: float
    total_transactions: int
    largest_transaction_id: Optional[int]
    largest_transaction_amount: Optional[float]

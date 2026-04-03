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

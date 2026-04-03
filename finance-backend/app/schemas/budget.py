import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float
    month: str

    @field_validator("monthly_limit")
    @classmethod
    def limit_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("monthly_limit must be greater than zero")
        return v

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: str) -> str:
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("month must be in YYYY-MM format")
        return v


class BudgetResponse(BaseModel):
    id: int
    category: str
    monthly_limit: float
    month: str
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetStatus(BaseModel):
    category: str
    month: str
    budget: float
    actual: float
    variance: float
    utilization_pct: float
    status: Literal["under_budget", "over_budget", "no_budget"]

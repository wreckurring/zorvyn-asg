from datetime import datetime

from pydantic import BaseModel

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: AuditAction
    resource_type: str
    resource_id: int
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuditLogs(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[AuditLogResponse]

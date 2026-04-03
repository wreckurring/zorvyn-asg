from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.access_control import require_admin
from app.models.user import User
from app.schemas.audit import PaginatedAuditLogs
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=PaginatedAuditLogs)
def list_audit_logs(
    resource_type: str | None = Query(None),
    user_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total, results = get_audit_logs(db, resource_type=resource_type, user_id=user_id, skip=skip, limit=limit)
    return PaginatedAuditLogs(total=total, skip=skip, limit=limit, results=results)

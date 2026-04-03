from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog


def record(
    db: Session,
    user_id: int,
    action: AuditAction,
    resource_type: str,
    resource_id: int,
    details: str | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(entry)
    db.commit()


def get_audit_logs(
    db: Session,
    resource_type: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, list[AuditLog]]:
    query = db.query(AuditLog)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    results = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return total, results

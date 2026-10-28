import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def log_transition(
    action: str,
    booking_id: Optional[uuid.UUID],
    user_id: Optional[uuid.UUID],
    previous_status: Optional[str],
    new_status: Optional[str],
    db: AsyncSession,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Appends an immutable audit log record to the database."""
    log_entry = AuditLog(
        booking_id=booking_id,
        user_id=user_id,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        metadata_json=metadata or {},
    )
    db.add(log_entry)
    await db.flush()
    return log_entry

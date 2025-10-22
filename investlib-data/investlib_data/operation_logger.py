"""Operation Logger for audit trail (append-only)."""

from sqlalchemy.orm import Session
from sqlalchemy import event
from investlib_data.models import OperationLog, OperationType, ExecutionStatus, ExecutionMode
from datetime import datetime
from typing import Dict, Any, List
import json
from uuid import uuid4


class OperationLogger:
    """Log investment operations with append-only enforcement."""

    def __init__(self, session: Session):
        self.session = session

    def log_operation(
        self,
        user_id: str,
        operation_type: str,
        symbol: str,
        recommendation: Dict[str, Any],
        modification: Dict[str, Any] = None,
        status: str = "EXECUTED",
        notes: str = None
    ) -> str:
        """Log an operation (append-only).

        Returns:
            operation_id (UUID)
        """
        operation_id = str(uuid4())

        log_entry = OperationLog(
            operation_id=operation_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            operation_type=OperationType[operation_type],
            symbol=symbol,
            original_recommendation=json.dumps(recommendation),
            user_modification=json.dumps(modification) if modification else None,
            execution_status=ExecutionStatus[status],
            execution_mode=ExecutionMode.SIMULATED,
            notes=notes
        )

        self.session.add(log_entry)
        self.session.commit()

        return operation_id

    def get_operations(
        self,
        user_id: str = None,
        symbol: str = None,
        limit: int = 100
    ) -> List[OperationLog]:
        """Query operations (read-only)."""
        query = self.session.query(OperationLog)

        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if symbol:
            query = query.filter(OperationLog.symbol == symbol)

        return query.order_by(OperationLog.timestamp.desc()).limit(limit).all()


# Enforce append-only at ORM level
@event.listens_for(OperationLog, 'before_update')
def prevent_update(mapper, connection, target):
    raise ValueError("OperationLog is append-only, updates not allowed")

@event.listens_for(OperationLog, 'before_delete')
def prevent_delete(mapper, connection, target):
    raise ValueError("OperationLog is append-only, deletes not allowed")

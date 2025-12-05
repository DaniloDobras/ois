from sqlalchemy.exc import SQLAlchemyError
from app.db.models import OutboxEvent


async def add_to_outbox_event(db, aggregate_type, aggregate_id, event_type, payload, status="NEW"):
    # Basic validation
    if not all([aggregate_type, aggregate_id, event_type]):
        raise ValueError("aggregate_type, aggregate_id, and event_type are required and cannot be empty.")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary.")
    if status not in ("NEW", "SENT", "FAIL"):
        raise ValueError("status must be one of: 'NEW', 'SENT', or 'FAIL'.")

    try:
        event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            status=status
        )
        db.add(event)
        db.flush()
        return event
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to add event to outbox: {str(e)}")

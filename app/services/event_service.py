import hashlib
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from app.models.event import Event
from app.schemas.event import EventCreate
from app.core.security import redact_sensitive_data
from app.core.logging import logger


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def generate_signature(self, service: str, message: str, level: str, event_type: str) -> str:
        """Generates a normalized hash signature for error deduplication and grouping."""
        # Normalize message by removing numbers/timestamps for grouping
        import re
        normalized_msg = re.sub(r"\d+", "N", message.strip().lower()[:128])
        raw = f"{service.lower()}:{level.upper()}:{event_type}:{normalized_msg}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def record_event(self, event_in: EventCreate) -> Event:
        """Normalizes, redacts, signs, and stores an incoming runtime event."""
        # Redact secrets from message and metadata
        clean_msg = redact_sensitive_data(event_in.message)
        clean_meta = redact_sensitive_data(event_in.metadata_json)

        signature = event_in.signature or self.generate_signature(
            service=event_in.service,
            message=clean_msg,
            level=event_in.level,
            event_type=event_in.event_type
        )

        timestamp = event_in.timestamp or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        event = Event(
            service=event_in.service,
            environment=event_in.environment,
            source=event_in.source,
            level=event_in.level.upper(),
            message=clean_msg,
            event_type=event_in.event_type,
            signature=signature,
            metadata_json=clean_meta,
            incident_id=event_in.incident_id,
            timestamp=timestamp
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.info(
            f"Event recorded: [{event.service}] [{event.level}] {event.message[:60]} (sig: {event.signature})",
            extra={"service": event.service, "level": event.level, "extra_data": {"event_id": event.id}}
        )
        return event

    def get_recent_events_for_service(self, service: str, window_seconds: int = 600, limit: int = 100) -> List[Event]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        stmt = (
            select(Event)
            .where(Event.service == service)
            .where(Event.timestamp >= cutoff)
            .order_by(desc(Event.timestamp))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_events_for_incident(self, incident_id: str, limit: int = 100) -> List[Event]:
        stmt = (
            select(Event)
            .where(Event.incident_id == incident_id)
            .order_by(desc(Event.timestamp))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

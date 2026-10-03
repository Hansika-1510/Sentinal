import logging
import json
import sys
from typing import Any, Dict
from datetime import datetime, timezone
from app.core.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "incident_id"):
            log_obj["incident_id"] = record.incident_id
        if hasattr(record, "service"):
            log_obj["service"] = record.service
        if hasattr(record, "action"):
            log_obj["action"] = record.action
        if hasattr(record, "actor"):
            log_obj["actor"] = record.actor
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj.update(record.extra_data)

        if record.exc_info and settings.DEBUG:
            log_obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger("incident_agent")
    logger.setLevel(log_level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()

import re
from typing import Any, Dict, List, Union
from app.core.config import settings


def redact_sensitive_data(data: Union[Dict[str, Any], List[Any], str]) -> Union[Dict[str, Any], List[Any], str]:
    """
    Recursively redacts sensitive keys such as passwords, tokens, and API keys.
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in settings.SENSITIVE_KEY_PATTERNS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Redact patterns like Bearer tokens or Authorization strings
        bearer_pattern = r"(Bearer\s+)[A-Za-z0-9_\-\.]{10,}"
        cleaned = re.sub(bearer_pattern, r"\1[REDACTED]", data, flags=re.IGNORECASE)
        return cleaned
    return data


def verify_api_key_or_token(provided_key: str, expected_key: str) -> bool:
    """Constant-time token/key comparison."""
    import hmac
    if not provided_key or not expected_key:
        return False
    return hmac.compare_digest(provided_key, expected_key)

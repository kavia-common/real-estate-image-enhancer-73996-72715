import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("audit")


def audit_event(action: str, user_id: Optional[str], details: Dict[str, Any]) -> None:
    # PUBLIC_INTERFACE
    """Emit an audit event.

    Args:
        action: The action performed (e.g., 'login', 'upload_image').
        user_id: The acting user's ID if available.
        details: Additional context, never include secrets or raw PII.
    """
    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "user_id": user_id,
        "details": details,
    }
    # In production, route to SIEM or append-only store.
    logger.info(json.dumps(payload))

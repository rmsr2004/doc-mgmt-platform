"""
service.py
----------
Audit-logging service — SR-06 / AD-05.

Three event categories are defined by the specification:

  1. Authentication events  (SR-06-A)
     Logged for every login attempt (success or failure) and every logout.
     Required fields: user identity, timestamp, source IP, outcome.

  2. Document access / sharing events  (SR-06-B)
     Logged whenever a document is uploaded, viewed, downloaded, or shared.
     Required fields: requesting user, document identifier, action, timestamp.

  3. Administrative actions  (SR-06-C)
     Logged whenever an admin enables/disables an account or changes a role.
     Required fields: administrator identity, target user, action, timestamp.

Dual output:
  • PostgreSQL audit_log table  — structured, queryable, persistent.
  • flask.current_app.logger   — levelled text log captured by Docker / stdout.

Log-level policy
----------------
  ERROR   Internal failure writing to the audit_log table.
  WARNING Suspicious / security-relevant failures:
            - login_failed  (bad credentials, locked account)
            - any event with outcome == 'failure'
  INFO    Normal security-relevant events (all successful operations):
            - login_success, logout
            - document_upload, document_view, document_download,
              document_share, shared_download
            - user_enabled, user_disabled

All three functions are intentionally fire-and-forget: a logging failure
must never break the primary user-facing request.  Errors are swallowed and
written to Flask's application logger so that they appear in server logs.
"""

import logging
from pathlib import Path
import traceback
import os

from app.config import BASE_DIR

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

log_dir_env = os.getenv("AUDIT_LOG_DIR")
log_dir = Path(log_dir_env) if log_dir_env else BASE_DIR / "logs"
log_path = log_dir / "audit.log"

# Setup dedicated file logger for audit
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

if not audit_logger.handlers:
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
    except (PermissionError, OSError):
        pass

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    audit_logger.addHandler(console_handler)

    audit_logger.propagate = False

def _log(level: int, message: str) -> None:
    """Emit *message* at *level* to the dedicated audit file logger."""
    try:
        audit_logger.log(level, message)
    except Exception:  # noqa: BLE001
        print(f"[audit_log fallback] {logging.getLevelName(level)}: {message}")

def _choose_level(outcome: str, action: str) -> int:
    """
    Map (outcome, action) to a logging level.

    WARNING — any failure outcome, or a failed login attempt.
    INFO    — everything else (successful, routine security event).
    """
    if outcome == "failure" or action == "login_failed":
        return logging.WARNING
    return logging.INFO

def _format_message(event_category: str, action: str, outcome: str, **extra) -> str:
    """Build a consistent, structured log line."""
    parts = [f"[AUDIT] category={event_category} action={action} outcome={outcome}"]
    for key, value in extra.items():
        if value is not None:
            parts.append(f"{key}={value}")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# SR-06-A  Authentication events
# ---------------------------------------------------------------------------

def log_auth_event(
    action: str,
    outcome: str,
    source_ip: str | None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> None:
    """
    Record an authentication event.

    Parameters
    ----------
    action         : 'login_success' | 'login_failed' | 'logout'
    outcome        : 'success' | 'failure'
    source_ip      : remote IP of the request (from request.remote_addr)
    actor_id       : users.id of the authenticated user (None for unknown users)
    actor_username : username as submitted (always recorded, even for bad creds)

    Log levels
    ----------
    WARNING  login_failed or outcome == 'failure'  (suspicious activity)
    INFO     login_success, logout                 (normal security event)
    """
    # Emit to file logger
    level = _choose_level(outcome, action)
    _log(
        level,
        _format_message(
            "auth", action, outcome,
            user=actor_username,
            user_id=actor_id,
            ip=source_ip,
        ),
    )


# ---------------------------------------------------------------------------
# SR-06-B  Document access / sharing events
# ---------------------------------------------------------------------------

def log_document_event(
    action: str,
    actor_id: int,
    actor_username: str,
    document_id: int,
    outcome: str = "success",
    source_ip: str | None = None,
) -> None:
    """
    Record a document access or sharing operation.

    Parameters
    ----------
    action         : 'document_upload' | 'document_view' | 'document_download'
                     | 'document_share' | 'shared_download'
    actor_id       : users.id of the requesting user
    actor_username : username of the requesting user
    document_id    : documents.id of the document being acted upon
    outcome        : 'success' | 'failure'
    source_ip      : remote IP of the request

    Log levels
    ----------
    WARNING  outcome == 'failure'  (unauthorised access attempt)
    INFO     outcome == 'success'  (normal document operation)
    """
    # Emit to file logger
    level = _choose_level(outcome, action)
    _log(
        level,
        _format_message(
            "document", action, outcome,
            user=actor_username,
            user_id=actor_id,
            doc_id=document_id,
            ip=source_ip,
        ),
    )


# ---------------------------------------------------------------------------
# SR-06-C  Administrative actions
# ---------------------------------------------------------------------------

def log_admin_event(
    action: str,
    admin_id: int,
    admin_username: str,
    target_user_id: int,
    outcome: str = "success",
    source_ip: str | None = None,
) -> None:
    """
    Record an administrative action that affects another user account.

    Parameters
    ----------
    action          : 'user_enabled' | 'user_disabled' | 'role_changed'
    admin_id        : users.id of the administrator performing the action
    admin_username  : username of the administrator
    target_user_id  : users.id of the user being acted upon
    outcome         : 'success' | 'failure'
    source_ip       : remote IP of the request

    Log levels
    ----------
    WARNING  outcome == 'failure'  (admin action that failed — investigate)
    INFO     outcome == 'success'  (normal administrative operation)
    """
    # Emit to file logger
    level = _choose_level(outcome, action)
    _log(
        level,
        _format_message(
            "admin", action, outcome,
            admin=admin_username,
            admin_id=admin_id,
            target_user_id=target_user_id,
            ip=source_ip,
        ),
    )
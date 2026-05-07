"""
audit_log.py
------------
Data Access Layer for the audit_log table.

This is the ONLY module allowed to write to the audit_log table.
All audit entries are inserted with parameterized queries (SR-05 compliance).

Called exclusively by app.components.audit_log.service — never directly
from route handlers.
"""

from . import utils


def insert_event(
    event_category: str,
    action: str,
    outcome: str,
    source_ip: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
    target_user_id: int | None = None,
    document_id: int | None = None,
) -> None:
    """
    Insert a single audit-log row.

    Parameters
    ----------
    event_category : 'auth' | 'document' | 'admin'
    action         : fine-grained event name (e.g. 'login_success')
    outcome        : 'success' | 'failure'
    source_ip      : remote IP address of the HTTP request (may be None)
    actor_id       : FK → users.id of the user performing the action
    actor_username : username snapshot (preserved even if the account is later deleted)
    target_user_id : FK → users.id of the affected user (admin events only)
    document_id    : FK → documents.id of the affected document (document events only)
    """
    utils.query_commit(
        """
        INSERT INTO audit_log
            (event_category, action, outcome, source_ip,
             actor_id, actor_username, target_user_id, document_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            event_category,
            action,
            outcome,
            source_ip,
            actor_id,
            actor_username,
            target_user_id,
            document_id,
        ),
    )

"""
audit_log component
===================
Centralised audit-logging service (SR-06 / AD-05).

Provides three public functions, one per event category:

  log_auth_event(...)      — login success/failure, logout
  log_document_event(...)  — upload, view, download, share
  log_admin_event(...)     — enable/disable account, role change

All writes go through dal.audit_log.insert_event so that the
no-raw-SQL rule (SR-05) is respected throughout.
"""

from .service import log_auth_event, log_document_event, log_admin_event

__all__ = ["log_auth_event", "log_document_event", "log_admin_event"]

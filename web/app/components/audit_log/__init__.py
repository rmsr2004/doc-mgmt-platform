"""
Data Access Layer (DAL) Component
=================================
Responsible for encapsulating all interactions with the PostgreSQL database,
ensuring safe, isolated, and consistent data querying.

Responsibilities:
- Execute database queries and data mutations.
- Prevent SQL injection through strict parameterization.
- Map database records to internal application structures cleanly.

Security relevance:
- SR-05: Ensures the integrity of interactions using parameterized queries or a secure ORM in all database operations.
- AD-04: Serves as the Secure Data Access Layer Encapsulating All Database Interactions.
"""
from .service import log_auth_event, log_document_event, log_admin_event

__all__ = ["log_auth_event", "log_document_event", "log_admin_event"]
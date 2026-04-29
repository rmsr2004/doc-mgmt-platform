"""
Data Access Layer (DAL) — AD-04
================================
Centralizes all database interactions for the application.

This component is the ONLY layer allowed to execute SQL queries.
All other components (auth_session, admin_service, document_service) must 
interact with the database exclusively through the functions exposed here.

Security guarantees (SR-05):
- All queries use parameterized statements — no string concatenation.
- No raw SQL is constructed from user-supplied input anywhere in this layer.
- Direct database access from outside this component is prohibited.

Modules:
- users.py      — User account operations (lookup, toggle active status)
- documents.py  — Document operations (ownership, access, upload metadata)
- utils.py      — Database connection management and query execution wrappers
"""
"""
Document Service
================
Responsible for handling document-related operations in the platform.

This component manages the upload, retrieval, listing, and access to
documents owned by users or explicitly shared with authorized reviewers.
It acts as the application layer for document workflows, coordinating
validation, authorization checks, and persistence through the Data Access Layer.

Responsibilities:
- Accept document uploads and associated metadata.
- List documents belonging to a user or shared with them.
- Retrieve document details and content securely.
- Enforce owner/reviewer-only access rules before serving documents.
- Delegate all database interactions to the Data Access Layer (DAL).
- Support secure storage and retrieval of uploaded files.

Security relevance:
- SR-01: Grants access to a document only if the user is the designated owner or an explicitly authorized reviewer.
- SR-04: Validates server integrity strictly through a predefined allowlist of MIME types and extensions.
- SR-05: Ensures integrity of database interactions using parameterized queries via the DAL.
- SR-09: Imposes a maximum file size limit and restricts the frequency of uploads per authenticated user.
- SR-10: Normalizes all uploaded filenames to prevent directory traversal and confines storage paths to a designated root.
- AD-01: Integrates with the Authorization Gateway to prevent unauthorized access.
- AD-03: Implements the Hardened Document Upload Pipeline (validation, isolation, throttling).
- AD-04: Relies on the Secure Data Access Layer to encapsulate all database interactions.

Architecture role:
This component represents the Document Service shown in the system
architecture. It is reached only through the protected application flow,
after authentication and authorization checks have been applied.
"""

from .routes import document_bp
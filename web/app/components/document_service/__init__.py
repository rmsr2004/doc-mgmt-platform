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
- List documents belonging to a user.
- Retrieve document details and content.
- Enforce owner/reviewer-only access rules before serving documents.
- Delegate all database interactions to the Data Access Layer (DAL).
- Support secure storage and retrieval of uploaded files.

Security relevance:
- Supports SR-01: owner/reviewer-only document access.
- Supports SR-04: upload validation by MIME type and extension.
- Supports SR-10: filename normalization and path confinement.
- Works with the Authorization Gateway / Guard Door to prevent
  unauthorized document access.
- Must never perform raw SQL directly; all persistence is delegated
  to the DAL (AD-04 / SR-05).

Architecture role:
This component represents the Document Service shown in the system
architecture. It is reached only through the protected application flow,
after authentication and authorization checks have been applied.
"""

from .routes import document_bp
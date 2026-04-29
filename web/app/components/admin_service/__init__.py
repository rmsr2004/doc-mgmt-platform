"""
Admin Service
=============
Responsible for administrative operations over user accounts and
platform configuration, exclusively accessible to users holding the
Administrator role.

This component exposes a set of protected endpoints that allow
administrators to inspect and manage registered user accounts,
including toggling their active status. All routes in this component
are guarded by both authentication and role-based access enforcement,
ensuring no non-administrator user can reach administrative functionality.

Responsibilities:
- List all registered user accounts and their current status.
- Toggle the active/inactive status of a user account (enable/disable).
- Enforce that the administrator cannot disable their own account.
- Delegate all database interactions to the Data Access Layer (DAL).
- Emit structured audit log events for every administrative action taken.

Security relevance:
- Implements SR-03: toggle user account active status.
- Implements SR-03a: disabled accounts rejected at authentication middleware.
- Implements SR-08: RBAC enforcement on all administrative endpoints.
- Implements SR-08a: HTTP 403 returned for non-administrator requests.
- Supports SR-06: all administrative actions are audit-logged (AD-05).
- Mitigates T-12: Privilege Abuse / Unauthorized Admin Access (MC-03).

Architecture role:
This component represents the Admin Backend shown in the system
architecture (AD-01). It is only reachable after passing through the
Single Access Point (API Gateway) and the Authorization Gateway,
which enforces the Administrator role check before any request
reaches this component.
"""

from .routes import admin_bp
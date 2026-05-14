"""
components/
-----------
Self-contained application components, each implementing one or more
architectural decisions (AD) from the system design.

Each component encapsulates its own routes, business logic, and security
configuration, and is registered independently in the application factory.

Components:
  - auth_session                : Authentication & Session Management (AD-02)
  - authorization               : Authorization Gateway enforcing RBAC & ownership (AD-01)
  - admin_service               : Administrative operations and user management (AD-01)
  - document_service            : Document upload, access, and sharing management
  - dal                         : Secure Data Access Layer (AD-04)
  - audit_log                   : Centralized Audit Logging and Security Monitoring (AD-05)
  - input_validation_filter     : Validation stage for upload pipeline (AD-03)
  - sanitizing_storage_adapter  : Isolation and sanitization for storage (AD-03)
  - upload_guard                : Upload rate limiting and throttling (AD-03 / AD-07)
"""
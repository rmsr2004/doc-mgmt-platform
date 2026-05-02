"""
components/
-----------
Self-contained application components, each implementing one or more
architectural decisions (AD) from the system design.

Each component encapsulates its own routes, business logic, and security
configuration, and is registered independently in the application factory.

Components:
  - auth_session                : Authentication & Session Management (AD-02)
  - dal                         : Secure Data Access Layer (AD-04)
  - admin_service               : Administrative operations and user management (AD-01)
  - document_service            : Document upload, access, and sharing management
  - input_validation_filter     : Input validation and sanitization for all incoming data (AD-03a)
  - sanitizing_storage_adapter  : Storage adapter that sanitizes data before saving to the database (AD-03b)
"""
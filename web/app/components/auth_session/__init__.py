"""
Auth & Session Component
========================
Responsible for handling user authentication workflows, session lifecycle management,
and core access protection mechanisms across the application.

Responsibilities:
- Authenticate users securely over encrypted channels.
- Manage secure session state and lifecycle (login, logout, timeouts).
- Apply rate limiting on authentication attempts to prevent brute-force attacks.
- Defend against Cross-Site Request Forgery (CSRF).

Security relevance:
- SR-02: Protects user sessions by imposing HttpOnly and Secure flags on all authentication cookies.
- SR-07: Applies rate limiting and temporary account lockout after a predefined number of failed authentication attempts.
- SR-11: Implements anti-CSRF measures (strict SameSite cookies and/or tokens) for all state-changing operations.
- SR-13: Authenticates all users before allowing access to protected resources, rejecting invalid, expired, or missing sessions.
- AD-01: Acts as the primary check in the Single Access Point with Authorization Gateway.
- AD-02: Dedicated Authentication and Session Management over Secure Channel.
- AD-07: Availability Protection through Targeted Rate Limiting and Monitoring.
"""
from .routes import auth_bp

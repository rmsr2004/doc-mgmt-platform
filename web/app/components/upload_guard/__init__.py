# Upload Guard
# ============
# Entry-point security component for the Upload Service.
#
# Architectural Decision addressed:
#   - AD-03c : Enforce upload rate limiting
#
# Security Requirements supported:
#   - SR-09b : Enforce upload request frequency limits per authenticated user
#
# Note:
#   File size enforcement (SR-09a) is handled by the nginx configuration, not by this component.
#
from .upload_rate_limiter import limiter, init_upload_rate_limiter
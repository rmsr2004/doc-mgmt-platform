
"""
Upload Guard Component
======================
Responsible for throttling and enforcing capacity constraints on incoming
file uploads to preserve system availability.

Responsibilities:
- Apply strict rate limits to file upload endpoints per user or IP.
- Work in conjunction with web server settings to enforce maximum file size limits.

Security relevance:
- SR-09: Restricts the frequency of uploads per authenticated user.
- AD-03: Forms the throttling stage of the Hardened Document Upload Pipeline.
- AD-07: Contributes to Availability Protection through Targeted Rate Limiting.
"""

from .upload_rate_limiter import limiter, init_upload_rate_limiter
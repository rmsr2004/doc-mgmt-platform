"""
Sanitizing Storage Adapter Component
====================================
Responsible for sanitizing user-provided filenames and ensuring safe,
isolated storage of files on the filesystem.

Responsibilities:
- Generate unique UUID-based filenames to prevent collisions and execution of malicious files.
- Confine all file storage to a designated root directory.
- Prevent path traversal attacks.

Security relevance:
- SR-10: Normalizes all uploaded filenames to prevent directory traversal and restricts storage paths to the designated root.
- AD-03: Forms the isolation and sanitization stage of the Hardened Document Upload Pipeline.
"""
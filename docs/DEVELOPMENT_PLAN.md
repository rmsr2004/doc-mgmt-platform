# DEVELOPMENT_PLAN.md
## Overview

This roadmap organises implementation work into six sequential phases. Each phase groups branches by architectural concern, ensuring that security controls are layered in the correct dependency order — foundational data access hardening before authorization, authorization before feature endpoints, and DevSecOps gates active throughout. Every branch maps to one or more Security Requirements (SR) and/or Architectural Decisions (AD) so that graders can trace a direct line from requirement → design → implementation.

**Dependency order rationale:**
1. Missing endpoints must be stubbed out first so later security phases have a complete surface to protect.
2. Data access must be hardened (parameterized queries) before any higher-level feature is built on top of it.
3. Authentication and sessions must be solid before RBAC can enforce meaningful identity.
4. RBAC enforcement wraps all endpoints — it can only be applied after both the endpoints and the identity layer exist.
5. File upload hardening is an isolated pipeline concern applied on top of the functional upload endpoint.
6. Audit logging depends on having final stable endpoint paths and access control in place.
7. DevSecOps gates run continuously from Phase 1 but are formalised and tightened in the final phase.

---

## Traceability Matrix

| SR / AD | Title | Phase |
|---|---|---|
| SR-01 | Secure password storage (bcrypt) | 2 |
| SR-02 | Strong password policy enforcement | 2 |
| SR-03 | Secure session cookie configuration | 2 |
| SR-04 | Session timeout and invalidation | 2 |
| SR-05 | File type validation (MIME + extension) | 4 |
| SR-06 | File size limit enforcement | 4 |
| SR-07 | Parameterized SQL queries (no raw string formatting) | 1 |
| SR-08 | Structured audit logging for sensitive operations | 5 |
| SR-09 | RBAC — role-based access to documents and admin | 3 |
| SR-10 | Secure file download (path traversal prevention) | 1 |
| SR-11 | Document sharing with access control enforcement | 1 |
| SR-12 | Admin user management endpoints | 1 |
| SR-13 | DevSecOps pipeline (SAST, SCA, container scanning) | 6 |
| SR-14 | Two-person rule for PR review | All phases |
| AD-01 | RBAC middleware architecture | 3 |
| AD-02 | Authentication and session management design | 2 |
| AD-03 | Upload pipeline hardening architecture | 4 |
| AD-04 | Data Access Layer (DAL) with parameterized queries | 1 |
| AD-05 | Audit logging architecture | 5 |
| AD-06 | DevSecOps pipeline architecture | 6 |
| AD-07 | Secrets and configuration management | 6 |

---

## Phase 1 — Missing Endpoints & DAL Baseline

**Goal:** Implement the three missing functional endpoints (download, share, admin user management) and harden the entire Data Access Layer with parameterized queries. This phase establishes the complete application surface and eliminates SQL injection at the foundation before any security control is layered on top.

**Duration estimate:** 1–2 weeks

---

### Branch: `feature/SR-10-secure-document-download`

**Purpose:** Implement the `GET /documents/<id>/download` endpoint. The implementation must prevent path traversal attacks by resolving file paths against a whitelisted storage root and rejecting any path that escapes that root.

**Key implementation tasks:**
- Add the download route in `routes/document_routes.py`
- Resolve the stored filename against `UPLOAD_FOLDER` using `os.path.realpath()` and verify the result starts with the canonical storage path
- Return the file using `flask.send_file()` with `as_attachment=True`
- Enforce that the requesting user owns the document or has been granted access (placeholder check — full enforcement applied in Phase 3)
- Write integration tests covering: valid download, path traversal attempt (`../../../etc/passwd`), and unauthorized access attempt

**SRs / ADs addressed:** SR-10, AD-04

---

### Branch: `feature/SR-11-document-sharing`

**Purpose:** Implement the `POST /documents/<id>/share` endpoint, which allows a document owner to grant read access to another user by user ID or email.

**Key implementation tasks:**
- Add a `document_shares` table (migration: `user_id`, `document_id`, `granted_by`, `granted_at`)
- Implement the share route; validate that the requesting user is the document owner
- Add DAL function `share_document(document_id, owner_id, target_user_id)` using parameterized queries
- Return `403 Forbidden` if requester is not the owner
- Write tests: owner shares successfully, non-owner is rejected, sharing with a non-existent user returns `404`

**SRs / ADs addressed:** SR-11, AD-04

---

### Branch: `feature/SR-12-admin-user-management`

**Purpose:** Implement admin-only endpoints for listing, promoting, demoting, and deactivating users (`GET /admin/users`, `PATCH /admin/users/<id>`, `DELETE /admin/users/<id>`).

**Key implementation tasks:**
- Add admin routes under a `/admin` blueprint
- Placeholder role check (`if session.get('role') != 'admin': abort(403)`) — full RBAC middleware applied in Phase 3
- DAL functions: `list_users()`, `update_user_role(user_id, role)`, `deactivate_user(user_id)` — all parameterized
- Write tests: admin can list/modify, non-admin receives `403`

**SRs / ADs addressed:** SR-12, AD-04

---

### Branch: `fix/SR-07-AD-04-parameterized-queries-dal`

**Purpose:** Audit and fix the entire Data Access Layer. Replace every string-formatted SQL query with psycopg2 parameterized statements.

**Key implementation tasks:**
- Grep the codebase for all `%` string interpolation and f-strings inside SQL strings: `grep -rn "execute.*%" app/dal/`
- Replace all instances with `cursor.execute(sql, (param1, param2))` form
- Create `tests/security/test_sql_injection.py` with payloads: `' OR '1'='1`, `'; DROP TABLE users; --`, `' UNION SELECT * FROM users--`
- Ensure all tests pass and no raw string formatting remains in DAL files

**SRs / ADs addressed:** SR-07, AD-04

---

## Phase 2 — Authentication & Session Management

**Goal:** Harden the authentication system by adding secure password storage, a strong password policy, and a fully hardened session configuration. This phase implements AD-02 in full.

**Duration estimate:** 1 week

---

### Branch: `feature/SR-01-password-hashing`

**Purpose:** Replace any plaintext or weakly hashed password storage with bcrypt (cost factor 12).

**Key implementation tasks:**
- Install `flask-bcrypt` or use `bcrypt` directly; pin version in `requirements.txt`
- Update `register` route: hash password with `bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`
- Update `login` route: verify with `bcrypt.checkpw()`
- Write migration script to re-hash any existing test accounts
- Unit tests: correct password passes, wrong password fails, timing is constant (no short-circuit)

**SRs / ADs addressed:** SR-01, AD-02

---

### Branch: `feature/SR-02-password-policy`

**Purpose:** Enforce a strong password policy at registration and on password change.

**Key implementation tasks:**
- Implement a `validate_password(password: str) -> bool` utility function
- Policy: minimum 12 characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special character
- Apply validation in the registration and password-change routes; return `400` with a descriptive error message on failure
- Unit tests covering boundary cases: exactly 12 chars, missing each character class, valid password

**SRs / ADs addressed:** SR-02, AD-02

---

### Branch: `security/SR-03-SR-04-session-hardening`

**Purpose:** Configure Flask sessions with `HttpOnly`, `Secure`, `SameSite=Strict` flags, enforce a server-side session TTL of 30 minutes, and invalidate sessions on logout.

**Key implementation tasks:**
- Switch to `flask-session` with a filesystem or Redis backend (store session data server-side; client only holds a random ID)
- Set `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_SAMESITE = 'Strict'`
- Set `PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)`
- On logout: call `session.clear()` and invalidate the server-side session file/key
- Integration tests: session cookie flags are present in response headers, expired session redirects to login, logout invalidates the session token

**SRs / ADs addressed:** SR-03, SR-04, AD-02

---

## Phase 3 — Authorization & RBAC

**Goal:** Implement the RBAC middleware (AD-01) that enforces role-based access control on all protected routes. This phase depends on Phase 2 (stable identity layer) and Phase 1 (all endpoints exist).

**Duration estimate:** 1 week

---

### Branch: `feature/SR-09-AD-01-rbac-middleware`

**Purpose:** Implement a reusable RBAC decorator/middleware that enforces role requirements on all routes and replaces the placeholder role checks from Phase 1.

**Key implementation tasks:**
- Define roles: `admin`, `editor`, `viewer`
- Implement `@require_role(*roles)` decorator that reads `session['role']`, aborts with `403` if not in allowed roles, and redirects to login if no session exists
- Apply decorator to all document routes and admin routes; replace all placeholder checks from Phases 1 and 2
- Enforce document ownership: editors may only modify their own documents unless they are admins
- Add a `roles` column to the `users` table if not present (migration)
- Integration tests: each role can access what it should and is blocked from what it should not; unauthenticated requests redirect to login

**SRs / ADs addressed:** SR-09, AD-01

---

## Phase 4 — Upload Pipeline Hardening

**Goal:** Apply the upload hardening architecture (AD-03) to ensure that file uploads cannot be used as an attack vector via malicious file types or oversized payloads.

**Duration estimate:** 3–5 days

---

### Branch: `feature/SR-05-SR-06-AD-03-upload-hardening`

**Purpose:** Harden the file upload endpoint with MIME type validation (magic bytes), extension whitelisting, and a file size limit.

**Key implementation tasks:**
- Install `python-magic`; validate MIME type by reading magic bytes from the uploaded stream — do not trust the `Content-Type` header
- Whitelist allowed MIME types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `image/png`, `image/jpeg`
- Whitelist allowed extensions: `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`
- Enforce a 10 MB size limit using `request.content_length` and a streaming read cap
- Sanitize the filename using `werkzeug.utils.secure_filename()`; store files with a UUID-based name to prevent filename collisions and enumeration
- Return `415 Unsupported Media Type` for disallowed types; `413 Payload Too Large` for oversized files
- Security tests: upload a `.php` file renamed as `.pdf`, upload a file exceeding 10 MB, upload a valid PDF

**SRs / ADs addressed:** SR-05, SR-06, AD-03

---

## Phase 5 — Data Access & Audit Logging

**Goal:** Implement structured audit logging (AD-05) that captures all security-sensitive operations. This phase runs after RBAC and all endpoints are stable so that logged events have correct actor identity and resource context.

**Duration estimate:** 3–5 days

---

### Branch: `feature/SR-08-AD-05-audit-logging`

**Purpose:** Implement a structured audit log that records authentication events, document operations, and admin actions.

**Key implementation tasks:**
- Create an `audit_log` table: `id`, `timestamp`, `user_id`, `username`, `action`, `resource_type`, `resource_id`, `ip_address`, `result` (`success`/`failure`)
- Implement `audit.log_event(action, resource_type, resource_id, result)` utility function that reads actor identity from the current session context
- Instrument the following events:
  - `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`, `AUTH_LOGOUT`
  - `DOCUMENT_UPLOAD`, `DOCUMENT_DOWNLOAD`, `DOCUMENT_DELETE`, `DOCUMENT_SHARE`
  - `ADMIN_USER_ROLE_CHANGE`, `ADMIN_USER_DEACTIVATE`
- Write audit entries using a parameterized INSERT inside a `try/finally` block so logging failures never crash the application
- Add a `GET /admin/audit-log` endpoint (admin-only, protected by RBAC from Phase 3)
- Tests: verify that login success and failure both produce audit entries with correct fields; verify that audit log endpoint is unreachable by non-admins

**SRs / ADs addressed:** SR-08, AD-05

---

## Phase 6 — DevSecOps & CI/CD Integrity

**Goal:** Formalise the DevSecOps pipeline (AD-06), integrate automated security scanning into GitHub Actions, and lock down secrets and configuration management (AD-07).

**Duration estimate:** 1 week

---

### Branch: `ci/AD-06-sast-sca-pipeline`

**Purpose:** Add automated SAST (Static Application Security Testing) and SCA (Software Composition Analysis) steps to the GitHub Actions CI pipeline. The pipeline must fail on any HIGH severity finding.

**Key implementation tasks:**
- Add `.github/workflows/security-pipeline.yml`
- Pipeline triggers: on every `push` to any branch and on every `pull_request` targeting `main`
- Jobs:
  1. **Lint & Unit Tests** — `flake8` + `pytest`
  2. **SAST** — `bandit -r app/ -ll` (fail on HIGH/MEDIUM findings)
  3. **SCA** — `safety check -r requirements.txt` (fail on known CVEs in dependencies)
  4. **Secrets scan** — `trufflehog filesystem . --only-verified` or `gitleaks detect`
- All jobs must pass before a PR can be merged (enforced via GitHub branch protection rules configured in Phase 1 setup)
- Document the pipeline in `docs/devsecops-pipeline.md`

**SRs / ADs addressed:** SR-13, AD-06

---

### Branch: `ci/AD-06-container-scanning`

**Purpose:** Add Docker image vulnerability scanning to the CI pipeline using Trivy.

**Key implementation tasks:**
- Add a `Container Scan` job to the security pipeline: `trivy image --exit-code 1 --severity HIGH,CRITICAL <image>`
- Build the Docker image as a CI artifact in a preceding job and pass it to the scan step
- Configure Trivy to fail the build on HIGH or CRITICAL CVEs in the base image or installed packages
- Pin base image to a specific SHA digest in `Dockerfile` (e.g., `FROM python:3.11-slim@sha256:...`) to prevent silent image drift

**SRs / ADs addressed:** SR-13, AD-06

---

### Branch: `security/AD-07-secrets-config-management`

**Purpose:** Remove all hardcoded secrets from the codebase and enforce environment-based configuration management.

**Key implementation tasks:**
- Audit codebase for hardcoded secrets: `grep -rn "SECRET_KEY\|PASSWORD\|API_KEY\|DATABASE_URL" app/` — none should be literal strings
- Move all secrets to environment variables loaded via `python-dotenv` from a `.env` file (which is in `.gitignore`)
- Provide a `.env.example` file with placeholder values and documentation for each variable
- Validate at startup that all required environment variables are present; raise a `RuntimeError` with a clear message if any are missing
- Add a pre-commit hook using `pre-commit` + `detect-secrets` to block accidental secret commits
- Update `docker-compose.yml` to pass secrets as environment variables, not hardcoded values

**SRs / ADs addressed:** AD-07, SR-13

---

## Phase Summary

| Phase | Branches | Primary SRs | Primary ADs | Dependency |
|---|---|---|---|---|
| 1 — Missing Endpoints & DAL | `feature/SR-10-*`, `feature/SR-11-*`, `feature/SR-12-*`, `fix/SR-07-AD-04-*` | SR-07, SR-10, SR-11, SR-12 | AD-04 | None |
| 2 — Auth & Sessions | `feature/SR-01-*`, `feature/SR-02-*`, `security/SR-03-SR-04-*` | SR-01, SR-02, SR-03, SR-04 | AD-02 | Phase 1 (stable DAL) |
| 3 — RBAC | `feature/SR-09-AD-01-*` | SR-09 | AD-01 | Phase 1 (all endpoints), Phase 2 (identity) |
| 4 — Upload Hardening | `feature/SR-05-SR-06-AD-03-*` | SR-05, SR-06 | AD-03 | Phase 1 (upload endpoint exists) |
| 5 — Audit Logging | `feature/SR-08-AD-05-*` | SR-08 | AD-05 | Phase 3 (RBAC stable), Phase 1 (all endpoints) |
| 6 — DevSecOps | `ci/AD-06-sast-sca-*`, `ci/AD-06-container-*`, `security/AD-07-*` | SR-13 | AD-06, AD-07 | All prior phases |

> **SR-14 (Two-Person Rule)** is not a phase — it is enforced as a process control on every PR in every phase via the branch protection rules defined in `GIT_CONVENTIONS.md`.

# GIT_CONVENTIONS.md
## 1. Overview

This document defines the mandatory Git workflow for our team of 3. All conventions below are **binding** — non-conforming commits, branches, or merges will be rejected during code review. The goal is to ensure full traceability from every code change back to the Security Requirements (SR-01 to SR-14) and Architectural Decisions (AD-01 to AD-07) defined in our design phase.

---

## 2. Commit Message Guidelines (Conventional Commits)

All commit messages **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification, extended with a mandatory security-traceability trailer.

### 2.1 Format

```
<type>(<scope>): <short description>

[optional body]

Refs: <SR-XX|AD-XX>[, <SR-YY|AD-YY>...]
```

### 2.2 Mandatory Fields

| Field | Rule |
|---|---|
| `type` | One of: `feat`, `fix`, `security`, `test`, `docs`, `refactor`, `ci`, `chore` |
| `scope` | The module or layer affected (e.g., `auth`, `dal`, `upload`, `rbac`, `ci`, `session`) |
| `short description` | Imperative, lowercase, max 72 characters, no period at end |
| `Refs:` trailer | **Mandatory.** Must reference at least one SR or AD from the project |

### 2.3 Commit Types

| Type | When to use |
|---|---|
| `feat` | Implementing new functional or security feature |
| `fix` | Correcting a bug or closing a vulnerability |
| `security` | Security-only change (hardening, config, validation) |
| `test` | Adding or fixing tests (unit, integration, security) |
| `docs` | Documentation changes only |
| `refactor` | Code restructuring without behaviour change |
| `ci` | Changes to CI/CD pipeline, GitHub Actions workflows |
| `chore` | Dependency updates, tooling, non-functional changes |

### 2.4 Examples

```
feat(auth): implement bcrypt password hashing on registration

Replace plaintext storage with bcrypt (cost factor 12).
Add unit tests for hash generation and verification.

Refs: SR-01, AD-02
```

```
security(session): enforce HttpOnly and Secure flags on session cookie

Configure Flask-Session to set HttpOnly=True, Secure=True,
and SameSite=Strict on all session cookies.

Refs: SR-03, AD-02
```

```
fix(dal): replace string-formatted queries with parameterized statements

All SELECT, INSERT, UPDATE, DELETE statements in document_dal.py
now use %s placeholders with psycopg2 to eliminate SQL injection.

Refs: SR-07, AD-04
```

```
ci(pipeline): add SAST scan step with Bandit to PR workflow

Bandit runs on every PR targeting main. Pipeline fails if
any HIGH severity finding is detected.

Refs: SR-13, AD-06
```

```
feat(upload): restrict MIME types to PDF, DOCX, PNG, JPEG

Validate MIME using python-magic (magic bytes), not Content-Type header.
Reject uploads exceeding 10 MB.

Refs: SR-05, SR-06, AD-03
```

### 2.5 Rules Summary

- ❌ `fix: stuff` — missing scope and `Refs` trailer
- ❌ `Fixed the login bug` — not Conventional Commits format
- ❌ `feat(auth): Add login endpoint` — capital letter in description
- ✅ `feat(auth): add JWT token generation on login` + `Refs: SR-02, AD-02`

---

## 3. Branch Naming Conventions

Branch names must follow a strict pattern to maintain traceability to SRs and ADs.

### 3.1 Format

```
<type>/<reference>-<short-slug>
```

| Segment | Values |
|---|---|
| `type` | `feature`, `fix`, `security`, `ci`, `docs`, `chore`, `test` |
| `reference` | `SR-XX`, `AD-XX`, or a combined identifier like `SR-02-AD-02` when work spans both |
| `short-slug` | Lowercase, hyphenated description of the work (max 40 chars) |

### 3.2 Examples

```
feature/SR-01-password-hashing
feature/SR-02-AD-02-secure-sessions
feature/SR-04-rbac-middleware
feature/SR-05-file-upload-validation
feature/SR-07-parameterized-queries
feature/SR-08-audit-logging
feature/AD-06-devsecops-pipeline
fix/SR-07-sql-injection-dal
fix/SR-10-path-traversal-download
security/SR-03-session-cookie-hardening
ci/AD-06-bandit-sast-workflow
docs/SR-14-two-person-rule-readme
chore/update-dependencies-flask
```

### 3.3 Rules

- All lowercase — no uppercase letters, spaces, or underscores.
- The reference must match an actual SR or AD from the project specification.
- If a branch addresses multiple SRs, list the primary one in the branch name and add the others in commit `Refs:` trailers.
- `main` is the only permanent branch. All feature/fix/security/ci branches are **ephemeral** — they are deleted after merge.

---

## 4. Step-by-Step: Creating a Branch Correctly

Every branch **must** originate from an up-to-date `main`. Never branch from another feature branch unless explicitly coordinated with the team.

### Step 1 — Switch to `main` and pull latest changes

```bash
git checkout main
git pull origin main
```

### Step 2 — Verify your working tree is clean

```bash
git status
# Expected: "nothing to commit, working tree clean"
```

If there are uncommitted changes, stash them first:

```bash
git stash
```

### Step 3 — Create and switch to the new branch

```bash
git checkout -b feature/SR-02-AD-02-secure-sessions
# or
git switch -c feature/SR-02-AD-02-secure-sessions
```

### Step 4 — Push the branch to the remote immediately

This makes the branch visible to teammates and enables early feedback:

```bash
git push -u origin feature/SR-02-AD-02-secure-sessions
```

### Step 5 — Work, commit, and push regularly

Commit logically — one commit per meaningful change, not one commit per file. Push at the end of every work session so teammates can see progress.

```bash
git add <files>
git commit -m "feat(session): configure Flask-Session with server-side storage

Use Flask-Session with filesystem backend. Session ID is a
cryptographically random token (secrets.token_hex). Set TTL to 30min.

Refs: SR-03, AD-02"

git push origin feature/SR-02-AD-02-secure-sessions
```

### Step 6 — Keep your branch up to date with `main`

If `main` has progressed while you were working, rebase your branch on top of it to avoid complex merge conflicts:

```bash
git fetch origin
git rebase origin/main
```

Resolve any conflicts, then push with `--force-with-lease` (never `--force`):

```bash
git push --force-with-lease origin feature/SR-02-AD-02-secure-sessions
```

---

## 5. Pull Request (PR) Rules — Mandatory Integration Gate

**All work must be integrated into `dev` exclusively via Pull Requests.** Direct pushes to `main` and/or `dev` are forbidden.

### 5.1 When to Open a PR

Open a PR when:
- The feature/fix/security work for a branch is complete and all local tests pass.
- You want early feedback (open a **Draft PR** to signal WIP status).

A branch should represent one SR or a tightly related group of SRs/ADs. Do not bundle unrelated changes.

### 5.2 PR Title Format

```
[SR-XX] <Conventional Commit summary>
```

Examples:
```
[SR-02][AD-02] feat(session): implement secure server-side session management
[SR-07][AD-04] fix(dal): replace all raw SQL with parameterized queries
[AD-06] ci(pipeline): add Bandit SAST and Trivy container scanning
```

### 5.3 PR Description Template

Each PR **must** include:

```markdown
## Summary
<!-- What does this PR implement? -->

## Security Requirements Addressed
<!-- List the SRs and ADs covered by this PR -->
- SR-XX: ...
- AD-XX: ...
```

### 5.4 After Merge

Delete the remote feature branch immediately after the PR is merged:

```bash
git push origin --delete feature/SR-02-AD-02-secure-sessions
git branch -d feature/SR-02-AD-02-secure-sessions
```

Update your local `main`:

```bash
git checkout main
git pull origin main
```

---

## 5. Quick Reference

```
Branch:   feature/SR-XX-short-slug
          fix/SR-XX-short-slug
          security/SR-XX-short-slug
          ci/AD-XX-short-slug

Commit:   <type>(<scope>): <description>
          \n
          [body]
          \n
          Refs: SR-XX[, AD-XX]

PR Title: [SR-XX][AD-XX] <type>(<scope>): <description>

Merge:    Squash and Merge (default)
Base:     Always branch from dev; never push directly to main|dev
```

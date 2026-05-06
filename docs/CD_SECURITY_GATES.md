# CD Security Gates Policy

**Referenced by:** SR-12j — Define security gate policy for CD dynamic testing

---

## Overview

The continuous delivery (CD) pipeline implements a tiered security gate policy that balances the need to catch critical issues before deployment while allowing gradual escalation of security controls as findings are reviewed and remediated.

---

## Gate Tiers

### Tier 1: Blocking Gates (Pipeline Failure)

These gates must pass completely. Any failure blocks the pipeline and prevents image promotion to the `dev` environment.

| Gate | Test | Purpose | Action on Failure |
|------|------|---------|-------------------|
| **Delivery Smoke Test** | `tests/test_delivery_auth_flow.py` | Verify the staged container boots correctly and basic auth flow works | Block promotion; alert team |
| **Dynamic API Security Test** | `tests/test_sr_12h_dynamic_api_security.py` | Verify that the running container exposes correct security headers and rejects invalid inputs | Block promotion; alert team |

**Rationale:**  
These tests validate that the core delivery criteria are met: the application starts correctly in the deployment environment, and the API enforces fundamental security boundaries (authentication, rate limiting, CSRF protection, etc.). Failures indicate functional or critical security regressions that must be addressed before moving forward.

---

### Tier 2: Reporting Gates (Report-Only Mode)

These gates run and generate findings but do not block the pipeline. Findings are captured and uploaded as artifacts for manual review. Over time, as findings are triaged and remediated, individual findings or categories may be promoted to blocking status.

| Gate | Test | Purpose | Action on Findings |
|------|------|---------|-------------------|
| **OWASP ZAP Baseline Scan** | `zap-baseline.py` against the staged container | Detect generic runtime security issues: missing security headers, error disclosure, insecure configuration, and other OWASP-categorized risks | Runs with `continue-on-error: true`; report uploaded as artifact; team reviews findings in next sprint |

**Rationale:**  
ZAP baseline scans can generate false positives and findings that are not immediately actionable (e.g., informational severity warnings about server technology disclosure). Allowing the scan to run report-only ensures visibility into dynamic issues while preventing CI/CD flakiness from blocking legitimate changes.

**Escalation Path:**  
- HIGH or CRITICAL findings identified in the report that are reproducible and validated by the team can be promoted to blocking gates in a future phase (e.g., by integrating ZAP findings parsing and failing the pipeline if specific severity thresholds are exceeded).

---

## Policy Decision Flow

```
  ┌─────────────────────────────────────┐
  │   Start Continuous Delivery Job     │
  └────────────────┬────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Deploy Staging     │
         │  Container          │
         └────────────┬────────┘
                      │
                      ▼
         ┌─────────────────────────────────┐
         │  Delivery Smoke Test (BLOCKING) │
         │  test_delivery_auth_flow.py     │
         └────────────┬────────────────────┘
                      │
               ┌──────┴──────┐
               │             │
            PASS           FAIL
               │             │
               ▼             ▼
      Continue    [STOP: Alert team]
               │       [Block promotion]
               ▼
  ┌─────────────────────────────────────────┐
  │  Dynamic API Security Test (BLOCKING)   │
  │  test_sr_12h_dynamic_api_security.py    │
  └────────────┬────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
     PASS           FAIL
        │             │
        ▼             ▼
   Continue    [STOP: Alert team]
        │       [Block promotion]
        ▼
  ┌─────────────────────────────────────┐
  │  ZAP Baseline Scan (REPORT-ONLY)    │
  │  continue-on-error: true            │
  └────────────┬────────────────────────┘
               │
        ┌──────┴───────┐
        │              │
     CLEAN      FINDINGS DETECTED
        │              │
        │              ▼
        │      ┌────────────────┐
        │      │ Upload Report  │
        │      │ to Artifacts   │
        │      └────────────────┘
        │              │
        └──────┬───────┘
               │
               ▼
     ┌──────────────────────────────────┐
     │  Promote Images to dev           │
     │  (Tag as dev, push to registry)  │
     └──────────────────────────────────┘
```

---

## Implementation in GitHub Actions

The CD workflow (`cd.yml`) enforces this policy as follows:

- **Blocking tests** omit the `continue-on-error` flag, causing any failure to halt the job.
- **Report-only gates** set `continue-on-error: true` and always upload findings.
- **Promotion condition** uses `if: success()`, which only executes if all blocking gates passed.

---

## References

- **SR-12j:** Define security gate policy for CD dynamic testing
- **SR-12h:** Dynamic API security test (blocking)
- **Delivery smoke test:** `tests/test_delivery_auth_flow.py`
- **Dynamic API security test:** `tests/test_sr_12h_dynamic_api_security.py`
- **ZAP baseline script:** OWASP ZAP stable image, `zap-baseline.py`

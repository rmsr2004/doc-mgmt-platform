# Secure Document Management Platform

**University of Coimbra — Master in Informatics Engineering (MEI)**  
**Course:** Secure Software (2025–2026)

## 👥 Team
- **João Afonso dos Santos Simões** (2022236316)
- **Rodrigo Miguel Santos Rodrigues** (2022233032)
- **Simão de Almeida Campanudo** (2022210333)

*(Baseline system initially provided by Prof. João R. Campos)*

---

## 🛡️ Project Overview & Security Journey

This repository hosts a web-based document management platform. Originally provided as a vulnerable, intentionally flawed baseline, the system was systematically transformed into a highly resilient and secure platform following a strict **"security-by-design"** philosophy.

The project bridges three major aspects of secure software engineering:

1. **Security Requirements Engineering:** Using the **SQUARE** methodology and **STRIDE** threat modeling, we analyzed misuse cases (e.g., IDOR, SQLi, CSRF, Malicious Uploads) and defined precise, testable security requirements.
2. **Secure Architecture & Design:** Implementation of security patterns such as Single Access Point, Guard Doors, and Role-Based Access Control (RBAC) to enforce strict trust boundaries.
3. **Secure Implementation & DevSecOps:** Mitigation of critical vulnerabilities in the codebase and integration of automated security verification mechanisms into the CI/CD pipeline.

### ✨ Key Security Enhancements

- **Robust Authentication & Session Management:** Migration to secure sessions over TLS (HTTPS), enforcement of `HttpOnly`, `Secure`, and `SameSite=Strict` cookie flags, and active CSRF token rotation (Synchronizer Token Pattern).
- **Role-Based Access Control (RBAC):** Strict isolation between standard users, reviewers, and administrators, preventing Insecure Direct Object References (IDOR) and Privilege Escalation.
- **Hardened File Upload Pipeline:** Multi-layered defense against malicious uploads, including MIME type validation via magic bytes, extension allowlisting, and robust filename sanitization to prevent Path Traversal.
- **Secure Data Access Layer (DAL):** Total eradication of SQL Injection vulnerabilities by encapsulating all database interactions with parameterized queries.
- **Availability Protection:** Infrastructure-level (Nginx) and Application-level (Flask-Limiter) rate limiting to mitigate brute-force credential attacks and Resource Exhaustion (DoS).
- **Comprehensive Audit Logging:** Centralized, tamper-evident logging for all security-relevant operations (authentication, document sharing, admin actions).

### 🚀 DevSecOps Integration
Our GitHub Actions CI/CD pipeline enforces continuous security verification (Shift-Left Security):
- **SAST:** Static analysis using *Bandit* to detect insecure coding patterns.
- **SCA:** Dependency vulnerability scanning using *pip-audit*.
- **Secret Scanning:** Detection of leaked credentials in the repository using *Gitleaks*.
- **Container Security:** Image vulnerability scanning and SBOM generation using *Trivy* and *Anchore*.
- **DAST:** Dynamic API security tests and baseline scans using *OWASP ZAP*.

---

## 💻 Technology Stack

- **Backend:** Python / Flask
- **Database:** PostgreSQL
- **Frontend:** HTML, CSS, JavaScript
- **Infrastructure:** Nginx (Reverse Proxy & TLS Termination)
- **Deployment:** Docker / Docker Compose
- **Automation:** GitHub Actions (CI/CD)

---

## ⚙️ Running the Application

The system is fully containerized and can be started locally using Docker Compose.

```bash
docker compose up --build
```
Once the containers start, the application will be available at:

https://localhost:443

The application should start within a few seconds. The `/health` endpoint can be used to verify that the system is running correctly.

To reset the database and recreate the initial dataset:
```bash
docker compose down -v
docker compose up --build
```

---

## Example Accounts

The initial database contains a few example users. (NOTE: these accounts must be kept)

| Username | Password      |
|------|---------------|
| admin | L\|fP1D%327mB |
| alice | tth1mJj5?£58  |
| bob | De586:Iq6}?!  |


---
## Application Endpoints

The web application exposes several HTTP endpoints.

### Existing Endpoints

The following endpoints are already exist in the baseline system.

#### Authentication

| Method | Endpoint | Description |
|------|------|------|
| GET | `/login` | Display login page |
| POST | `/login` | Authenticate user |
| GET | `/logout` | Terminate the current session |

#### Documents

| Method | Endpoint | Description |
|------|------|------|
| GET | `/documents` | List documents belonging to the authenticated user |
| POST | `/documents/upload` | Upload a new document |
| GET | `/documents/<id>` | View document details |

#### System

| Method | Endpoint | Description |
|------|------|------|
| GET | `/` | Redirect to login or documents page |
| GET | `/health` | Application health check |

### Additional System Functionality

The following endpoints represent functionality that is part of the **intended system design** but is **not implemented in the baseline version** of the application.

Students are expected to implement these endpoints as part of the project.

| Method | Endpoint | Description |
|------|------|------|
| GET | `/documents/<id>/download` | Download a document |
| POST | `/documents/<id>/share` | Share a document with another user |
| GET | `/shared` | List documents shared with the current user |
| GET | `/shared/<id>/download` | Download a shared document |
| GET | `/admin/users` | List system users |
| POST | `/admin/users/<id>/enable` | Enable a user account |
| POST | `/admin/users/<id>/disable` | Disable a user account |

These endpoints must be implemented and are expected by an automated validation tool. Students may extend the system by implementing other additional features as required by the project.

---

## CI/CD Pipeline

The repository includes a basic GitHub Actions pipeline composed of three workflows:
- Integration – verifies that the system builds and runs correctly
- Delivery – prepares the application artifacts for deployment
- Deployment – deploys the system to a target environment

These workflows provide a starting point that can be improved as part of the project.

---

## Baseline System

You can analyze the baseline system in the `baseline-system` branch (https://github.com/rmsr2004/doc-mgmt-platform/tree/baseline-system)
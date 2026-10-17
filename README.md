# KJBN Produce Procurement & Payout Engine

> **Problem 4: Produce Procurement & Payout**  
> A farm buying centre procurement, moisture penalisation rules engine, and weekly payout reconciliation system where every rupee is explainable.

---

## 1. Title and one-liner
**KJBN Produce Procurement & Payout Engine (Problem 4)**: An audit-grade farm produce buying centre rules engine that evaluates effective-dated crop pricing, penalises high-moisture deliveries, generates immutable weekly payouts with advance recovery capping, and provides live delivery breakdowns.

## 2. Live links
- **Live UI**: Pending deployment (see Section 5a)
- **API Base URL**: Pending deployment
- **Interactive API Docs (Swagger / OpenAPI)**: `/docs`
- **Test Credentials**: No authentication required (open reviewer access)
- *Note*: Free-tier services may experience a ~30–50 second cold-start spin-up on initial request.

## 3. Tech stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy ORM, Pydantic v2 (Python provides native arbitrary-precision `Decimal` arithmetic for zero binary-float money drift).
- **Frontend**: TypeScript, React 18, Vite, Tailwind CSS, Lucide icons (Type-safe client with live calculated breakdown previews).
- **Database**: SQLite (persisted to file/volume, schema-managed, atomic transactions).
- **Testing**: Pytest, Pytest-cov, HTTPX for API integration tests.
- **Hosting / Containerisation**: Docker, Docker Compose, Render / Vercel configurations.

## 4. Architecture
*Detailed component diagram, folder structure, and domain layer explanations will be populated across milestones M1–M6.*

## 5. Running locally
*Prerequisites, step-by-step installation, migration, seed, and one-command run instructions.*

## 5a. Deployment
*Production build, container specs, and deployment instructions.*

## 6. Running tests and coverage
*Automated test suites, coverage reports, and boundary test definitions.*

## 7. API overview
*Table of endpoints, methods, parameters, and error status codes.*

## 8. Business rules and assumptions
*Mapping of Rule 1 through Rule 7 to code implementation, test cases, and numbered assumptions.*

## 9. Error handling and logging
*Standardised error envelope, structured JSON logging with correlation IDs, and transaction rollback policies.*

## 10. Reviewer aids
*Reviewer clock override via `X-Test-Clock` header, quick seed commands, and edge-case verification steps.*

## 11. Known limitations
*Explicit documentation of scope boundaries, deferrals, and operational constraints.*

## 12. AI and third-party usage
*Disclosure of AI tooling and link to PROMPTS.md.*

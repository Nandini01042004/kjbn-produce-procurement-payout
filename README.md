# KJBN Produce Procurement & Payout Engine

> **Problem 4: Produce Procurement & Payout**  
> An audit-grade farm produce buying centre rules engine that evaluates effective-dated crop pricing, penalises high-moisture deliveries, generates immutable weekly payouts with advance recovery capping, and provides live delivery breakdowns where every rupee is explainable.

---

## 1. Title and one-liner
**KJBN Produce Procurement & Payout Engine (Problem 4)**: An audit-grade farm produce buying centre rules engine that evaluates effective-dated crop pricing, penalises high-moisture deliveries, generates immutable weekly payouts with advance recovery capping, and provides live delivery breakdowns.

## 2. Live links
- **Public GitHub Repository**: [https://github.com/Nandini01042004/kjbn-produce-procurement-payout](https://github.com/Nandini01042004/kjbn-produce-procurement-payout)
- **Live Web UI**: [https://kjbn-produce-procurement-payout.vercel.app](https://kjbn-produce-procurement-payout.vercel.app) *(or local preview: `http://localhost:5173`)*
- **API Base URL**: `http://localhost:8000/api` *(or deployed backend)*
- **Interactive Swagger / OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Test Credentials**: Open reviewer access (no authentication required).
- *Cold-start notice*: Free-tier hosting providers (Render/Koyeb) spin down after inactivity and may require a ~30–50 second cold-start delay on first request.

## 3. Tech stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2 (Chosen because Python provides native arbitrary-precision `Decimal` arithmetic, eliminating binary floating-point round-off errors in financial and weight calculations).
- **Frontend**: TypeScript, React 18, Vite, Tailwind CSS, Lucide icons (Chosen for instant reactive client-side preview calculations and responsive mobile/desktop usability).
- **Database**: SQLite (persisted to file `procurement.db`, supporting transactions, foreign keys, and atomic row-level locking).
- **Testing**: Pytest 8.1, Pytest-cov 4.1, HTTPX test client.
- **Hosting / CI**: Docker multi-stage builds, Docker Compose, Render (`render.yaml`), Vercel (`vercel.json`), GitHub Actions (`.github/workflows/ci.yml`).

## 4. Architecture

### System Architecture & Request Flow
```
                                 [ Web Browser / Reviewer ]
                                             │
                                   HTTP / X-Test-Clock
                                             ▼
                             ┌───────────────────────────────┐
                             │       FastAPI API Layer       │
                             │  - Request ID Middleware      │
                             │  - Reviewer Clock Override    │
                             │  - Unified Error Envelope     │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │    Domain Services Layer      │
                             │  (DeliveryService,            │
                             │   PayoutService, LedgerService│
                             └───────────────┬───────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
     ┌───────────────────────────────┐               ┌───────────────────────────────┐
     │   Pure Rules Engine Layer     │               │      Persistence Layer        │
     │  - Rule 1: Effective Pricing  │               │  - SQLAlchemy ORM             │
     │  - Rule 2: Moisture Penalty   │               │  - SQLite (procurement.db)    │
     │  - Rule 3: Frozen Breakdown   │               │  - Atomic Transactions        │
     │  - Rule 4: Monday-Sunday Week │               │  - Schema Constraints         │
     │  - Rule 5: 30% Advance Cap    │               └───────────────────────────────┘
     │  - Rule 6: Immutability / Note│
     │  - Rule 7: Grade/Weight Valid.│
     └───────────────────────────────┘
```

### Folder Structure
- `backend/app/domain/rules.py`: **Pure business rules engine** (Rule 1 through Rule 7). Has zero dependencies on HTTP or databases for sub-second, deterministic testing.
- `backend/app/domain/services.py`: Domain application services coordinating business rules with transactional persistence.
- `backend/app/domain/errors.py`: Custom domain exception classes mapping to distinct HTTP status codes (400, 404, 409, 422).
- `backend/app/models/`: SQLAlchemy database entities with composite indexes and Decimal field precision.
- `backend/app/schemas/`: Pydantic validation schemas with `ConfigDict` and typed data shapes.
- `backend/app/api/`: FastAPI route handlers, CORS configuration, correlation logging, and clock override middleware.
- `backend/seed.py`: Idempotent database seed script populating realistic Indian agricultural data (Maize, Turmeric, Groundnut).
- `backend/tests/`: Fast unit and integration tests covering every numeric boundary rule and edge case.
- `frontend/src/`: React TypeScript client with live calculated preview cards, weekly statements, and reviewer tools.

**Why business rules live in `app/domain/rules.py`**:
Separating the rules into a pure functional module ensures that price resolution, moisture penalisation, and advance recovery math are tested independently from web frameworks or database engines. A developer or auditor can locate and verify any rule in under 30 seconds.

## 5. Running locally

### Prerequisites
- Python 3.12+
- Node.js 20+ (with npm)
- Git

### Environment Configuration
Copy the committed `.env.example` template:
```bash
cp .env.example .env
```
Environment variables:
- `APP_ENV`: `development` or `production`
- `LOG_LEVEL`: `INFO` or `DEBUG`
- `HOST`: `0.0.0.0`
- `PORT`: `8000`
- `DATABASE_URL`: `sqlite:///./procurement.db`
- `CORS_ORIGINS`: `http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173`
- `VITE_API_BASE_URL`: `http://localhost:8000/api`

### Step-by-Step Bring-Up
1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   # source .venv/bin/activate
   pip install -r requirements.txt
   python seed.py
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Frontend Setup** (in a second terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser. API docs are available at `http://localhost:8000/docs`.

### One-Command Bring-Up (Docker Compose)
To run the full stack locally via Docker:
```bash
docker compose up --build
```

### One-Command Bring-Up (Native Script)
- Windows: `scripts\run_local.bat`
- Linux/macOS: `bash scripts/run_local.sh`

## 5a. Deployment
- **Container Specs**: `backend/Dockerfile` builds a Python 3.12 slim image; `frontend/Dockerfile` builds an Nginx image serving optimized static assets.
- **Render Deployment**: Configured via `render.yaml`. Backend is deployed as a Web Service running `uvicorn` with `python seed.py` run on build. Frontend is deployed as a Static Site with SPA rewrites.
- **Vercel Deployment**: Configured via `frontend/vercel.json` with wildcard rewrite to `/index.html` for single-page routing.
- **How to Redeploy**: Every git push to branch `main` automatically triggers GitHub Actions CI and webhook redeployments on connected hosting providers.
- **How to Re-seed Hosted Instance**: Make an authenticated or admin POST request to `POST /api/admin/reset-seed` or click the "Re-seed Data" button directly in the UI header banner.

## 6. Running tests and coverage

### Test Commands
Run the complete test suite (both business rules and API integration tests):
```bash
cd backend
pytest -v
```

Generate full code coverage report:
```bash
pytest -v --cov=app --cov-report=term --cov-report=html:htmlcov tests/
```

### Coverage Statistics
- **Total Backend Coverage**: **83%** (Committed in `coverage.txt`)
- **Pure Business Rules Layer (`app/domain/rules.py`)**: **100%**
- **Domain Services Layer (`app/domain/services.py`)**: **89%**
- **Domain Errors Layer (`app/domain/errors.py`)**: **95%**
- **What is covered**: All 7 business rules, all numerical boundary conditions (14.99%, 17.6%, 10% caps), frozen delivery breakdowns, sequential payout advance drain, credit/debit adjustments, and HTTP exception handling.
- **What is deliberately not covered**: Development reload utilities and CLI entrypoints (`if __name__ == '__main__':`).

## 7. API overview

| Method | Endpoint | Purpose | Key Error Codes |
|---|---|---|---|
| `GET` | `/api/health` | Service health, DB connectivity, UTC/IST clocks | `500` |
| `POST`| `/api/admin/reset-seed` | Re-seeds database with initial test dataset | `500` |
| `GET` | `/api/farmers` | List registered farmers with outstanding advances | `200` |
| `POST`| `/api/farmers` | Register a new farmer | `409` (Duplicate phone), `422` |
| `GET` | `/api/farmers/{id}/ledger` | Complete financial ledger (deliveries, advances, payouts) | `404` |
| `GET` | `/api/crops` | List crops with moisture thresholds and allowed grades | `200` |
| `POST`| `/api/crops` | Register a new crop | `409`, `422` |
| `GET` | `/api/price-lists` | List effective-dated prices (filter by crop, grade) | `200` |
| `POST`| `/api/price-lists` | Add effective price entry (never overwrites) | `409` (Duplicate date), `422` |
| `GET` | `/api/price-lists/history` | Chronological pricing history for crop and grade | `404` |
| `POST`| `/api/deliveries/preview` | **Live calculated preview** before saving | `400` (Missing price), `422` |
| `POST`| `/api/deliveries` | Record delivery with frozen breakdown & optional adjustment | `400`, `404`, `422` |
| `GET` | `/api/deliveries` | List recorded deliveries with frozen breakdowns | `200` |
| `POST`| `/api/advances` | Issue cash advance (increments outstanding advance) | `404`, `422` |
| `POST`| `/api/payouts/generate` | Generate / recalculate weekly draft payout (Mon-Sun) | `404`, `409` (Finalised exists) |
| `POST`| `/api/payouts/{id}/finalise` | Finalise payout, deduct advance, and lock permanently | `404`, `409` (Already finalised) |
| `POST`| `/api/payouts/{id}/mark-paid` | Mark finalised payout as paid | `400`, `404` |
| `GET` | `/api/payouts/{id}` | Detailed weekly statement with arithmetic reconciliation | `404` |

Interactive OpenAPI documentation is available at `/docs`.

## 8. Business rules and assumptions

### Business Rules Mapping
- **Rule 1 (Price Lookup by Effective Date)**:
  - *Enforcement*: `app/domain/rules.py::lookup_applicable_price`
  - *Tests*: `tests/test_rules.py::test_rule_1_price_lookup_exact_effective_date`, `test_rule_1_price_lookup_latest_on_or_before`, `test_rule_1_missing_price_combination_rejected`, `test_rule_1_adding_backdated_price_entry_does_not_alter_existing_delivery`
- **Rule 2 (Moisture Penalisation & Max Rejection)**:
  - *Enforcement*: `app/domain/rules.py::calculate_moisture_deduction`
  - *Tests*: `tests/test_rules.py::test_rule_2_moisture_at_or_below_threshold`, `test_rule_2_moisture_at_14_99_percent`, `test_rule_2_moisture_at_15_00_percent`, `test_rule_2_moisture_example_17_6_percent`, `test_rule_2_moisture_capped_at_10_percent`, `test_rule_2_moisture_above_crop_max_rejected`
- **Rule 3 (Frozen Delivery Breakdown & Invariant Enforcement)**:
  - *Enforcement*: `app/domain/rules.py::compute_delivery_breakdown`
  - *Tests*: `tests/test_rules.py::test_rule_3_breakdown_arithmetic_and_rounding`
- **Rule 4 (Weekly Monday–Sunday Settlement Window)**:
  - *Enforcement*: `app/domain/rules.py::calculate_weekly_boundaries`, `app/domain/services.py::PayoutService.generate_draft`
  - *Tests*: `tests/test_rules.py::test_rule_4_weekly_boundaries_monday_to_sunday`, `test_rule_4_week_with_zero_deliveries`
- **Rule 5 (Advance Recovery 30% Cap on Finalisation Only)**:
  - *Enforcement*: `app/domain/rules.py::calculate_payout_totals`, `app/domain/services.py::PayoutService.finalise`
  - *Tests*: `tests/test_rules.py::test_rule_5_advance_deduction_capped_at_30_percent`, `test_rule_5_sequential_payouts_drain_advance`, `test_rule_5_draft_does_not_reduce_advance_until_finalised`
- **Rule 6 (Finalised Payout Immutability & Credit/Debit Notes)**:
  - *Enforcement*: `app/domain/services.py::PayoutService.finalise`, `DeliveryService.create`
  - *Tests*: `tests/test_rules.py::test_rule_6_finalised_payout_cannot_be_re_finalised_or_drafted`, `test_rule_6_credit_debit_note_lands_in_next_payout`
- **Rule 7 (Input Validation: Allowed Grades, Positive Values, Future Dates)**:
  - *Enforcement*: `app/domain/rules.py::validate_delivery_inputs`
  - *Tests*: `tests/test_rules.py::test_rule_7_invalid_grade_rejected`, `test_rule_7_non_positive_values_rejected`, `test_rule_7_future_delivery_rejected`

### Numbered Assumptions
1. **Assumption 1 (Moisture Deduction Truncation)**: The problem defines "deduct 1% of gross weight for every full 1% above threshold". We interpret "full 1%" as the mathematical integer floor of `(moisture - threshold)`. E.g., at 14.99% with a 14% threshold, excess is 0.99%, resulting in 0% deduction. At 17.6%, excess is 3.6%, resulting in 3% deduction.
2. **Assumption 2 (Invariant: Net + Deduction = Gross)**: To prevent fraction-of-a-gram leakage, `deduction_kg` is rounded half-up to 2 decimals, and `net_kg` is calculated as `gross_kg - deduction_kg`, strictly satisfying `gross_kg == net_kg + deduction_kg`.
3. **Assumption 3 (Weekly Cycle Boundaries)**: Weeks run Monday 00:00:00 UTC through Sunday 23:59:59.999999 UTC (aligned to IST business days). A delivery timestamp within this range is aggregated into that week's payout.
4. **Assumption 4 (Credit/Debit Note Adjustments)**: Once a payout is finalised, mistakes cannot be resolved by editing past rows. Adjustments are submitted as fresh deliveries with `is_credit_debit_note=true` referencing `reference_delivery_id`, landing in the next unfinalised payout.
5. **Assumption 5 (Zero-Delivery Weeks)**: If a payout is generated for a week with zero deliveries, it generates a draft statement with ₹0.00 gross, ₹0.00 advance deduction, and ₹0.00 net.

## 9. Error handling and logging

### Error Response Shape
Every API error adheres to a uniform JSON contract:
```json
{
  "error": {
    "code": "PRICE_LIST_NOT_FOUND",
    "message": "No active price-list entry found for crop 'Maize' and grade 'A' on or before 2026-08-15.",
    "request_id": "req-9c8f12a3d4e5",
    "details": null
  }
}
```
Validation failures return HTTP 422 with an array of problematic fields in `details`.

### Logging Strategy
- Every incoming HTTP request is assigned a unique `request_id` (via `X-Request-ID` or UUID).
- Domain rule violations (e.g., moisture exceeded, future date) log at `WARN` level with context and identifiers.
- Unhandled errors log at `ERROR` level with full stack trace on the server, but return a sanitized HTTP 500 referencing the `request_id` to prevent internal data leaks.
- On hosted instances, logs are viewable directly in the provider dashboard (Render / Koyeb CLI).

## 10. Reviewer aids
- **Reviewer Clock Override (`X-Test-Clock`)**: Send the `X-Test-Clock: YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` HTTP header with any request, or use the interactive input in the Web UI top banner. Future-dating rules and historical price lookups evaluate relative to this clock.
- **One-Click Data Re-Seed**: Call `POST /api/admin/reset-seed` or click "Re-seed Data" in the UI banner to reset the database to clean sample data at any point.
- **Sample Seed Entities**:
  - **Farmers**: Ramesh Patel (Advance: ₹5,000), Suresh Gowda (Advance: ₹15,000), Lakshmi Devi (Advance: ₹0), Anjanappa M (Advance: ₹25,000).
  - **Crops**: Maize (Threshold: 14%, Max: 20%), Turmeric (Threshold: 12%, Max: 18%), Groundnut (Threshold: 9%, Max: 15%).
  - **Price Lists**: Multi-tier effective dates (2026-09-01, 2026-10-01, 2026-10-10).

## 11. Known limitations
- **Multi-Centre Scoping**: Multi-buying-centre isolation is drafted as a stretch feature; all current transactions belong to a single primary buying centre.
- **Automated Bank Integration**: Payout disbursement is simulated via the "Mark as Paid" status transition; direct NACH/NEFT bank API integrations are not connected.
- **Database Engine**: Production defaults to file-persisted SQLite; while PostgreSQL is fully supported by switching `DATABASE_URL`, SQLite was selected for self-contained, zero-setup reproducibility.

## 12. AI and third-party usage
- A comprehensive log of every prompt and action taken is committed in [PROMPTS.md](file:///c:/KJBN/PROMPTS.md).


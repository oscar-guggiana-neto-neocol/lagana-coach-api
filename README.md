# LaganaCoach API

FastAPI backend for the LaganaCoach platform. It exposes a secure, API-first service for managing coaches, players, lessons, strokes, invoices, and authentication with JWT. The service targets Railway deployment with PostgreSQL, Alembic migrations, and automated CI.

## 1. Overview & Architecture
- **Stack**: FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, python-jose JWT auth, passlib bcrypt hashing.
- **Pattern**: Layered structure – `models`, `schemas` (Pydantic), `routers`, `services`, `core` (config/security), plus utilities.
- **Auth**: JWT access + refresh tokens, role-based authorization (`admin`, `coach`) with scoped data access.
- **Storage**: Invoice PDFs/CSVs generated via ReportLab to `storage/invoices` (configurable).
- **Docs**: OpenAPI available at `/docs` and `/redoc`.
- **Tests**: Pytest suite covering auth, scoping, invoicing, and password reset flows.

Directory highlights:
```
app/
  api/v1/routers     # FastAPI routers per resource
  core               # Settings, security helpers
  db                 # Session and Alembic base classes
  models             # SQLAlchemy models and enums
  schemas            # Pydantic models
  services           # Business logic (auth, invoices, email)
  utils              # Reusable helpers
alembic/              # Migration scripts
scripts/export_schema.sh
```

## 2. Local Setup
1. **Clone & virtualenv**
   ```bash
   cd lagana-coach-api
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install .[dev]  # optional, installs pytest/ruff/black via pyproject extras
   ```
2. **Environment**
   ```bash
   cp .env.example .env
   # update DATABASE_URL, SECRET_KEY, SMTP, etc.
   ```
3. **Database**
   ```bash
   createdb LaganaCoach
   alembic upgrade head
   ```
4. **Run dev server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. **Run tests & linters** (requires dev deps)
   ```bash
   SECRET_KEY=test pytest
   ruff check .
   black --check .
   ```

## 3. Environment Variables
Refer to `.env.example`. Key settings:
- `DATABASE_URL` (preferred) or `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD/DB_SSLMODE`
- `SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_EXPIRES_MIN`, `JWT_REFRESH_EXPIRES_MIN`
- `ALLOWED_ORIGINS` (comma separated, e.g. `http://localhost:8080`)
- SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS`
- `FRONTEND_BASE_URL`
- `FILE_STORAGE_DIR` (defaults to `storage`)
- `PORT` for deployment platforms that inject the port

## 4. Database & Migrations
- PostgreSQL schema defined in `db/schema.sql` and Alembic migration `alembic/versions/0001_initial.py`.
- Association tables cover many-to-many player/coach, lesson/player, lesson/stroke relationships.
- Export updated schema via:
  ```bash
  DATABASE_URL=postgres://... ./scripts/export_schema.sh
  ```
- Run migrations locally: `alembic upgrade head`
- On Railway, run migrations via one-off job or shell:
  ```bash
  railway run --service lagana-coach-api "alembic upgrade head"
  ```

## 5. Running the Service
- **Development**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **Production**: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- **Docker**: Provided `Dockerfile` installs dependencies from `requirements.txt` and executes the production command.

## 6. API Highlights
- Auth: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, password reset endpoints.
- Coaches: Admin-only management, `GET /api/v1/coaches/me` for coach self-profile.
- Players: CRUD with coach scoping; search and pagination on `GET /api/v1/players`.
- Lessons: CRUD, filterable listing, duration validation, stroke & player associations.
- Invoices: Guided flow (`/generate/prepare`, `/generate/confirm`, `/issue`, `/mark-paid`) including PDF/CSV generation.
- Clubs & Strokes: Admin catalog maintenance.
- Detailed OpenAPI docs available at runtime.

## 7. Invoice Generation Flow
1. **Prepare**: coach posts period, system returns eligible `executed` lessons not yet invoiced plus totals.
2. **Confirm**: coach submits selected lesson IDs; API creates invoice + line items and moves lessons to `invoiced` status.
3. **Issue**: generates PDF (ReportLab) + CSV into `FILE_STORAGE_DIR` and switches status to `issued`.
4. **Mark paid**: `POST /{id}/mark-paid` toggles status to `paid` for bookkeeping.

PDF generator is template-driven for future refinements; update `app/services/invoice.py` to adjust layout.

## 8. Frontend Integration
- Default frontend expects `API_BASE_URL` pointing to `/api/v1`. Configure CORS via `ALLOWED_ORIGINS`.
- The companion Flask web app lives in `../lagana-coach-web` and consumes this API using fetch calls.

## 9. Railway Deployment
### Using Docker (recommended)
1. Push repo to GitHub.
2. Create Railway service from GitHub, enable Dockerfile autodetect.
3. Set environment variables (see section 3) and Railway’s `PORT` is injected automatically.
4. Attach Railway PostgreSQL and set `DATABASE_URL` secret.

### Using Nixpacks / Buildpacks
- Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Ensure `requirements.txt` exists (provided).

### Migrations
- Create Railway job: `alembic upgrade head`
- Run after deployments or automate via deployment hooks.

## 10. Security Considerations
- Passwords hashed with bcrypt via passlib; no plaintext stored or logged.
- JWT secrets sourced from environment; rotate regularly.
- Role-based access enforcement: coaches limited to their players/lessons/invoices, admins full access.
- CORS restricted by `ALLOWED_ORIGINS` to prevent unauthorized browser clients.
- Password reset tokens stored with expiration + single-use guard; email delivery via SMTP.
- Sensitive operations avoid logging PII or secrets.

## 11. Maintenance & Future Extensions
- Add new fields via SQLAlchemy model updates + Alembic migration.
- Additional routers can follow existing structure (`app/api/v1/routers`).
- Extend invoice templates or integrate external storage in `app/services/invoice.py`.
- Swap email provider by updating `app/services/email.py`.

## 12. Troubleshooting
- **Database connection errors**: verify `DATABASE_URL` and network access (Railway Postgres typically requires SSL).
- **CORS issues**: update `ALLOWED_ORIGINS` to include the web app domain.
- **Port conflicts**: ensure no local process uses the configured `PORT`.
- **SMTP failures**: check credentials; when unset, the service logs a warning and skips send.
- **ReportLab missing fonts**: extend PDF generation if you need custom fonts (install into Docker image).

---

### Quick Commands
- Format: `black .`
- Lint: `ruff check .`
- Tests: `SECRET_KEY=test pytest`
- Run migrations: `alembic upgrade head`
- Export schema: `DATABASE_URL=... ./scripts/export_schema.sh`

# Arlo Cloud Testing Deployment Plan

_Written 2026-06-20 based on exploration of the gwexploratoryaudits/arlo fork._

---

## Summary

| Option | Status | Effort |
|--------|--------|--------|
| **Heroku** (new app) | First-class, fully configured | Low |
| **Heroku Review Apps** | Built-in support via `FLASK_ENV=staging` | Low |
| **Docker** | Not present in repo | High (write from scratch) |
| **VPS / "Sprite"** | Undocumented but feasible | Medium |
| **Cypress E2E** | Implemented, runs locally or against a deployed instance | Low |
| **Artillery load test** | Documented but not yet scripted | Medium |

**Fastest path:** Deploy to a new Heroku app using `FLASK_ENV=development` + nOAuth (the built-in pass-through auth) so you skip Auth0 setup entirely.

---

## What the Repo Provides

### Processes (Procfile)

```
release:      ./heroku-release-phase.sh      # alembic upgrade head on every deploy
web:          gunicorn server.app:app --preload --max-requests 1000 ...
worker:       python -m server.worker.worker  # background task processor
slack_worker: python -m server.activity_log.slack_worker
```

For a minimal test instance, only `web` is needed if you set `RUN_BACKGROUND_TASKS_IMMEDIATELY=true`.

### Stack

- **Python 3.11**, **Poetry**, **Flask 3**, **Gunicorn 23**
- **React/TypeScript** frontend built with Vite → `client/build/` served as static files
- **PostgreSQL only** (no SQLite option); Alembic for migrations
- **nOAuth** — a stub OAuth server bundled in the repo; used by `FLASK_ENV=development` and `FLASK_ENV=test` to bypass real Auth0

---

## Option 1: Heroku (Recommended — Easiest)

### What's already there

- `app.json` — defines buildpacks, addons, formation, auto-generates `ARLO_SESSION_SECRET`
- `Procfile` — web + worker + slack_worker + release (migrations)
- `server/config.py` — detects `FLASK_ENV=staging` and derives `HTTP_ORIGIN` from `HEROKU_APP_NAME` (Heroku Review Apps support built-in)
- Build: `heroku-postbuild` in `package.json` runs `yarn build` to compile the React app

### Fix needed in app.json

The addon `heroku-postgresql:hobby-free` was discontinued. Change it to:

```json
"heroku-postgresql:mini"
```

### Steps for a new test app

```bash
heroku create arlo-test-YOURNAME
heroku addons:create heroku-postgresql:mini

# Required env vars
heroku config:set \
  FLASK_ENV=development \
  ARLO_SESSION_SECRET=$(openssl rand -hex 32) \
  ARLO_HTTP_ORIGIN=https://arlo-test-YOURNAME.herokuapp.com \
  RUN_BACKGROUND_TASKS_IMMEDIATELY=true \
  ARLO_FILE_UPLOAD_STORAGE_PATH=/tmp/arlo-uploads

# Skip worker dyno for minimal test
heroku ps:scale worker=0 slack_worker=0

git push heroku main
```

With `FLASK_ENV=development`, nOAuth is activated — no Auth0 credentials needed. The release phase runs `alembic upgrade head` automatically.

### Heroku Review Apps (per-PR staging)

`server/config.py` already handles this:

```python
if os.environ.get("FLASK_ENV") == "staging":
    HTTP_ORIGIN = f"https://{os.environ['HEROKU_APP_NAME']}.herokuapp.com"
```

Enable in the Heroku Dashboard: connect the GitHub repo, create a pipeline, enable Review Apps. Each PR gets its own ephemeral app with its own DB. Fix the `hobby-free` → `mini` addon in `app.json` first.

---

## Option 2: VPS / "Sprite" (e.g., DigitalOcean Droplet, Hetzner)

No systemd units or nginx config exist in the repo, but the path is straightforward on **Ubuntu 24**.

### Setup

```bash
# 1. Install system deps (requires Ubuntu 24)
make dev-environment      # installs Python 3.11, Node 22, Poetry, Yarn, postgres

# 2. Install app deps
make install              # poetry install + yarn --cwd client install

# 3. Set up databases
make dev-dbs              # creates postgres user 'arlo', runs resetdb

# 4. Build frontend
yarn --cwd client build

# 5. Set env vars (in a .env file or systemd EnvironmentFile)
export FLASK_ENV=development
export DATABASE_URL=postgresql://arlo:arlo@localhost:5432/arlo
export ARLO_SESSION_SECRET=$(openssl rand -hex 32)
export ARLO_HTTP_ORIGIN=https://YOUR_DOMAIN
export RUN_BACKGROUND_TASKS_IMMEDIATELY=true
export ARLO_FILE_UPLOAD_STORAGE_PATH=/var/lib/arlo/uploads

# 6. Run migrations
poetry run alembic upgrade head

# 7. Start app
poetry run gunicorn server.app:app --bind 0.0.0.0:5000 --preload
```

### Still needed (not in repo)

- **nginx/Caddy** as reverse proxy (TLS termination, static file serving)
- **systemd units** for gunicorn, worker (if needed), and nOAuth
- **Firewall rules** (ufw)

A minimal Caddy config would proxy `localhost:5000` and handle Let's Encrypt automatically. Estimated ~2 hours to hand-roll.

---

## Option 3: Docker (Not Yet Available)

No `Dockerfile` or `docker-compose.yml` exists. Writing one from scratch would require:

- Multi-stage build (Node build stage → Python runtime stage)
- Postgres service in compose
- Volume for file uploads
- Health checks

This is a medium-effort task (~1 day). The Heroku path is strictly easier for cloud testing.

---

## Testing Tooling

### Unit / Integration Tests (server)

```bash
make test
# → pytest -n auto --ignore=server/tests/arlo-extra-tests
```

Uses `pytest-xdist` for parallel execution against a local `arlotest` PostgreSQL DB. Includes `pytest-alembic` for migration correctness.

```bash
make -C client test
# → vitest (frontend unit tests)
```

### End-to-End Tests (Cypress)

```bash
./client/run-cypress-tests.sh
```

Starts the full dev stack (`run-dev.sh`: nOAuth + Flask + Vite), waits for port 3000, then runs Cypress. Can also point Cypress at a deployed instance by setting the base URL.

To run E2E against a cloud instance:

```bash
CYPRESS_BASE_URL=https://arlo-test-YOURNAME.herokuapp.com \
  yarn --cwd client cypress run
```

### Load Testing (Artillery — Planned, Not Implemented)

`docs/loadtesting.md` documents an **Artillery** / **Serverless Artillery** (AWS Lambda) approach designed to bypass Auth0 using nOAuth. No scripts are committed yet. Key design points from the doc:

- Use `FLASK_ENV=development` (nOAuth) so load tests don't hit real OAuth
- `scripts/seed-probely-db.sh` + `probely-data/` show a pattern for seeding a DB with test data before a test run
- Serverless Artillery runs load generation from Lambda to avoid client-side bottlenecks

Estimated ~1 day to write a basic Artillery script suite against a Heroku test instance.

### Security / DAST (Probely)

`scripts/seed-probely-db.sh` and `probely-data/probely-arlo.db` suggest **Probely** (a DAST scanner) has been run against a seeded Arlo instance. The seed script populates a known-state DB for repeatable scans.

---

## Required Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Always | PostgreSQL URL |
| `ARLO_SESSION_SECRET` | Always | Cookie signing key |
| `ARLO_HTTP_ORIGIN` | Always | Full origin (e.g. `https://arlo.example.com`) |
| `FLASK_ENV` | Always | `development` uses nOAuth; `production` requires Auth0 |
| `ARLO_FILE_UPLOAD_STORAGE_PATH` | Always | Local path or `s3://bucket/prefix` |
| `ARLO_SUPPORT_AUTH0_*` | Production only | Skip with `FLASK_ENV=development` |
| `ARLO_AUDITADMIN_AUTH0_*` | Production only | Skip with `FLASK_ENV=development` |
| `ARLO_SMTP_*` | Production only | Email login codes for jurisdiction admins |
| `RUN_BACKGROUND_TASKS_IMMEDIATELY` | Optional | `true` → skip worker dyno, run tasks inline |
| `AWS_*` | Optional | Only if using S3 for file storage |

---

## Recommended Path for Quick Cloud Testing

1. **Fix `app.json`** — change `heroku-postgresql:hobby-free` to `heroku-postgresql:mini`
2. **Create Heroku app** — `heroku create arlo-test-YOURNAME`
3. **Set env vars** — `FLASK_ENV=development`, `RUN_BACKGROUND_TASKS_IMMEDIATELY=true`, origin, session secret, local file path
4. **Push** — `git push heroku main` (builds frontend, runs migrations, starts web dyno)
5. **Run Cypress E2E** against the live URL to validate

For per-PR automated testing, enable Heroku Review Apps in the pipeline (low config, already supported by the codebase).

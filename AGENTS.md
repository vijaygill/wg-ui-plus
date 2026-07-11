# AGENTS.md

## Project overview

WireGuard UI Plus — a Dockerised Django + Angular app for managing a WireGuard VPN. Two main components:
- **Backend**: Django REST API (`src/api_project/`) with SQLite (`/data/wg_ui_plus.db`)
- **Frontend**: Angular 21 + PrimeNG SPA (`src/clientapp/`), output served by Django via `django-spa` middleware

## Key commands

### Python tests (run inside dev Docker container)
```bash
# From repo root, enter dev shell first:
./run-dev-shell.sh
# Then inside the container:
cd /app/api_project
../scripts/run-tests.sh
# Or directly:
pytest --doctest-modules --junitxml=junit/test-results.xml --cov=com --cov-report=xml --cov-report=html
```

### Angular build
```bash
# Build (in dev container or host):
cd src/clientapp && npm install && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/"
# Watch mode:
ng build --configuration development --watch --prerender=false --deploy-url="/" --base-href="/"
```

### Angular tests
```bash
cd src/clientapp && ng test
```

### Docker image build
```bash
./build-docker-images.sh dev     # dev image
./build-docker-images.sh live    # live image
./build-docker-images.sh all     # both
```

### Local dev (all inside Docker)
```bash
# Terminal 1: Angular watch build
./run-ng-build-watch.sh
# Terminal 2: Django dev server
./run-app-dev.sh
# Terminal 3: Dev shell for editing / running tests
./run-dev-shell.sh
```

## Architecture notes

- **Single multi-stage `Dockerfile`** with 5 targets: `base-dev` (Debian/Node), `base-live` (Alpine/Python), `builder` (Angular build), `dev` (dev shell), `live` (production)
- Angular build output (`dist/wg-ui-plus/browser/`) is volume-mounted into the Django container at `/app/clientapp`
- Django serves the SPA and static files via `whitenoise` + `django-spa`
- Startup sequence (in `scripts/run-app.sh`): backup_db → makemigrations → migrate → db_init_db_on_start → clear_cache → wg_generate_config → runserver on `:8000`
- WireGuard config lives at `/config/wireguard/wg0.conf`
- Environment config in `docker-env.txt` (gitignored: use `docker-env-dev.txt` for local overrides)
- Custom Django management commands in `src/api_project/api_app/management/commands/`
- REST API routes all under `/api/v1/` (data, auth, control endpoints)
- CI builds all stages from scratch (no pre-built base images); Docker BuildKit caching compensates

## Branching (from devenv.md)

- `feature/*` — new features, messy commits OK
- `experimental/*` — ad-hoc experiments, may be promoted or dropped
- `develop` — semi-stable, **squash merge** from feature branches
- `main` — releases only, merged from develop, triggers Docker image push

## Gotchas

- Default login: `admin/admin`
- The `config/` and `data/` directories are gitignored — they hold runtime state (SQLite DB, WireGuard config)
- CI builds multi-arch images (amd64 on ubuntu-latest, arm64 on self-hosted runner)
- The `--prerender=false` flag is required on Angular build for this SPA
- `docker-env-dev.txt` is gitignored; `docker-env.txt` is committed as a template
- Python deps are installed with `--break-system-packages` (no venv used)

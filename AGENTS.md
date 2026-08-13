# AGENTS.md

## Project at a glance

WireGuard UI Plus is a Dockerized Django/DRF backend and Angular 22 single-page
application for managing a WireGuard VPN. The frontend and backend run in one
container; Django serves the Angular build through `django-spa` and WhiteNoise.

Important paths:

- `src/api_project/` — Django project and the `api_app` application. Models,
  serializers, viewsets, WireGuard helpers, MCP integration, migrations, and
  management commands live here.
- `src/clientapp/src/app/` — Angular components, routes, services, and shared
  Material modules. The app uses standalone components alongside
  `AppSharedModule`; component styles are SCSS.
- `scripts/` — container startup, Angular watch-build, test, and WireGuard/
  iptables monitoring scripts.
- `Dockerfile` — the source of truth for development and production images.
- `data/` and `config/` — runtime mounts. Their runtime contents are ignored;
  placeholder files in these directories may be tracked, so do not edit or
  commit generated runtime state.

## Development workflow

### Every development session (required)

The current workspace/container does not provide reliable facilities for
executing or testing this project's Angular or Django/backend code. Always use
the `wg-ui-dev-shell` container for Angular builds, backend tests, Django
commands, and any other executable validation. Before attempting validation,
check that the `wg-ui-dev-shell` container is available. If it is not
available, stop and ask the user to run `./run-dev-shell.sh`; do not test
elsewhere or silently start it. Start it from the repository root with:

```bash
./run-dev-shell.sh
```

Once available, run backend tests, Django management commands, and ad hoc
Angular commands inside this shell. The standalone launch scripts
`run-ng-build-watch.sh` and `run-app-dev.sh` are for live development processes
only and are not alternatives for executable validation.

In this development environment, the IDE itself runs inside a container, so
mounts exposed to its Docker CLI may not work correctly when images are run
directly from the IDE container. This is an environment limitation, not a
repository-enforced configuration; use `wg-ui-dev-shell` for the supported
interactive testing and inspection workflow. It provides the useful
repository mapping `/workspace` → `/wg-ui-plus`, making changes available for
testing in the shell container.

After the shell starts, access the mounted repository at `/wg-ui-plus`:

```bash
cd /wg-ui-plus
cd /wg-ui-plus/src/clientapp       # Angular commands
cd /app/api_project                # Django commands and tests
```

Docker is the supported development environment. Build both local images from
the repository root (the script does not use positional target arguments):

```bash
./build-docker-images.sh
```

For the live development loop, run the standalone launch scripts in separate
terminals:

```bash
./run-ng-build-watch.sh  # Angular development build/watch
./run-app-dev.sh         # Django runserver on http://localhost:8000
```

The development-container launch scripts use `docker-env-dev.txt` when it
exists, otherwise `docker-env.txt`. This applies to `run-ng-build-watch.sh`,
`run-app-dev.sh`, and `run-dev-shell.sh`; the image-build script invokes
`docker build` separately and does not use those environment-file run options.
The launch scripts mount the repository and
`src/clientapp/dist/wg-ui-plus/browser` into containers and expect the
`wg-ui-plus-dev` image to exist. They also pass WireGuard capabilities,
networking sysctls, `/config`, `/data`, and host modules; use a host with
Docker privileges suitable for WireGuard work.

For ad hoc frontend work, the dev shell is required because the Docker image
installs Angular CLI globally. From `./run-dev-shell.sh`, run:

```bash
cd /wg-ui-plus/src/clientapp
npm install
ng build --configuration production --prerender=false --deploy-url=/ --base-href=/
ng test
```

On the host, install/use a compatible Angular CLI explicitly; `@angular/cli`
is not a project dependency. The application is a Django-backed SPA, so retain
`--prerender=false` and the root deploy/base URLs for production-like builds.
The repository currently has no Angular `*.spec.ts` files, but the Karma target
is configured. The generated `dist/`, Angular cache, and `node_modules/` are
build artifacts, not source changes.

## Backend tests and commands

Inside `./run-dev-shell.sh`, the repository is at `/wg-ui-plus` and the Django
project is also mounted at `/app/api_project`:

```bash
cd /app/api_project
../scripts/run-tests.sh
```

That script runs pytest doctests, writes JUnit output under `junit/`, and emits
coverage XML/HTML. The equivalent command below mirrors
`scripts/run-tests.sh`, but its `--cov=com` target appears stale because the
application code is under `src/api_project/api_app`; do not change the script
without separately addressing that configuration:

```bash
pytest --doctest-modules --junitxml=junit/test-results.xml --cov=com --cov-report=xml --cov-report=html
```

The main checked-in backend tests are `tests/test_mcp.py`; there is also a
minimal `src/test_sample-tests.py`. Run focused tests with pytest when useful.
Use Django management commands from `/app/api_project`, for example:

```bash
./manage.py makemigrations
./manage.py migrate
./manage.py check
```

Do not hand-edit migration files; review generated migrations before including
them.

## Runtime and architecture

- `Dockerfile` stages are `base-dev` (Debian, Node, Python, WireGuard tools),
  `base-live` (Alpine/Python runtime), `builder` (Angular production build),
  `dev`, and `live`. Python packages are installed in the images with pip
  using `--break-system-packages`; there is no requirements lock file or venv.
- The live image copies Angular output to `/app/clientapp`, Django to
  `/app/api_project`, and starts `/app/scripts/run-app.sh` as a non-root user.
- Startup backs up the SQLite database, runs `makemigrations` and `migrate`,
  initializes application/MCP state, clears cache, generates WireGuard files,
  brings up `/config/wireguard/wg0.conf` when present, then runs Django's
  development server on `0.0.0.0:8000`. The database is
  `/data/wg_ui_plus.db`; generated config/scripts are under `/config`.
- API routes are split between `src/api_project/api_app/urls.py` (the
  `/api/v1/data/`, `/api/v1/auth/`, and `/api/v1/control/` routes) and
  `src/api_project/api_project/urls.py` (the `/mcp` Streamable HTTP endpoint).
- The domain model is `ServerConfiguration`, `Peer`, `PeerGroup`, and `Target`.
  Peer groups connect peers to targets; WireGuard configuration and iptables
  changes are generated from those relationships.
- Runtime configuration is environment-driven where documented in `README.md`
  (WireGuard network/ports, DNS, host name, timezone, CORS/CSRF, logging,
  email, and `WG_MCP_SERVER_ENABLED`). MCP is disabled by default, but when the
  environment variable is absent an existing database setting controls it.
  The endpoint accepts `Bearer` and legacy `Token` authorization and exposes
  curated tools described in `docs/MCP.md`. Treat the MCP token as a high-privilege
  credential: it can access peer configuration/QR data and WireGuard/control
  operations, has no per-user authorization boundary, and must not be exposed
  casually. Keep credentials and tokens out of the repository and logs.

## Deployment and safety warnings

- The example Compose file is a template, not production-ready configuration:
  it uses placeholder paths/host values, maps host UDP `1195` to container
  `51820`, sets `CORS_ALLOW_ALL_ORIGINS=true`, and includes `PUID`/`PGID`
  variables that the application does not consume. Configure
  `WG_PORT_EXTERNAL` consistently with the router and host mapping, restrict
  CORS, and use authentication, TLS, and a reverse proxy before exposing the
  UI beyond a trusted network.
- The default first-login credentials are `admin` / `admin`; change the
  password immediately. Do not treat the development server, broad host/CORS
  settings, or the example environment as hardened production settings.
- Persist and back up both `/data` and `/config` before upgrades. Container
  startup mutates the database, regenerates WireGuard configuration, and may
  start WireGuard; test changes against disposable mounts where possible.
- Local application run scripts publish TCP `8000` and UDP `1196` and use
  privileged WireGuard-related Docker options. `run-app-live.sh` uses the
  common wrapper, which bind-mounts the repository's `data/` and `config/`; it
  does not provide a production volume/reverse-proxy setup. Use explicit
  durable volume mounts or the Compose example for real deployment.

## CI and repository conventions

The GitHub Actions Docker workflow builds and pushes the `live` target for
amd64 on `ubuntu-latest` and arm64 on a `self-hosted` runner, then creates
multi-architecture manifests for pushes/releases. It is triggered for changes
under `src/`, `scripts/`, `Dockerfile`, or `LICENSE` on `develop`/`master`, as
well as selected pull-request, release, and manual events. Keep Docker build
inputs and image metadata in mind when changing those paths.

Branch documentation is inconsistent: the active Docker workflow targets
`develop` and `master`. Do not silently treat either description as universally
authoritative; check the active workflow, current repository policy, and branch
protection before making branch or release decisions.

Use feature branches such as `feature/<short-name>` for normal work and
`experimental/<short-name>` for disposable experiments. Preserve the
repository's existing branch policy rather than assuming a `main` or `master`
release convention without checking.

Before finishing code changes, inspect `git diff`, avoid committing runtime
data, generated artifacts, credentials, or tokens, and run the smallest
relevant backend/frontend/Docker validation available in the dev environment.

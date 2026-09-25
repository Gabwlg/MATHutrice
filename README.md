# MATHutrice

LLM-based tutor that helps EPF first-year students practise mathematical tools through notions, competences and training. See [`CONTEXT.md`](CONTEXT.md) for the vocabulary used throughout the code and this README, and [`docs/adr/`](docs/adr) for the decisions behind it.

Students train on notions and get scored per competence; teachers track progression and upload reference material; an LLM chat, backed by an OpenAI-compatible **LLM endpoint**, answers questions and evaluates open-ended answers.

## Running locally

Requires Python 3.14 (pinned in `.python-version`) and [uv](https://docs.astral.sh/uv/).

```sh
git clone -b course-2026 <your fork URL> mathutrice
cd mathutrice
uv sync
. .venv/bin/activate
cp .env.example .env
```

Without `uv`, `pip install -e .` in a Python 3.14 virtual environment installs the project from `pyproject.toml` instead of the lockfile.

`.env.example` lists and documents every variable the application reads; the defaults work out of the box except `LLM_API_KEY`, which you must set to a key for the LLM endpoint (Mistral by default — a free account works, at <https://console.mistral.ai>).

Start the app from the repository root:

```sh
uvicorn mathutrice.app:app --port 8000
```

To check that a clone actually runs — startup, sign-in, chat streaming — follow [`docs/smoke-test.md`](docs/smoke-test.md).

## Configuration

Every variable is documented in `.env.example`. The ones worth knowing about going in:

| Variable | Purpose |
| --- | --- |
| `AUTH_MODE` | `entra` (default) or `dev`. See **Dev sign-in** below. |
| `SESSION_SECRET` | Signs session cookies. Always required; see the caveat below. |
| `DATABASE_URL` | Defaults to a local SQLite file; point it at PostgreSQL in deployed environments. |
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | The **LLM endpoint** (see `CONTEXT.md`). `LLM_API_KEY` is required — the app refuses to start without it. |
| `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, `REDIRECT_URL`, `POST_LOGOUT_REDIRECT_URL` | Microsoft Entra ID app registration. Required only when `AUTH_MODE=entra`. |

## Dev sign-in

With `AUTH_MODE=dev`, the app starts without any Entra configuration, and `/` redirects to `/dev/login`: a page to sign in as any email from an allowed domain (`@epfedu.fr` or `@epf.fr`) with any role (Student, Teacher, Admin) and no proof of identity — the **connexion de développement** described in `CONTEXT.md`. A warning shows on the sign-in page itself, a red banner marks every page after sign-in while dev mode is active, and the app prints a startup warning.

`DEV_LOGIN_KEY`, when set, is a shared key the sign-in form must also submit; it keeps casual visitors out of a deployed fork that runs in dev mode. Leave it empty locally.

**`SESSION_SECRET` caveat**: `.env.example` ships a placeholder value for local use. If a deployed fork keeps that placeholder, anyone who knows it can forge a session cookie and sign in as any user, bypassing `DEV_LOGIN_KEY` entirely. Always set a real random secret before deploying, and especially so when `AUTH_MODE=dev`.

Scripts can sign in the same way with a single form POST, keeping the session cookie for later requests:

```sh
curl -c cookies.txt -b cookies.txt \
  -d "email=alice@epfedu.fr" -d "role=student" \
  http://localhost:8000/dev/login
curl -b cookies.txt http://localhost:8000/
```

Add `-d "key=<DEV_LOGIN_KEY>"` when the target deployment sets one.

## Deploying

Before exposing a deployment publicly, check:

- [ ] `AUTH_MODE` non défini ou `entra` — dev sign-in must not be reachable in production.
- [ ] `SESSION_SECRET` is a real random secret, not the `.env.example` placeholder.
- [ ] `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, `REDIRECT_URL` and `POST_LOGOUT_REDIRECT_URL` are set for this fork's own Entra app registration and URL.
- [ ] `LLM_API_KEY` is set.
- [ ] On the Mistral free plan, training use is turned off in the admin panel under Privacy.
- [ ] `DATABASE_URL` points at PostgreSQL, not the default SQLite file.

# FairAid Backend

Transparent, explainable pre-screening of bursary / financial-aid schemes for students. Advisory only:
the system never submits applications or makes binding funding decisions (human-in-the-loop policy).

Ported from FastAPI to **Django + Django REST Framework**. The HTTP API is unchanged: same URLs
(`/api/...`), same JSON shapes, same JWT session behaviour.

## Layout

```
config/                  Django project: settings/{base,dev,prod,test}.py, urls.py, wsgi/asgi
apps/
  common/                Domain exceptions + the single place they become HTTP responses
  accounts/              User + RefreshToken models, JWT tokens, auth/session/user services, permissions
  schemes/               BursaryScheme model, service, default scheme data, `seed_schemes` command
  prescreening/          PrescreenRecord model + service + views
    engine/              PURE PYTHON decision engine (rules/, tree, evaluator, explainer, types)
  fairness/              PURE PYTHON audit (metrics, demographics, mitigations, audit) + staff-only view
  governance/            Human-in-the-loop policy + guardrail endpoints
tests/                   pytest suite incl. parity tests against the original FastAPI output
docs/                    openapi.json (generated), Postman collection
```

### Responsibilities and dependency direction

| Layer | Job | Knows about |
|---|---|---|
| `views.py` | Parse/validate input, call one service, serialise output | serializers, services, permissions |
| `serializers.py` | Request/response shape and validation | models (some) |
| `services.py` | Business workflows and transactions | models, engine, other services |
| `models.py` | Persistence only | Django ORM |
| `prescreening/engine`, `fairness/` | Eligibility + fairness logic | **nothing from Django** |
| `prescreening/adapters.py` | Convert model/serializer data to engine types | models, engine |

Rules: views never touch the ORM; services never touch `request`; the engine never imports Django.
To add an eligibility criterion, drop a module in `apps/prescreening/engine/rules/` and register it in
its `__init__.py`. To add a fairness mitigation, add a function to `apps/fairness/mitigations.py`.

## Setup

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                  # set SECRET_KEY (and DATABASE_URL for Postgres)
python manage.py migrate
python manage.py createsuperuser                      # prompts: email, full name, password
python manage.py seed_schemes                         # idempotent; writes straight to the DB
python manage.py runserver                            # Swagger UI at /docs, schema at /openapi.json
```

Other commands:

```bash
python manage.py fairness_audit [--applicants 300 --seed 42]
pytest
```

`manage.py` uses `config.settings.dev`; `wsgi.py`/`asgi.py` use `config.settings.prod`, which refuses
to start without `SECRET_KEY`. Run in production with `gunicorn config.wsgi`.

## Authentication & roles

Unchanged: `POST /api/auth/login` (form fields `username`=email, `password`) returns a 30-minute access
token and a 7-day refresh token tied to a server-side session; refresh tokens rotate and reuse revokes the
session; logout revokes the access token immediately.

| Endpoint | Public | Student | Admin | Superuser |
|---|:-:|:-:|:-:|:-:|
| `POST /auth/signup`, `/auth/login`, `/auth/refresh` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/logout`, `/auth/logout-all`, `GET /auth/me` | | ✅ | ✅ | ✅ |
| `GET /schemes`, `/governance/*` | ✅ | ✅ | ✅ | ✅ |
| `POST /prescreen`, `GET /prescreen/history` | | ✅ | | |
| `POST /schemes`, `GET /fairness/audit` | | | ✅ | ✅ |
| `/users` (create admins, change roles, deactivate) | | | | ✅ |

## AI explanation assistant (`apps/explanations`)

Turns the decision tree's stored result into plain language and answers follow-up questions. The model only
**explains**: `match_status` always comes from the engine, and the model's text is shown only if it passes
`grounding/guardrails.py` (no contradiction of the engine, no promises, links or invented numbers).

| Endpoint | What it does |
|---|---|
| `POST /api/prescreen/history/{id}/explain` | Conversational explanation of every scheme (1 model call, cached) |
| `POST /api/prescreen/history/{id}/ask` | Follow-up question; remembers the last `LLM_HISTORY_TURNS` turns |
| `GET/DELETE /api/prescreen/history/{id}/conversation` | Read or clear that run's conversation |
| `GET /api/explanations/quota` | Provider, model and remaining quota (admin) |

**What-if questions** ("what if my income were 200k?"): the model only translates the question into a change.
The change is validated (only `nqf_level`, `household_income`, `field_of_study`, `region`; every value must appear
in what the student wrote; never disability), the decision tree is re-run on it, and the before/after results come
from the engine. Nothing is saved.

**Choosing the model** (`LLM_PROVIDER` in `.env`):

| | `gemini` (free tier) | `ollama` (e.g. Llama 3.2 3B) |
|---|---|---|
| Limits | ~5 requests/min and a small daily budget; a shared gate serialises requests and falls back to engine wording | none; still one request at a time |
| Hosting | none | you run Ollama (`ollama pull llama3.2:3b`) |
| Quality | strong | weaker; expect more rejected answers (the engine wording is shown instead) |
| Data | prompts leave your server | stays on your server |

With no key, or with the model down, every endpoint still works using the engine's own wording.


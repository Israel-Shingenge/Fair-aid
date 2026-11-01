# FairAid frontend

Student-facing HTML, CSS and JavaScript for FairAid. This folder is the frontend contribution only. No Django backend files have been changed.

## Run locally

Open this folder in VS Code and serve it with Live Server, or run `python -m http.server 5500` from inside the folder and visit `http://localhost:5500`. Do not open `index.html` directly from the iPhone Files app: use a served URL.

## Connect to the Django backend

The API defaults to `http://localhost:8000`. If needed, set the API address in `index.html` **before** the `js/app.js` script tag:

```html
<script>window.FAIRAID_API_BASE = 'http://192.168.1.10:8000';</script>
```

Use your laptop's reachable LAN IP when testing from a phone on the same Wi-Fi. This setting alone does not expose Django to the network: the backend developer must configure allowed hosts, listening interface, CORS and any required firewall rules. Never use a public HTTP API for real student data.

## API integration

The Django REST Framework backend preserves the `/api/` endpoints. The frontend calls `/api/auth/signup`, `/api/auth/login` (form encoded), `/api/auth/refresh`, `/api/auth/logout`, `/api/schemes`, `/api/prescreen`, `/api/prescreen/history`, and the history explanation endpoints.

The `POST /api/prescreen` endpoint returns an array of scheme results, **not** a run ID. The frontend looks up the saved run in history using the submitted circumstances and result values. For identical concurrent screenings this cannot guarantee unique identification; a backend response containing the run ID would be a more reliable future contract.

## Testing without the backend

The sample-student button starts a **fictional, browser-only** flow with invented schemes and simple illustrative rules. It is not real eligibility advice, authentication or persistent history. Real API integration needs a running Django server.

## Scope

Only files in this frontend folder belong to this contribution. Do not change the backend `apps/`, `config/`, or `manage.py` to accommodate the frontend without coordination with its owner.


## Student guide and homepage

The homepage uses one fixed campus photograph behind the hero and half-width frosted information section. The footer is dark translucent glass. The second-section link opens `#guide`, a frontend-only student guide describing the five inputs, rule-based pre-screening, classification, AI explanations, history, and advisory safeguards. This does not change Django backend code.


## General screening flow (31 October 2026)
- Explore Funding and View Details are informational. Scheme details do not start scheme-specific screening.
- Check Eligibility is in the main navigation and on the homepage. It sends the five existing fields to POST /api/prescreen without a scheme ID.
- The results page displays every result returned by the API, sorted by Likely eligible, Possibly eligible, Not eligible, then by criteria-match score. It does not manufacture results for directory entries.
- No backend files or endpoints were changed. The local sample-student mode uses fictional schemes and illustrative results only.
- Real sign-in, API screening and history still require a running, reachable Django backend with suitable CORS settings.

## Vertex-AI-Testing (google-genai)

Small Python CLI chatbot that calls Gemini models using the `google-genai` SDK.

- `main.py` loads settings from `.env` (via `python-dotenv`)
- It supports **two backends**:
  - **Gemini Developer API** (API key auth)
  - **Vertex AI** (OAuth/IAM via Application Default Credentials, or Vertex API key setups)

> Note: The current `SYSTEM_PROMPT` in `main.py` is a mental health support companion prompt. This is not medical care. If you or someone else is in immediate danger, call your local emergency number. In the US, you can call or text `988` for the Suicide & Crisis Lifeline.

## Requirements

- Python `>= 3.12` (see `pyproject.toml`)
- Dependencies are pinned in `uv.lock` and declared in `pyproject.toml`

## Install

### Option A: uv (recommended)

This repo includes `uv.lock`.

```bash
uv sync
```

### Option B: pip

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install google-genai python-dotenv
```

## Configuration

Create a `.env` file (use `.env.example` as a template).

### Gemini Developer API (API key)

Fastest local setup. Uses an API key and does not require `gcloud`.

`.env`:

```env
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_API_KEY=AIza...your_api_key...
GEMINI_MODEL=gemini-2.5-flash
```

Important:

- `main.py` validates that `GOOGLE_API_KEY` looks like a real API key (typically starts with `AIza`).
- OAuth access tokens / ephemeral tokens (often starting with `AQ...`, `ya29...`, or `Bearer ...`) are not API keys and will fail.

### Vertex AI (ADC / OAuth)

Use this when you want IAM-based auth, GCP project scoping, enterprise controls, or when a model is only available to you via Vertex.

#### Local development (your personal Google account)

1. Authenticate Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

This saves a credential file to `~/.config/gcloud/application_default_credentials.json`. The SDK picks it up automatically — no extra env vars needed for auth.

2. Set Vertex-related env vars in `.env`:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

> **Do not use `gcloud auth application-default login` credentials in production.** They are tied to your personal Google account and expire. Use a service account instead (see below).

#### Production (service account)

Service accounts are GCP identities created for applications rather than people. They authenticate without a browser and are the correct credential type for deployed workloads.

**Option A — Running on Google Cloud (Cloud Run, GKE, GCE, Cloud Functions, etc.)**

Attach a service account to your compute resource at deploy time. The SDK picks up credentials automatically from the GCP metadata server — no key files or env vars needed.

1. Create a service account in your GCP project and grant it the `Vertex AI User` role (`roles/aiplatform.user`).
2. Attach it to your Cloud Run service, GCE instance, etc. during deployment.
3. Your `.env` needs only:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

**Option B — Running outside Google Cloud (on-prem, other cloud, CI/CD)**

1. Create a service account and grant it the `Vertex AI User` role (`roles/aiplatform.user`).
2. Download a JSON key file from the GCP Console (IAM & Admin → Service Accounts → Keys).
3. Point the SDK at it via `GOOGLE_APPLICATION_CREDENTIALS`:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

> **Security:** Never commit JSON key files or secrets to source control. Add them to `.gitignore`. Prefer Option A (attached service account) when possible to avoid managing key files altogether.

Notes:

- `GOOGLE_CLOUD_LOCATION` must be a region supported by your Vertex setup (commonly `us-central1`).
- You may also need to enable the Vertex AI API (`aiplatform.googleapis.com`) in your GCP project.

## Run

With uv:

```bash
uv run python main.py
```

With venv:

```bash
.venv/bin/python main.py
```

## Gemini API vs Vertex AI (what’s different?)

Both can run Gemini models, but they differ in how you authenticate, manage access, and operate in production.

### Gemini Developer API

- Auth: API key (`GOOGLE_API_KEY` / `GEMINI_API_KEY`)
- Best for: quick local experiments, prototypes, simple deployments
- Operational model: not tied to a GCP project/region in the same way as Vertex

### Vertex AI

- Auth: OAuth/IAM (ADC) and GCP project scoping (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`)
- Best for: production workloads on GCP, centralized billing, IAM controls, auditability, quotas by project, regional placement
- Operational model: requests are scoped to a specific GCP project and region

In this repo, the switch is controlled by:

- `GOOGLE_GENAI_USE_VERTEXAI=true|false` (see `main.py`)

## Project Basics

- `main.py`: REPL-style CLI loop:
  - Builds a `genai.Client(...)` for either Developer API or Vertex
  - Calls `client.models.generate_content(...)`
  - Passes `SYSTEM_PROMPT` via `types.GenerateContentConfig(system_instruction=...)`
- `.env.example`: template env file
- `pyproject.toml`: Python version + dependencies
- `uv.lock`: locked dependency set for `uv`

## Troubleshooting

### `401 UNAUTHENTICATED: API keys are not supported by this API`

Common causes:

- You are using a token (OAuth/ephemeral) in `GOOGLE_API_KEY` instead of an API key.
- You intended to use Vertex, but `GOOGLE_GENAI_USE_VERTEXAI` is `false` / unset.

Fix:

- For Developer API: use a real API key (`AIza...`) and keep `GOOGLE_GENAI_USE_VERTEXAI=false`.
- For Vertex: set `GOOGLE_GENAI_USE_VERTEXAI=true` and run `gcloud auth application-default login`.

### `GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_VERTEXAI=true`

Set `GOOGLE_CLOUD_PROJECT` in `.env` (and usually `GOOGLE_CLOUD_LOCATION`).

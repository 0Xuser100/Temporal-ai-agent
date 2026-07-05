# Temporal Agent — AI Contract Review Pipeline

Hands-on Python project for learning [Temporal](https://temporal.io/) by building an
AI-powered contract review system:

- **`apps/client-app`** — FastAPI service that starts workflows and talks to Temporal
  (Signals, Queries, Updates). It never imports worker code.
- **`apps/ai-contract-review`** — Temporal worker that runs the workflows: fan-out to
  child workflows (one per PDF), extract text from S3 PDFs, summarize with an LLM,
  synthesize a risk report, then pause for human-in-the-loop approval.

## Repository layout

```text
.
├── apps/
│   ├── client-app/                  # FastAPI client API (start/query/signal workflows)
│   │   └── main.py
│   └── ai-contract-review/          # Temporal worker + workflows
│       ├── worker.py                # Runs the workflows + activities
│       ├── parent_workflow.py       # ContractReviewWorkflow (fan-out + HITL review)
│       ├── child_workflow.py        # PDFSummaryWorkflow (extract + summarize one PDF)
│       ├── activities.py            # extract_pdf / call_llm activities
│       └── prompts.py               # LLM prompt templates
└── setup/
    └── samples-server/              # Local Temporal server (Docker Compose)
```

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — dependency management and running the apps
- **Docker + Docker Compose** — for the local Temporal server
- Access to an **S3-compatible bucket** (AWS S3, MinIO, etc.) holding the contract PDFs
- An **OpenAI-compatible API key** for the LLM activity

## How to run

### Step 0 — Install uv (first time only)

All apps are run with [uv](https://docs.astral.sh/uv/), which also installs their
dependencies automatically on first run.

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the install with `uv --version` (restart your terminal if the command is not
found).

Then run the three pieces **in this order**:

### Step 1 — Start the Temporal server (Docker)

```bash
cd setup/samples-server/compose
docker compose -f docker-compose-postgres.yml up -d
```

Local endpoints once it is up:

- Temporal Frontend (gRPC): `localhost:7233`
- Temporal Web UI: <http://localhost:8080>

### Step 2 — Start the client app (FastAPI)

```bash
cd apps/client-app
cp .env.example .env        # first time only — defaults work for the local server
uv run uvicorn main:app --reload
```

The API is now available at <http://localhost:8000> (interactive docs at
<http://localhost:8000/docs>).

### Step 3 — Start the contract-review worker

```bash
cd apps/ai-contract-review
cp .env.example .env        # first time only — fill in S3 + OpenAI credentials
uv run python worker.py
```

You should see: `Worker running on: 'contract-review-queue'`

### Step 4 — Trigger a review

With all three running, start a review through the client app:

```bash
curl -X POST http://localhost:8000/contract-review/start \
  -H "Content-Type: application/json" \
  -d '{
    "s3_paths": [
      "s3://temporal-dev/ContractReview/nda-innovate-consultpro.pdf",
      "s3://temporal-dev/ContractReview/software-license-globalsoft.pdf"
    ],
    "max_revisions": 2
  }'
```

Then use the returned `workflow_id` to check status, read the report, and
approve/revise — see [apps/client-app/README.md](apps/client-app/README.md) for the
full endpoint list. Watch the workflow execute live at <http://localhost:8080>.

## Configuration

Each app reads its settings from a `.env` file (copy `.env.example` in each app dir):

| Variable | Used by | Description |
|---|---|---|
| `TEMPORAL_HOST` | both | Temporal frontend, e.g. `localhost:7233` |
| `TEMPORAL_NAMESPACE` | both | e.g. `default` |
| `TEMPORAL_CONTRACT_REVIEW_TASK_QUEUE` | client-app | e.g. `contract-review-queue` |
| `TEMPORAL_PDF_PROCESS_TASK_QUEUE` | client-app | legacy PDF queue name |
| `TEMPORAL_TASK_QUEUE` | worker | must match the client queue, e.g. `contract-review-queue` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | worker | S3 credentials |
| `AWS_REGION` | worker | e.g. `us-west-2` |
| `AWS_S3_ENDPOINT_URL` | worker | S3 endpoint URL |
| `S3_BUCKET` | worker | Bucket holding the contract PDFs |
| `TEMP_DIR` | worker | Local scratch dir for downloads (e.g. `pdf-pipeline`) |
| `OPENAI_API_KEY` | worker | API key for the LLM |
| `OPENAI_MODEL` | worker | e.g. `gpt-4.1-mini-2025-04-14` |

> The client-app task queue (`TEMPORAL_CONTRACT_REVIEW_TASK_QUEUE`) and the worker task
> queue (`TEMPORAL_TASK_QUEUE`) must be the same value, otherwise the worker never
> picks up the workflow.

## What you learn from this project

- **Client/worker decoupling** — the FastAPI app starts workflows by string name; only
  the worker imports the workflow code.
- **Fan-out with child workflows** — one `PDFSummaryWorkflow` per PDF, running in
  parallel, with `ParentClosePolicy` control.
- **Activities with heartbeats, retries, and timeouts** — see `DEFAULT_RETRY_POLICY`
  in the workflow files.
- **Human-in-the-loop** — the workflow pauses on `workflow.wait_condition` until a
  reviewer submits a decision via an **Update**, with **Signals** for reviewer
  assignment and **Queries** for status/report reads.

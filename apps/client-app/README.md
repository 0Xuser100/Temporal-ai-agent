# Client App

FastAPI service that starts contract-review workflows on Temporal and interacts with
them (status Queries, reviewer Signals, approve/revise Updates). It is fully decoupled
from the worker — workflows are referenced by string name and payloads are plain JSON.

## Prerequisites

1. **Install [uv](https://docs.astral.sh/uv/)** (first time only):

   ```powershell
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. The **Temporal server must be running** (see the
   [root README](../../README.md)):

   ```bash
   cd ../../setup/samples-server/compose
   docker compose -f docker-compose-postgres.yml up -d
   ```

## Running

1. Create your `.env` (first time only — the defaults match the local Temporal server):

   ```bash
   cp .env.example .env
   ```

2. Start the FastAPI service:

   ```bash
   uv run uvicorn main:app --reload
   ```

The API runs at <http://localhost:8000> — interactive docs at
<http://localhost:8000/docs>.

> To actually execute workflows you also need the worker running — see
> [../ai-contract-review/README.md](../ai-contract-review/README.md).

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/contract-review/start` | Start a `ContractReviewWorkflow` |
| `GET` | `/contract-review/{workflow_id}/status` | Execution status + workflow state (Query) |
| `GET` | `/contract-review/{workflow_id}/report` | Full risk report (Query) |
| `POST` | `/contract-review/{workflow_id}/assign` | Assign a reviewer (Signal) |
| `POST` | `/contract-review/{workflow_id}/revise` | Request a revision with feedback (Update) |
| `GET` | `/contract-review/{workflow_id}/approve` | Approve the report (Update) |

## Usage

Start a review:

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

Check status and read the report (use the `workflow_id` from the response above):

```bash
curl http://localhost:8000/contract-review/<workflow_id>/status
curl http://localhost:8000/contract-review/<workflow_id>/report
```

Assign a reviewer, then approve or request a revision:

```bash
curl -X POST http://localhost:8000/contract-review/<workflow_id>/assign \
  -H "Content-Type: application/json" \
  -d '{"name": "Mahmoud"}'

# request changes
curl -X POST http://localhost:8000/contract-review/<workflow_id>/revise \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Expand the liability section."}'

# or approve
curl http://localhost:8000/contract-review/<workflow_id>/approve
```

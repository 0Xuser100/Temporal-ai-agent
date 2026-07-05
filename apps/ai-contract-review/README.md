# AI Contract Review — Temporal Worker

Temporal worker that reviews contract PDFs stored in S3:

1. **Fan-out** — the parent `ContractReviewWorkflow` starts one `PDFSummaryWorkflow`
   child per PDF, all in parallel.
2. **Extract + summarize** — each child downloads its PDF from S3, extracts Markdown
   with `pymupdf4llm` (batched, with activity heartbeats), and asks the LLM for a
   summary and key risks.
3. **Synthesize** — the parent combines all summaries into a single risk report via
   the LLM.
4. **Human-in-the-loop** — the workflow pauses (`awaiting-review`) until a reviewer
   approves or requests a revision (up to `max_revisions` cycles, 3-day timeout).

## Files

```text
worker.py             # Connects to Temporal and runs workflows + activities
parent_workflow.py    # ContractReviewWorkflow — fan-out, synthesis, HITL review
child_workflow.py     # PDFSummaryWorkflow — extract + summarize one PDF
activities.py         # extract_pdf (S3 + PyMuPDF) and call_llm (OpenAI) activities
prompts.py            # Summary / synthesis / revision prompt templates
```

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

1. Create your `.env` and fill in the credentials (first time only):

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |---|---|
   | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 credentials |
   | `AWS_REGION` | e.g. `us-west-2` |
   | `AWS_S3_ENDPOINT_URL` | S3 endpoint URL |
   | `S3_BUCKET` | Bucket holding the contract PDFs |
   | `TEMP_DIR` | Local scratch dir for downloads (e.g. `pdf-pipeline`) |
   | `OPENAI_API_KEY` | API key for the LLM |
   | `OPENAI_MODEL` | e.g. `gpt-4.1-mini-2025-04-14` |
   | `TEMPORAL_HOST` | `localhost:7233` for the local server |
   | `TEMPORAL_NAMESPACE` | `default` |
   | `TEMPORAL_TASK_QUEUE` | `contract-review-queue` — must match the client app |

2. Start the worker:

   ```bash
   uv run python worker.py
   ```

   You should see: `Worker running on: 'contract-review-queue'`

## Triggering a review

Workflows are started through the client app — see
[../client-app/README.md](../client-app/README.md). In short:

```bash
curl -X POST http://localhost:8000/contract-review/start \
  -H "Content-Type: application/json" \
  -d '{"s3_paths": ["s3://temporal-dev/ContractReview/nda-innovate-consultpro.pdf"], "max_revisions": 2}'
```

Watch the parent and child workflows execute in the Temporal Web UI at
<http://localhost:8080>.

## Workflow interaction surface

- **Query `get_status`** — current phase (`extracting` / `analyzing` /
  `awaiting-review` / `revising` / `completed`), PDFs processed, report preview.
- **Query `get_report`** — the full risk report; read this before deciding.
- **Signal `assign_reviewer`** — record who is reviewing.
- **Update `submit_decision`** — `approve` to finish, or `revise` with feedback
  (feedback is required and validated) to trigger another LLM revision cycle.

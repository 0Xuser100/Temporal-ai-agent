# Temporal Agent — PDF Extraction Pipeline

Hands-on Python project for learning [Temporal](https://temporal.io/) by building the same
PDF-to-Markdown pipeline twice:

1. **Plain Python** — a simple synchronous script.
2. **Temporal** — the same pipeline as a durable workflow with retries and timeouts.

Both apps download a PDF from S3, extract its text to Markdown with `pymupdf4llm`, and
upload the `.md` result back to S3.

## Repository layout

```text
.
├── apps/
│   ├── pdf-extractions-01/            # Plain Python baseline (no Temporal)
│   │   └── process_pdf.py
│   └── pdf-extraction-02-temporal/    # Same pipeline as a Temporal workflow
│       ├── worker.py                  # Runs the workflow + activities
│       ├── workflow_process_pdf.py    # PDFPipelineWorkflow definition
│       ├── activities.py              # download / extract / upload activities
│       └── helpers.py                 # input/output dataclasses + S3 helpers
└── setup/
    └── samples-server/                # Local Temporal server (Docker Compose)
```

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — used to manage dependencies and run the apps
- **Docker + Docker Compose** — for the local Temporal server
- Access to an **S3-compatible bucket** (AWS S3, MinIO, etc.)

## Configuration

Each app reads its settings from a `.env` file. Copy the example and fill in your values:

```bash
cp apps/pdf-extractions-01/.env.example apps/pdf-extractions-01/.env
cp apps/pdf-extraction-02-temporal/.env.example apps/pdf-extraction-02-temporal/.env
```

Required variables:

| Variable | Used by | Description |
|---|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | both | S3 credentials |
| `AWS_REGION` | both | e.g. `us-west-2` |
| `AWS_S3_ENDPOINT_URL` | both | S3 endpoint URL |
| `S3_BUCKET` | both | Target bucket name |
| `TEMP_DIR` | both | Local scratch dir for downloads (e.g. `pdf-pipeline`) |
| `TEMPORAL_HOST` | app 02 | Temporal frontend, e.g. `localhost:7233` |
| `TEMPORAL_NAMESPACE` | app 02 | e.g. `default` |
| `TEMPORAL_PDF_PROCESS_TASK_QUEUE` | app 02 | e.g. `pdf-pipeline-queue` |

## Quick start

### Example 1 — Plain Python pipeline

The non-Temporal baseline. Just run the script with an S3 path:

```bash
cd apps/pdf-extractions-01
uv run python process_pdf.py s3://your-bucket/path/to/file.pdf
```

What it does:

1. Downloads the PDF from S3.
2. Extracts Markdown with `pymupdf4llm`.
3. Uploads the generated `.md` file back to S3.

### Example 2 — Temporal pipeline

**Step 1 — Start the local Temporal server:**

```bash
cd setup/samples-server/compose
docker compose -f docker-compose-postgres.yml up -d
```

Local endpoints:

- Temporal Frontend (gRPC): `localhost:7233`
- Temporal Web UI: <http://localhost:8080>

**Step 2 — Start the worker** (it connects to Temporal and polls the task queue):

```bash
cd apps/pdf-extraction-02-temporal
uv run python worker.py
```

You should see: `Worker started. Polling task queue: 'pdf-pipeline-queue'`

**Step 3 — Trigger a workflow.** With the worker running, start a
`PDFPipelineWorkflow` run from the Temporal Web UI (or the `temporal` CLI),
passing an input of `{ "s3_path": "s3://your-bucket/path/to/file.pdf" }`.
Watch it execute live in the UI at <http://localhost:8080>.

## What you learn from each stage

**Plain Python pipeline**
- a straightforward synchronous batch script
- moving files between S3 and local temp storage

**Temporal pipeline**
- workflow vs. activity boundaries
- automatic retries and timeouts (see `DEFAULT_RETRY` in `workflow_process_pdf.py`)
- running the worker separately from whatever triggers the workflow
- durable orchestration around the exact same business logic

## Suggested learning order

1. Run the plain script and watch it process a PDF end to end.
2. Start the Temporal server and worker, then trigger the workflow.
3. Open the Temporal Web UI and inspect the workflow history, activities, and retries.
4. Compare `process_pdf.py` with `workflow_process_pdf.py` + `activities.py` to see how
   the same steps map onto Temporal's model.

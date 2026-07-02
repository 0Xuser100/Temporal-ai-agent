# Client App

FastAPI service that submits PDF processing jobs to Temporal and returns the result.

## Running

1. Start the FastAPI service:

   ```bash
   uv run uvicorn main:app --reload
   ```

2. Start the worker:

   ```bash
   uv run python worker.py
   ```

## Usage

Submit a PDF for processing:

```bash
curl -X POST http://localhost:8000/process-pdf \
  -H "Content-Type: application/json" \
  -d '{"s3_path": "s3://temporal-dev/files/Mahmoud_Abdulhamid.pdf"}'
```

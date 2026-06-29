import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from dotenv import load_dotenv
from temporalio.client import Client


load_dotenv()

TEMPORAL_HOST      = os.environ["TEMPORAL_HOST"]
TEMPORAL_NAMESPACE = os.environ["TEMPORAL_NAMESPACE"]
TEMPORAL_PDF_PROCESS_TASK_QUEUE = os.environ["TEMPORAL_PDF_PROCESS_TASK_QUEUE"]
TEMPORAL_CONTRACT_REVIEW_TASK_QUEUE = os.environ["TEMPORAL_CONTRACT_REVIEW_TASK_QUEUE"]


app = FastAPI(
    title="PDF Extraction Client",
    description="Submits PDF processing jobs to Temporal and returns the result.",
    version="1.0.0",
)

class ProcessPDFRequest(BaseModel):
    s3_path: str

class ProcessPDFExecuteResponse(BaseModel):
    workflow_id: str
    results: dict

async def get_temporal_client() -> Client:
    return await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status":"ok"}


@app.post("/process-pdf",response_model=ProcessPDFExecuteResponse)
async def process_pdf(request:ProcessPDFRequest):
    workflow_id=f"pdf-pipeline-{uuid.uuid4()}"
    Client=await get_temporal_client()
    results=await Client.execute_workflow(
        "PDFPipelineWorkflow",
        args=[
            {
                "s3_path":request.s3_path
            }
        ],
        id=workflow_id,
        task_queue=TEMPORAL_PDF_PROCESS_TASK_QUEUE,
        result_type=dict,
    )

    return ProcessPDFExecuteResponse (
        workflow_id=workflow_id,
        results=results
    )
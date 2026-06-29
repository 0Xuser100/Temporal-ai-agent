from loguru import logger
from pathlib import Path

import pymupdf4llm
from temporalio import activity

from helpers import (
    get_s3_client, parse_s3_path, TEMP_DIR,
    DownloadInput, DownloadOutput, 
    ExtractInput, ExtractOutput,
    UploadInput, UploadOutput
)
import sys

logger.add(
    sys.stderr, 
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {message}", 
    level="INFO"
)
log = logger


# ── Step 1: Download ─────────────────────────────────────────────────────────
@activity.defn
async def download_pdf(params:DownloadInput)-> DownloadOutput: # we now treat DownloadInput as data type so that we type params:DownloadInput
    bucket,key=parse_s3_path(params.s3_path)
    filename=Path(key).name

    local_path=str(Path(TEMP_DIR)/filename)
    activity.logger.info(f"Downloading: s3://{bucket}/{key} => {local_path}")
    s3_client = get_s3_client()
    s3_client.download_file(
        bucket,
        key,
        local_path
    )
    activity.logger.info(f"COMPLETED Downloading : {local_path} ")
    return DownloadOutput(local_path = local_path)

# ── Step 2: Extract to Markdown ───────────────────────────────────────────────
@activity.defn
async def extract_to_markdown(params:ExtractInput) -> ExtractOutput:
    activity.logger.info(f"Extracting text from {params.local_path}")
    markdown_text = pymupdf4llm.to_markdown(params.local_path)
    activity.logger.info(f"Extraction complete — {len(markdown_text)} characters")
    return ExtractOutput(markdown_text=markdown_text)


# ── Step 3: Upload Markdown  to s3 ──────────────────────────────────────────────────
@activity.defn
async def upload_markdown(params: UploadInput) -> UploadOutput:
    bucket, key = parse_s3_path(params.original_s3_path)
    md_key=key.replace(".pdf",".md")

    activity.logger.info(f"Uploading markdown → s3://{bucket}/{md_key}")

    s3_client = get_s3_client()

    s3_client.put_object(
        Bucket=bucket,
        Key=md_key,

        Body=params.markdown_text.encode("utf-8"),
        ContentType="text/markdown",
    )
    
    output_path = f"s3://{bucket}/{md_key}"
    activity.logger.info(f"Upload complete: {output_path}")
    return UploadOutput(output_s3_path=output_path)
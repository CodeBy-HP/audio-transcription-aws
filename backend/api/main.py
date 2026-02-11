"""
Audio Transcription API (FastAPI).

This service is the control plane for user transcription jobs. It authenticates
requests with Clerk JWTs, keeps user/job metadata in DynamoDB, and creates
presigned S3 upload forms so clients can upload audio directly to S3 without
passing large files through the API.

Primary responsibilities:
- Health check endpoint for uptime probes.
- Authenticated job creation (`POST /api/jobs`) with input validation.
- User bootstrap in DynamoDB (`users` table) on first authenticated activity.
- Job read/list endpoints scoped by authenticated `clerk_user_id`.

The actual transcription processing is asynchronous and handled by downstream
queue/worker components after upload completes.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from fastapi import Depends, FastAPI, HTTPException
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

app = FastAPI(title="Audio Transcription API", version="0.1.0")

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1")),
)
s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1")),
)

USERS_TABLE = os.getenv("USERS_TABLE_NAME", "")
JOBS_TABLE = os.getenv("JOBS_TABLE_NAME", "")
AUDIO_BUCKET = os.getenv("AUDIO_BUCKET_NAME", "")
PRESIGNED_EXPIRES_SECONDS = int(os.getenv("PRESIGNED_EXPIRES_SECONDS", "900"))
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(100 * 1024 * 1024)))

ALLOWED_FILE_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL", ""))
clerk_guard = ClerkHTTPBearer(clerk_config)


class CreateJobRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    file_size: int = Field(gt=0)
    content_type: str = Field(min_length=1, max_length=120)
    language: str = Field(default="en", min_length=2, max_length=10)


class CreateJobResponse(BaseModel):
    job_id: str
    status: str
    upload: dict[str, Any]


class JobListResponse(BaseModel):
    jobs: list[dict[str, Any]]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_extension(filename: str) -> str:
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _to_plain(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item)


def _assert_db_env_configured() -> None:
    missing = []
    if not USERS_TABLE:
        missing.append("USERS_TABLE_NAME")
    if not JOBS_TABLE:
        missing.append("JOBS_TABLE_NAME")
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}",
        )


async def get_current_auth_context(
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
) -> dict[str, Any]:
    claims = creds.decoded
    return {
        "clerk_user_id": claims["sub"],
        "email": claims.get("email", ""),
    }


async def get_current_user_id(
    auth_ctx: dict[str, Any] = Depends(get_current_auth_context),
) -> str:
    return auth_ctx["clerk_user_id"]


def ensure_user_exists(clerk_user_id: str, email: str = "") -> None:
    _assert_db_env_configured()
    users_table = dynamodb.Table(USERS_TABLE)
    now = _now_iso()
    users_table.update_item(
        Key={"clerk_user_id": clerk_user_id},
        UpdateExpression=(
            "SET #updated_at = :updated_at, "
            "#email = if_not_exists(#email, :email), "
            "#created_at = if_not_exists(#created_at, :created_at)"
        ),
        ExpressionAttributeNames={
            "#updated_at": "updated_at",
            "#email": "email",
            "#created_at": "created_at",
        },
        ExpressionAttributeValues={
            ":updated_at": now,
            ":email": email,
            ":created_at": now,
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/jobs", response_model=CreateJobResponse)
async def create_job(
    payload: CreateJobRequest,
    auth_ctx: dict[str, Any] = Depends(get_current_auth_context),
) -> CreateJobResponse:
    _assert_db_env_configured()
    if not AUDIO_BUCKET:
        raise HTTPException(status_code=500, detail="AUDIO_BUCKET_NAME is not configured")

    clerk_user_id = auth_ctx["clerk_user_id"]
    ensure_user_exists(clerk_user_id, auth_ctx.get("email", ""))

    ext = _extract_extension(payload.filename)
    if ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    expected_mime = ALLOWED_FILE_TYPES[ext]
    if payload.content_type.lower() != expected_mime:
        raise HTTPException(status_code=400, detail="Invalid content_type for file extension")

    if payload.file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max size {MAX_FILE_SIZE_BYTES} bytes",
        )

    job_id = str(uuid.uuid4())
    now = _now_iso()
    object_key = f"audio/{clerk_user_id}/{job_id}/original{ext}"

    jobs_table = dynamodb.Table(JOBS_TABLE)
    jobs_table.put_item(
        Item={
            "clerk_user_id": clerk_user_id,
            "job_id": job_id,
            "filename": payload.filename,
            "file_size": payload.file_size,
            "content_type": payload.content_type,
            "language": payload.language,
            "status": "PENDING_UPLOAD",
            "s3_audio_key": object_key,
            "created_at": now,
            "updated_at": now,
        }
    )

    presigned_post = s3_client.generate_presigned_post(
        Bucket=AUDIO_BUCKET,
        Key=object_key,
        Fields={"Content-Type": payload.content_type},
        Conditions=[
            {"Content-Type": payload.content_type},
            ["content-length-range", 1, MAX_FILE_SIZE_BYTES],
            ["eq", "$key", object_key],
        ],
        ExpiresIn=PRESIGNED_EXPIRES_SECONDS,
    )

    return CreateJobResponse(
        job_id=job_id,
        status="PENDING_UPLOAD",
        upload={
            "type": "presigned_post",
            "url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "expires_in": PRESIGNED_EXPIRES_SECONDS,
            "object_key": object_key,
        },
    )


@app.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    clerk_user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    _assert_db_env_configured()
    jobs_table = dynamodb.Table(JOBS_TABLE)
    response = jobs_table.get_item(Key={"clerk_user_id": clerk_user_id, "job_id": job_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_plain(item)


@app.get("/api/jobs", response_model=JobListResponse)
async def list_jobs(
    clerk_user_id: str = Depends(get_current_user_id),
    limit: int = 20,
) -> JobListResponse:
    _assert_db_env_configured()
    jobs_table = dynamodb.Table(JOBS_TABLE)
    query_limit = max(1, min(limit, 100))

    response = jobs_table.query(
        KeyConditionExpression=Key("clerk_user_id").eq(clerk_user_id),
        Limit=query_limit,
    )
    jobs = [_to_plain(i) for i in response.get("Items", [])]
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return JobListResponse(jobs=jobs)


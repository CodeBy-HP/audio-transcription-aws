import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3


AWS_REGION = os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1"))
NOTIFICATION_QUEUE_URL = os.getenv("NOTIFICATION_QUEUE_URL", "")
USERS_TABLE_NAME = os.getenv("USERS_TABLE_NAME", "")
JOBS_TABLE_NAME = os.getenv("JOBS_TABLE_NAME", "")
TRANSCRIPT_BUCKET_NAME = os.getenv("TRANSCRIPT_BUCKET_NAME", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
DOWNLOAD_URL_TTL_SECONDS = int(os.getenv("DOWNLOAD_URL_TTL_SECONDS", "86400"))

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
ses = boto3.client("ses", region_name=AWS_REGION)

users_table = dynamodb.Table(USERS_TABLE_NAME) if USERS_TABLE_NAME else None
jobs_table = dynamodb.Table(JOBS_TABLE_NAME) if JOBS_TABLE_NAME else None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_email(clerk_user_id: str) -> str:
    response = users_table.get_item(Key={"clerk_user_id": clerk_user_id})
    item = response.get("Item", {})
    return item.get("email", "").strip()


def get_job(clerk_user_id: str, job_id: str) -> dict[str, Any]:
    response = jobs_table.get_item(Key={"clerk_user_id": clerk_user_id, "job_id": job_id})
    return response.get("Item", {})


def build_download_url(transcript_key: str) -> str:
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": TRANSCRIPT_BUCKET_NAME, "Key": transcript_key},
        ExpiresIn=DOWNLOAD_URL_TTL_SECONDS,
    )


def send_email(to_email: str, subject: str, body_text: str) -> None:
    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body_text}},
        },
    )


def handle_completed(clerk_user_id: str, job_id: str, job: dict[str, Any], to_email: str) -> None:
    filename = job.get("filename", "your audio file")
    transcript_key = job.get("s3_transcript_key", "")
    if not transcript_key:
        raise RuntimeError(f"Missing transcript key for completed job {job_id}")

    download_url = build_download_url(transcript_key)
    subject = "Your transcription is ready"
    body = (
        f"Hi,\n\n"
        f"Your transcription is complete.\n"
        f"Job ID: {job_id}\n"
        f"Filename: {filename}\n"
        f"Generated at: {now_iso()}\n\n"
        f"Download link (expires in 24h):\n{download_url}\n\n"
        f"- Audio Transcription Platform"
    )
    send_email(to_email, subject, body)


def handle_failed(clerk_user_id: str, job_id: str, job: dict[str, Any], to_email: str) -> None:
    filename = job.get("filename", "your audio file")
    error_message = job.get("error_message", "Unknown error")
    subject = "Your transcription failed"
    body = (
        f"Hi,\n\n"
        f"We could not complete your transcription.\n"
        f"Job ID: {job_id}\n"
        f"Filename: {filename}\n"
        f"Reason: {error_message}\n\n"
        f"Please try uploading again.\n\n"
        f"- Audio Transcription Platform"
    )
    send_email(to_email, subject, body)


def handler(event, context):  # noqa: ANN001
    if not USERS_TABLE_NAME or not JOBS_TABLE_NAME or not TRANSCRIPT_BUCKET_NAME or not SENDER_EMAIL:
        raise RuntimeError(
            "Missing required env vars: USERS_TABLE_NAME, JOBS_TABLE_NAME, TRANSCRIPT_BUCKET_NAME, SENDER_EMAIL"
        )

    records = event.get("Records", [])
    for record in records:
        body = json.loads(record["body"])
        clerk_user_id = body["clerk_user_id"]
        job_id = body["job_id"]
        status = body["status"]

        job = get_job(clerk_user_id, job_id)
        if not job:
            print(f"Job not found, skipping notification: user={clerk_user_id}, job={job_id}")
            continue

        to_email = get_user_email(clerk_user_id)
        if not to_email:
            print(f"No user email found, skipping notification: user={clerk_user_id}, job={job_id}")
            continue

        if status == "COMPLETED":
            handle_completed(clerk_user_id, job_id, job, to_email)
        elif status == "FAILED":
            handle_failed(clerk_user_id, job_id, job, to_email)
        else:
            print(f"Unknown notification status={status}, user={clerk_user_id}, job={job_id}")

    return {"statusCode": 200, "body": "ok"}

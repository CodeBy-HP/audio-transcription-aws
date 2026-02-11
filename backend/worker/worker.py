import json
import os
import tempfile
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote_plus

import boto3
from transformers import pipeline


AWS_REGION = os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1"))
TRANSCRIPTION_QUEUE_URL = os.getenv("TRANSCRIPTION_QUEUE_URL", "")
NOTIFICATION_QUEUE_URL = os.getenv("NOTIFICATION_QUEUE_URL", "")
AUDIO_BUCKET_NAME = os.getenv("AUDIO_BUCKET_NAME", "")
TRANSCRIPT_BUCKET_NAME = os.getenv("TRANSCRIPT_BUCKET_NAME", "")
JOBS_TABLE_NAME = os.getenv("JOBS_TABLE_NAME", "")

WHISPER_MODEL_LOCAL_PATH = os.getenv("WHISPER_MODEL_LOCAL_PATH", "/models/whisper-model")
WHISPER_MODEL_ID = os.getenv("WHISPER_MODEL_ID", "openai/whisper-tiny")
POLL_WAIT_SECONDS = int(os.getenv("POLL_WAIT_SECONDS", "20"))

sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
jobs_table = dynamodb.Table(JOBS_TABLE_NAME) if JOBS_TABLE_NAME else None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_required_env() -> None:
    required = {
        "TRANSCRIPTION_QUEUE_URL": TRANSCRIPTION_QUEUE_URL,
        "NOTIFICATION_QUEUE_URL": NOTIFICATION_QUEUE_URL,
        "AUDIO_BUCKET_NAME": AUDIO_BUCKET_NAME,
        "TRANSCRIPT_BUCKET_NAME": TRANSCRIPT_BUCKET_NAME,
        "JOBS_TABLE_NAME": JOBS_TABLE_NAME,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def parse_s3_event_from_sqs(message_body: str) -> dict[str, Any]:
    body = json.loads(message_body)
    record = body["Records"][0]
    return {
        "bucket": record["s3"]["bucket"]["name"],
        "key": unquote_plus(record["s3"]["object"]["key"]),
    }


def extract_identity_from_key(key: str) -> tuple[str, str]:
    # Expected: audio/{clerk_user_id}/{job_id}/original.ext
    parts = key.split("/")
    if len(parts) < 4 or parts[0] != "audio":
        raise ValueError(f"Unexpected audio key format: {key}")
    return parts[1], parts[2]


def update_job_status(
    clerk_user_id: str,
    job_id: str,
    status: str,
    transcript_key: str | None = None,
    error_message: str | None = None,
) -> None:
    expression = "SET #status = :status, #updated_at = :updated_at"
    names = {"#status": "status", "#updated_at": "updated_at"}
    values: dict[str, Any] = {
        ":status": status,
        ":updated_at": now_iso(),
    }

    if transcript_key:
        expression += ", #s3_transcript_key = :s3_transcript_key, #completed_at = :completed_at"
        names["#s3_transcript_key"] = "s3_transcript_key"
        names["#completed_at"] = "completed_at"
        values[":s3_transcript_key"] = transcript_key
        values[":completed_at"] = now_iso()

    if error_message:
        expression += ", #error_message = :error_message"
        names["#error_message"] = "error_message"
        values[":error_message"] = error_message[:1000]

    jobs_table.update_item(
        Key={"clerk_user_id": clerk_user_id, "job_id": job_id},
        UpdateExpression=expression,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def notify(clerk_user_id: str, job_id: str, status: str, transcript_key: str | None = None) -> None:
    payload = {
        "clerk_user_id": clerk_user_id,
        "job_id": job_id,
        "status": status,
        "s3_transcript_key": transcript_key,
        "timestamp": now_iso(),
    }
    sqs.send_message(QueueUrl=NOTIFICATION_QUEUE_URL, MessageBody=json.dumps(payload))


def build_transcriber():
    model_source = WHISPER_MODEL_LOCAL_PATH if os.path.exists(WHISPER_MODEL_LOCAL_PATH) else WHISPER_MODEL_ID
    print(f"Loading transcription model from: {model_source}")
    return pipeline(
        task="automatic-speech-recognition",
        model=model_source,
        device=-1,  # CPU
    )


def process_message(message: dict[str, Any], transcriber) -> None:
    receipt_handle = message["ReceiptHandle"]
    message_body = message["Body"]
    clerk_user_id = "unknown"
    job_id = "unknown"
    local_file = None
    try:
        s3_event = parse_s3_event_from_sqs(message_body)
        clerk_user_id, job_id = extract_identity_from_key(s3_event["key"])
        update_job_status(clerk_user_id, job_id, "PROCESSING")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as tmp:
            local_file = tmp.name

        s3.download_file(s3_event["bucket"], s3_event["key"], local_file)
        result = transcriber(local_file)
        transcript_text = result["text"].strip() if isinstance(result, dict) else str(result)

        transcript_key = f"transcripts/{clerk_user_id}/{job_id}/transcript.txt"
        s3.put_object(
            Bucket=TRANSCRIPT_BUCKET_NAME,
            Key=transcript_key,
            Body=transcript_text.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )

        update_job_status(clerk_user_id, job_id, "COMPLETED", transcript_key=transcript_key)
        notify(clerk_user_id, job_id, "COMPLETED", transcript_key=transcript_key)

        sqs.delete_message(QueueUrl=TRANSCRIPTION_QUEUE_URL, ReceiptHandle=receipt_handle)
    except Exception as exc:
        print(f"Job failed: user={clerk_user_id}, job={job_id}, error={exc}")
        update_job_status(clerk_user_id, job_id, "FAILED", error_message=str(exc))
        notify(clerk_user_id, job_id, "FAILED")
        # Do not delete message so SQS retry/DLQ flow can work.
    finally:
        if local_file and os.path.exists(local_file):
            os.remove(local_file)


def main() -> None:
    assert_required_env()
    transcriber = build_transcriber()
    print("Worker started. Polling transcription queue...")

    while True:
        response = sqs.receive_message(
            QueueUrl=TRANSCRIPTION_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=POLL_WAIT_SECONDS,
            VisibilityTimeout=900,
        )
        messages = response.get("Messages", [])
        if not messages:
            continue

        for message in messages:
            process_message(message, transcriber)

        time.sleep(0.2)


if __name__ == "__main__":
    main()

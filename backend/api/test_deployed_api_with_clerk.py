#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import boto3


def load_dotenv(path: str | None = None) -> None:
    env_path = Path(path) if path else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def http_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url=url, method=method, data=data)
    req.add_header("accept", "application/json")
    req.add_header("content-type", "application/json")
    req.add_header("user-agent", "audiotrans-e2e-tester/1.0")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    try:
        with urllib.request.urlopen(req) as res:
            status = res.getcode()
            payload = res.read().decode("utf-8")
            return status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        parsed: dict[str, Any]
        try:
            parsed = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            parsed = {"raw_error_body": payload}
        return exc.code, parsed


def http_bytes(
    method: str,
    url: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url=url, method=method, data=body)
    req.add_header("accept", "*/*")
    req.add_header("user-agent", "audiotrans-e2e-tester/1.0")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    try:
        with urllib.request.urlopen(req) as res:
            return res.getcode(), res.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def encode_multipart_form_data(
    fields: dict[str, str],
    file_field_name: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
) -> tuple[bytes, str]:
    boundary = f"----audiotrans-boundary-{secrets.token_hex(12)}"
    lines: list[bytes] = []

    for key, value in fields.items():
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"))
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))

    lines.append(f"--{boundary}".encode("utf-8"))
    lines.append(
        f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_name}"'.encode(
            "utf-8"
        )
    )
    lines.append(f"Content-Type: {content_type}".encode("utf-8"))
    lines.append(b"")
    lines.append(file_bytes)
    lines.append(f"--{boundary}--".encode("utf-8"))
    lines.append(b"")

    body = b"\r\n".join(lines)
    return body, boundary


def create_clerk_user(secret_key: str, email: str, password: str, clerk_api_base_url: str) -> str:
    status, data = http_json(
        method="POST",
        url=f"{clerk_api_base_url.rstrip('/')}/v1/users",
        body={"email_address": [email], "password": password},
        headers={"authorization": f"Bearer {secret_key}"},
    )
    if status not in {200, 201}:
        raise RuntimeError(f"Create user failed ({status}): {json.dumps(data)}")
    user_id = data.get("id", "")
    if not user_id:
        raise RuntimeError(f"Create user response missing id: {json.dumps(data)}")
    return user_id


def get_clerk_user_by_email(secret_key: str, email: str, clerk_api_base_url: str) -> str:
    query = urllib.parse.urlencode([("email_address[]", email)])
    status, data = http_json(
        method="GET",
        url=f"{clerk_api_base_url.rstrip('/')}/v1/users?{query}",
        headers={"authorization": f"Bearer {secret_key}"},
    )
    if status != 200:
        raise RuntimeError(f"Lookup user by email failed ({status}): {json.dumps(data)}")

    if not isinstance(data, list) or not data:
        raise RuntimeError(f"No Clerk user found for email: {email}")

    user_id = str(data[0].get("id", "")).strip()
    if not user_id:
        raise RuntimeError(f"Lookup user response missing id: {json.dumps(data)}")
    return user_id


def find_or_create_clerk_user(secret_key: str, email: str, password: str, clerk_api_base_url: str) -> tuple[str, str]:
    try:
        user_id = create_clerk_user(secret_key, email, password, clerk_api_base_url)
        return user_id, "created"
    except RuntimeError as exc:
        msg = str(exc)
        if "form_identifier_exists" not in msg:
            raise
        user_id = get_clerk_user_by_email(secret_key, email, clerk_api_base_url)
        return user_id, "existing"


def create_clerk_session(secret_key: str, user_id: str, clerk_api_base_url: str) -> str:
    status, data = http_json(
        method="POST",
        url=f"{clerk_api_base_url.rstrip('/')}/v1/sessions",
        body={"user_id": user_id},
        headers={"authorization": f"Bearer {secret_key}"},
    )
    if status not in {200, 201}:
        raise RuntimeError(f"Create session failed ({status}): {json.dumps(data)}")
    session_id = data.get("id", "")
    if not session_id:
        raise RuntimeError(f"Create session response missing id: {json.dumps(data)}")
    return session_id


def create_session_token(secret_key: str, session_id: str, clerk_api_base_url: str) -> str:
    status, data = http_json(
        method="POST",
        url=f"{clerk_api_base_url.rstrip('/')}/v1/sessions/{session_id}/tokens",
        body={},
        headers={"authorization": f"Bearer {secret_key}"},
    )
    if status not in {200, 201}:
        raise RuntimeError(f"Create session token failed ({status}): {json.dumps(data)}")
    token = data.get("jwt", "")
    if not token:
        raise RuntimeError(f"Session token response missing jwt: {json.dumps(data)}")
    return token


def call_create_job_endpoint(
    api_base_url: str,
    bearer_token: str,
    filename: str,
    file_size: int,
    content_type: str,
    requester_email: str,
) -> tuple[int, dict[str, Any]]:
    payload = {
        "filename": filename,
        "file_size": file_size,
        "content_type": content_type,
        "language": "en",
        "email": requester_email,
    }
    return http_json(
        method="POST",
        url=f"{api_base_url.rstrip('/')}/api/jobs",
        body=payload,
        headers={"authorization": f"Bearer {bearer_token}"},
    )


def upload_file_with_presigned_post(upload: dict[str, Any], audio_path: Path, content_type: str) -> tuple[int, str]:
    upload_type = upload.get("type")
    if upload_type != "presigned_post":
        return 0, f"Unsupported upload type: {upload_type}"

    url = str(upload.get("url", "")).strip()
    fields = upload.get("fields", {})
    if not url or not isinstance(fields, dict):
        return 0, "Invalid presigned upload payload."

    file_bytes = audio_path.read_bytes()
    body, boundary = encode_multipart_form_data(
        fields={str(k): str(v) for k, v in fields.items()},
        file_field_name="file",
        file_name=audio_path.name,
        file_bytes=file_bytes,
        content_type=content_type,
    )
    status, resp = http_bytes(
        method="POST",
        url=url,
        body=body,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )
    return status, resp.decode("utf-8", errors="replace")


def get_job_status(api_base_url: str, bearer_token: str, job_id: str) -> tuple[int, dict[str, Any]]:
    return http_json(
        method="GET",
        url=f"{api_base_url.rstrip('/')}/api/jobs/{job_id}",
        headers={"authorization": f"Bearer {bearer_token}"},
    )


def get_aws_region() -> str:
    return os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1")).strip()


def fetch_transcript_text(bucket_name: str, transcript_key: str) -> str:
    s3 = boto3.client("s3", region_name=get_aws_region())
    response = s3.get_object(Bucket=bucket_name, Key=transcript_key)
    body = response["Body"].read()
    return body.decode("utf-8", errors="replace")


def main() -> int:
    # Load default repo .env before parsing args so env-backed defaults work.
    load_dotenv(None)

    parser = argparse.ArgumentParser(
        description=(
            "Run end-to-end backend test: create Clerk user/session token, create API job, upload audio, poll job status."
        )
    )
    parser.add_argument("--env-file", default="", help="Optional path to .env file")
    parser.add_argument(
        "--api-base-url",
        default="",
        help="Deployed API base URL. Can also be set via API_BASE_URL env var.",
    )
    parser.add_argument(
        "--user-email",
        default="",
        help="Optional test user email. If omitted, script generates a unique one.",
    )
    parser.add_argument(
        "--audio-file",
        default="",
        help="Audio file path for end-to-end upload test.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=5,
        help="Polling interval for GET /api/jobs/{job_id} (default: 5).",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=int,
        default=300,
        help="Overall timeout for polling job completion (default: 300).",
    )
    parser.add_argument(
        "--show-transcript",
        action="store_true",
        help="Fetch and print transcript text from S3 after COMPLETED status.",
    )
    parser.add_argument(
        "--save-transcript-path",
        default="",
        help="Optional output file path to save transcript text.",
    )
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file)

    api_base_url = args.api_base_url.strip() or require_env("API_BASE_URL")
    clerk_secret_key = require_env("CLERK_SECRET_KEY")
    clerk_api_base_url = os.getenv("CLERK_API_BASE_URL", "https://api.clerk.com").strip()

    test_email = args.user_email.strip()
    if not test_email:
        suffix = f"{int(time.time())}-{secrets.token_hex(3)}"
        test_email = f"api-test-{suffix}@example.com"

    test_password = os.getenv("CLERK_TEST_USER_PASSWORD", "P@ssw0rd!test123")
    audio_file_value = args.audio_file.strip() or os.getenv("E2E_AUDIO_FILE", "backend/api/harvard.wav").strip()
    audio_path = Path(audio_file_value).resolve()
    if not audio_path.exists():
        raise RuntimeError(f"Audio file not found: {audio_path}")
    if not audio_path.is_file():
        raise RuntimeError(
            f"Audio path is not a file: {audio_path}. "
            "Set E2E_AUDIO_FILE to an actual file (for example backend/api/harvard.wav)."
        )

    file_size = audio_path.stat().st_size
    guessed_type = mimetypes.guess_type(audio_path.name)[0]
    content_type = guessed_type or "audio/wav"

    print("[0/8] Starting end-to-end test")
    print(f"      api_base_url={api_base_url}")
    print(f"      audio_file={audio_path}")
    print(f"      file_size={file_size} bytes")
    print(f"      content_type={content_type}")

    print(f"[1/8] Creating or reusing Clerk user: {test_email}")
    user_id, user_mode = find_or_create_clerk_user(
        clerk_secret_key, test_email, test_password, clerk_api_base_url
    )
    print(f"      user_id={user_id} ({user_mode})")

    print("[2/8] Creating Clerk session")
    session_id = create_clerk_session(clerk_secret_key, user_id, clerk_api_base_url)
    print(f"      session_id={session_id}")

    print("[3/8] Creating short-lived Clerk session token")
    token = create_session_token(clerk_secret_key, session_id, clerk_api_base_url)
    print(f"      token_prefix={token[:24]}...")

    print("[4/8] Calling deployed API POST /api/jobs")
    status, data = call_create_job_endpoint(
        api_base_url=api_base_url,
        bearer_token=token,
        filename=audio_path.name,
        file_size=file_size,
        content_type=content_type,
        requester_email=test_email,
    )
    print(f"      create_job_status={status}")
    print(f"      create_job_response={json.dumps(data, indent=2)}")
    if status not in {200, 201}:
        print("FAIL: API did not accept token or create job.")
        return 1

    job_id = str(data.get("job_id", "")).strip()
    upload = data.get("upload", {})
    if not job_id or not isinstance(upload, dict):
        print("FAIL: Missing job_id/upload payload from create job response.")
        return 1

    print(f"[5/8] Uploading audio to S3 using presigned form (job_id={job_id})")
    upload_status, upload_body = upload_file_with_presigned_post(upload, audio_path, content_type)
    print(f"      upload_status={upload_status}")
    if upload_status not in {200, 201, 204}:
        print(f"FAIL: Upload failed. Response body: {upload_body}")
        return 1
    print("      upload_response=OK")

    print("[6/8] Polling job status until COMPLETED or FAILED")
    poll_timeout = max(10, args.poll_timeout_seconds)
    poll_interval = max(1, args.poll_interval_seconds)
    deadline = time.time() + poll_timeout
    final_status = ""
    final_payload: dict[str, Any] = {}

    while time.time() < deadline:
        # Clerk session tokens are short-lived; refresh on each poll request.
        poll_token = create_session_token(clerk_secret_key, session_id, clerk_api_base_url)
        poll_http_status, poll_payload = get_job_status(api_base_url, poll_token, job_id)
        if poll_http_status != 200:
            print(
                f"      poll_http_status={poll_http_status}, "
                f"poll_payload={json.dumps(poll_payload)}"
            )
            time.sleep(poll_interval)
            continue

        current = str(poll_payload.get("status", "")).strip()
        print(f"      job_status={current}")
        final_status = current
        final_payload = poll_payload

        if current in {"COMPLETED", "FAILED"}:
            break
        time.sleep(poll_interval)

    if final_status not in {"COMPLETED", "FAILED"}:
        print("FAIL: Polling timed out before terminal status.")
        return 1

    print("[7/8] Final job payload")
    print(json.dumps(final_payload, indent=2))

    print("[8/8] End-to-end result")
    if final_status == "COMPLETED":
        transcript_bucket = os.getenv("TRANSCRIPT_BUCKET_NAME", "").strip()
        transcript_key = str(final_payload.get("s3_transcript_key", "")).strip()
        should_fetch_transcript = args.show_transcript or bool(args.save_transcript_path.strip())
        if should_fetch_transcript:
            if not transcript_bucket:
                print("WARN: TRANSCRIPT_BUCKET_NAME is not set, skipping transcript fetch.")
            elif not transcript_key:
                print("WARN: s3_transcript_key missing in job payload, skipping transcript fetch.")
            else:
                print("[9/9] Fetching transcript text from S3")
                text = fetch_transcript_text(transcript_bucket, transcript_key)
                if args.show_transcript:
                    print("----- Transcript Start -----")
                    print(text)
                    print("------ Transcript End ------")

                save_path = args.save_transcript_path.strip()
                if save_path:
                    output_path = Path(save_path).resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(text, encoding="utf-8")
                    print(f"Transcript saved to: {output_path}")

        print("PASS: Full flow completed (API -> S3 upload -> queue/worker -> job completion).")
        return 0

    print("FAIL: Job reached FAILED state. Check worker/notification logs for details.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

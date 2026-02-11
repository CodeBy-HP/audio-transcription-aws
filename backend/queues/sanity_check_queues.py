#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from uuid import uuid4

from common import get_sqs_client, load_dotenv, require_env


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def print_header(title: str) -> None:
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def test_queue(sqs, queue_name: str, queue_url: str, wait_seconds: int) -> bool:
    print_header(f"[{queue_name}] Starting sanity flow")
    test_id = f"{queue_name.lower()}-{uuid4().hex[:12]}"
    payload = {
        "type": "queue_sanity_test",
        "queue": queue_name,
        "test_id": test_id,
        "timestamp": now_iso(),
    }
    body = json.dumps(payload)

    print(f"[{queue_name}] Sending test message")
    send_resp = sqs.send_message(QueueUrl=queue_url, MessageBody=body)
    message_id = send_resp.get("MessageId", "unknown")
    print(f"[{queue_name}] Sent message_id={message_id}")

    print(f"[{queue_name}] Receiving message (wait up to {wait_seconds}s)")
    recv_resp = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=wait_seconds,
        VisibilityTimeout=30,
    )
    messages = recv_resp.get("Messages", [])
    if not messages:
        print(f"[{queue_name}] FAIL: No message received")
        return False

    msg = messages[0]
    receipt_handle = msg["ReceiptHandle"]
    recv_body = msg.get("Body", "")
    try:
        parsed = json.loads(recv_body)
    except json.JSONDecodeError:
        print(f"[{queue_name}] FAIL: Received body is not valid JSON")
        return False

    if parsed.get("test_id") != test_id:
        print(
            f"[{queue_name}] FAIL: Received unexpected message "
            f"(expected test_id={test_id}, got={parsed.get('test_id')})"
        )
        return False

    print(f"[{queue_name}] Received expected message test_id={test_id}")
    print(f"[{queue_name}] Deleting message")
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    print(f"[{queue_name}] PASS")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sanity-check transcription and notification SQS queues."
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional path to .env file. Default: repo-root .env",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=20,
        help="Long polling wait time used for receive_message (default: 20).",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file or None)
    transcription_queue_url = require_env("TRANSCRIPTION_QUEUE_URL")
    notification_queue_url = require_env("NOTIFICATION_QUEUE_URL")
    wait_seconds = max(1, min(args.wait_seconds, 20))

    print_header("SQS Queue Sanity Checks")
    print("Checking required queue operations: send -> receive -> delete")

    sqs = get_sqs_client()

    t_ok = test_queue(
        sqs=sqs,
        queue_name="TRANSCRIPTION",
        queue_url=transcription_queue_url,
        wait_seconds=wait_seconds,
    )
    n_ok = test_queue(
        sqs=sqs,
        queue_name="NOTIFICATION",
        queue_url=notification_queue_url,
        wait_seconds=wait_seconds,
    )

    print_header("Summary")
    print(f"TRANSCRIPTION queue: {'PASS' if t_ok else 'FAIL'}")
    print(f"NOTIFICATION queue: {'PASS' if n_ok else 'FAIL'}")

    if t_ok and n_ok:
        print("All queue sanity checks passed.")
        return 0

    print("One or more queue sanity checks failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

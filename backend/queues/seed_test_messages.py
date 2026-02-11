#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from uuid import uuid4

from common import get_sqs_client, load_dotenv, require_env


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def send_batch(sqs, queue_name: str, queue_url: str, count: int) -> None:
    print(f"\n[{queue_name}] Sending {count} test message(s)")
    for i in range(1, count + 1):
        payload = {
            "type": "manual_seed_message",
            "queue": queue_name,
            "sequence": i,
            "seed_id": uuid4().hex,
            "timestamp": now_iso(),
        }
        resp = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))
        print(f"[{queue_name}] Sent {i}/{count} message_id={resp.get('MessageId', 'unknown')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed SQS queues with test messages.")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional path to .env file. Default: repo-root .env",
    )
    parser.add_argument(
        "--target",
        choices=["transcription", "notification", "both"],
        default="both",
        help="Which queue(s) to seed.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of messages to send per selected queue (default: 1).",
    )
    args = parser.parse_args()

    count = max(1, args.count)
    load_dotenv(args.env_file or None)
    sqs = get_sqs_client()

    transcription_queue_url = require_env("TRANSCRIPTION_QUEUE_URL")
    notification_queue_url = require_env("NOTIFICATION_QUEUE_URL")

    print("Starting SQS seed operation...")
    print(f"Target: {args.target}")
    print(f"Count per queue: {count}")

    if args.target in {"transcription", "both"}:
        send_batch(sqs, "TRANSCRIPTION", transcription_queue_url, count)

    if args.target in {"notification", "both"}:
        send_batch(sqs, "NOTIFICATION", notification_queue_url, count)

    print("\nSeed operation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

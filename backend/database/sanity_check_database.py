#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from common import get_dynamodb_resource, load_dotenv, require_env


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run sanity checks against users/jobs DynamoDB tables."
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional path to .env file. Default: repo-root .env",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete test records at the end (recommended).",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file or None)

    users_table_name = require_env("USERS_TABLE_NAME")
    jobs_table_name = require_env("JOBS_TABLE_NAME")

    dynamodb = get_dynamodb_resource()
    users_table = dynamodb.Table(users_table_name)
    jobs_table = dynamodb.Table(jobs_table_name)

    test_user_id = f"sanity-user-{uuid4().hex[:10]}"
    test_job_id = f"sanity-job-{uuid4().hex[:10]}"
    created_at = now_iso()

    print("Running DynamoDB sanity checks...")
    print(f"Users table: {users_table_name}")
    print(f"Jobs table: {jobs_table_name}")

    # 1) Insert user row.
    users_table.put_item(
        Item={
            "clerk_user_id": test_user_id,
            "email": "sanity@example.com",
            "created_at": created_at,
            "updated_at": created_at,
        }
    )
    print("OK: put_item(users)")

    # 2) Insert job row.
    jobs_table.put_item(
        Item={
            "clerk_user_id": test_user_id,
            "job_id": test_job_id,
            "filename": "sanity.wav",
            "file_size": 12345,
            "content_type": "audio/wav",
            "language": "en",
            "status": "PENDING_UPLOAD",
            "s3_audio_key": f"audio/{test_user_id}/{test_job_id}/original.wav",
            "created_at": created_at,
            "updated_at": created_at,
        }
    )
    print("OK: put_item(jobs)")

    # 3) Get user.
    user_res = users_table.get_item(Key={"clerk_user_id": test_user_id})
    assert "Item" in user_res, "get_item(users) did not return test row"
    print("OK: get_item(users)")

    # 4) Get job.
    job_res = jobs_table.get_item(Key={"clerk_user_id": test_user_id, "job_id": test_job_id})
    assert "Item" in job_res, "get_item(jobs) did not return test row"
    print("OK: get_item(jobs)")

    # 5) Query jobs by partition key.
    query_res = jobs_table.query(
        KeyConditionExpression=Key("clerk_user_id").eq(test_user_id),
        Limit=10,
    )
    query_items = query_res.get("Items", [])
    assert any(i.get("job_id") == test_job_id for i in query_items), "query(jobs) missing test row"
    print("OK: query(jobs by clerk_user_id)")

    # 6) Update status.
    update_time = now_iso()
    jobs_table.update_item(
        Key={"clerk_user_id": test_user_id, "job_id": test_job_id},
        UpdateExpression="SET #status = :status, #updated_at = :updated_at",
        ExpressionAttributeNames={"#status": "status", "#updated_at": "updated_at"},
        ExpressionAttributeValues={":status": "PROCESSING", ":updated_at": update_time},
    )
    updated_job = jobs_table.get_item(
        Key={"clerk_user_id": test_user_id, "job_id": test_job_id}
    ).get("Item", {})
    assert updated_job.get("status") == "PROCESSING", "update_item(jobs) did not apply"
    print("OK: update_item(jobs)")

    if args.cleanup:
        jobs_table.delete_item(Key={"clerk_user_id": test_user_id, "job_id": test_job_id})
        users_table.delete_item(Key={"clerk_user_id": test_user_id})
        print("OK: cleanup(delete_item users/jobs)")
    else:
        print("Note: test rows kept. Run with --cleanup to auto-delete.")

    print("All sanity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

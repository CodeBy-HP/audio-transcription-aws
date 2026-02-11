#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import get_dynamodb_resource, load_dotenv, require_env


def _delete_all_items(table, key_names: list[str]) -> int:
    deleted = 0
    scan_kwargs = {}

    while True:
        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])

        if items:
            with table.batch_writer() as batch:
                for item in items:
                    key = {k: item[k] for k in key_names}
                    batch.delete_item(Key=key)
                    deleted += 1

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset DynamoDB tables used by the project (delete all rows)."
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional path to .env file. Default: repo-root .env",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file or None)
    users_table_name = require_env("USERS_TABLE_NAME")
    jobs_table_name = require_env("JOBS_TABLE_NAME")

    if not args.yes:
        print("This will DELETE ALL ITEMS from:")
        print(f"- {users_table_name}")
        print(f"- {jobs_table_name}")
        confirm = input("Type 'reset' to continue: ").strip().lower()
        if confirm != "reset":
            print("Aborted.")
            return 1

    dynamodb = get_dynamodb_resource()
    users_table = dynamodb.Table(users_table_name)
    jobs_table = dynamodb.Table(jobs_table_name)

    users_deleted = _delete_all_items(users_table, ["clerk_user_id"])
    jobs_deleted = _delete_all_items(jobs_table, ["clerk_user_id", "job_id"])

    print("Reset completed.")
    print(f"Users rows deleted: {users_deleted}")
    print(f"Jobs rows deleted: {jobs_deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

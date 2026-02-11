from __future__ import annotations

import os
from pathlib import Path

import boto3


def _strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_dotenv(path: str | None = None) -> None:
    """Load key=value pairs from .env into process env if keys are not already set."""
    env_path = Path(path) if path else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_wrapping_quotes(value)
        if key and key not in os.environ:
            os.environ[key] = value


def get_aws_region() -> str:
    return os.getenv("AWS_REGION", os.getenv("DEFAULT_AWS_REGION", "us-east-1"))


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=get_aws_region())

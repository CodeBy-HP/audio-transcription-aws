#!/usr/bin/env python3
"""
Create a Lambda deployment zip for notification worker using Docker.

This mirrors the Docker-based packaging approach used in the project so
dependencies are built against a Lambda-compatible environment.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def ensure_docker() -> None:
    try:
        run_command(["docker", "info"])
    except Exception as exc:
        raise RuntimeError("Docker is not available. Start Docker Desktop and retry.") from exc


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if "__pycache__" in file_path.parts:
                continue
            if file_path.suffix == ".pyc":
                continue
            zf.write(file_path, file_path.relative_to(source_dir))


def main() -> int:
    notify_dir = Path(__file__).resolve().parent
    build_dir = notify_dir / ".lambda_build"
    package_dir = build_dir / "package"
    zip_path = notify_dir / "notify_lambda.zip"
    requirements_file = notify_dir / "requirements.txt"

    try:
        ensure_docker()

        remove_path(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
        package_dir.mkdir(parents=True, exist_ok=True)

        if requirements_file.exists() and requirements_file.read_text(encoding="utf-8").strip():
            run_command(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{notify_dir}:/var/task",
                    "-w",
                    "/var/task",
                    "public.ecr.aws/sam/build-python3.11",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                    "-t",
                    ".lambda_build/package",
                ]
            )

        shutil.copy2(notify_dir / "lambda_handler.py", package_dir / "lambda_handler.py")

        remove_path(zip_path)
        zip_directory(package_dir, zip_path)

        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"Created: {zip_path} ({size_mb:.2f} MB)")
        return 0
    except Exception as exc:
        print(f"Packaging failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


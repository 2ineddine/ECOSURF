import argparse
import json
import os
import subprocess
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig


DEFAULT_BUCKET = "ecosurf-dataset"
DEFAULT_PREFIX = "perch/"
DEFAULT_FILES = [
    "perch_embeddings_FINAL.npy",
    "perch_info_FINAL.pkl",
    "labels.npy",
    "embeddings_2d_ALL.npy",
    "perch_info_sample10.pkl",
    "perch_embeddings_sample10.faiss",
    "perch_embeddings_sample10.npy",
]


def load_credentials(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_credentials_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = [
        Path("credentials.json"),
        Path("src") / "credentials.json",
        Path("..") / "credentials.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("credentials.json not found")


def build_s3_client(creds: dict):
    return boto3.client(
        "s3",
        region_name=creds.get("region", "eu-west-2"),
        aws_access_key_id=creds.get("ACCESS_KEY"),
        aws_secret_access_key=creds.get("SECRET_KEY"),
        endpoint_url=creds.get("endpoint", "https://s3.eu-west-2.wasabisys.com"),
    )


def download_files(
    client,
    bucket: str,
    prefix: str,
    files: list[str],
    dest_dir: Path,
):
    dest_dir.mkdir(parents=True, exist_ok=True)
    config = TransferConfig(
        multipart_threshold=32 * 1024 * 1024,
        multipart_chunksize=32 * 1024 * 1024,
        max_concurrency=4,
    )

    for name in files:
        key = f"{prefix}{name}"
        dest = dest_dir / name
        if dest.exists():
            print(f"[skip] {dest}")
            continue
        print(f"[download] s3://{bucket}/{key} -> {dest}")
        client.download_file(bucket, key, str(dest), Config=config)


def run_cmd(cmd: list[str]):
    print(f"[run] {' '.join(cmd)}")
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Setup Perch embeddings and run ECOSURF.")
    parser.add_argument("--creds", default=None, help="Path to credentials.json")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help="S3 bucket name")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="S3 prefix for perch files")
    parser.add_argument("--dest", default="perch2", help="Destination folder")
    parser.add_argument("--install", action="store_true", help="pip install -r requirements.txt")
    parser.add_argument("--run", action="store_true", help="Run app: python main.py")
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES, help="Override file list")
    args = parser.parse_args()

    creds_path = find_credentials_path(args.creds)
    creds = load_credentials(creds_path)
    client = build_s3_client(creds)
    dest_dir = Path(args.dest)

    download_files(client, args.bucket, args.prefix, args.files, dest_dir)

    if args.install:
        run_cmd(["pip", "install", "-r", "requirements.txt"])

    if args.run:
        run_cmd(["python", "main.py"])


if __name__ == "__main__":
    main()

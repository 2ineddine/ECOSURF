#!/usr/bin/env python3
import os
import sys
import json

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("boto3 non installe. Installation...")
    os.system(f"{sys.executable} -m pip install boto3")
    import boto3
    from botocore.exceptions import ClientError


DATA_FILES = [
    "embeddings_2d_ALL.npy",
    "labels_v2.npy",
    "perch_info_FINAL.pkl",
    "perch_embeddings_FINAL.npy",
    "perch_embeddings_sample10.npy",
    "perch_embeddings_sample10.faiss",
    "perch_info_sample10.pkl",
]

S3_PREFIX = "perch2/"
LOCAL_DIR = "perch2"


def load_credentials():
    creds_paths = [
        "credentials.json",
        "src/credentials.json",
        os.path.join(os.path.dirname(__file__), "credentials.json"),
    ]
    for path in creds_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    return None


def get_s3_client(creds):
    return boto3.client(
        "s3",
        endpoint_url=creds["endpoint"],
        aws_access_key_id=creds["ACCESS_KEY"],
        aws_secret_access_key=creds["SECRET_KEY"],
    )


def download_file(s3, bucket, s3_key, local_path):
    try:
        response = s3.head_object(Bucket=bucket, Key=s3_key)
        total_size = response["ContentLength"]
    except ClientError:
        return False, "Fichier non trouve sur S3"

    downloaded = 0
    chunk_size = 1024 * 1024

    try:
        with open(local_path, "wb") as f:
            response = s3.get_object(Bucket=bucket, Key=s3_key)
            body = response["Body"]
            while True:
                chunk = body.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                pct = int(downloaded * 100 / total_size)
                bar = "=" * (pct // 2) + " " * (50 - pct // 2)
                sys.stdout.write(f"\r  [{bar}] {pct}% ({downloaded // 1024 // 1024}MB)")
                sys.stdout.flush()
        print()
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("ECOSURF - Telechargement des donnees")
    print("=" * 60)
    print()

    creds = load_credentials()
    if not creds:
        print("ERREUR: credentials.json non trouve")
        print("Creez un fichier credentials.json avec:")
        print('{')
        print('  "endpoint": "https://...",')
        print('  "ACCESS_KEY": "...",')
        print('  "SECRET_KEY": "...",')
        print('  "bucket": "..."')
        print('}')
        return 1

    print(f"Credentials: OK")
    print(f"Endpoint: {creds['endpoint']}")
    print(f"Bucket: {creds['bucket']}")
    print()

    try:
        s3 = get_s3_client(creds)
        s3.list_buckets()
        print("Connexion S3: OK")
    except Exception as e:
        print(f"ERREUR connexion S3: {e}")
        return 1

    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)
        print(f"Dossier cree: {LOCAL_DIR}/")
    else:
        print(f"Dossier existant: {LOCAL_DIR}/")

    print()
    print("Telechargement des fichiers...")
    print("-" * 60)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for filename in DATA_FILES:
        local_path = os.path.join(LOCAL_DIR, filename)
        s3_key = S3_PREFIX + filename

        if os.path.exists(local_path):
            size_mb = os.path.getsize(local_path) / 1024 / 1024
            print(f"[SKIP] {filename} (existe deja, {size_mb:.1f}MB)")
            skip_count += 1
            continue

        print(f"[DOWN] {filename}")
        ok, err = download_file(s3, creds["bucket"], s3_key, local_path)

        if ok:
            size_mb = os.path.getsize(local_path) / 1024 / 1024
            print(f"  OK ({size_mb:.1f}MB)")
            success_count += 1
        else:
            print(f"  ERREUR: {err}")
            fail_count += 1
            if os.path.exists(local_path):
                os.remove(local_path)

    print()
    print("=" * 60)
    print("RESUME")
    print("=" * 60)
    print(f"Telecharges: {success_count}")
    print(f"Deja presents: {skip_count}")
    print(f"Echecs: {fail_count}")
    print()

    if fail_count == 0:
        print("Tous les fichiers sont prets.")
        print("Lancez l'application avec: python src/main.py")
        return 0
    else:
        print("Certains fichiers n'ont pas pu etre telecharges.")
        print("Verifiez votre connexion et vos credentials.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

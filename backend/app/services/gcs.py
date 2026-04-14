# import os
# from google.cloud import storage as gcs_lib

# _client = None

# def _get_client():
#     global _client
#     if _client is None:
#         _client = gcs_lib.Client()
#     return _client

# def get_bucket_name() -> str:
#     name = os.getenv("GCS_BUCKET_NAME")
#     if not name:
#         raise RuntimeError("GCS_BUCKET_NAME env var not set")
#     return name

# def upload_text(gcs_path: str, content: str, content_type="application/json") -> str:
#     """Upload string content. Returns the gcs_path (used as the stored reference)."""
#     bucket = _get_client().bucket(get_bucket_name())
#     blob = bucket.blob(gcs_path)
#     blob.upload_from_string(content.encode("utf-8"), content_type=content_type)
#     return gcs_path

# def download_text(gcs_path: str) -> str:
#     """Download and return content as string."""
#     bucket = _get_client().bucket(get_bucket_name())
#     blob = bucket.blob(gcs_path)
#     return blob.download_as_text(encoding="utf-8")

# def exists(gcs_path: str) -> bool:
#     bucket = _get_client().bucket(get_bucket_name())
#     return bucket.blob(gcs_path).exists()

import os
from google.cloud import storage as gcs_lib

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = gcs_lib.Client()
    return _client

def get_bucket_name() -> str:
    name = os.getenv("GCS_BUCKET_NAME")
    if not name:
        raise RuntimeError("GCS_BUCKET_NAME env var not set")
    return name

def upload_text(gcs_path: str, content: str, content_type="application/json") -> str:
    bucket = _get_client().bucket(get_bucket_name())
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(content.encode("utf-8"), content_type=content_type)
    return gcs_path  # return path so callers can store it in DB

def download_text(gcs_path: str) -> str:
    bucket = _get_client().bucket(get_bucket_name())
    return bucket.blob(gcs_path).download_as_text(encoding="utf-8")

def file_exists(gcs_path: str) -> bool:
    bucket = _get_client().bucket(get_bucket_name())
    return bucket.blob(gcs_path).exists()
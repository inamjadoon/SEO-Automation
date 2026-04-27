# import os
# from app.schemas.content_document import ContentDocument
# from app.services.gcs import upload_text


# def generate_llms_text(doc: ContentDocument) -> str:
#     lines = []

#     # Title
#     lines.append(f"# {doc.site_id} Knowledge Base\n")

#     # Iterate pages
#     for page in doc.pages:
#         lines.append(f"## {page.title}")
#         lines.append(f"URL: {doc.base_url}{page.url}")
#         lines.append(f"Type: {page.type}")

#         if page.metadata:
#             for k, v in page.metadata.items():
#                 lines.append(f"{k}: {v}")

#         lines.append("")
#         lines.append(page.content.strip())
#         lines.append("\n---\n")

#     return "\n".join(lines)


# def save_llms_file(site_id: str, text: str) -> str:
#     if not site_id:
#         raise ValueError("site_id is empty — cannot build GCS path")
    
#     gcs_path = f"{site_id}/llms.txt"
#     result = upload_text(gcs_path, text, content_type="text/plain")
#     return result
import logging
from app.schemas.content_document import ContentDocument
from app.services.gcs import upload_text

logger = logging.getLogger("llms_service")

GCS_BUCKET_NAME = "ai-seo-files"
GCS_PUBLIC_BASE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"


def generate_llms_text(doc: ContentDocument) -> str:
    lines = []

    lines.append(f"# {doc.site_id} Knowledge Base\n")

    for page in doc.pages:
        lines.append(f"## {page.title}")
        lines.append(f"URL: {doc.base_url}{page.url}")
        lines.append(f"Type: {page.type}")

        if page.metadata:
            for k, v in page.metadata.items():
                lines.append(f"{k}: {v}")

        lines.append("")
        lines.append(page.content.strip())
        lines.append("\n---\n")

    return "\n".join(lines)


def save_llms_file(site_id: str, text: str) -> str:
    if not site_id:
        raise ValueError("site_id is empty — cannot build GCS path")

    gcs_path = f"{site_id}/llms.txt"
    upload_text(gcs_path, text, content_type="text/plain")

    public_url = f"{GCS_PUBLIC_BASE}/{gcs_path}"
    logger.info("llms.txt uploaded for site %s → %s", site_id, public_url)
    return public_url
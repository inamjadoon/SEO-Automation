import os
from app.schemas.content_document import ContentDocument
from app.services.gcs import upload_text


def generate_llms_text(doc: ContentDocument) -> str:
    lines = []

    # Title
    lines.append(f"# {doc.store_id} Knowledge Base\n")

    # Iterate pages
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


def save_llms_file(store_id: str, text: str) -> str:
    # base_dir = f"generated/{store_id}"
    # os.makedirs(base_dir, exist_ok=True)

    # file_path = os.path.join(base_dir, "llms.txt")

    # with open(file_path, "w", encoding="utf-8") as f:
    #     f.write(text)

    # return file_path
    gcs_path = f"{store_id}/llms.txt"
    return upload_text(gcs_path, text, content_type="text/plain")

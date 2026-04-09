from fastapi import APIRouter, HTTPException
from pathlib import Path
import os

router = APIRouter(prefix="/sites", tags=["Get Generated Files"])


@router.get("/auto-register/{site_id}/files/debug")
def debug_path(site_id: str):
    base = Path("generated") / site_id
    def safe_list(p):
        try:
            return [str(x.relative_to(Path("generated"))) for x in p.rglob("*") if x.is_file()]
        except:
            return []
    return {
        "cwd": str(Path.cwd()),
        "exists": base.exists(),
        "all_files": safe_list(base) if base.exists() else []
    }


@router.get("/auto-register/{site_id}/files")
def get_site_files(site_id: str):
    base = Path("generated") / site_id

    if not base.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No generated files found for site '{site_id}'"
        )

    api_base = os.getenv("API_BASE", "http://localhost:8000")
    result = {"site_id": site_id, "groups": [], "total_files": 0}

    # ── 1. LLM text file ─────────────────────────────────────────────────────
    llm_file = base / "llms.txt"
    if not llm_file.exists():
        llm_file = base / "llm.txt"
    if llm_file.exists():
        result["groups"].append({
            "type": "llm",
            "label": "LLM Context",
            "icon": "📄",
            "files": [{
                "name": llm_file.name,
                "url": f"{api_base}/llms/{site_id}",
                "size": llm_file.stat().st_size,
            }]
        })

    # ── 2. JSON-LD pages ──────────────────────────────────────────────────────
    # structure: jsonld/pages/*.jsonld  +  jsonld/*.jsonld (root level like homepage.jsonld)
    jsonld_files = []

    # jsonld/pages/*.jsonld
    pages_dir = base / "jsonld" / "pages"
    if pages_dir.exists():
        for f in sorted(pages_dir.glob("*.jsonld")):
            stem = f.stem  # e.g. "our-success-stories" or "Urraan"
            page_path = "/" if stem.lower() in ("home", "homepage") else f"/{stem}"
            jsonld_files.append({
                "name": f.name,
                "url": f"{api_base}/sites/{site_id}/jsonld?path={page_path}",
                "size": f.stat().st_size,
                "page_path": page_path,
            })

    # jsonld/*.jsonld (root level, e.g. homepage.jsonld)
    jsonld_dir = base / "jsonld"
    if jsonld_dir.exists():
        for f in sorted(jsonld_dir.glob("*.jsonld")):
            stem = f.stem
            page_path = "/" if stem.lower() in ("home", "homepage") else f"/{stem}"
            jsonld_files.append({
                "name": f.name,
                "url": f"{api_base}/sites/{site_id}/jsonld?path={page_path}",
                "size": f.stat().st_size,
                "page_path": page_path,
            })

    if jsonld_files:
        result["groups"].append({
            "type": "jsonld",
            "label": "JSON-LD / Pages",
            "icon": "{}",
            "files": jsonld_files,
        })

    # ── 3. FAQ files — jsonld/faqs/*.jsonld ───────────────────────────────────
    faq_files = []

    # Try jsonld/faqs/ first, then jsonld/faq/, then faq/
    for faq_candidate in [base / "jsonld" / "faqs", base / "jsonld" / "faq", base / "faq"]:
        if faq_candidate.exists():
            for f in sorted(faq_candidate.glob("*.jsonld")):
                stem = f.stem
                page_path = "/" if stem.lower() in ("home", "homepage") else f"/{stem}"
                faq_files.append({
                    "name": f.name,
                    "url": f"{api_base}/sites/{site_id}/faqs/{f.name}",
                    "size": f.stat().st_size,
                    "page_path": page_path,
                })
            break  # stop at first folder that exists

    if faq_files:
        result["groups"].append({
            "type": "faq",
            "label": "FAQ Schema",
            "icon": "❓",
            "files": faq_files,
        })

    # ── 4. Articles ───────────────────────────────────────────────────────────
    articles_dir = base / "articles"
    if articles_dir.exists():
        article_files = []
        for f in sorted(articles_dir.rglob("*.jsonld")):
            article_files.append({
                "name": f.name,
                "url": f"{api_base}/sites/{site_id}/jsonld?path=/articles/{f.stem}",
                "size": f.stat().st_size,
                "page_path": f"/articles/{f.stem}",
            })
        if article_files:
            result["groups"].append({
                "type": "articles",
                "label": "Articles",
                "icon": "📰",
                "files": article_files,
            })

    result["total_files"] = sum(len(g["files"]) for g in result["groups"])
    return result

# @router.get("/auto-register/{site_id}/files/debug")
# def debug_path(site_id: str):
#     base = Path("generated") / site_id
#     return {
#         "cwd": str(Path.cwd()),
#         "looking_for": str(base.resolve()),
#         "exists": base.exists(),
#         "generated_exists": Path("generated").exists(),
#         "generated_contents": [str(p) for p in Path("generated").iterdir()] if Path("generated").exists() else []
#     }
@router.get("/auto-register/{site_id}/files/debug")
def debug_path(site_id: str):
    base = Path("generated") / site_id
    
    # Check all possible faq locations
    faq_candidates = [
        base / "jsonld" / "faqs",
        base / "jsonld" / "faq", 
        base / "faq",
    ]
    
    faq_info = {}
    for p in faq_candidates:
        faq_info[str(p)] = {
            "exists": p.exists(),
            "files": [str(f.name) for f in p.glob("*")] if p.exists() else []
        }
    
    return {
        "cwd": str(Path.cwd()),
        "all_files": [str(x.relative_to(base)) for x in base.rglob("*") if x.is_file()],
        "faq_candidates": faq_info
    }
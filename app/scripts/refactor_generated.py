
from __future__ import annotations

import json
import os
from pathlib import Path

from app.database import SessionLocal
from app.models.entity import Entity


ROOT = Path("generated")


def _target_rel_path(entity: Entity) -> Path:
    """
    Compute the relative JSON-LD path inside the site folder for an entity.
    """
    etype = (entity.entity_type or "").lower()
    slug = entity.entity_id or "item"
    path = (entity.canonical_url or "/").strip() or "/"

    if path == "/":
        return Path("jsonld/homepage.jsonld")

    if etype == "product":
        return Path("jsonld/products") / f"{slug}.jsonld"
    if etype in {"article", "blog"}:
        return Path("jsonld/articles") / f"{slug}.jsonld"

    # default to generic page
    return Path("jsonld/pages") / f"{slug}.jsonld"


def main() -> None:
    ROOT.mkdir(exist_ok=True)

    session = SessionLocal()
    site_manifest: dict[str, dict[str, str]] = {}

    try:
        entities = session.query(Entity).all()
        for e in entities:
            # Skip entities we can't safely assign to a site
            if not e.site_id or not e.jsonld_path:
                continue

            src = Path(e.jsonld_path)
            if not src.exists():
                continue

            site_id = e.site_id
            site_root = ROOT / site_id
            rel_path = _target_rel_path(e)
            dest = site_root / rel_path

            dest.parent.mkdir(parents=True, exist_ok=True)

            try:
                src.rename(dest)
            except OSError:
                # If move fails, skip this entity
                continue

            # Update DB path so existing code continues to work
            e.jsonld_path = str(dest)

            # Add to manifest mapping
            canonical = (e.canonical_url or "/").strip() or "/"
            mf = site_manifest.setdefault(site_id, {})
            # Ensure paths in manifest are relative and POSIX-style
            mf[canonical] = str(rel_path).replace(os.sep, "/")

        session.commit()

    finally:
        session.close()

    # Write manifest.json per site
    for site_id, mapping in site_manifest.items():
        site_root = ROOT / site_id
        if not site_root.exists():
            continue
        manifest_path = site_root / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()


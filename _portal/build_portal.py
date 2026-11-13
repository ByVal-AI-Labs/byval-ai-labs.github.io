#!/usr/bin/env python3
"""Assemble the Workbench site.

Every top-level folder with a meta.json and an index.html is a *section*, published by one source
repository. This script validates each section, renders the landing page from
_portal/template.html, and copies everything into the output folder that GitHub Pages deploys.
A broken section is skipped with a warning, so it never takes the rest of the portal down.

Usage:
    python3 _portal/build_portal.py [--out _site]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PORTAL_DIR = Path(__file__).resolve().parent
ROOT = PORTAL_DIR.parent
TEMPLATE = PORTAL_DIR / "template.html"

SECTION_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SECTIONS_MARKER = "<!--PORTAL_SECTIONS-->"
COUNT_MARKER = "<!--PORTAL_COUNT-->"
DEFAULT_CATEGORY = "General"
DEFAULT_ORDER = 100
STRING_FIELDS = ("title", "description", "owner", "category", "updated")
REQUIRED_FIELDS = ("title", "description")


class SectionError(Exception):
    """A section folder does not follow the portal contract (see README.md)."""


def load_section(folder: Path) -> dict[str, object]:
    if not SECTION_NAME.match(folder.name):
        raise SectionError("folder name must be lowercase letters, digits and hyphens")
    if not (folder / "index.html").is_file():
        raise SectionError("missing index.html")
    try:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SectionError(f"meta.json is not valid JSON: {error}") from error
    if not isinstance(meta, dict):
        raise SectionError("meta.json must be a JSON object")
    for field in REQUIRED_FIELDS:
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            raise SectionError(f"meta.json needs a non-empty string '{field}'")
    for field in STRING_FIELDS:
        if field in meta and not isinstance(meta[field], str):
            raise SectionError(f"meta.json '{field}' must be a string")
    order = meta.get("order", DEFAULT_ORDER)
    if not isinstance(order, int) or isinstance(order, bool):
        raise SectionError("meta.json 'order' must be an integer")
    return {
        "slug": folder.name,
        "title": meta["title"].strip(),
        "description": meta["description"].strip(),
        "owner": meta.get("owner", "").strip(),
        "category": meta.get("category", "").strip() or DEFAULT_CATEGORY,
        "updated": meta.get("updated", "").strip(),
        "order": order,
    }


def discover_sections() -> list[dict[str, object]]:
    sections = []
    for folder in sorted(ROOT.iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "_")):
            continue
        if not (folder / "meta.json").is_file():
            print(f"::warning::{folder.name}/ has no meta.json — not published")
            continue
        try:
            sections.append(load_section(folder))
        except SectionError as error:
            print(f"::warning::{folder.name}/ skipped: {error}")
    return sections


def _format_date(value: str) -> str:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return f"{moment.day} {moment:%b %Y}"


def render_card(section: dict[str, object]) -> str:
    esc = lambda key: html.escape(str(section[key]))  # noqa: E731 — local shorthand
    meta_bits = []
    if section["owner"]:
        meta_bits.append(f"<span>{esc('owner')}</span>")
    updated = _format_date(str(section["updated"]))
    if updated:
        meta_bits.append(f'<span>Updated <time datetime="{esc("updated")}">{updated}</time></span>')
    meta = f'<div class="card-meta">{"".join(meta_bits)}</div>' if meta_bits else ""
    return (
        f'<a class="card" href="{esc("slug")}/">'
        f'<h3>{esc("title")}</h3><p>{esc("description")}</p>{meta}'
        f'<span class="card-go" aria-hidden="true">Open →</span></a>'
    )


def render_sections(sections: list[dict[str, object]]) -> str:
    if not sections:
        return '<p class="empty">No sections published yet.</p>'
    groups: dict[str, list[dict[str, object]]] = {}
    for section in sorted(sections, key=lambda s: (s["order"], str(s["title"]).lower())):
        groups.setdefault(str(section["category"]), []).append(section)
    parts = []
    for category, members in groups.items():  # insertion order = lowest order first
        cards = "".join(render_card(section) for section in members)
        parts.append(f'<section class="group"><h2>{html.escape(category)}</h2><div class="grid">{cards}</div></section>')
    return "\n".join(parts)


def build(out: Path) -> int:
    sections = discover_sections()
    template = TEMPLATE.read_text(encoding="utf-8")
    for marker in (SECTIONS_MARKER, COUNT_MARKER):
        if template.count(marker) != 1:
            print(f"✘ {TEMPLATE.relative_to(ROOT)} must contain {marker} exactly once", file=sys.stderr)
            return 1
    count = f"{len(sections)} section{'s' if len(sections) != 1 else ''}"
    page = template.replace(SECTIONS_MARKER, render_sections(sections)).replace(COUNT_MARKER, count)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for section in sections:
        shutil.copytree(ROOT / str(section["slug"]), out / str(section["slug"]))
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / ".nojekyll").touch()
    print(f"✔ built {out} with {count}: {', '.join(str(s['slug']) for s in sections) or '—'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="_site", help="output folder (default: _site)")
    args = parser.parse_args()
    out = Path(args.out)
    return build(out if out.is_absolute() else ROOT / out)


if __name__ == "__main__":
    sys.exit(main())

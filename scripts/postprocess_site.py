#!/usr/bin/env python3

from __future__ import annotations

import os
import re
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
TEXT_SUFFIXES = {".css", ".html", ".json", ".txt", ".xml"}
GOOGLE_FONT_IMPORT = re.compile(
    r'@import\s*(?:url\(\s*)?(?:"https://fonts\.googleapis\.com[^"]+"|\'https://fonts\.googleapis\.com[^\']+\')\s*\)?\s*;?',
    re.IGNORECASE,
)
GOOGLE_FONT_URL = re.compile(
    r'https://fonts\.googleapis\.com[^\s"\')]+',
    re.IGNORECASE,
)
GOOGLE_GSTATIC_URL = re.compile(
    r'https://fonts\.gstatic\.com[^\s"\')]+',
    re.IGNORECASE,
)


def remove_sidecars() -> None:
    for root, _, files in os.walk(DOCS_DIR):
        root_path = Path(root)
        for filename in files:
            if filename.startswith("._") or filename == ".DS_Store":
                (root_path / filename).unlink()


def normalize_text_files() -> None:
    for path in DOCS_DIR.rglob("*"):
        if "site_libs" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if any(part.startswith("._") for part in path.parts):
            continue

        content = path.read_text(encoding="utf-8")
        normalized = "\n".join(line.rstrip() for line in content.splitlines())
        if content.endswith("\n") or normalized:
            normalized += "\n"

        if normalized != content:
            path.write_text(normalized, encoding="utf-8")


def remove_external_font_imports() -> None:
    for path in DOCS_DIR.rglob("*.css"):
        if any(part.startswith("._") for part in path.parts):
            continue

        content = path.read_text(encoding="utf-8")
        normalized = GOOGLE_FONT_IMPORT.sub("", content)
        normalized = GOOGLE_FONT_URL.sub("", normalized)
        normalized = GOOGLE_GSTATIC_URL.sub("", normalized)
        if normalized != content:
            path.write_text(normalized, encoding="utf-8")


def main() -> int:
    if not DOCS_DIR.exists():
        raise SystemExit(f"docs 目录不存在: {DOCS_DIR}")

    remove_sidecars()
    normalize_text_files()
    remove_external_font_imports()
    print("Postprocessed generated site output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

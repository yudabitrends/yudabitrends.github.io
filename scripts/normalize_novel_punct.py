#!/usr/bin/env python3
"""Normalize Chinese-context punctuation across novel qmd files.

What this does, in order, per non-YAML / non-code-block region of each file:

1. ``**Speaker**:`` → ``**Speaker**：``
2. ASCII ``"`` / ``'`` curlified per line, but only when adjacent to CJK or
   surrounded by whitespace — pure English clauses keep their straight quotes.
3. Half-width ``, ; : ? !`` → full-width ``，；：？！`` whenever an adjacent
   non-space character (looking back first, then forward) is CJK (incl. curly
   quotes and other Chinese-typography filler chars).

The transformation is **idempotent**: re-running on already-clean text is a
no-op. The CLI accepts file paths and either writes back in place or reports
violations only (``--check``).

Build scripts can also ``from normalize_novel_punct import transform_md_body``
to get the same normalization applied to source MD content before it is laid
into a qmd template.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# -- Character classification --------------------------------------------------

CJK_RANGES = (
    (0x3400, 0x4DBF),   # CJK Ext A
    (0x4E00, 0x9FFF),   # CJK Unified
    (0xF900, 0xFAFF),   # CJK Compat Ideographs
    (0x20000, 0x2FFFF), # CJK Ext B-F
    (0x3000, 0x303F),   # CJK punctuation
    (0xFF00, 0xFFEF),   # Fullwidth forms
)

# Curly quotes, em-dash, ellipsis — count as CJK-adjacent for punctuation
# normalization. This is what makes ``"建议作者澄清","建议者补充"`` work:
# the inner ``,`` is between two ``"`` (U+201D / U+201C), and we treat those
# as Chinese-typography filler so the comma gets normalized to ``，``.
CJK_LIKE_EXTRA = set("""‘’“”—…""")

HALF_TO_FULL = {",": "，", ";": "；", ":": "：", "?": "？", "!": "！"}

DIALOG_HEADER = re.compile(r"(\*\*[^*\n]+\*\*)([:：])")

# HTML entities like &middot; &amp; &larr; &rarr; &#8212; etc. The trailing
# ``;`` is structural and must never be converted to full-width.
HTML_ENTITY_TAIL = re.compile(r"&(#[0-9]+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);")


def is_cjk(ch: str) -> bool:
    if not ch:
        return False
    if ch in CJK_LIKE_EXTRA:
        return True
    cp = ord(ch)
    for lo, hi in CJK_RANGES:
        if lo <= cp <= hi:
            return True
    return False


# -- Quote curlification -------------------------------------------------------

def _neighbors(line: str, i: int) -> tuple[str, str]:
    """Return the nearest non-whitespace neighbors on each side of position ``i``."""
    j = i - 1
    while j >= 0 and line[j] in (" ", "\t"):
        j -= 1
    prev = line[j] if j >= 0 else ""
    k = i + 1
    while k < len(line) and line[k] in (" ", "\t"):
        k += 1
    nxt = line[k] if k < len(line) else ""
    return prev, nxt


def _curlify_line(line: str) -> str:
    """Per-line alternating open/close toggle for ASCII ``"`` and ``'``.

    Rule: a quote is only converted to its **opening** form if the nearest
    non-space neighbor on either side is CJK (or CJK-like). Once we have
    emitted a Chinese-style opening curly quote, we are inside a Chinese-style
    quotation — any matching ASCII ``"`` we encounter before the line ends is
    forced to the closing curly form, regardless of its local context. This
    keeps pairs from going mismatched when an English phrase is wrapped by
    Chinese text (e.g. ``他说："Don't decorate."``).
    """
    dq_open = True   # next " is treated as the opening one
    sq_open = True
    inside_dq = False  # we have already emitted a curly opening "
    inside_sq = False
    out: list[str] = []
    in_inline_code = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]

        if ch == "`":
            in_inline_code = not in_inline_code
            out.append(ch)
            i += 1
            continue
        if in_inline_code:
            out.append(ch)
            i += 1
            continue

        if ch == '"':
            if inside_dq:
                out.append("”")
                inside_dq = False
                dq_open = True
            else:
                prev, nxt = _neighbors(line, i)
                if is_cjk(prev) or is_cjk(nxt):
                    out.append("“")
                    inside_dq = True
                    dq_open = False
                else:
                    out.append(ch)
        elif ch == "'":
            if inside_sq:
                out.append("’")
                inside_sq = False
                sq_open = True
            else:
                prev, nxt = _neighbors(line, i)
                if is_cjk(prev) or is_cjk(nxt):
                    out.append("‘")
                    inside_sq = True
                    sq_open = False
                else:
                    out.append(ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def curlify_quotes(text: str) -> str:
    """Curlify ASCII ``"`` / ``'`` per line. Toggles reset on each line so a
    paragraph break that happens to have unbalanced quotes doesn't cascade.
    """
    return "\n".join(_curlify_line(line) for line in text.split("\n"))


# -- Half-width → full-width punctuation --------------------------------------

def _html_entity_positions(text: str) -> set[int]:
    """Return positions whose ``;`` closes an HTML entity (skip those)."""
    return {m.end() - 1 for m in HTML_ENTITY_TAIL.finditer(text)}


def normalize_half_to_full(text: str) -> str:
    """Convert ``, ; : ? !`` to full-width forms inside CJK context."""
    out: list[str] = []
    n = len(text)
    in_inline_code = False
    entity_semis = _html_entity_positions(text)
    for i, ch in enumerate(text):
        if ch == "`":
            in_inline_code = not in_inline_code
            out.append(ch)
            continue
        if in_inline_code:
            out.append(ch)
            continue
        # Preserve trailing ``;`` of HTML entities (&middot; &amp; &larr; …)
        if ch == ";" and i in entity_semis:
            out.append(ch)
            continue
        if ch in HALF_TO_FULL:
            # look back
            j = i - 1
            while j >= 0 and text[j] in (" ", "\t"):
                j -= 1
            prev = text[j] if j >= 0 else ""
            # look forward
            k = i + 1
            while k < n and text[k] in (" ", "\t"):
                k += 1
            nxt = text[k] if k < n else ""

            # Special-case URLs: ``http://`` / ``https://`` / ``ftp://``.
            # The ``:`` after the scheme is preceded by ascii letters, so
            # is_cjk(prev) is False; this is just a defensive guard.
            if ch == ":" and prev.isalpha() and nxt == "/":
                out.append(ch)
                continue

            if is_cjk(prev) or is_cjk(nxt):
                out.append(HALF_TO_FULL[ch])
                continue
        out.append(ch)
    return "".join(out)


def normalize_dialog_headers(text: str) -> str:
    """``**X**:`` → ``**X**：`` regardless of what follows."""
    return DIALOG_HEADER.sub(lambda m: f"{m.group(1)}：", text)


# -- High-level transforms ----------------------------------------------------

def transform_md_body(text: str) -> str:
    """Normalize a chunk of Markdown body text (no YAML, no full qmd shell).

    Order matters:
    1. ``**Speaker**:`` → ``**Speaker**：``.
    2. ``, ; : ? !`` → full-width whenever an adjacent non-space character is
       CJK. Must run **before** quote curlification, otherwise a quote like
       ``…吗?"`` would see ASCII ``?`` on one side and fail to curlify the
       closing ``"``.
    3. Quote curlification.
    4. ``, ; : ? !`` → full-width **again**: the curly quotes we just emitted
       are themselves CJK-like, so any half-width punctuation that sits next
       to them (e.g. ``Excuse me?”``) now becomes eligible for conversion.
       This second pass is what makes the transformation idempotent.
    """
    text = normalize_dialog_headers(text)
    text = normalize_half_to_full(text)
    text = curlify_quotes(text)
    text = normalize_half_to_full(text)
    return text


def transform_qmd(text: str) -> str:
    """Normalize a full qmd: skip YAML frontmatter and fenced code blocks."""
    lines = text.split("\n")
    out: list[str] = []
    in_yaml = False
    yaml_fences_seen = 0
    in_code_fence = False

    # Detect YAML only if the first non-blank line is ``---``.
    first_non_blank = next((ln for ln in lines if ln.strip() != ""), "")
    has_yaml = first_non_blank.strip() == "---"

    for line in lines:
        stripped = line.strip()

        if has_yaml and yaml_fences_seen < 2:
            out.append(line)
            if stripped == "---":
                yaml_fences_seen += 1
                if yaml_fences_seen == 1:
                    in_yaml = True
                elif yaml_fences_seen == 2:
                    in_yaml = False
            continue

        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            out.append(line)
            continue
        if in_code_fence:
            out.append(line)
            continue

        out.append(transform_md_body(line))

    return "\n".join(out)


# -- CLI ----------------------------------------------------------------------

def _diff_count(before: str, after: str) -> int:
    """Count differing characters (cheap stand-in for ``how many fixes``)."""
    if before == after:
        return 0
    # cheap approximation: count positions where char differs
    return sum(1 for a, b in zip(before, after) if a != b) + abs(len(before) - len(after))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report files that would change; non-zero exit if any",
    )
    args = parser.parse_args(argv)

    files_changed = 0
    total_changes = 0
    for p in args.paths:
        if not p.is_file():
            print(f"skip (not a file): {p}", file=sys.stderr)
            continue
        original = p.read_text(encoding="utf-8")
        normalized = transform_qmd(original)
        diff = _diff_count(original, normalized)
        if diff == 0:
            continue
        files_changed += 1
        total_changes += diff
        if args.check:
            print(f"would change: {p}  (~{diff} edits)")
        else:
            p.write_text(normalized, encoding="utf-8")
            print(f"normalized:   {p}  (~{diff} edits)")

    if args.check:
        if files_changed:
            print(f"\n{files_changed} file(s) would change, ~{total_changes} edits total.")
            return 1
        print("all clean ✓")
        return 0
    print(f"\n{files_changed} file(s) normalized, ~{total_changes} edits total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

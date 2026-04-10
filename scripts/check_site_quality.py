#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, unquote
import sys
import re


SITE_URL = "https://yudabitrends.github.io"
DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"

CRITICAL_PAGES = {
    "index.html": {
        "lang": "en",
        "title": "Yuda Bi",
        "description": "Academic homepage of Yuda Bi, featuring research in statistical physics, information geometry, theoretical neuroscience, and spectral methods.",
    },
    "publications.html": {
        "lang": "en",
        "title": "Publications – Yuda Bi",
        "description": "Peer-reviewed publications by Yuda Bi on statistical physics, information geometry, spectral graph theory, and theoretical neuroscience.",
    },
    "novels.html": {
        "lang": "zh-CN",
        "title": "小说 – Yuda Bi",
        "description": "Yuda Bi 的小说作品页，收录《漫长的求证》和《被剪枝的世界》，以中文印刷出版风格呈现。",
    },
    "novels/manchangdeqiuzheng/index.html": {
        "lang": "zh-CN",
        "title": "漫长的求证 – Yuda Bi",
        "description": "长篇小说《漫长的求证》章节目录页，关于县城、物理、异乡与漫长求索。",
    },
    "novels/beijianzhideshijie/index.html": {
        "lang": "zh-CN",
        "title": "被剪枝的世界 – Yuda Bi",
        "description": "长篇小说《被剪枝的世界》章节目录页，关于系统、记录重写与不被覆盖的真实。",
    },
}

DISALLOWED_SNIPPETS = {
    "visitor-badge.laobi.icu": "第三方 visitor badge 仍存在于生成站点中",
    "link.rel = 'canonical'": "仍存在运行时 canonical 注入脚本",
}

DISALLOWED_CSS_PATTERNS = {
    re.compile(r'@import\s*(?:url\()?["\']https://fonts\.googleapis\.com', re.IGNORECASE): "Google Fonts 依赖仍存在于生成站点中",
    re.compile(r'url\(["\']?https://fonts\.gstatic\.com', re.IGNORECASE): "Google Fonts preconnect 仍存在于生成站点中",
}

DISALLOWED_HTML_SNIPPETS = {
    "fonts.googleapis.com": "Google Fonts 依赖仍存在于生成站点中",
    "fonts.gstatic.com": "Google Fonts preconnect 仍存在于生成站点中",
}

SKIP_SCHEMES = {"", "mailto", "tel", "javascript", "data", "blob"}


@dataclass
class ParsedPage:
    title: str = ""
    html_lang: Optional[str] = None
    meta_name: Dict[str, str] = field(default_factory=dict)
    meta_property: Dict[str, str] = field(default_factory=dict)
    canonicals: List[str] = field(default_factory=list)
    links: List[Tuple[str, str]] = field(default_factory=list)


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = ParsedPage()
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}

        if tag == "html":
            self.page.html_lang = attr_map.get("lang") or attr_map.get("xml:lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attr_map.get("name")
            prop = attr_map.get("property")
            content = attr_map.get("content", "")
            if name:
                self.page.meta_name[name] = content
            if prop:
                self.page.meta_property[prop] = content
        elif tag == "link":
            href = attr_map.get("href")
            if href:
                self.page.links.append((tag, href))
            rel_values = {part.strip().lower() for part in attr_map.get("rel", "").split()}
            if "canonical" in rel_values and href:
                self.page.canonicals.append(href)
        elif tag in {"a", "img", "script", "source"}:
            attr_name = "href" if tag == "a" else "src"
            target = attr_map.get(attr_name)
            if target:
                self.page.links.append((tag, target))

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.page.title += data


def parse_page(page_path: Path) -> ParsedPage:
    parser = SiteHTMLParser()
    parser.feed(page_path.read_text(encoding="utf-8"))
    parser.close()
    parser.page.title = parser.page.title.strip()
    return parser.page


def iter_html_pages() -> List[Path]:
    return [
        path
        for path in DOCS_DIR.rglob("*.html")
        if not any(part.startswith("._") for part in path.parts)
    ]


def iter_text_assets() -> List[Path]:
    allowed_suffixes = {".css", ".html", ".js"}
    return [
        path
        for path in DOCS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed_suffixes
        and not any(part.startswith("._") for part in path.parts)
    ]


def normalize_site_url(url: str) -> Tuple[str, str]:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return parsed.netloc, path


def expected_canonical(rel_path: str) -> str:
    if rel_path == "index.html":
        return f"{SITE_URL}/"
    if rel_path.endswith("index.html"):
        web_path = rel_path[: -len("index.html")]
        return f"{SITE_URL}/{web_path}".replace("//", "/", 1).replace("https:/", "https://")
    return f"{SITE_URL}/{rel_path}"


def resolve_docs_target(source_path: Path, raw_target: str) -> Optional[Path]:
    parsed = urlparse(raw_target)
    scheme = parsed.scheme.lower()

    if scheme and scheme not in {"http", "https"}:
        return None
    if scheme in {"http", "https"}:
        if normalize_site_url(raw_target)[0] != normalize_site_url(SITE_URL)[0]:
            return None
        target_path = unquote(parsed.path or "/")
        return resolve_site_path(target_path)

    path_text = unquote(parsed.path)
    if not path_text:
        return None
    if path_text.startswith("/"):
        return resolve_site_path(path_text)

    return resolve_candidate((source_path.parent / path_text).resolve())


def resolve_site_path(path_text: str) -> Optional[Path]:
    clean_path = path_text.lstrip("/")
    if not clean_path:
        return resolve_candidate(DOCS_DIR / "index.html")
    return resolve_candidate(DOCS_DIR / clean_path)


def resolve_candidate(candidate: Path) -> Optional[Path]:
    try:
        candidate.relative_to(DOCS_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_dir():
        index_candidate = candidate / "index.html"
        if index_candidate.exists():
            return index_candidate
        return candidate
    if candidate.exists():
        return candidate

    if candidate.suffix == "":
        html_candidate = candidate.with_suffix(".html")
        if html_candidate.exists():
            return html_candidate
        index_candidate = candidate / "index.html"
        if index_candidate.exists():
            return index_candidate

    return None


def check_metadata(rel_path: str, expected: Dict[str, str], errors: List[str]) -> None:
    page_path = DOCS_DIR / rel_path
    if not page_path.exists():
        errors.append(f"{rel_path}: 关键页面缺失")
        return

    parsed = parse_page(page_path)
    description = parsed.meta_name.get("description", "")
    og_description = parsed.meta_property.get("og:description", "")
    twitter_description = parsed.meta_name.get("twitter:description", "")
    og_title = parsed.meta_property.get("og:title", "")
    twitter_title = parsed.meta_name.get("twitter:title", "")

    if parsed.html_lang != expected["lang"]:
        errors.append(f"{rel_path}: lang 应为 {expected['lang']}，实际为 {parsed.html_lang!r}")

    if parsed.title != expected["title"]:
        errors.append(f"{rel_path}: <title> 应为 {expected['title']!r}，实际为 {parsed.title!r}")

    if description != expected["description"]:
        errors.append(f"{rel_path}: meta description 未匹配预期文案")

    if og_title != expected["title"]:
        errors.append(f"{rel_path}: og:title 未与页面标题同步")

    if twitter_title != expected["title"]:
        errors.append(f"{rel_path}: twitter:title 未与页面标题同步")

    if og_description != description:
        errors.append(f"{rel_path}: og:description 未与页面 description 同步")

    if twitter_description != description:
        errors.append(f"{rel_path}: twitter:description 未与页面 description 同步")

    if not parsed.canonicals:
        errors.append(f"{rel_path}: 缺少静态 canonical link")
    else:
        actual_canonical = parsed.canonicals[0]
        if normalize_site_url(actual_canonical) != normalize_site_url(expected_canonical(rel_path)):
            errors.append(
                f"{rel_path}: canonical 不符合预期，实际为 {actual_canonical!r}"
            )

    for meta_key, label in (("og:image", "og:image"), ("twitter:image", "twitter:image")):
        image_target = parsed.meta_property.get(meta_key) if meta_key.startswith("og:") else parsed.meta_name.get(meta_key)
        if not image_target:
            errors.append(f"{rel_path}: 缺少 {label}")
            continue
        resolved = resolve_docs_target(page_path, image_target)
        if resolved is None or not resolved.exists():
            errors.append(f"{rel_path}: {label} 指向了不存在的站内资源 {image_target!r}")


def check_internal_links(errors: List[str]) -> None:
    for html_path in iter_html_pages():
        parsed = parse_page(html_path)
        for tag, raw_target in parsed.links:
            parsed_url = urlparse(raw_target)
            if parsed_url.scheme.lower() in SKIP_SCHEMES and not parsed_url.path:
                continue
            if raw_target.startswith("#"):
                continue
            resolved = resolve_docs_target(html_path, raw_target)
            if resolved is None:
                continue
            if not resolved.exists():
                rel_source = html_path.relative_to(DOCS_DIR)
                errors.append(f"{rel_source}: {tag} 指向不存在的站内资源 {raw_target!r}")


def check_disallowed_snippets(errors: List[str]) -> None:
    for asset_path in iter_text_assets():
        content = asset_path.read_text(encoding="utf-8")
        for needle, message in DISALLOWED_SNIPPETS.items():
            if needle in content:
                rel_source = asset_path.relative_to(DOCS_DIR)
                errors.append(f"{rel_source}: {message}")
        if asset_path.suffix.lower() == ".html":
            for needle, message in DISALLOWED_HTML_SNIPPETS.items():
                if needle in content:
                    rel_source = asset_path.relative_to(DOCS_DIR)
                    errors.append(f"{rel_source}: {message}")
        if asset_path.suffix.lower() == ".css":
            for pattern, message in DISALLOWED_CSS_PATTERNS.items():
                if pattern.search(content):
                    rel_source = asset_path.relative_to(DOCS_DIR)
                    errors.append(f"{rel_source}: {message}")


def main() -> int:
    if not DOCS_DIR.exists():
        print(f"docs 目录不存在: {DOCS_DIR}", file=sys.stderr)
        return 1

    errors: List[str] = []

    for rel_path, expected in CRITICAL_PAGES.items():
        check_metadata(rel_path, expected, errors)

    check_internal_links(errors)
    check_disallowed_snippets(errors)

    if errors:
        print("Site quality checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Site quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

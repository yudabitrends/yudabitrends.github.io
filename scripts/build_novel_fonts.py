#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import shutil
import string
import subprocess
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "files" / "fonts"
DOCS_DIR = ROOT / "docs"

FONT_SOURCES = {
    "novel-songti": {
        "url": "https://cdn.jsdelivr.net/gh/adobe-fonts/source-han-serif@release/SubsetOTF/CN/SourceHanSerifCN-Regular.otf",
        "filename": "SourceHanSerifCN-Regular.otf",
    },
    "novel-kaiti": {
        "url": "https://github.com/lxgw/LxgwWenkaiGB/releases/download/v1.522/LXGWWenKaiGB-Regular.ttf",
        "filename": "LXGWWenKaiGB-Regular.ttf",
    },
}

EXTRA_CHARS = (
    "“”‘’《》「」『』【】—–…·、。，；：？！（）〔〕〈〉﹏"
    "复制搜索链接隐藏其它匹配结果清除提交搜索已复制展开或折叠导航栏小说Novels"
    "档消取文件页面切换主题深浅色加载更多上一章下一章目录返回首页关于我"
)

PUNCT_RANGES = (
    (0x3000, 0x303F),
    (0xFF00, 0xFFEF),
)

HTML_TAG_RE = re.compile(r"<[^>]+>")

OLD_FONT_ARTIFACTS = [
    FONT_DIR / "novel-fonts.css",
    FONT_DIR / "noto-serif-sc",
    FONT_DIR / "lxgw-wenkai-screen",
]


def ensure_pyftsubset() -> str:
    pyftsubset = shutil.which("pyftsubset")
    if not pyftsubset:
        raise SystemExit("未找到 pyftsubset，请先安装 fonttools。")
    return pyftsubset


def build_charset_file(temp_dir: Path) -> Path:
    charset = set(string.printable)
    charset.update(EXTRA_CHARS)

    for start, end in PUNCT_RANGES:
        charset.update(chr(cp) for cp in range(start, end + 1))

    source_files = [ROOT / "novels.qmd", *sorted((ROOT / "novels").rglob("*.qmd"))]
    for path in source_files:
        if path.name.startswith("._") or not path.is_file():
            continue
        charset.update(path.read_text(encoding="utf-8", errors="ignore"))

    docs_novels = DOCS_DIR / "novels"
    html_files = []
    if (DOCS_DIR / "novels.html").is_file():
        html_files.append(DOCS_DIR / "novels.html")
    if docs_novels.is_dir():
        html_files.extend(sorted(docs_novels.rglob("*.html")))
    for path in html_files:
        if path.name.startswith("._") or not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        text = HTML_TAG_RE.sub(" ", html)
        charset.update(text)

    charset_file = temp_dir / "novel_chars.txt"
    charset_file.write_text("".join(sorted(charset)), encoding="utf-8")
    return charset_file


CACHE_DIR = Path("/tmp/font-cache")


def download_font(url: str, destination: Path) -> None:
    cached = CACHE_DIR / destination.name
    if cached.is_file() and cached.stat().st_size > 0:
        destination.write_bytes(cached.read_bytes())
        return
    with urllib.request.urlopen(url) as response:
        destination.write_bytes(response.read())


def subset_font(pyftsubset: str, source: Path, charset_file: Path, output: Path, flavor: str) -> None:
    command = [
        pyftsubset,
        str(source),
        f"--text-file={charset_file}",
        f"--output-file={output}",
        f"--flavor={flavor}",
        "--layout-features=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--recommended-glyphs",
        "--ignore-missing-glyphs",
    ]
    subprocess.run(command, check=True)


def clean_old_artifacts() -> None:
    for artifact in OLD_FONT_ARTIFACTS:
        if artifact.is_dir():
            shutil.rmtree(artifact)
        elif artifact.exists():
            artifact.unlink()


def main() -> int:
    pyftsubset = ensure_pyftsubset()
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    clean_old_artifacts()

    with tempfile.TemporaryDirectory(prefix="novel-font-build-") as temp_root:
        temp_dir = Path(temp_root)
        charset_file = build_charset_file(temp_dir)

        for output_stem, source_info in FONT_SOURCES.items():
            source_path = temp_dir / source_info["filename"]
            download_font(source_info["url"], source_path)

            subset_font(
                pyftsubset,
                source_path,
                charset_file,
                FONT_DIR / f"{output_stem}-subset.woff2",
                "woff2",
            )
            subset_font(
                pyftsubset,
                source_path,
                charset_file,
                FONT_DIR / f"{output_stem}-subset.woff",
                "woff",
            )

    print("Novel font subsets rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import shutil
import string
import subprocess
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "files" / "fonts"

FONT_SOURCES = {
    "novel-songti": {
        "url": "https://github.com/lxgw/LxgwZhiSong/releases/download/v0.527/LXGWZhiSongMN.ttf",
        "filename": "LXGWZhiSongMN.ttf",
    },
    "novel-kaiti": {
        "url": "https://github.com/lxgw/LxgwWenkaiGB/releases/download/v1.522/LXGWWenKaiGB-Regular.ttf",
        "filename": "LXGWWenKaiGB-Regular.ttf",
    },
}

EXTRA_CHARS = (
    "“”‘’《》「」『』【】—–…·、。，；：？！（）〔〕〈〉﹏"
    "复制搜索链接隐藏其它匹配结果清除提交搜索已复制展开或折叠导航栏小说Novels"
)

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

    source_files = [ROOT / "novels.qmd", *sorted((ROOT / "novels").rglob("*.qmd"))]
    for path in source_files:
        if path.name.startswith("._") or not path.is_file():
            continue
        charset.update(path.read_text(encoding="utf-8", errors="ignore"))

    charset_file = temp_dir / "novel_chars.txt"
    charset_file.write_text("".join(sorted(charset)), encoding="utf-8")
    return charset_file


def download_font(url: str, destination: Path) -> None:
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

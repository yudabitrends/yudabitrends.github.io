#!/usr/bin/env python3
"""Build the ICA book figures -> docs/ica/fig/*.svg

    python3 book/figures/make_figures.py                 # every chapter
    python3 book/figures/make_figures.py fastica         # one chapter module (book/figures/fastica.py)

Each chapter keeps its figures in book/figures/<chapter-slug>.py, registered with
@figure from figstyle.py. Needs numpy and matplotlib; every figure is seeded.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle  # noqa: E402


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(names):
    mods = [p for p in sorted(HERE.glob("*.py")) if p.name not in ("figstyle.py", "make_figures.py")]
    if names:
        mods = [p for p in mods if p.stem in names]
    for p in mods:
        before = set(figstyle.FIGS)
        load(p)
        for name in [n for n in figstyle.FIGS if n not in before]:
            figstyle.FIGS[name]()


if __name__ == "__main__":
    main(sys.argv[1:])

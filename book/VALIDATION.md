# ICA textbook validation and reproduction

The editable source is book/src/*.html. The build generates docs/ica/*.html,
docs/ica/code/*.py and docs/ica/search-index.json. Do not edit generated copies.

## Reproduce locally

Requires Node.js 18 or later and Python 3.12 (the CI configuration uses Node 22).
Create a virtual environment and install the pinned numerical dependencies:

    python -m venv .venv
    # Activate the environment using the command for your operating system.
    python -m pip install -r book/requirements-figures.txt
    node book/build.mjs --strict
    python scripts/check_book.py --run-code --report book-results.json
    python scripts/test_book_quality.py
    python scripts/tests_foundations.py
    python scripts/tests_algorithms.py
    python scripts/tests_advanced.py
    python scripts/tests_math_background.py
    python scripts/tests_figures.py
    python scripts/tests_performance_figure.py
    python scripts/tests_beginner.py
    node scripts/tests_beginner_lab.cjs
    python scripts/check_site_quality.py
    python -m http.server 8000 --bind 127.0.0.1 --directory docs

Open http://127.0.0.1:8000/ica/ in a browser. Local full-book search needs HTTP;
opening index.html with a file:// URL can block the index fetch.

## What the checks establish

- Strict build: valid KaTeX, known references, ID uniqueness, available figures,
  source-language count balance and generated chapter examples.
- Example runner: every explicitly marked Python block parses and executes;
  chapters run in separate processes, and blocks within a chapter run in order.
  Printed output blocks are excluded. --only slug1,slug2 limits the runner.
- Numerical regressions: known identities, counterexamples, synthetic separation,
  variance calculations, degenerate inputs and explicit convergence failure.
- Website regressions: missing local resources and fragments are errors, as are
  duplicate page IDs. The search index must point to real bilingual sections;
  downloadable examples must agree with their chapter sources.
- Browser review: language persistence, search, navigation, code/solution controls,
  desktop and mobile geometry, images and formula/error indicators.

Successful execution is not a proof of every theorem or a test of every possible
data distribution. Scientific assumptions, proof logic, translation equivalence,
quoted numerical output and bibliographic attribution still need review whenever
content changes. Monte Carlo outputs can vary in their final digits across BLAS
implementations; convergence failures must not be silently discarded.

The publishing workflow rebuilds the textbook and runs these checks before
uploading docs/. A successful local build does not itself publish the website.

## 维护说明

只修改 book/src 中的教材源码；网页、下载脚本和搜索索引均由构建生成。
每个 pre.code 块必须标 data-code="python"（可运行）或 data-code="output"
（示例输出）。同章代码按顺序共享变量，不同章节相互隔离。

新增公式应通过严格 KaTeX 检查，新增定理须明确假设并给出证明或可靠出处。
代码修改后应同时检查展示的输出，不能仅以“程序没有报错”替代数值核验。
概率定理、有限样本保证、总体结果、数值收敛与科学解释需要分别陈述。

## Figure reproduction

The figures use seeded synthetic data and the same /T whitening convention as
the text. To regenerate a chapter, run:

    python book/figures/make_figures.py fastica

Omit the chapter argument to regenerate all figures. Figure generation additionally
requires the pinned Matplotlib dependency in requirements-figures.txt. The
model-order and performance plots explicitly report convergence or selection
failures; inspect those diagnostics before changing a caption or interpreting an
error bar. Regenerating a figure is separate from building the HTML pages.

## Beginner guide

The unnumbered start-here.html is generated from book/src/_start-here.html.
The chapter-guide and chapter-recap additions must not renumber existing sections,
formal results or exercises. The guide and chapter introductions are searchable.
The four-point experiment is an exact finite probability model, not an estimator.
The JavaScript tests check its moments, inverse rotation, allowed ambiguities and
explicit zero-covariance dependence counterexample. Static text remains usable
when JavaScript is unavailable.

#!/usr/bin/env node
// Build the bilingual ICA book.
//
//   book/book.json         parts, chapters, titles, summaries, KaTeX macros
//   book/src/_index.html   body of the book's front page
//   book/src/<slug>.html   one chapter body per file (see book/AUTHORING.md)
//   -> docs/ica/index.html and docs/ica/<slug>.html, docs/sitemap.xml
//
// Math is pre-rendered with KaTeX (book/vendor/katex.mjs), so the published
// pages need no JavaScript to show formulas; docs/assets/katex holds the CSS
// and fonts. Requires Node 18+ and nothing else.
//
// Usage:
//   node book/build.mjs                    build everything into docs/ica
//   node book/build.mjs --only a,b         build only these chapters
//   node book/build.mjs --out DIR          write pages to DIR instead
//   node book/build.mjs --check            build to a temp dir, report only
//   node book/build.mjs --strict           exit 1 on any warning

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import katex from './vendor/katex.mjs';

const BOOK = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(BOOK, '..');
const DOCS = path.join(REPO, 'docs');

const args = parseArgs(process.argv.slice(2));
const OUT = args.check
  ? fs.mkdtempSync(path.join(os.tmpdir(), 'ica-book-check-'))
  : path.resolve(args.out || path.join(DOCS, 'ica'));
const ONLY = args.only ? new Set(args.only.split(',').map((s) => s.trim()).filter(Boolean)) : null;

const M = JSON.parse(fs.readFileSync(path.join(BOOK, 'book.json'), 'utf8'));
const warnings = [];
const warn = (where, msg) => warnings.push(`${where}: ${msg}`);

// ---------------------------------------------------------------- chapters
const chapters = [];
{
  let n = 0;
  let a = 0;
  M.parts.forEach((part, pi) => {
    part.chapters.forEach((c) => {
      const num = part.appendix ? String.fromCharCode(65 + a++) : String(++n);
      chapters.push({
        ...c,
        num,
        appendix: !!part.appendix,
        part,
        partIndex: pi,
        file: `${c.slug}.html`,
        src: path.join(BOOK, 'src', `${c.slug}.html`),
      });
    });
  });
}
const GUIDE = {slug: 'start-here', file: 'start-here.html', title: {en: 'Start here: a beginner guide to ICA', zh: '从这里开始：ICA 新手指南'}};
const guideSource = fs.readFileSync(path.join(BOOK, 'src', '_start-here.html'), 'utf8');
const bySlug = Object.fromEntries(chapters.map((c) => [c.slug, c]));
if (ONLY) {
  if (!ONLY.size) throw new Error('empty chapter selection');
  for (const slug of ONLY) if (!bySlug[slug]) throw new Error('unknown chapter slug: ' + slug);
}
const chapterLabel = (c) =>
  c.appendix ? { en: `Appendix ${c.num}`, zh: `附录 ${c.num}` } : { en: `Chapter ${c.num}`, zh: `第 ${c.num} 章` };

const KINDS = {
  definition: ['Definition', '定义'],
  theorem: ['Theorem', '定理'],
  lemma: ['Lemma', '引理'],
  proposition: ['Proposition', '命题'],
  corollary: ['Corollary', '推论'],
  example: ['Example', '例'],
  remark: ['Remark', '注'],
  algorithm: ['Algorithm', '算法'],
  assumption: ['Assumption', '假设'],
  fact: ['Fact', '事实'],
};

// --------------------------------------------------------------- helpers
function parseArgs(a) {
  const o = {};
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--only' || a[i] === '--out') {
      const key = a[i].slice(2);
      if (!a[i + 1] || a[i + 1].startsWith('--')) throw new Error('missing value for ' + a[i]);
      o[key] = a[++i];
    }
    else if (a[i] === '--check') o.check = true;
    else if (a[i] === '--strict') o.strict = true;
    else if (a[i] === '--no-sitemap') o.noSitemap = true;
    else throw new Error(`unknown argument ${a[i]}`);
  }
  return o;
}
function attrs(s) {
  const o = {};
  for (const m of (s || '').matchAll(/([\w-]+)="([^"]*)"/g)) o[m[1]] = m[2];
  return o;
}
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const decode = (s) =>
  s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp;/g, ' ').replace(/&quot;/g, '"').replace(/&amp;/g, '&');
const bi = (en, zh, cls = '') =>
  `<span lang="en"${cls ? ` class="${cls}"` : ''}>${en}</span><span lang="zh-CN"${cls ? ` class="${cls}"` : ''}>${zh}</span>`;
const stripTags = (s) => s.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

// Part heading: 'Part I · Foundations'; just 'Appendix' when label and title coincide.
const partName = (part, l) => (part.label[l] === part.title[l] ? part.label[l] : `${part.label[l]} · ${part.title[l]}`);

// ------------------------------------------------- pass 1: collect labels
// Every numbered thing is found by the same regexes, in document order, in
// both passes, so numbers agree between a page and references to it.
const RE = {
  h2: /<h2((?:\s+[\w-]+="[^"]*")*)\s*>([\s\S]*?)<\/h2>/g,
  env: /<div\s+class="env"((?:\s+[\w-]+="[^"]*")*)\s*>/g,
  eq: /<div\s+class="eq"((?:\s+[\w-]+="[^"]*")*)\s*>([\s\S]*?)<\/div>/g,
  fig: /<figure((?:\s+[\w-]+="[^"]*")*)\s*>([\s\S]*?)<\/figure>/g,
  ex: /<div\s+class="exercise"((?:\s+[\w-]+="[^"]*")*)\s*>/g,
};

const labels = {}; // id -> {slug, file, kind, num, en, zh}
const sources = {};
const allIds = {};

for (const c of chapters) {
  const L = chapterLabel(c);
  labels[c.slug] = { slug: c.slug, file: c.file, kind: 'chapter', num: c.num, en: L.en, zh: L.zh };
  if (!fs.existsSync(c.src)) continue;
  const raw = fs.readFileSync(c.src, 'utf8');
  sources[c.slug] = raw;
  const text = raw.replace(/<!--[\s\S]*?-->/g, '').replace(/<pre\b[\s\S]*?<\/pre>/g, '');
  for (const m of text.matchAll(/\sid="([^"]+)"/g)) {
    (allIds[m[1]] ||= []).push(c.slug);
  }
  let k = 0;
  for (const m of text.matchAll(RE.h2)) {
    const a = attrs(m[1]);
    k++;
    if (!a.id) { warn(c.slug, `<h2> without id: ${stripTags(m[2]).slice(0, 60)}`); continue; }
    labels[a.id] = { slug: c.slug, file: c.file, kind: 'section', num: `${c.num}.${k}`, en: `Section ${c.num}.${k}`, zh: `第 ${c.num}.${k} 节` };
  }
  k = 0;
  for (const m of text.matchAll(RE.env)) {
    const a = attrs(m[1]);
    k++;
    const kind = KINDS[a['data-kind']];
    if (!kind) { warn(c.slug, `env with unknown data-kind="${a['data-kind']}"`); continue; }
    if (a.id) labels[a.id] = { slug: c.slug, file: c.file, kind: 'env', num: `${c.num}.${k}`, en: `${kind[0]} ${c.num}.${k}`, zh: `${kind[1]} ${c.num}.${k}` };
  }
  k = 0;
  for (const m of text.matchAll(RE.eq)) {
    const a = attrs(m[1]);
    if (!a.id) continue;
    k++;
    labels[a.id] = { slug: c.slug, file: c.file, kind: 'eq', num: `${c.num}.${k}`, en: `(${c.num}.${k})`, zh: `(${c.num}.${k})` };
  }
  let kf = 0;
  let kt = 0;
  for (const m of text.matchAll(RE.fig)) {
    const a = attrs(m[1]);
    const isTable = /\btable\b/.test(a.class || '');
    const num = isTable ? `${c.num}.${++kt}` : `${c.num}.${++kf}`;
    if (a.id) labels[a.id] = isTable
      ? { slug: c.slug, file: c.file, kind: 'table', num, en: `Table ${num}`, zh: `表 ${num}` }
      : { slug: c.slug, file: c.file, kind: 'figure', num, en: `Figure ${num}`, zh: `图 ${num}` };
  }
  k = 0;
  for (const m of text.matchAll(RE.ex)) {
    const a = attrs(m[1]);
    k++;
    if (a.id) labels[a.id] = { slug: c.slug, file: c.file, kind: 'exercise', num: `${c.num}.${k}`, en: `Exercise ${c.num}.${k}`, zh: `习题 ${c.num}.${k}` };
  }
}
for (const [id, where] of Object.entries(allIds)) {
  if (where.length > 1) warn(where.join(','), `duplicate id "${id}"`);
}

// ------------------------------------------------------------- math
function renderMath(tex, display, where) {
  try {
    return katex.renderToString(decode(tex).trim(), {
      displayMode: display,
      macros: { ...M.macros },
      throwOnError: true,
      strict: 'ignore',
      trust: false,
      output: 'htmlAndMathml',
    });
  } catch (e) {
    warn(where, `KaTeX: ${e.message.split('\n')[0]}  in  ${display ? '$$' : '$'}${tex.trim().slice(0, 80)}`);
    return `<code class="math-error" title="${esc(e.message)}">${esc(tex)}</code>`;
  }
}

// --------------------------------------------- pass 2: render a chapter
function renderChapter(c) {
  const where = c.slug;
  const store = [];
  const keep = (html) => `\u0000${store.push(html) - 1}\u0000`;
  const restore = (s) => s.replace(/\u0000(\d+)\u0000/g, (_, i) => restore(store[+i]));

  let t = sources[c.slug];
  t = t.replace(/<!--[\s\S]*?-->/g, '');
  t = t.replace(/<pre\b[\s\S]*?<\/pre>/g, (m) => keep(m));
  t = t.replace(/\\\$/g, () => keep('$'));

  // numbered and unnumbered display equations
  let k = 0;
  t = t.replace(RE.eq, (m, a, body) => {
    const at = attrs(a);
    const mm = body.match(/^\s*\$\$([\s\S]*?)\$\$\s*$/);
    if (!mm) { warn(where, `div.eq must contain exactly one $$...$$ block`); return m; }
    let tex = mm[1];
    let idAttr = '';
    if (at.id) {
      k++;
      tex = `${tex}\\tag{${c.num}.${k}}`;
      idAttr = ` id="${at.id}"`;
    }
    return `<div class="eq"${idAttr}>${keep(renderMath(tex, true, where))}</div>`;
  });
  t = t.replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => `<div class="eq">${keep(renderMath(tex, true, where))}</div>`);
  t = t.replace(/\$([^$]+?)\$/g, (m, tex) => keep(renderMath(tex, false, where)));
  if (/\$/.test(t.replace(/\u0000\d+\u0000/g, ''))) warn(where, 'unmatched $ left in text (escape a literal dollar as \\$)');

  // sections
  const sections = [];
  k = 0;
  t = t.replace(RE.h2, (m, a, inner) => {
    const at = attrs(a);
    k++;
    const num = `${c.num}.${k}`;
    const id = at.id || `sec-${c.slug}-${k}`;
    sections.push({ id, num, inner });
    return `<h2 id="${id}"><a class="secno" href="#${id}">${num}</a> ${inner}</h2>`;
  });

  // theorem-like environments
  k = 0;
  t = t.replace(RE.env, (m, a) => {
    const at = attrs(a);
    k++;
    const kindName = at['data-kind'];
    const kind = KINDS[kindName] || ['Note', '注'];
    const id = at.id || `${kindName}-${c.slug}-${k}`;
    const nameEn = at['data-en'] ? ` (${at['data-en']})` : '';
    const nameZh = at['data-zh'] ? `（${at['data-zh']}）` : '';
    const head = `<p class="env-head">${bi(`<b>${kind[0]} ${c.num}.${k}</b>${nameEn}`, `<b>${kind[1]} ${c.num}.${k}</b>${nameZh}`)}</p>`;
    return `<div class="env env-${kindName}" id="${id}">${head}`;
  });

  t = t.replace(/<div\s+class="proof"((?:\s+[\w-]+="[^"]*")*)\s*>/g, (m, a) => {
    const at = attrs(a);
    const label = at['data-en'] ? bi(`Proof (${at['data-en']}).`, `证明（${at['data-zh'] || at['data-en']}）`) : bi('Proof.', '证明');
    return `<div class="proof"${at.id ? ` id="${at.id}"` : ''}><p class="proof-head">${label}</p>`;
  });

  // exercises and solutions
  k = 0;
  t = t.replace(RE.ex, (m, a) => {
    const at = attrs(a);
    k++;
    const id = at.id || `ex-${c.slug}-${k}`;
    const lvl = at['data-level'];
    const LV = { basic: ['basic', '基础'], intermediate: ['intermediate', '进阶'], advanced: ['advanced', '硬核'] }[lvl];
    const tag = LV ? ` <span class="ex-level ex-${lvl}">${bi(LV[0], LV[1])}</span>` : '';
    return `<div class="exercise" id="${id}"><p class="ex-head">${bi(`<b>Exercise ${c.num}.${k}</b>`, `<b>习题 ${c.num}.${k}</b>`)}${tag}</p>`;
  });
  t = t.replace(/<details\s+class="solution"((?:\s+[\w-]+="[^"]*")*)\s*>(\s*<summary)?/g, (m, a, hasSummary) =>
    hasSummary ? m : `<details class="solution"><summary>${bi('Show solution', '查看解答')}</summary>`);

  // figures and tables
  let kf = 0;
  let kt = 0;
  t = t.replace(RE.fig, (m, a, inner) => {
    const at = attrs(a);
    const isTable = /\btable\b/.test(at.class || '');
    const num = isTable ? `${c.num}.${++kt}` : `${c.num}.${++kf}`;
    const [en, zh] = isTable ? [`Table ${num}.`, `表 ${num}`] : [`Figure ${num}.`, `图 ${num}`];
    let done = { en: false, zh: false };
    const body = inner.replace(/<figcaption>([\s\S]*?)<\/figcaption>/, (fm, cap) => {
      const cap2 = cap
        .replace(/<span lang="en">/, () => { done.en = true; return `<span lang="en"><b>${en}</b> `; })
        .replace(/<span lang="zh-CN">/, () => { done.zh = true; return `<span lang="zh-CN"><b>${zh}</b> `; });
      return `<figcaption>${cap2}</figcaption>`;
    });
    if (!done.en || !done.zh) warn(where, `figure ${num}: figcaption needs <span lang="en"> and <span lang="zh-CN">`);
    for (const s of inner.matchAll(/<img\b[^>]*\bsrc="([^"]+)"/g)) {
      if (!/^https?:/.test(s[1]) && !fs.existsSync(path.join(DOCS, 'ica', s[1]))) warn(where, `missing image docs/ica/${s[1]}`);
    }
    const cls = at.class ? ` class="${at.class}"` : '';
    const id = at.id ? ` id="${at.id}"` : '';
    // Keep authored dimensions/alt text; diagrams below the reading position
    // need not compete with the first screen for bandwidth or decoding.
    const lazyBody = body.replace(/<img\b([^>]*?)(\/?)>/g, (tag, attributes, slash) => {
      const loading = /\bloading=/.test(attributes) ? '' : ' loading="lazy"';
      const decoding = /\bdecoding=/.test(attributes) ? '' : ' decoding="async"';
      return `<img${attributes}${loading}${decoding}${slash}>`;
    });
    return `<figure${cls}${id}>${lazyBody}</figure>`;
  });

  // cross-references
  t = t.replace(/<a\s+class="ref"\s+data-ref="([^"]+)"\s*>([\s\S]*?)<\/a>/g, (m, id, inner) => {
    const L = labels[id];
    if (!L) { warn(where, `unresolved reference "${id}"`); return `<span class="ref-missing" title="${esc(id)}">[?]</span>`; }
    const href = L.kind === 'chapter' ? L.file : `${L.slug === c.slug ? '' : L.file}#${id}`;
    const text = inner.trim() ? inner : L.kind === 'eq' ? L.en : bi(L.en, L.zh);
    return `<a class="ref" href="${href}">${text}</a>`;
  });

  // language balance (a rough guard against a missing translation)
  const nEn = (sources[c.slug].match(/\slang="en"/g) || []).length;
  const nZh = (sources[c.slug].match(/\slang="zh-CN"/g) || []).length;
  if (nEn !== nZh) warn(where, `lang="en" blocks (${nEn}) and lang="zh-CN" blocks (${nZh}) differ`);

  return { body: restore(t), sections: sections.map((s) => ({ ...s, inner: restore(s.inner) })) };
}

// ------------------------------------------------------------- templates
const cssPath = path.join(DOCS, 'assets', 'book.css');
const cssVer = fs.existsSync(cssPath)
  ? crypto.createHash('md5').update(fs.readFileSync(cssPath)).digest('hex').slice(0, 8)
  : 'dev';

const HEAD_SCRIPT = `<script>(function(){var v=null;try{v=localStorage.getItem('ica-book-lang')}catch(e){}if(v!=='en'&&v!=='zh'&&v!=='both'){v=/^zh/i.test(navigator.language||'')?'zh':'en'}var d=document.documentElement;d.setAttribute('data-lang',v);if(v==='zh')d.setAttribute('lang','zh-CN')})();</script>`;

const jsPath = path.join(DOCS, 'assets', 'book.js');
const jsVer = fs.existsSync(jsPath) ? crypto.createHash('md5').update(fs.readFileSync(jsPath)).digest('hex').slice(0, 8) : 'dev';
const BODY_SCRIPT = `<script src="../assets/book.js?v=${jsVer}" defer></script>`;

function head({ title, description, canonical }) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(description)}">
  <meta name="author" content="${esc(M.author)}">
  <link rel="canonical" href="${canonical}">
  <meta property="og:type" content="book">
  <meta property="og:url" content="${canonical}">
  <meta property="og:site_name" content="Yuda Bi">
  <meta property="og:title" content="${esc(title)}">
  <meta property="og:description" content="${esc(description)}">
  <meta property="og:image" content="${M.siteUrl}/assets/og-card.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../assets/katex/katex.min.css">
  <link rel="stylesheet" href="../assets/book.css?v=${cssVer}">
  ${HEAD_SCRIPT}
</head>`;
}

function bar() {
  return `<header class="bar">
  <div class="bar-inner">
    <button class="nav-toggle" type="button" aria-controls="book-nav" aria-expanded="false">${bi('Contents', '目录')}</button>
    <a class="bar-title" href="index.html">${bi(M.short.en, M.short.zh)}</a>
    <a class="bar-home" href="../">Yuda Bi</a>
    <button class="book-search-toggle" type="button" hidden aria-haspopup="dialog">${bi('Search', '搜索')}</button>
    <div class="lang-switch" role="group" aria-label="Language / 语言">
      <button type="button" data-set-lang="en" aria-pressed="false">EN</button><button type="button" data-set-lang="zh" aria-pressed="false">中文</button><button type="button" data-set-lang="both" aria-pressed="false">EN + 中文</button>
    </div>
  </div>
</header>`;
}

function sidebar(current, sections) {
  let h = `<nav class="book-nav" id="book-nav" aria-label="Contents / 目录">
  <a class="nav-top${current ? '' : ' is-current'}" href="index.html">${bi('Contents', '目录')}</a>`;
  h += '\n  <a class="nav-start' + (current?.slug === GUIDE.slug ? ' is-current' : '') + '" href="start-here.html">' + bi('Start here', '新手指南') + '</a>';
  h += '\n  <a class="nav-glossary" href="start-here.html#guide-glossary">' + bi('Glossary & symbols', '术语与符号速查') + '</a>';
  if (current?.slug === GUIDE.slug) {
    h += '<ol class="nav-sections beginner-sections">';
    for (const section of sections) h += '<li><a href="#' + section.id + '">' + section.inner + '</a></li>';
    h += '</ol>';
  }
  for (const part of M.parts) {
    h += `\n  <p class="nav-part">${bi(partName(part, 'en'), partName(part, 'zh'))}</p>\n  <ol class="nav-chapters">`;
    for (const pc of part.chapters) {
      const c = bySlug[pc.slug];
      const cur = current && current.slug === c.slug;
      const missing = !sources[c.slug];
      h += `\n    <li${cur ? ' class="is-current"' : ''}><a href="${c.file}"${cur ? ' aria-current="page"' : ''}${missing ? ' class="is-draft"' : ''}><span class="nav-num">${c.num}</span><span class="nav-title">${bi(c.title.en, c.title.zh)}</span></a>`;
      if (cur && sections.length) {
        h += `\n      <ol class="nav-sections">`;
        for (const s of sections) h += `\n        <li><a href="#${s.id}"><span class="nav-num">${s.num}</span><span class="nav-title">${s.inner}</span></a></li>`;
        h += `\n      </ol>`;
      }
      h += `</li>`;
    }
    h += `\n  </ol>`;
  }
  return h + `\n</nav>`;
}

function foot() {
  return `<footer class="book-foot">
  <p>&copy; ${M.year} ${esc(M.author)} &middot; <a href="../">${bi('Homepage', '主页')}</a> &middot; <a href="index.html">${bi('Contents', '目录')}</a></p>
  <p class="foot-note">${bi('Formulas typeset with KaTeX.', '公式由 KaTeX 排版。')}</p>
  <dialog class="book-search" id="book-search" aria-labelledby="search-title">
    <form method="dialog"><button class="search-close" aria-label="Close search / 关闭搜索">×</button></form>
    <h2 id="search-title">${bi('Search this book', '搜索全书')}</h2>
    <label for="book-search-input">${bi('Keyword, phrase or chapter title', '关键词、短语或章节标题')}</label>
    <input id="book-search-input" type="search" autocomplete="off" placeholder="FastICA / 白化 / identifiability">
    <p id="book-search-status" role="status" aria-live="polite"></p>
    <ol id="book-search-results"></ol>
  </dialog>
</footer>`;
}

function pager(prev, next) {
  const link = (c, dir) => {
    if (!c) return `<span class="pager-${dir} is-empty"></span>`;
    const L = chapterLabel(c);
    const arrow = dir === 'prev' ? '&larr; ' : '';
    const arrowR = dir === 'next' ? ' &rarr;' : '';
    return `<a class="pager-${dir}" href="${c.file}" rel="${dir}"><span class="pager-kicker">${arrow}${bi(L.en, L.zh)}${arrowR}</span><span class="pager-title">${bi(c.title.en, c.title.zh)}</span></a>`;
  };
  return `<nav class="pager" aria-label="Chapters">${link(prev, 'prev')}${link(next, 'next')}</nav>`;
}

function chapterPage(c, idx) {
  const { body, sections } = renderChapter(c);
  const L = chapterLabel(c);
  const prev = chapters[idx - 1];
  const next = chapters[idx + 1];
  const kickerEn = c.appendix ? L.en : `${c.part.label.en} · ${L.en}`;
  const kickerZh = c.appendix ? L.zh : `${c.part.label.zh} · ${L.zh}`;
  return `${head({
    title: `${L.en}. ${c.title.en} | ${M.short.en}`,
    description: c.summary.en,
    canonical: `${M.siteUrl}/ica/${c.file}`,
  })}
<body class="book">
<a class="skip" href="#content">${bi('Skip to content', '跳到正文')}</a>
${bar()}
<div class="layout">
${sidebar(c, sections)}
<main class="content" id="content">
<article class="chapter">
<header class="chapter-head">
  <p class="chapter-kicker">${bi(kickerEn, kickerZh)}</p>
  <h1>${bi(c.title.en, c.title.zh)}</h1>
  <p class="chapter-summary" lang="en">${c.summary.en}</p>
  <p class="chapter-summary" lang="zh-CN">${c.summary.zh}</p>
</header>
<div class="chapter-tools">
  <a href="#${sections[0]?.id || 'content'}"><span lang="en">Go to chapter text</span><span lang="zh-CN">直接读正文</span></a>
  <a href="start-here.html#guide-glossary"><span lang="en">Glossary &amp; symbols</span><span lang="zh-CN">术语与符号</span></a>
  <a href="code/${c.slug}.py" download>${bi('Download chapter Python', '下载本章 Python')}</a>
  <button type="button" class="solutions-toggle" hidden>${bi('Expand all solutions', '展开全部解答')}</button>
</div>
${body}
</article>
${pager(prev, next)}
</main>
</div>
${foot()}
${BODY_SCRIPT}
</body>
</html>
`;
}

// Math and cross-references only (no numbering) for the front page.
function renderFragment(src, where) {
  const store = [];
  const keep = (html) => `\u0000${store.push(html) - 1}\u0000`;
  const restore = (s) => s.replace(/\u0000(\d+)\u0000/g, (_, i) => restore(store[+i]));
  let t = src.replace(/<!--[\s\S]*?-->/g, '');
  t = t.replace(/<pre\b[\s\S]*?<\/pre>/g, (m) => keep(m));
  t = t.replace(/\\\$/g, () => keep('$'));
  t = t.replace(RE.eq, (_, attributes, body) => {
    const a = attrs(attributes);
    const tex = body.trim().replace(/^\$\$|\$\$$/g, '');
    return `<div class="eq"${a.id ? ' id="' + esc(a.id) + '"' : ''}>${keep(renderMath(tex, true, where))}</div>`;
  });
  t = t.replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => `<div class="eq">${keep(renderMath(tex, true, where))}</div>`);
  t = t.replace(/\$([^$]+?)\$/g, (m, tex) => keep(renderMath(tex, false, where)));
  t = t.replace(/<a\s+class="ref"\s+data-ref="([^"]+)"\s*>([\s\S]*?)<\/a>/g, (m, id, inner) => {
    const L = labels[id];
    if (!L) { warn(where, `unresolved reference "${id}"`); return `<span class="ref-missing">[?]</span>`; }
    const href = L.kind === 'chapter' ? L.file : `${L.file}#${id}`;
    return `<a class="ref" href="${href}">${inner.trim() ? inner : L.kind === 'eq' ? L.en : bi(L.en, L.zh)}</a>`;
  });
  if (/\$/.test(t.replace(/\u0000\d+\u0000/g, ''))) warn(where, 'unmatched $ left in front page');
  if ((src.match(/ lang="en"/g) || []).length !== (src.match(/ lang="zh-CN"/g) || []).length) warn(where, 'front-page translations are unbalanced');
  return restore(t);
}

function beginnerPage() {
  const body = renderFragment(guideSource, 'start-here');
  const sections = [...guideSource.matchAll(/<h2 id="([^"]+)"[^>]*>([\s\S]*?)<\/h2>/g)].map(m => ({id:m[1],inner:m[2]}));
  const ids = [...guideSource.matchAll(/\sid="([^"]+)"/g)].map(m=>m[1]);
  if (new Set(ids).size !== ids.length) warn('start-here', 'duplicate guide IDs');
  const labPath = path.join(DOCS, 'assets', 'book-lab.js');
  const labVer = crypto.createHash('md5').update(fs.readFileSync(labPath)).digest('hex').slice(0,8);
  return `${head({title: GUIDE.title.en + ' | ' + M.short.en, description: 'Learn ICA with a worked mixing example, a visual experiment, a glossary and a guided reading route.', canonical: M.siteUrl + '/ica/' + GUIDE.file})}
<body class="book book-beginner">
<a class="skip" href="#content">${bi('Skip to content','跳到正文')}</a>
${bar()}
<div class="layout">
${sidebar(GUIDE,sections)}
<main class="content" id="content"><article class="chapter">
<header class="chapter-head"><p class="chapter-kicker">${bi('A gentle starting point','先懂直觉，再读推导')}</p>
<h1>${bi(GUIDE.title.en,GUIDE.title.zh)}</h1>
<p lang="en" class="chapter-summary">One small calculation, one visual experiment, and a route into the full textbook.</p>
<p lang="zh-CN" class="chapter-summary">从一次小计算、一个可视化实验，走进完整教材。</p></header>
<div class="chapter-tools"><a href="#guide-paths">${bi('Reading route','学习路线')}</a><a href="#guide-notation">${bi('Symbols','符号速查')}</a><a href="#guide-glossary">${bi('Glossary','术语速查')}</a><button type="button" class="solutions-toggle" hidden>${bi('Expand all solutions','展开全部解答')}</button></div>
${body}
</article></main></div>
${foot()}
${BODY_SCRIPT}
<script src="../assets/book-lab.js?v=${labVer}" defer></script>
</body></html>`;
}

function indexPage() {
  const introSrc = path.join(BOOK, 'src', '_index.html');
  const intro = fs.existsSync(introSrc) ? renderFragment(fs.readFileSync(introSrc, 'utf8'), 'index') : '';
  let toc = '';
  for (const part of M.parts) {
    toc += `\n<section class="toc-part">\n  <h2>${bi(partName(part, 'en'), partName(part, 'zh'))}</h2>\n  <ol class="toc-chapters">`;
    for (const pc of part.chapters) {
      const c = bySlug[pc.slug];
      const L = chapterLabel(c);
      toc += `\n    <li><a href="${c.file}"><span class="toc-label">${bi(L.en, L.zh)}</span><span class="toc-title">${bi(c.title.en, c.title.zh)}</span></a>
      <p lang="en">${c.summary.en}</p>
      <p lang="zh-CN">${c.summary.zh}</p></li>`;
    }
    toc += `\n  </ol>\n</section>`;
  }
  return `${head({ title: `${M.title.en} | ${M.short.en}`, description: M.description.en, canonical: `${M.siteUrl}/ica/` })}
<body class="book book-home">
<a class="skip" href="#content">${bi('Skip to content', '跳到正文')}</a>
${bar()}
<div class="layout">
${sidebar(null, [])}
<main class="content" id="content">
<header class="cover">
  <p class="cover-kicker">${bi('An open book · bilingual', '开放教材 · 中英双语')}</p>
  <h1>${bi(M.title.en, M.title.zh)}</h1>
  <p class="cover-author">${esc(M.author)}</p>
  <p class="cover-desc" lang="en">${M.description.en}</p>
  <p class="cover-desc" lang="zh-CN">${M.description.zh}</p>
  <p class="cover-actions"><a class="btn" href="start-here.html">${bi('Start with the beginner guide', '从新手指南开始')} &rarr;</a></p>
</header>
${intro}
<h2 class="toc-heading" id="contents">${bi('Contents', '目录')}</h2>
${toc}
</main>
</div>
${foot()}
${BODY_SCRIPT}
</body>
</html>
`;
}

// Search data and downloadable examples are derived from the same chapter sources.
function plainSource(text) {
  return decode(text.replace(/\$\$[\s\S]*?\$\$|\$[^$]+\$/g, (math) => math.replace(/</g, '&lt;').replace(/>/g, '&gt;')).replace(/<pre\b[\s\S]*?<\/pre>/g, ' ').replace(/<a\s+class="ref"[^>]*>[\s\S]*?<\/a>/g, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ')).trim();
}
function searchIndex() {
  const entries = [];
  for (const c of [...chapters, GUIDE]) {
    const src = c.slug === GUIDE.slug ? guideSource : sources[c.slug];
    if (!src) continue;
    const guide = src.match(/<aside class="chapter-guide"[^>]*>[\s\S]*?<\/aside>/);
    if (guide) entries.push({url:c.file+'#guide-'+c.slug,en:c.title.en,zh:c.title.zh,sectionEn:'First-pass guide',sectionZh:'入门导读',text:plainSource(guide[0])});
    for (const match of src.matchAll(/<h2\s+id="([^"]+)"[^>]*>([\s\S]*?)<\/h2>([\s\S]*?)(?=<h2\b|$)/g)) {
      const heading = (lang) => plainSource(match[2].match(new RegExp('<span lang="' + lang + '">([\\s\\S]*?)</span>'))?.[1] || '');
      entries.push({url:c.file+'#'+match[1],en:c.title.en,zh:c.title.zh,sectionEn:heading('en'),sectionZh:heading('zh-CN'),text:plainSource(match[3])});
    }
  }
  return entries;
}
function writeExamples(c) {
  const snippets = [...sources[c.slug].matchAll(/<pre\b[^>]*data-code="python"[^>]*>\s*<code>([\s\S]*?)<\/code>\s*<\/pre>/g)].map((m) => decode(m[1]));
  if (!snippets.length) { warn(c.slug, 'no marked Python examples'); return; }
  const dir = path.join(OUT, 'code');
  fs.mkdirSync(dir, {recursive: true});
  fs.writeFileSync(path.join(dir, c.slug + '.py'), '# ' + c.title.en + '\n# Generated from book/src/' + c.slug + '.html; edit the chapter source.\n# Requires Python 3, NumPy and SciPy. Run the blocks in this order.\n\n' + snippets.join('\n\n# Next example (shares the chapter namespace).\n\n') + '\n');
}

// ------------------------------------------------------------------ main
fs.mkdirSync(OUT, { recursive: true });
let built = 0;
chapters.forEach((c, i) => {
  if (ONLY && !ONLY.has(c.slug)) return;
  if (!sources[c.slug]) { warn(c.slug, 'no source file yet (book/src/' + c.slug + '.html)'); return; }
  writeExamples(c);
  fs.writeFileSync(path.join(OUT, c.file), chapterPage(c, i));
  built++;
});
if (!ONLY) {
  fs.writeFileSync(path.join(OUT, 'index.html'), indexPage());
  fs.writeFileSync(path.join(OUT, GUIDE.file), beginnerPage());
  fs.mkdirSync(path.join(OUT, 'code'), {recursive:true});
  fs.copyFileSync(path.join(BOOK, 'requirements-examples.txt'), path.join(OUT, 'code', 'requirements.txt'));
  fs.writeFileSync(path.join(OUT, 'search-index.json'), JSON.stringify(searchIndex()));
}

if (ONLY && !args.check) {
  const indexPath = path.join(OUT, 'search-index.json');
  if (fs.existsSync(indexPath)) {
    const selectedFiles = new Set([...ONLY].map((slug) => bySlug[slug].file));
    const previous = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    const entries = previous.filter((item) => !selectedFiles.has(item.url.split('#')[0]));
    entries.push(...searchIndex().filter((item) => selectedFiles.has(item.url.split('#')[0])));
    fs.writeFileSync(indexPath, JSON.stringify(entries));
  } else {
    fs.writeFileSync(indexPath, JSON.stringify(searchIndex().filter((item) => ONLY.has(item.url.split('.html')[0]))));
  }
}

if (!ONLY && !args.check && !args.out && !args.noSitemap) {
  const today = new Date().toISOString().slice(0, 10);
  const urls = [`${M.siteUrl}/`, `${M.siteUrl}/ica/`, `${M.siteUrl}/ica/${GUIDE.file}`, ...chapters.filter((c) => sources[c.slug]).map((c) => `${M.siteUrl}/ica/${c.file}`)];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((u) => `  <url>\n    <loc>${u}</loc>\n    <lastmod>${today}</lastmod>\n  </url>`)
    .join('\n')}\n</urlset>\n`;
  fs.writeFileSync(path.join(DOCS, 'sitemap.xml'), xml);
}

console.log(`Built ${built} chapter(s)${ONLY ? '' : ' plus the contents and beginner guide'} into ${OUT}`);
if (warnings.length) {
  console.log(`\n${warnings.length} warning(s):`);
  for (const w of warnings) console.log('  - ' + w);
  if (args.strict) process.exit(1);
} else {
  console.log('No warnings.');
}

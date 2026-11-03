// Executes the shipped reader script against a small DOM fixture; no npm dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'docs/assets/book.js'), 'utf8');
let checks = 0;

class Element {
  constructor(tag, attrs = {}, parent = null) {
    this.tagName = tag.toUpperCase(); this.attributes = new Map(Object.entries(attrs));
    this.parentElement = parent; this.children = []; this.listeners = new Map(); this.dataset = {};
    if (parent) parent.children.push(this);
    const classes = new Set();
    this.classList = {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)};
  }
  get lang() { return this.getAttribute('lang') || ''; }
  set lang(v) { this.setAttribute('lang', v); }
  getAttribute(k) { return this.attributes.has(k) ? this.attributes.get(k) : null; }
  setAttribute(k, v) { this.attributes.set(k, String(v)); }
  removeAttribute(k) { this.attributes.delete(k); }
  addEventListener(type, callback) { const list = this.listeners.get(type) || []; list.push(callback); this.listeners.set(type, list); }
  click() { for (const callback of this.listeners.get('click') || []) callback({target: this}); }
  descendants() { return this.children.flatMap(child => [child, ...child.descendants()]); }
  querySelectorAll(selector) {
    assert.equal(selector, '[lang="en"], [lang="zh-CN"]');
    return this.descendants().filter(node => ['en', 'zh-CN'].includes(node.getAttribute('lang')));
  }
  querySelector(selector) {
    const match = /^\[lang="(en|zh-CN)"\]$/.exec(selector);
    assert.ok(match, 'Unexpected element query: ' + selector);
    return this.descendants().find(node => node.getAttribute('lang') === match[1]) || null;
  }
  scrollIntoView(options) { this.scrollCalls = this.scrollCalls || []; this.scrollCalls.push(options); }
  closest(selector) {
    if (selector === 'details') {for (let n = this; n; n = n.parentElement) if (n.tagName === 'DETAILS') return n; return null;}
    const match = /^(body )?\[lang="(en|zh-CN)"\]$/.exec(selector);
    assert.ok(match, 'Unsupported closest selector: ' + selector);
    for (let node = this; node; node = node.parentElement) {
      if (node.getAttribute('lang') !== match[2]) continue;
      if (!match[1]) return node;
      for (let ancestor = node.parentElement; ancestor; ancestor = ancestor.parentElement) if (ancestor.tagName === 'BODY') return node;
    }
    return null;
  }
}

function harness(initial, source = script) {
  const html = new Element('html', {lang: initial === 'zh' ? 'zh-CN' : 'en', 'data-lang': initial});
  const body = new Element('body', {}, html), article = new Element('article', {}, body);
  const en = new Element('p', {lang: 'en'}, article), zh = new Element('p', {lang: 'zh-CN'}, article);
  const sameEn = new Element('span', {lang: 'en'}, en), sameZh = new Element('span', {lang: 'zh-CN'}, zh);
  const crossZh = new Element('span', {lang: 'zh-CN'}, en), crossEn = new Element('span', {lang: 'en'}, zh);
  const deepEn = new Element('span', {lang: 'en'}, crossZh);
  const authoredTrue = new Element('span', {lang: 'en', 'aria-hidden': 'true'}, article);
  const authoredFalse = new Element('span', {lang: 'zh-CN', 'aria-hidden': 'false'}, article);
  const katex = new Element('span', {class: 'katex-html', 'aria-hidden': 'true'}, en);
  const buttons = ['en', 'zh', 'both'].map(mode => {const b = new Element('button', {}, body); b.dataset.setLang = mode; return b;});
  const saved = new Map(), windowEvents = new Map(); let readyCalls = 0;
  const solutions = [new Element('details', {}, article), new Element('details', {}, article)];
  solutions[0].open = false; solutions[1].open = true;
  const solutionToggle = new Element('button', {}, article);
  const solutionEn = new Element('span', {lang: 'en'}, solutionToggle);
  const solutionZh = new Element('span', {lang: 'zh-CN'}, solutionToggle);
  const fragment = new Element('span', {id: 'exercise-answer'}, solutions[0]);
  const location = {hash: ''}, frames = [];
  function verify(mode) {
    for (const n of [en, sameEn, solutionEn]) assert.equal(n.getAttribute('aria-hidden'), mode === 'zh' ? 'true' : null, 'English visibility must ignore html language');
    for (const n of [zh, sameZh, solutionZh]) assert.equal(n.getAttribute('aria-hidden'), mode === 'en' ? 'true' : null, 'Chinese visibility must ignore html language');
    for (const n of [crossZh, crossEn, deepEn]) assert.equal(n.getAttribute('aria-hidden'), 'true', 'Opposite-language nesting remains hidden');
    assert.equal(authoredTrue.getAttribute('aria-hidden'), 'true', 'Restore authored true');
    assert.equal(authoredFalse.getAttribute('aria-hidden'), mode === 'en' ? 'true' : 'false', 'Restore authored false');
    assert.equal(katex.getAttribute('aria-hidden'), 'true', 'Keep visual KaTeX markup hidden');
  }
  const add = html.classList.add;
  html.classList.add = name => {if (name === 'book-render-ready') {verify(html.getAttribute('data-lang')); readyCalls++;} add(name);};
  const document = {
    documentElement: html, body,
    querySelectorAll(selector) {
      if (selector === '.lang-switch button') return buttons;
      if (selector === 'details.solution') return solutions;
      if (['pre.code[data-code="python"]', '.code-copy'].includes(selector)) return [];
      throw new Error('Unexpected document query: ' + selector);
    },
    querySelector(selector) {assert.ok(['.nav-toggle', '.solutions-toggle', '.book-search-toggle'].includes(selector), selector); return selector === '.solutions-toggle' ? solutionToggle : null;},
    getElementById(id) {return id === 'exercise-answer' ? fragment : null;}
  };
  const context = {document, location, requestAnimationFrame(callback) {frames.push(callback);}, window: {addEventListener(type, callback) {windowEvents.set(type, callback);}}, localStorage: {setItem(k, v) {saved.set(k, v);}}, console};
  assert.equal(html.classList.contains('book-render-ready'), false, 'No-JS state uses ordinary rendering');
  vm.runInNewContext(source, context, {filename: 'book.js'});
  assert.equal(readyCalls, 1, 'Initial accessibility synchronization precedes enhancement');
  assert.equal(html.classList.contains('book-render-ready'), true); verify(initial);
  for (const mode of ['en', 'zh', 'both', 'zh', 'en', 'both']) {
    buttons.find(b => b.dataset.setLang === mode).click(); verify(mode);
    assert.equal(html.getAttribute('data-lang'), mode);
    assert.equal(html.lang, mode === 'zh' ? 'zh-CN' : 'en');
    assert.equal(saved.get('ica-book-lang'), mode);
    buttons.forEach(b => assert.equal(b.getAttribute('aria-pressed'), String(b.dataset.setLang === mode)));
  }
  assert.equal(readyCalls, 7, 'Every switch synchronizes accessibility');
  const labelsBefore = solutionToggle.children.slice();
  solutionToggle.click();
  assert.deepEqual(solutions.map(s => s.open), [true, true]);
  assert.equal(solutionEn.textContent, 'Collapse all solutions');
  assert.equal(solutionToggle.getAttribute('aria-expanded'), 'true');
  buttons.find(b => b.dataset.setLang === 'zh').click(); verify('zh');
  solutionToggle.click();
  assert.deepEqual(solutions.map(s => s.open), [false, false]);
  assert.equal(solutionEn.textContent, 'Expand all solutions');
  assert.equal(solutionToggle.getAttribute('aria-expanded'), 'false');
  assert.deepEqual(solutionToggle.children, labelsBefore, 'Solution labels must remain the cached accessible nodes');
  solutions[1].open = true;
  windowEvents.get('beforeprint')();
  assert.deepEqual(solutions.map(s => s.open), [true, true], 'Printing reveals every answer');
  windowEvents.get('afterprint')();
  assert.deepEqual(solutions.map(s => s.open), [false, true], 'Printing restores previous answer choices');
  location.hash = '#exercise-answer'; windowEvents.get('hashchange')();
  assert.equal(solutions[0].open, true, 'A deep fragment reveals its answer before scrolling');
  assert.equal(frames.length, 1); frames.shift()();
  assert.equal(fragment.scrollCalls.length, 1);
  assert.equal(frames.length, 1); frames.shift()();
  assert.equal(fragment.scrollCalls.length, 2, 'Fragment alignment settles over two frames');
  fragment.scrollCalls.forEach(call => {assert.equal(call.block, 'start'); assert.equal(call.behavior, 'instant');});
  windowEvents.get('hashchange')(); location.hash = '#different-target'; frames.shift()();
  assert.equal(fragment.scrollCalls.length, 2, 'Stale scheduled fragments must not move the reader');
  location.hash = '#%'; assert.doesNotThrow(() => windowEvents.get('hashchange')());
}
for (const initial of ['en', 'zh', 'both']) {harness(initial); checks++;}
// The fixture must catch the actual root-language ancestry bug.
const regression = script.replace(/body \[lang=/g, '[lang=');
assert.notEqual(regression, script);
assert.throws(() => harness('en', regression), /Chinese visibility must ignore html language/);
checks++;


// Verify that progressive containment cannot become active in print or no-JS mode.
const css = fs.readFileSync(path.join(root, 'docs/assets/book.css'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
let autoRules = 0;
function inspectCss(text, parents = []) {
  let start = 0;
  while (true) {
    const open = text.indexOf('{', start); if (open < 0) break;
    const selector = text.slice(start, open).trim();
    let end = open + 1, depth = 1;
    while (end < text.length && depth) {if (text[end] === '{') depth++; if (text[end] === '}') depth--; end++;}
    assert.equal(depth, 0, 'Balanced CSS block');
    const body = text.slice(open + 1, end - 1);
    if (selector.startsWith('@')) inspectCss(body, [...parents, selector]);
    else if (/content-visibility\s*:\s*auto(?:;|$)/.test(body)) {
      autoRules++;
      assert.ok(parents.includes('@media screen'), 'Containment must not apply to print');
      assert.ok(parents.some(p => p.startsWith('@supports')), 'Unsupported browsers retain ordinary rendering');
      assert.ok(selector.startsWith('.book-render-ready .chapter >'), 'No-JS and non-chapter content retain ordinary rendering');
    }
    start = end;
  }
}
inspectCss(css); assert.ok(autoRules > 0); checks++;

function attrs(tag) {const a = {}; for (const m of tag.matchAll(/([\w-]+)\s*=\s*"([^"]*)"/g)) a[m[1]] = m[2]; return a;}
let figures = 0;
for (const file of fs.readdirSync(path.join(root, 'book/src')).filter(f => f.endsWith('.html') && !f.startsWith('_'))) {
  const source = fs.readFileSync(path.join(root, 'book/src', file), 'utf8');
  const generated = fs.readFileSync(path.join(root, 'docs/ica', file), 'utf8');
  assert.ok(!/<html[^>]*class="[^"]*book-render-ready/.test(generated), 'No-JS HTML keeps normal rendering');
  const before = [...source.matchAll(/<img\b[^>]*>/g)].map(m => attrs(m[0]));
  const after = [...generated.matchAll(/<img\b[^>]*>/g)].map(m => attrs(m[0]));
  assert.equal(after.length, before.length, file + ': retain every image');
  for (let i = 0; i < before.length; i++) {
    for (const key of ['src', 'alt', 'width', 'height']) assert.equal(after[i][key], before[i][key], file + ': preserve ' + key);
    assert.ok(Number(after[i].width) > 0 && Number(after[i].height) > 0, file + ': reserve valid dimensions');
    assert.equal(after[i].loading, before[i].loading || 'lazy', file + ': lazy loading');
    assert.equal(after[i].decoding, before[i].decoding || 'async', file + ': async decoding');
    figures++;
  }
}
assert.ok(figures > 0); checks++;
console.log('PASS ' + checks + ' rendering checks: en/zh/both and switches, nested-language regression, original ARIA, pre-enable synchronization, print restoration, fragment settling, CSS fallback, no-JS markup, and ' + figures + ' generated images.');

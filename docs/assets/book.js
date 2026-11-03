/* Progressive enhancements for the static ICA textbook. */
(function () {
  'use strict';
  var d = document.documentElement;
  var langButtons = document.querySelectorAll('.lang-switch button');
  function language() { return d.getAttribute('data-lang') || 'en'; }
  function label(en, zh) { return language() === 'zh' ? zh : language() === 'both' ? en + ' / ' + zh : en; }
  // Offscreen auto-rendered blocks stay in the accessibility tree. Mirror
  // the language CSS explicitly, without overwriting KaTeX's aria-hidden.
  var languageNodes = Array.from(document.body.querySelectorAll('[lang="en"], [lang="zh-CN"]')).map(function (node) {
    var lang = node.getAttribute('lang');
    return { node: node, lang: lang, originalHidden: node.getAttribute('aria-hidden'),
      nestedOpposite: !!node.parentElement.closest(lang === 'en' ? 'body [lang="zh-CN"]' : 'body [lang="en"]') };
  });
  function markLanguage() {
    languageNodes.forEach(function (item) {
      var hidden = item.nestedOpposite || (language() === 'en' && item.lang === 'zh-CN') || (language() === 'zh' && item.lang === 'en');
      if (hidden) item.node.setAttribute('aria-hidden', 'true');
      else if (item.originalHidden === null) item.node.removeAttribute('aria-hidden');
      else item.node.setAttribute('aria-hidden', item.originalHidden);
    });
    // Without JavaScript the complete static chapter uses ordinary rendering.
    d.classList.add('book-render-ready');
    langButtons.forEach(function (button) { button.setAttribute('aria-pressed', String(button.dataset.setLang === language())); });
    document.querySelectorAll('.code-copy').forEach(function (button) { button.textContent = label('Copy code', '复制代码'); });
    if (searchDialog && searchDialog.open) renderSearch();
  }
  langButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var lang = button.dataset.setLang;
      d.setAttribute('data-lang', lang); d.lang = lang === 'zh' ? 'zh-CN' : 'en';
      try { localStorage.setItem('ica-book-lang', lang); } catch (_) {}
      markLanguage();
    });
  });
  var navToggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('book-nav');
  function closeNav(restoreFocus) {
    document.body.classList.remove('nav-open');
    if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
    if (restoreFocus && navToggle) navToggle.focus();
  }
  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = !document.body.classList.contains('nav-open');
      document.body.classList.toggle('nav-open', open);
      navToggle.setAttribute('aria-expanded', String(open));
      if (open) nav.querySelector('a').focus();
    });
    nav.addEventListener('click', function (event) { if (event.target.closest('a')) closeNav(false); });
    document.addEventListener('click', function (event) {
      if (document.body.classList.contains('nav-open') && !nav.contains(event.target) && !navToggle.contains(event.target)) closeNav(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && document.body.classList.contains('nav-open')) closeNav(true);
    });
  }
  var solutions = Array.from(document.querySelectorAll('details.solution'));
  var solutionToggle = document.querySelector('.solutions-toggle');
  if (solutionToggle && solutions.length) {
    solutionToggle.hidden = false;
    function updateSolutions() {
      var allOpen = solutions.every(function (item) { return item.open; });
      solutionToggle.querySelector('[lang="en"]').textContent = allOpen ? 'Collapse all solutions' : 'Expand all solutions';
      solutionToggle.querySelector('[lang="zh-CN"]').textContent = allOpen ? '收起全部解答' : '展开全部解答';
      solutionToggle.setAttribute('aria-expanded', String(allOpen));
    }
    solutionToggle.addEventListener('click', function () {
      var open = !solutions.every(function (item) { return item.open; });
      solutions.forEach(function (item) { item.open = open; }); updateSolutions();
    });
    solutions.forEach(function (item) { item.addEventListener('toggle', updateSolutions); });
    updateSolutions();
  }
  // Reveal an exercise solution if a cross-reference points inside its closed details.
  function revealFragment() {
    var id; try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    var target = id && document.getElementById(id);
    function stillCurrent() { try { return decodeURIComponent(location.hash.slice(1)) === id; } catch (_) { return false; } }
    if (target) {
      var details = target.closest('details'); if (details) details.open = true;
      // Native fragment scrolling can precede the layout of nearby auto blocks.
      // Settle that layout before aligning the target under the sticky header.
      requestAnimationFrame(function () {
        if (!stillCurrent()) return;
        target.scrollIntoView({ block: 'start', behavior: 'instant' });
        requestAnimationFrame(function () {
          if (document.getElementById(id) === target && stillCurrent()) target.scrollIntoView({ block: 'start', behavior: 'instant' });
        });
      });
    }
  }
  window.addEventListener('hashchange', revealFragment); revealFragment();
  // Copy only runnable examples; a blocked clipboard leaves selectable source intact.
  document.querySelectorAll('pre.code[data-code="python"]').forEach(function (pre) {
    var button = document.createElement('button'); button.type = 'button'; button.className = 'code-copy';
    button.textContent = label('Copy code', '复制代码'); pre.before(button);
    button.addEventListener('click', async function () {
      try {
        await navigator.clipboard.writeText(pre.querySelector('code').textContent);
        button.textContent = label('Copied', '已复制');
      } catch (_) {
        var range = document.createRange(); range.selectNodeContents(pre.querySelector('code'));
        var selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
        button.textContent = label('Selected — press Ctrl/Cmd+C', '已选中，请按 Ctrl/Cmd+C');
      }
    });
  });
  var searchDialog = document.getElementById('book-search');
  var searchToggle = document.querySelector('.book-search-toggle');
  var searchInput = document.getElementById('book-search-input');
  var searchResults = document.getElementById('book-search-results');
  var searchStatus = document.getElementById('book-search-status');
  var index = null, loading = null, timer;
  function normalize(value) { return value.normalize('NFKC').toLocaleLowerCase(); }
  function renderSearch() {
    if (!index) return;
    var query = normalize(searchInput.value.trim());
    searchResults.replaceChildren();
    if (query.length < 2) { searchStatus.textContent = label('Enter at least two characters. Esc closes search.', '请输入至少两个字符。按 Esc 关闭搜索。'); return; }
    var terms = query.split(/\s+/).filter(Boolean);
    var matches = index.map(function (entry) {
      var heading = normalize(entry.en + ' ' + entry.zh + ' ' + entry.sectionEn + ' ' + entry.sectionZh);
      var full = normalize(heading + ' ' + entry.text);
      return { entry: entry, score: terms.every(function (term) { return full.includes(term); }) ? terms.reduce(function (score, term) { return score + (heading.includes(term) ? 10 : 1); }, 0) : 0 };
    }).filter(function (item) { return item.score; }).sort(function (a, b) { return b.score - a.score; });
    searchStatus.textContent = matches.length ? label(matches.length + ' matching sections; showing up to 30.', '找到 ' + matches.length + ' 个小节，最多显示 30 个。') : label('No matches. Try another term or its translation.', '没有结果。请尝试其他关键词或其英文译名。');
    matches.slice(0, 30).forEach(function (item) {
      var entry = item.entry, li = document.createElement('li'), a = document.createElement('a');
      a.href = entry.url; a.textContent = label(entry.en + ' — ' + entry.sectionEn, entry.zh + ' — ' + entry.sectionZh);
      var p = document.createElement('p'), text = entry.text;
      var at = normalize(text).indexOf(terms[0]), start = Math.max(0, at - 50);
      p.textContent = (start ? '…' : '') + text.slice(start, start + 220) + (text.length > start + 220 ? '…' : '');
      li.append(a, p); searchResults.append(li);
    });
  }
  async function openSearch() {
    closeNav(false); searchDialog.showModal(); searchInput.focus();
    if (index) { renderSearch(); return; }
    searchStatus.textContent = label('Loading the local book index…', '正在载入本书索引……');
    try {
      if (!loading) loading = fetch('search-index.json').then(function (response) { if (!response.ok) throw new Error('index unavailable'); return response.json(); });
      index = await loading; renderSearch();
    } catch (_) {
      loading = null;
      searchStatus.textContent = label('Search could not load. Use the contents, or open the book through a local HTTP server instead of file://.', '搜索索引未能载入。可先使用目录；若直接打开了本地文件，请通过本地 HTTP 服务器访问。');
    }
  }
  if (searchDialog && searchToggle && typeof searchDialog.showModal === 'function') {
    searchToggle.hidden = false; searchToggle.addEventListener('click', openSearch);
    searchDialog.addEventListener('keydown', function (event) { if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); searchDialog.close(); } });
    searchInput.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(renderSearch, 120); });
    searchResults.addEventListener('click', function (event) { if (event.target.closest('a')) searchDialog.close(); });
    document.addEventListener('keydown', function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); if (!searchDialog.open) openSearch(); }
    });
  }
  // Printed copies include solutions, then restore the reader's previous choices.
  var beforePrint = null;
  window.addEventListener('beforeprint', function () { beforePrint = solutions.map(function (item) { return item.open; }); solutions.forEach(function (item) { item.open = true; }); });
  window.addEventListener('afterprint', function () { if (beforePrint) solutions.forEach(function (item, i) { item.open = beforePrint[i]; }); beforePrint = null; });
  markLanguage();
})();

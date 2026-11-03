/* Counts one homepage opening, then reads aggregate statistics from this origin.
   No cookies, persistent browser identifiers, or third-party requests. */
(function () {
  'use strict';
  var root = document.getElementById('visitor-stats');
  if (!root || root.dataset.initialized === 'true') return;
  root.dataset.initialized = 'true';

  var count = document.getElementById('visitor-stats-count');
  var since = document.getElementById('visitor-stats-since');
  var status = document.getElementById('visitor-stats-status');
  var empty = document.getElementById('visitor-stats-empty');
  var list = document.getElementById('visitor-region-list');
  var more = document.getElementById('visitor-stats-more');
  var moreList = document.getElementById('visitor-region-more');
  var other = document.getElementById('visitor-stats-other');
  var refresh = document.getElementById('visitor-stats-refresh');
  if (!count || !since || !status || !empty || !list || !more || !moreList || !refresh) return;

  var started = false;
  var busy = false;
  var lastData = null;
  var countries;
  try { countries = new Intl.DisplayNames(['zh-Hans', 'en'], { type: 'region' }); } catch (_) { countries = null; }
  var countryFallback = { CN: '中国', US: '美国', GB: '英国', CA: '加拿大', AU: '澳大利亚', JP: '日本', KR: '韩国', SG: '新加坡', DE: '德国', FR: '法国', HK: '中国香港', MO: '中国澳门', TW: '中国台湾' };
  var chineseRegions = {
    'beijing':'北京','tianjin':'天津','hebei':'河北','shanxi':'山西','inner mongolia':'内蒙古','nei mongol':'内蒙古',
    'liaoning':'辽宁','jilin':'吉林','heilongjiang':'黑龙江','shanghai':'上海','jiangsu':'江苏','zhejiang':'浙江',
    'anhui':'安徽','fujian':'福建','jiangxi':'江西','shandong':'山东','henan':'河南','hubei':'湖北','hunan':'湖南',
    'guangdong':'广东','guangxi':'广西','hainan':'海南','chongqing':'重庆','sichuan':'四川','guizhou':'贵州',
    'yunnan':'云南','tibet':'西藏','xizang':'西藏','shaanxi':'陕西','gansu':'甘肃','qinghai':'青海','ningxia':'宁夏','xinjiang':'新疆',
    'hong kong':'香港','macau':'澳门','macao':'澳门','taiwan':'台湾'
  };
  var usRegions = {
    'alabama':'阿拉巴马','alaska':'阿拉斯加','arizona':'亚利桑那','arkansas':'阿肯色','california':'加利福尼亚','colorado':'科罗拉多',
    'connecticut':'康涅狄格','delaware':'特拉华','district of columbia':'哥伦比亚特区','florida':'佛罗里达','georgia':'佐治亚',
    'hawaii':'夏威夷','idaho':'爱达荷','illinois':'伊利诺伊','indiana':'印第安纳','iowa':'艾奥瓦','kansas':'堪萨斯','kentucky':'肯塔基',
    'louisiana':'路易斯安那','maine':'缅因','maryland':'马里兰','massachusetts':'马萨诸塞','michigan':'密歇根','minnesota':'明尼苏达',
    'mississippi':'密西西比','missouri':'密苏里','montana':'蒙大拿','nebraska':'内布拉斯加','nevada':'内华达','new hampshire':'新罕布什尔',
    'new jersey':'新泽西','new mexico':'新墨西哥','new york':'纽约','north carolina':'北卡罗来纳','north dakota':'北达科他','ohio':'俄亥俄',
    'oklahoma':'俄克拉何马','oregon':'俄勒冈','pennsylvania':'宾夕法尼亚','rhode island':'罗得岛','south carolina':'南卡罗来纳',
    'south dakota':'南达科他','tennessee':'田纳西','texas':'得克萨斯','utah':'犹他','vermont':'佛蒙特','virginia':'弗吉尼亚',
    'washington':'华盛顿','west virginia':'西弗吉尼亚','wisconsin':'威斯康星','wyoming':'怀俄明'
  };

  function formatNumber(value) { return value.toLocaleString('en-US'); }
  function validCount(value) { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0; }
  function validDate(value) { return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value) && Number.isFinite(Date.parse(value)); }
  function cleanData(data) {
    if (!data || data.ok !== true || !validCount(data.totalViews) || !Array.isArray(data.regions) || !validDate(data.updatedAt)) throw new Error('Invalid statistics');
    if (data.since !== null && !validDate(data.since)) throw new Error('Invalid start date');
    var rows = data.regions.map(function (row) {
      if (!row || !validCount(row.views) || row.views > data.totalViews || typeof row.country !== 'string' || !/^[A-Za-z]{2}$/.test(row.country) || typeof row.region !== 'string' || row.region.length > 120) throw new Error('Invalid region totals');
      return { country: row.country.toUpperCase(), region: row.region.trim(), views: row.views };
    }).filter(function (row) { return row.views > 0; });
    rows.sort(function (a, b) { return b.views - a.views; });
    var knownViews = rows.reduce(function (sum, row) { return sum + row.views; }, 0);
    if (knownViews > data.totalViews) throw new Error('Inconsistent region totals');
    if (data.otherViews !== undefined && (!validCount(data.otherViews) || knownViews + data.otherViews !== data.totalViews)) throw new Error('Inconsistent other-region totals');
    return { totalViews: data.totalViews, regions: rows, otherViews: data.otherViews || 0, since: data.since, updatedAt: data.updatedAt };
  }
  function regionName(row) {
    var country = row.country === 'ZZ' || row.country === 'XX' ? '未识别地区' : countryFallback[row.country];
    if (!country) {
      try { country = countries ? countries.of(row.country) : row.country; } catch (_) { country = row.country; }
    }
    var region = row.region;
    var normalized = region.toLowerCase().replace(/\s+(province|autonomous region|zhuang autonomous region|hui autonomous region|uyghur autonomous region)$/i, '').trim();
    if (row.country === 'CN') region = chineseRegions[normalized] || region;
    if (row.country === 'US') region = usRegions[normalized] || region;
    return country + (region && region !== country ? ' · ' + region : '');
  }
  function regionRow(row, total) {
    var item = document.createElement('li');
    var bar = document.createElement('span');
    var label = document.createElement('span');
    var value = document.createElement('span');
    var share = document.createElement('small');
    var percentage = total ? row.views / total * 100 : 0;
    bar.className = 'visitor-region-bar';
    bar.style.width = Math.min(100, percentage).toFixed(2) + '%';
    bar.setAttribute('aria-hidden', 'true');
    label.className = 'visitor-region-name';
    label.lang = 'zh-CN';
    label.textContent = regionName(row);
    value.className = 'visitor-region-value';
    value.textContent = formatNumber(row.views);
    share.textContent = '(' + percentage.toFixed(percentage < 10 ? 1 : 0) + '%)';
    value.appendChild(share);
    item.appendChild(bar); item.appendChild(label); item.appendChild(value);
    return item;
  }
  function render(data, readOnly) {
    lastData = data;
    count.textContent = formatNumber(data.totalViews);
    if (data.since) {
      var date = new Date(data.since);
      since.textContent = 'Since ' + date.toLocaleDateString('en-US', {year:'numeric', month:'short', day:'numeric'}) + ' · 自 ' + date.toLocaleDateString('zh-CN');
    } else {
      since.textContent = 'Counting starts with the first visit · 首次访问后开始累计';
    }
    list.replaceChildren(); moreList.replaceChildren();
    data.regions.forEach(function (row, index) { (index < 5 ? list : moreList).appendChild(regionRow(row, data.totalViews)); });
    list.hidden = !data.regions.length;
    more.hidden = data.regions.length <= 5;
    if (other) { other.hidden = !data.otherViews; other.textContent = data.otherViews ? 'Other regions · 其他地区：' + formatNumber(data.otherViews) : ''; }
    empty.hidden = data.regions.length > 0;
    if (!data.regions.length) empty.textContent = data.totalViews === 0 ? 'No visits recorded yet · 暂无访问记录' : 'Region breakdown is not available yet · 地区汇总暂不可用';
    root.dataset.state = 'ready';
    status.textContent = readOnly ? 'Latest available totals · 最新统计' : 'Updated · 已更新';
    status.title = new Date(data.updatedAt).toLocaleString();
  }
  function unavailable() {
    root.dataset.state = 'unavailable';
    if (lastData) {
      status.textContent = 'Refresh unavailable · 刷新失败，保留上次统计';
    } else {
      count.textContent = '—';
      status.textContent = 'Statistics unavailable · 统计暂不可用';
      empty.textContent = 'Please try again later · 请稍后刷新统计';
      empty.hidden = false; list.hidden = true; more.hidden = true;
    }
  }
  async function request(method) {
    var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer;
    var options = { method:method, credentials:'omit', mode:'same-origin', cache:'no-store', referrerPolicy:'strict-origin', headers:{'Accept':'application/json'} };
    if (method === 'POST') { options.headers['Content-Type'] = 'application/json'; options.body = JSON.stringify({page:'/'}); }
    if (controller) options.signal = controller.signal;
    var timeout = new Promise(function (_, reject) { timer = setTimeout(function () { if (controller) controller.abort(); reject(new Error('Statistics timeout')); }, 5000); });
    try {
      var operation = (async function () {
        var response = await fetch('/api/site-stats' + (method === 'POST' ? '/visit' : ''), options);
        if (!response.ok) throw new Error('Statistics unavailable');
        return cleanData(await response.json());
      })();
      return await Promise.race([operation, timeout]);
    } finally { clearTimeout(timer); }
  }
  async function update(recordVisit) {
    if (busy) return;
    busy = true; root.setAttribute('aria-busy','true'); refresh.disabled = true;
    try {
      if (typeof fetch !== 'function') throw new Error('Fetch unavailable');
      var data;
      var readOnly = !recordVisit;
      if (recordVisit) {
        // Never retry a POST: a timed-out request may already have been counted.
        try { data = await request('POST'); } catch (_) { readOnly = true; data = await request('GET'); }
      } else { data = await request('GET'); }
      render(data, readOnly);
    } catch (_) { unavailable(); }
    finally { busy = false; root.setAttribute('aria-busy','false'); refresh.hidden = false; refresh.disabled = false; }
  }
  refresh.addEventListener('click', function () { update(false); });
  function start() {
    if (started || document.visibilityState !== 'visible' || document.prerendering) return;
    started = true;
    document.removeEventListener('visibilitychange', start);
    document.removeEventListener('prerenderingchange', start);
    update(true);
  }
  function schedule() {
    document.addEventListener('visibilitychange', start);
    document.addEventListener('prerenderingchange', start);
    if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(start, {timeout:2000});
    else setTimeout(start, 200);
  }
  if (document.readyState === 'complete') schedule();
  else window.addEventListener('load', schedule, {once:true});
})();

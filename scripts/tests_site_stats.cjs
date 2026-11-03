/* Frontend behavior checks: no real network calls or visit records. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../docs/assets/visitor-stats.js'), 'utf8');

class Element {
  constructor() { this.dataset = {}; this.style = {}; this.attributes = {}; this.listeners = {}; this.children = []; this._text = ''; this.hidden = false; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set innerHTML(_) { throw new Error('Statistics must not use HTML insertion'); }
  setAttribute(key, value) { this.attributes[key] = value; }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  addEventListener(type, listener) { (this.listeners[type] ||= []).push(listener); }
  removeEventListener(type, listener) { this.listeners[type] = (this.listeners[type] || []).filter(item => item !== listener); }
  dispatch(type) { for (const listener of [...(this.listeners[type] || [])]) listener(); }
}
const payload = (overrides = {}) => ({
  ok: true, since: '2026-11-03T06:00:00.000Z', totalViews: 120, updatedAt: '2026-11-03T06:05:00.000Z',
  regions: [{country:'US', region:'Georgia', views:80}, {country:'CN',region:'Guangdong',views:40}], ...overrides
});
const reply = data => ({ok:true, json:async () => data});
async function drain() { for (let i = 0; i < 8; i++) await new Promise(resolve => setImmediate(resolve)); }
function harness(responses, visibility = 'visible') {
  const ids = ['visitor-stats','visitor-stats-count','visitor-stats-since','visitor-stats-status','visitor-stats-empty','visitor-region-list','visitor-stats-more','visitor-region-more','visitor-stats-other','visitor-stats-refresh'];
  const nodes = Object.fromEntries(ids.map(id => [id,new Element()]));
  nodes['visitor-stats-count'].textContent = '—';
  const document = new Element();
  Object.assign(document, {readyState:'complete', visibilityState:visibility, getElementById:id => nodes[id], createElement:() => new Element()});
  const idle = [];
  const calls = [];
  const window = new Element();
  window.requestIdleCallback = callback => idle.push(callback);
  const context = vm.createContext({document,window,Intl,Date,Number,Promise,AbortController,setTimeout,clearTimeout,fetch:async (url,options) => {
    calls.push({url,options});
    const response = responses.shift();
    if (response instanceof Error) throw response;
    if (!response) throw new Error('Unplanned request');
    return response;
  }});
  vm.runInContext(source,context);
  return {nodes,document,calls,context,async start(){idle.forEach(fn => fn());await drain();},async refresh(){nodes['visitor-stats-refresh'].dispatch('click');await drain();}};
}

test('one same-origin POST renders real counts and readable regions',async () => {
  const h=harness([reply(payload())]); await h.start();
  assert.equal(h.calls.length,1); assert.equal(h.calls[0].url,'/api/site-stats/visit');
  assert.equal(h.calls[0].options.method,'POST'); assert.equal(h.calls[0].options.credentials,'omit');
  assert.equal(h.calls[0].options.mode,'same-origin'); assert.equal(h.calls[0].options.cache,'no-store');
  assert.deepEqual(JSON.parse(h.calls[0].options.body),{page:'/'});
  assert.equal(h.nodes['visitor-stats-count'].textContent,'120');
  assert.match(h.nodes['visitor-region-list'].textContent,/美国 · 佐治亚/);
  assert.match(h.nodes['visitor-region-list'].textContent,/中国 · 广东/);
  assert.equal(h.nodes['visitor-stats'].attributes['aria-busy'],'false');
});
test('POST failure falls back to GET; refresh never records another visit',async () => {
  const h=harness([new Error('network'),reply(payload()),reply(payload({totalViews:121}))]); await h.start();await h.refresh();
  assert.deepEqual(h.calls.map(call=>call.options.method),['POST','GET','GET']);
  assert.equal(h.nodes['visitor-stats-count'].textContent,'121');
});
test('service failure is visible and never masquerades as zero visits',async () => {
  const h=harness([{ok:false},{ok:false}]);await h.start();
  assert.equal(h.nodes['visitor-stats-count'].textContent,'—');
  assert.match(h.nodes['visitor-stats-status'].textContent,/统计暂不可用/);
  assert.equal(h.nodes['visitor-stats-refresh'].disabled,false);
  assert.equal(h.nodes['visitor-stats-refresh'].hidden,false);
});
test('hidden documents wait; repeated visibility changes and script inclusion do not double count',async () => {
  const h=harness([reply(payload())],'hidden');await h.start();assert.equal(h.calls.length,0);
  h.document.visibilityState='visible';h.document.dispatch('visibilitychange');await drain();
  h.document.dispatch('visibilitychange');vm.runInContext(source,h.context);await drain();
  assert.equal(h.calls.length,1);
});
test('a real empty dataset shows zero and more than five regions remain accessible',async () => {
  const h=harness([reply(payload({totalViews:0,regions:[]})),reply(payload({totalViews:6,regions:['US','CN','GB','AU','JP','SG'].map(country=>({country,region:'',views:1}))}))]);
  await h.start();assert.equal(h.nodes['visitor-stats-count'].textContent,'0');assert.match(h.nodes['visitor-stats-empty'].textContent,/暂无访问记录/);
  await h.refresh();assert.equal(h.nodes['visitor-region-list'].children.length,5);assert.equal(h.nodes['visitor-region-more'].children.length,1);assert.equal(h.nodes['visitor-stats-more'].hidden,false);
});
test('invalid counts are rejected and a failed refresh retains the last real result',async () => {
  const invalid=harness([reply(payload({totalViews:-1})),reply(payload({totalViews:'120'}))]);await invalid.start();assert.equal(invalid.nodes['visitor-stats-count'].textContent,'—');
  const h=harness([reply(payload()),reply(payload({regions:[{country:'US',region:'Georgia',views:121}]}))]);await h.start();await h.refresh();
  assert.equal(h.nodes['visitor-stats-count'].textContent,'120');assert.match(h.nodes['visitor-stats-status'].textContent,/保留上次统计/);
});
test('region strings are plain text and never inserted as HTML',async () => {
  const value='<img src=x onerror=alert(1)>';const h=harness([reply(payload({regions:[{country:'US',region:value,views:120}]}))]);await h.start();
  assert.match(h.nodes['visitor-region-list'].textContent,/<img src=x onerror=alert\(1\)>/);assert.equal(h.nodes['visitor-stats'].dataset.state,'ready');
});
test('regions omitted by the API are shown as a separate aggregate',async () => {
  const h=harness([reply(payload({totalViews:150,otherViews:30}))]);await h.start();
  assert.equal(h.nodes['visitor-stats-count'].textContent,'150');assert.equal(h.nodes['visitor-stats-other'].hidden,false);
  assert.match(h.nodes['visitor-stats-other'].textContent,/其他地区：30/);
});

import assert from 'node:assert/strict';
import test from 'node:test';
import worker, { SQL } from './worker.mjs';

const SINCE = '2026-11-03T00:00:00.000Z';
function database() {
  const state = { since: SINCE, updatedAt: SINCE, regions: new Map(), calls: [] };
  return {
    state,
    prepare(sql) { return { sql, args: [], bind(...args) { this.args = args; return this; } }; },
    async batch(statements) {
      state.calls.push(statements.map(({ sql, args }) => ({ sql, args })));
      return statements.map(({ sql, args }) => {
        let results = [];
        if (sql === SQL.touch) state.updatedAt = args[1];
        else if (sql === SQL.increment) {
          const key = JSON.stringify(args);
          const row = state.regions.get(key) || { country: args[0], region: args[1], views: 0 };
          state.regions.set(key, { ...row, views: row.views + 1 });
        } else if (sql === SQL.totals) results = [{
          since: state.since, updated_at: state.updatedAt,
          total_views: [...state.regions.values()].reduce((sum, row) => sum + row.views, 0)
        }];
        else if (sql === SQL.regions) results = [...state.regions.values()]
          .sort((a, b) => b.views - a.views || a.country.localeCompare(b.country) || a.region.localeCompare(b.region))
          .slice(0, 100);
        else throw new Error('Unexpected SQL');
        return { success: true, results };
      });
    }
  };
}
function visit({ origin = 'https://yuda-bi.com', contentType = 'application/json',
  body = JSON.stringify({ page: '/' }), cf = { country: 'CN', region: 'Beijing' }, extraHeaders = {} } = {}) {
  const headers = { 'Content-Type': contentType, ...extraHeaders };
  if (origin !== null) headers.Origin = origin;
  const request = new Request('https://yuda-bi.com/api/site-stats/visit', { method: 'POST', headers, body });
  if (cf) Object.defineProperty(request, 'cf', { value: cf });
  return request;
}

test('zero reads are initialized values and never increment', async () => {
  const DB = database();
  const response = await worker.fetch(new Request('https://yuda-bi.com/api/site-stats'), { DB });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('Cache-Control'), 'no-store');
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), null);
  assert.deepEqual(await response.json(), { ok: true, since: SINCE, totalViews: 0, regions: [], otherViews: 0, updatedAt: SINCE });
  assert.deepEqual(DB.state.calls[0].map(item => item.sql), [SQL.totals, SQL.regions]);
});

test('visits use one batch and only bind trusted coarse geography', async () => {
  const DB = database();
  const response = await worker.fetch(visit({
    cf: { country: 'CN', region: '  Bei\u0000jing  ', city: 'Never stored' },
    extraHeaders: { 'CF-Connecting-IP': '192.0.2.123', 'CF-IPCountry': 'US', 'User-Agent': 'private UA' }
  }), { DB });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.totalViews, 1);
  assert.deepEqual(result.regions, [{ country: 'CN', region: 'Beijing', views: 1 }]);
  assert.equal(DB.state.calls.length, 1);
  assert.deepEqual(DB.state.calls[0].map(item => item.sql), [SQL.touch, SQL.increment, SQL.totals, SQL.regions]);
  const bound = JSON.stringify(DB.state.calls);
  for (const value of ['192.0.2.123', 'private UA', 'Never stored']) assert.ok(!bound.includes(value));
  await worker.fetch(visit(), { DB });
  const current = await (await worker.fetch(new Request('https://yuda-bi.com/api/site-stats'), { DB })).json();
  assert.equal(current.totalViews, 2);
  assert.equal(current.regions[0].views, 2);
});

test('missing geography cannot be supplied through client headers', async () => {
  const DB = database();
  const response = await worker.fetch(visit({ cf: null, extraHeaders: { 'CF-IPCountry': 'CN' } }), { DB });
  assert.deepEqual((await response.json()).regions, [{ country: 'ZZ', region: '', views: 1 }]);
});

test('cross-origin, malformed, forged, excessive bodies never reach D1', async () => {
  const cases = [
    [visit({ origin: null }), 403],
    [visit({ origin: 'https://yuda-bi.com.evil.example' }), 403],
    [visit({ extraHeaders: { 'Sec-Fetch-Site': 'cross-site' } }), 403],
    [visit({ contentType: 'text/plain' }), 415],
    [visit({ body: '{invalid' }), 400], [visit({ body: 'null' }), 400], [visit({ body: '[]' }), 400],
    [visit({ body: JSON.stringify({ page: '/ica/' }) }), 400],
    [visit({ body: JSON.stringify({ page: '/', country: 'US', region: 'Fake' }) }), 400],
    [visit({ body: ' '.repeat(257) }), 413],
    [visit({ extraHeaders: { 'Content-Length': '1000000' } }), 413]
  ];
  for (const [request, status] of cases) {
    const DB = database();
    const response = await worker.fetch(request, { DB });
    assert.equal(response.status, status);
    assert.equal((await response.json()).ok, false);
    assert.equal(DB.state.calls.length, 0);
  }
});

test('only exact production host, endpoints, methods are served', async () => {
  const cases = [
    ['https://other.workers.dev/api/site-stats', 'GET', 404, null],
    ['https://yuda-bi.com/api/site-stats-else', 'GET', 404, null],
    ['https://yuda-bi.com/', 'GET', 404, null],
    ['https://yuda-bi.com/api/site-stats', 'POST', 405, 'GET'],
    ['https://yuda-bi.com/api/site-stats/visit', 'GET', 405, 'POST'],
    ['https://yuda-bi.com/api/site-stats/visit', 'OPTIONS', 405, 'POST']
  ];
  for (const [url, method, status, allow] of cases) {
    const DB = database();
    const response = await worker.fetch(new Request(url, { method }), { DB });
    assert.equal(response.status, status);
    assert.equal(response.headers.get('Allow'), allow);
    assert.equal(DB.state.calls.length, 0);
  }
});

test('storage failures never fabricate zero totals', async () => {
  const request = () => new Request('https://yuda-bi.com/api/site-stats');
  const cases = [undefined, {}, { DB: { prepare() {}, batch() { throw new Error('private detail'); } } }];
  const uninitialized = database();
  uninitialized.batch = async () => [{ success: true, results: [] }, { success: true, results: [] }];
  cases.push({ DB: uninitialized });
  for (const env of cases) {
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { ok: false, error: 'stats_unavailable' });
  }
});

test('result is bounded and reports omitted regional views', async () => {
  const DB = database();
  for (let i = 0; i < 105; i++) DB.state.regions.set(String(i), { country: 'US', region: `Region ${i}`, views: 1 });
  const result = await (await worker.fetch(new Request('https://yuda-bi.com/api/site-stats'), { DB })).json();
  assert.equal(result.totalViews, 105);
  assert.equal(result.regions.length, 100);
  assert.equal(result.otherViews, 5);
});

/** Anonymous homepage page-view totals. No IP addresses or visitor IDs are stored. */
const SITE_ORIGIN = 'https://yuda-bi.com';
const MAX_BODY_BYTES = 256;
const MAX_REGIONS = 100;

export const SQL = Object.freeze({
  touch: `INSERT INTO site_stats_meta (id, since, updated_at) VALUES (1, ?, ?)
    ON CONFLICT(id) DO UPDATE SET updated_at = MAX(site_stats_meta.updated_at, excluded.updated_at)`,
  increment: `INSERT INTO site_stats_regions (country, region, views) VALUES (?, ?, 1)
    ON CONFLICT(country, region) DO UPDATE SET views = site_stats_regions.views + 1`,
  totals: `SELECT since, updated_at,
    (SELECT COALESCE(SUM(views), 0) FROM site_stats_regions) AS total_views
    FROM site_stats_meta WHERE id = 1`,
  regions: `SELECT country, region, views FROM site_stats_regions
    ORDER BY views DESC, country ASC, region ASC LIMIT ${MAX_REGIONS}`
});

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Cross-Origin-Resource-Policy': 'same-origin',
      ...extraHeaders
    }
  });
}

function error(code, status, headers) {
  return json({ ok: false, error: code }, status, headers);
}

async function readSmallJson(request) {
  const declaredSize = request.headers.get('Content-Length');
  if (declaredSize !== null && (!/^\d+$/.test(declaredSize) || Number(declaredSize) > MAX_BODY_BYTES)) {
    return { error: 'body_too_large', status: 413 };
  }
  if (!request.body) return { error: 'invalid_json', status: 400 };
  const reader = request.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: false });
  let length = 0;
  let text = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > MAX_BODY_BYTES) {
        await reader.cancel();
        return { error: 'body_too_large', status: 413 };
      }
      text += decoder.decode(value, { stream: true });
    }
    text += decoder.decode();
    const body = JSON.parse(text);
    if (!body || typeof body !== 'object' || Array.isArray(body) ||
        Object.keys(body).some(key => key !== 'page') ||
        (body.page !== undefined && body.page !== '/' && body.page !== '/index.html')) {
      return { error: 'invalid_payload', status: 400 };
    }
    return { body };
  } catch {
    return { error: 'invalid_json', status: 400 };
  } finally {
    reader.releaseLock();
  }
}

function geography(request) {
  // Cloudflare supplies cf independently of user-controlled request headers/body.
  const source = request.cf || {};
  const country = typeof source.country === 'string' && /^[A-Z]{2}$/.test(source.country)
    ? source.country : 'ZZ';
  const region = country !== 'ZZ' && typeof source.region === 'string'
    ? source.region.normalize('NFC').replace(/[\u0000-\u001f\u007f]/g, '').trim().slice(0, 100)
    : '';
  return { country, region };
}

function snapshot(results) {
  if (!Array.isArray(results) || results.some(result => !result || result.success === false)) {
    throw new Error('Database batch failed');
  }
  const totals = results.at(-2)?.results?.[0];
  const regions = results.at(-1)?.results;
  if (!totals || !Array.isArray(regions) ||
      !Number.isSafeInteger(totals.total_views) || totals.total_views < 0 ||
      !Number.isFinite(Date.parse(totals.since)) || !Number.isFinite(Date.parse(totals.updated_at)) ||
      regions.some(row => !Number.isSafeInteger(row.views) || row.views < 0 ||
        typeof row.country !== 'string' || typeof row.region !== 'string')) {
    throw new Error('Database not initialized or invalid result');
  }
  const displayedViews = regions.reduce((sum, row) => sum + row.views, 0);
  if (displayedViews > totals.total_views) throw new Error('Inconsistent totals');
  return {
    ok: true,
    since: totals.since,
    totalViews: totals.total_views,
    regions,
    otherViews: totals.total_views - displayedViews,
    updatedAt: totals.updated_at
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.origin !== SITE_ORIGIN) return error('not_found', 404);
    const isRead = url.pathname === '/api/site-stats';
    const isVisit = url.pathname === '/api/site-stats/visit';
    if (!isRead && !isVisit) return error('not_found', 404);
    if ((isRead && request.method !== 'GET') || (isVisit && request.method !== 'POST')) {
      return error('method_not_allowed', 405, { Allow: isRead ? 'GET' : 'POST' });
    }
    if (isVisit) {
      if (request.headers.get('Origin') !== SITE_ORIGIN ||
          (request.headers.has('Sec-Fetch-Site') && request.headers.get('Sec-Fetch-Site') !== 'same-origin')) {
        return error('origin_not_allowed', 403);
      }
      if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get('Content-Type') || '')) {
        return error('json_required', 415);
      }
      const parsed = await readSmallJson(request);
      if (parsed.error) return error(parsed.error, parsed.status);
    }
    if (!env?.DB || typeof env.DB.prepare !== 'function' || typeof env.DB.batch !== 'function') {
      return error('stats_unavailable', 503);
    }
    try {
      const statements = [];
      if (isVisit) {
        const now = new Date().toISOString();
        const { country, region } = geography(request);
        statements.push(
          env.DB.prepare(SQL.touch).bind(now, now),
          env.DB.prepare(SQL.increment).bind(country, region)
        );
      }
      statements.push(env.DB.prepare(SQL.totals), env.DB.prepare(SQL.regions));
      // D1 batch runs transactionally: the aggregate increment and returned reads agree.
      return json(snapshot(await env.DB.batch(statements)));
    } catch {
      // Do not log requests/addresses or fabricate zero counts on storage failure.
      return error('stats_unavailable', 503);
    }
  }
};

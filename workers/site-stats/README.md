# Anonymous homepage view statistics

A dependency-free Cloudflare Worker backed by one D1 binding named `DB`.

## Counting and privacy

- One accepted `POST /api/site-stats/visit` records one homepage view. Reloads
  count again: this is page views (PV), not unique people (UV). The frontend
  sends the POST only once per opening and does not automatically retry it.
- Counts start when `schema.sql` initializes the database. Historical traffic
  is not invented. An initialized empty database returns a real zero.
- The app stores only country, province-level region, aggregate view totals,
  and global start/update timestamps. Location comes from Cloudflare
  `request.cf`, never client-submitted region data. The Worker never reads or
  stores IP addresses, city, coordinates, user agents, cookies, or visitor IDs.
- Region inference can be inaccurate and reflects VPN/proxy exit locations.
- Origin validation limits cross-site submissions but is not bot detection.
  Custom clients can forge headers, while disabled/blocked JavaScript can
  undercount. These numbers are not audited or deduplicated audience size.
- These application tables do not control Cloudflare infrastructure telemetry.

## Dashboard deployment

1. Use the existing D1 database `homepage-site-stats` in the existing account
   (ID `3dd38d17-dd23-44b5-a0e5-8cb0bef3e186`, Asia-Pacific location hint).
2. Run all of `schema.sql` in its SQL console. Re-running it preserves counts
   and the original start time.
3. Use the Worker `yuda-homepage-stats`. Replace its starter module
   with the complete contents of `worker.mjs`; no bundler is needed.
4. Add a D1 database binding named exactly `DB`, selecting that database.
5. Deploy and add only the route **`yuda-bi.com/api/site-stats*`** in the
   existing zone. Do not use a whole-site wildcard. Homepage/ICA documents
   and static assets continue on the existing hosting and caching path.
6. Exclude this API from future Cache Everything rules. The responses send
   `Cache-Control: no-store`. No DNS or existing HTML cache changes are needed.

The production origin is fixed to `https://yuda-bi.com`; `workers.dev` previews
intentionally return 404. No API key is embedded in the homepage.

`wrangler.jsonc` records the real Worker, D1 binding, database ID and narrow
production route; it contains no credentials. Future CLI deployments should
explicitly use this configuration, for example
`wrangler deploy --config workers/site-stats/wrangler.jsonc` from the repository
root after authenticating to the existing account. `workers_dev` and
`preview_urls` are disabled in this configuration; the custom-domain route is
the intended entry point. The GitHub Pages workflow validates this backend but
does not deploy the Worker or mutate D1.

## API

- `GET /api/site-stats` reads the public aggregate without recording a visit.
- `POST /api/site-stats/visit` requires Origin `https://yuda-bi.com` and
  Content-Type `application/json`. Its body is a JSON object with `page: /`
  (or `/index.html`), or an empty object. It is limited to 256 bytes. Other
  keys/pages are rejected. If Sec-Fetch-Site is present, it must be same-origin.
- Both successful methods return `ok: true`, `since` (ISO), `totalViews`
  (integer), `regions` (country/region/views), `otherViews` (integer), and
  `updatedAt` (ISO).
- Countries use ISO-2 codes or `ZZ` for unknown; unknown region is empty.
  Regions sort by views descending, then country/region; the largest 100
  rows are returned. `otherViews` counts visits outside those returned rows.
- All responses use no-store and no cross-origin access-control headers.
  Missing/misconfigured storage returns 503 and `ok: false`, never false zeros.

After a POST timeout, the frontend may fall back to GET. It must not retry
POST because the first write may already have committed. For live acceptance
testing, open the real homepage rather than repeatedly submitting synthetic
POSTs that would inflate the public count.

## Consistency and tests

Region increments use parameterized SQLite UPSERT. Metadata, increment and
returned reads execute in one transactional D1 batch. Total views are derived
from SUM of region views, eliminating a redundant counter that could drift.

From the repository root (Node 22+ and Python 3, no dependencies):

```sh
node --check workers/site-stats/worker.mjs
node --test workers/site-stats/worker.test.mjs
python workers/site-stats/test_sql.py
```

The JS tests cover endpoints, origin, payload bounds, trusted geography,
privacy and database failures. Python executes the exact SQL exported by the
Worker, verifying initialization, rollback, parameterization, and 600 writes
from concurrent connections. A live D1/route check is still required.

## Official references

- https://developers.cloudflare.com/d1/worker-api/d1-database/
- https://developers.cloudflare.com/d1/worker-api/prepared-statements/
- https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties
- https://developers.cloudflare.com/workers/configuration/routing/routes/

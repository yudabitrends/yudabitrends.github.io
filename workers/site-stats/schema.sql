-- Run once in the chosen D1 database. Re-running preserves existing counters.
CREATE TABLE IF NOT EXISTS site_stats_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  since TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS site_stats_regions (
  country TEXT NOT NULL CHECK (length(country) = 2),
  region TEXT NOT NULL,
  views INTEGER NOT NULL CHECK (views >= 0),
  PRIMARY KEY (country, region)
) WITHOUT ROWID;

INSERT OR IGNORE INTO site_stats_meta (id, since, updated_at)
VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

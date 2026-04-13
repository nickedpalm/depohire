-- Page view tracking for listing analytics
CREATE TABLE IF NOT EXISTS page_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_slug TEXT NOT NULL,
  path TEXT NOT NULL,
  referrer TEXT DEFAULT '',
  ip_hash TEXT DEFAULT '',
  user_agent TEXT DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_page_views_slug ON page_views(listing_slug);
CREATE INDEX IF NOT EXISTS idx_page_views_created ON page_views(created_at);

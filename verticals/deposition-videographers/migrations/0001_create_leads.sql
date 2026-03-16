-- D1 fallback leads table
-- Used only when the primary VPS API is unreachable
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  attorney_name TEXT NOT NULL,
  attorney_email TEXT NOT NULL,
  attorney_phone TEXT DEFAULT '',
  case_details TEXT DEFAULT '',
  city TEXT DEFAULT '',
  providers_json TEXT DEFAULT '[]',
  forwarded INTEGER DEFAULT 0,
  forwarded_at TEXT
);

-- Reviews table for native first-party reviews
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  provider_slug TEXT NOT NULL,
  reviewer_name TEXT DEFAULT '',
  reviewer_email TEXT DEFAULT '',
  rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
  comment TEXT DEFAULT '',
  approved INTEGER DEFAULT 0
);

-- Suppression list for CAN-SPAM unsubscribes
CREATE TABLE IF NOT EXISTS suppression_list (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  created_at TEXT NOT NULL,
  reason TEXT DEFAULT 'unsubscribe',
  UNIQUE(email)
);

-- Removal requests for listed businesses
CREATE TABLE IF NOT EXISTS removal_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_slug TEXT NOT NULL,
  email TEXT NOT NULL,
  business_name TEXT,
  reason TEXT,
  created_at TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_suppression_email ON suppression_list(email);
CREATE INDEX IF NOT EXISTS idx_removal_status ON removal_requests(status);

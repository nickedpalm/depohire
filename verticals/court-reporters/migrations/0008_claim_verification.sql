-- Add verification columns to claimed_listings
-- NOTE: Columns already exist from prior manual DB setup; skipping ALTER TABLE

-- SMS verification codes
CREATE TABLE IF NOT EXISTS verification_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_id INTEGER NOT NULL,
  listing_slug TEXT NOT NULL,
  code TEXT NOT NULL,
  phone_sent_to TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  attempts INTEGER DEFAULT 0,
  verified INTEGER DEFAULT 0,
  FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- Pending claims awaiting manual review
CREATE TABLE IF NOT EXISTS pending_claims (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_id INTEGER NOT NULL,
  listing_slug TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  reviewed_at TEXT,
  reviewed_by TEXT,
  decision TEXT,
  notes TEXT,
  FOREIGN KEY (provider_id) REFERENCES providers(id)
);

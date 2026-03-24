-- Stripe subscription tracking for Featured/City Pro tiers

CREATE TABLE IF NOT EXISTS subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_slug TEXT NOT NULL,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT UNIQUE,
  customer_email TEXT,
  plan TEXT NOT NULL DEFAULT 'featured',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  canceled_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_slug ON subscriptions(listing_slug);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub ON subscriptions(stripe_subscription_id);

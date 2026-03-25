-- Add provider_id to subscriptions for proper ownership tracking
ALTER TABLE subscriptions ADD COLUMN provider_id INTEGER REFERENCES providers(id);

-- Backfill provider_id from claimed_listings where possible
UPDATE subscriptions SET provider_id = (
  SELECT cl.provider_id FROM claimed_listings cl
  WHERE cl.listing_slug = subscriptions.listing_slug
) WHERE provider_id IS NULL;

-- Idempotency table for Stripe webhook events
CREATE TABLE IF NOT EXISTS processed_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  event_type TEXT,
  processed_at TEXT NOT NULL
);

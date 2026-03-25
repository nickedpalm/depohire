-- Cleanup expired sessions and magic links
DELETE FROM sessions WHERE expires_at < datetime('now');
DELETE FROM magic_links WHERE expires_at < datetime('now') AND used = 1;

-- D1/SQLite doesn't support ALTER CONSTRAINT, so cascade must be handled in application code.
-- Create index to speed up orphan cleanup queries
CREATE INDEX IF NOT EXISTS idx_photos_listing ON provider_photos(listing_slug);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_magic_links_expires ON magic_links(expires_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_provider ON subscriptions(provider_id);

export interface Env {
  LEADS_DB: D1Database;
  PHOTOS?: R2Bucket;
  LISTMONK_URL?: string;
  LISTMONK_USER?: string;
  LISTMONK_PASS?: string;
  SITE_DOMAIN?: string;      // e.g. "depohire.com"
  SITE_NAME?: string;        // e.g. "DepoHire"
  SITE_TAGLINE?: string;     // e.g. "Find certified deposition videographers"
  SITE_FROM_EMAIL?: string;  // e.g. "DepoHire <noreply@depohire.com>"
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  TURNSTILE_SECRET_KEY?: string;
}

export interface Env {
  LEADS_DB: D1Database;
  PHOTOS?: R2Bucket;

  // Site identity (REQUIRED for each vertical)
  SITE_DOMAIN?: string;      // e.g. "yourdomain.com"
  SITE_NAME?: string;        // e.g. "YourDirectory"
  SITE_TAGLINE?: string;     // e.g. "Find professionals near you"
  SITE_FROM_EMAIL?: string;  // e.g. "YourDir <noreply@yourdomain.com>"
  COMPANY_ADDRESS?: string;  // e.g. "123 Main St, City, ST 12345"

  // Listmonk email
  LISTMONK_URL?: string;
  LISTMONK_USER?: string;
  LISTMONK_PASS?: string;
  LISTMONK_LIST_ID?: string;              // newsletter list ID (number as string)
  LISTMONK_MAGICLINK_TEMPLATE_ID?: string; // transactional template for magic links
  LISTMONK_GUIDE_TEMPLATE_ID?: string;     // transactional template for guide delivery
  LISTMONK_PASSTHROUGH_TEMPLATE_ID?: string; // passthrough template for HTML body emails

  // Payments
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;

  // Security
  TURNSTILE_SECRET_KEY?: string;
  HASH_SALT?: string;        // per-vertical salt for IP hashing

  // Phone verification
  TWILIO_ACCOUNT_SID?: string;
  TWILIO_AUTH_TOKEN?: string;
  TWILIO_PHONE_NUMBER?: string;

  // Admin
  ADMIN_EMAIL?: string;
}

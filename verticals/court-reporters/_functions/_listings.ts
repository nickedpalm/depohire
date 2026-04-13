/**
 * Listing contact lookup helpers for claim verification.
 *
 * - getListingContact: fetch phone/website_domain for a listing slug
 * - domainsMatch: check if an email domain matches a listing's website domain
 */

interface ListingContact {
  phone: string | null;
  website_domain: string | null;
}

/** Module-level cache for listing contacts (lives for the worker invocation). */
let contactsCache: Record<string, ListingContact> | null = null;

/**
 * Fetch the contact info for a listing by slug.
 * Reads `/data/listing-contacts.json` from the same origin as the request.
 * Returns null if the slug is not found or the fetch fails.
 */
export async function getListingContact(
  slug: string,
  requestUrl: string,
): Promise<ListingContact | null> {
  if (!contactsCache) {
    try {
      const origin = new URL(requestUrl).origin;
      const resp = await fetch(`${origin}/data/listing-contacts.json`);
      if (!resp.ok) {
        console.error(`Failed to fetch listing-contacts.json: ${resp.status}`);
        return null;
      }
      contactsCache = await resp.json() as Record<string, ListingContact>;
    } catch (err) {
      console.error('Error fetching listing-contacts.json:', err);
      return null;
    }
  }

  return contactsCache[slug] ?? null;
}

/** Common free/consumer email providers that should never count as a domain match. */
const FREE_EMAIL_PROVIDERS = new Set([
  'gmail.com',
  'yahoo.com',
  'yahoo.co.uk',
  'hotmail.com',
  'outlook.com',
  'live.com',
  'msn.com',
  'aol.com',
  'icloud.com',
  'me.com',
  'mail.com',
  'protonmail.com',
  'proton.me',
  'zoho.com',
  'ymail.com',
  'gmx.com',
  'gmx.net',
]);

/**
 * Check whether an email address's domain matches a listing's website domain.
 *
 * - Strips "www." from both sides before comparing.
 * - Common consumer email providers (gmail, yahoo, etc.) always return false.
 * - Comparison is case-insensitive.
 */
export function domainsMatch(
  email: string,
  websiteDomain: string | null,
): boolean {
  if (!websiteDomain) return false;

  const atIdx = email.lastIndexOf('@');
  if (atIdx < 0) return false;

  const emailDomain = email.slice(atIdx + 1).toLowerCase().replace(/^www\./, '');
  if (FREE_EMAIL_PROVIDERS.has(emailDomain)) return false;

  const siteDomain = websiteDomain.toLowerCase().replace(/^www\./, '');

  return emailDomain === siteDomain;
}

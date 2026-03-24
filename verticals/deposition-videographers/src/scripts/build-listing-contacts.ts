/**
 * Build-time script: generates public/data/listing-contacts.json
 *
 * For each listing, extracts slug, normalized phone (E.164 +1XXXXXXXXXX),
 * and website domain (no protocol, no www., no paths).
 *
 * Usage:
 *   npx tsx src/scripts/build-listing-contacts.ts
 *
 * Also runs automatically during `astro build` via the integration in astro.config.ts.
 */

import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const LISTINGS_DIR = join(PROJECT_ROOT, 'src', 'data', 'listings');
const OUTPUT_DIR = join(PROJECT_ROOT, 'public', 'data');
const OUTPUT_FILE = join(OUTPUT_DIR, 'listing-contacts.json');

interface ContactEntry {
  phone: string | null;
  website_domain: string | null;
}

/**
 * Normalize a phone number to E.164 format (+1XXXXXXXXXX).
 * Returns null if the input is missing, empty, or can't be parsed to 10+ digits.
 */
function normalizePhone(raw: string | undefined | null): string | null {
  if (!raw || typeof raw !== 'string') return null;

  // Strip everything that isn't a digit or leading +
  const stripped = raw.replace(/[^\d+]/g, '');

  // Extract just the digits
  const digits = stripped.replace(/\D/g, '');

  if (digits.length === 0) return null;

  // Already has country code (11 digits starting with 1 for US/CA)
  if (digits.length === 11 && digits.startsWith('1')) {
    return `+${digits}`;
  }

  // Standard 10-digit US/CA number — prepend +1
  if (digits.length === 10) {
    return `+1${digits}`;
  }

  // International number with explicit + prefix — return as-is with +
  if (raw.trim().startsWith('+') && digits.length >= 7) {
    return `+${digits}`;
  }

  // 7-digit local number or other oddity — skip
  return null;
}

/**
 * Extract the bare domain from a URL string.
 * Strips protocol, www., paths, query strings, fragments, and trailing slashes.
 * Returns null if input is missing or unparseable.
 */
function extractDomain(raw: string | undefined | null): string | null {
  if (!raw || typeof raw !== 'string') return null;

  let url = raw.trim();
  if (url.length === 0) return null;

  // Ensure there's a protocol so URL constructor can parse it
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url;
  }

  try {
    const parsed = new URL(url);
    let host = parsed.hostname.toLowerCase();

    // Strip www.
    if (host.startsWith('www.')) {
      host = host.slice(4);
    }

    // Reject if it looks like an IP or is empty
    if (!host || host === 'localhost') return null;

    return host;
  } catch {
    // Malformed URL — try a regex fallback
    const match = url.match(/(?:https?:\/\/)?(?:www\.)?([^\/\s?#]+)/i);
    if (match && match[1]) {
      return match[1].toLowerCase();
    }
    return null;
  }
}

function main() {
  const files = readdirSync(LISTINGS_DIR).filter((f) => f.endsWith('.json'));

  const index: Record<string, ContactEntry> = {};
  let total = 0;
  let withPhone = 0;
  let withDomain = 0;

  for (const file of files) {
    const raw = readFileSync(join(LISTINGS_DIR, file), 'utf-8');
    let listings: any[];

    try {
      listings = JSON.parse(raw);
    } catch (e) {
      console.warn(`  Skipping ${file}: invalid JSON`);
      continue;
    }

    if (!Array.isArray(listings)) {
      listings = [listings];
    }

    for (const listing of listings) {
      if (!listing.slug) continue;

      const phone = normalizePhone(listing.phone);
      const website_domain = extractDomain(listing.website);

      index[listing.slug] = { phone, website_domain };
      total++;
      if (phone) withPhone++;
      if (website_domain) withDomain++;
    }
  }

  mkdirSync(OUTPUT_DIR, { recursive: true });
  writeFileSync(OUTPUT_FILE, JSON.stringify(index, null, 2) + '\n');

  console.log(`[build-listing-contacts] ${total} listings indexed`);
  console.log(`  ${withPhone} with phone, ${withDomain} with website domain`);
  console.log(`  Written to ${OUTPUT_FILE}`);
}

main();

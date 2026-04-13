/**
 * POST /api/auth/resend-code
 * Resend SMS verification code. Rate-limited to 3 per listing per hour.
 *
 * Body: { listing_slug: string }
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';
import { getListingContact } from '../../_listings';
import { normalizePhone, generateCode, sendVerificationSMS } from '../../_twilio';

const MAX_RESENDS_PER_HOUR = 3;

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;

  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let body: { listing_slug?: string };
  try { body = await request.json(); } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const slug = (body.listing_slug || '').trim();
  if (!slug) return jsonResponse({ error: 'listing_slug is required' }, 400, origin);

  const now = new Date().toISOString();
  const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString();

  // Rate limit: check how many codes sent in the last hour
  const recentCount = await env.LEADS_DB.prepare(
    `SELECT COUNT(*) as cnt FROM verification_codes
     WHERE provider_id = ? AND listing_slug = ? AND created_at > ?`
  ).bind(provider.id, slug, oneHourAgo).first<{ cnt: number }>();

  if (recentCount && recentCount.cnt >= MAX_RESENDS_PER_HOUR) {
    return jsonResponse({
      error: 'Too many code requests. Please wait an hour or request manual review.',
    }, 429, origin);
  }

  // Get listing phone
  const contact = await getListingContact(slug, request.url);
  const phone = contact?.phone ? normalizePhone(contact.phone) : null;

  if (!phone) {
    return jsonResponse({ error: 'No phone number available for this listing.' }, 400, origin);
  }

  // Invalidate any existing unused codes for this provider + listing
  await env.LEADS_DB.prepare(
    `UPDATE verification_codes SET verified = 1 WHERE provider_id = ? AND listing_slug = ? AND verified = 0`
  ).bind(provider.id, slug).run();

  // Generate and store new code
  const code = generateCode();
  const codeExpiry = new Date(Date.now() + 10 * 60 * 1000).toISOString();

  await env.LEADS_DB.prepare(
    `INSERT INTO verification_codes (provider_id, listing_slug, code, phone_sent_to, created_at, expires_at)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(provider.id, slug, code, phone, now, codeExpiry).run();

  // Send SMS
  const sent = await sendVerificationSMS(phone, code, env);

  if (!sent) {
    return jsonResponse({ error: 'Failed to send SMS. Please try again or request manual review.' }, 500, origin);
  }

  return jsonResponse({ ok: true, message: 'New code sent.' }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

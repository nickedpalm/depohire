/**
 * POST /api/auth/verify-phone
 * Verify the 6-digit SMS code to complete a listing claim.
 *
 * Body: { code: string, listing_slug: string }
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';
import { notifyAdminPendingClaim } from '../../_admin';

const MAX_ATTEMPTS = 5;

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;

  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let body: { code?: string; listing_slug?: string };
  try { body = await request.json(); } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const code = (body.code || '').trim();
  const slug = (body.listing_slug || '').trim();

  if (!code || !slug) {
    return jsonResponse({ error: 'code and listing_slug are required' }, 400, origin);
  }

  if (!/^\d{6}$/.test(code)) {
    return jsonResponse({ error: 'Code must be 6 digits' }, 400, origin);
  }

  const now = new Date().toISOString();

  // Find the most recent unused verification code for this provider + listing
  const record = await env.LEADS_DB.prepare(
    `SELECT id, code, expires_at, attempts, verified
     FROM verification_codes
     WHERE provider_id = ? AND listing_slug = ? AND verified = 0
     ORDER BY created_at DESC
     LIMIT 1`
  ).bind(provider.id, slug).first<{
    id: number; code: string; expires_at: string; attempts: number; verified: number;
  }>();

  if (!record) {
    return jsonResponse({ error: 'No pending verification. Please request a new code.' }, 404, origin);
  }

  if (record.expires_at < now) {
    return jsonResponse({ error: 'Code expired. Please request a new one.', expired: true }, 410, origin);
  }

  // Increment attempts
  const newAttempts = record.attempts + 1;
  await env.LEADS_DB.prepare(
    `UPDATE verification_codes SET attempts = ? WHERE id = ?`
  ).bind(newAttempts, record.id).run();

  // Check max attempts
  if (newAttempts >= MAX_ATTEMPTS) {
    // Fall back to manual review
    await env.LEADS_DB.prepare(
      `INSERT INTO pending_claims (provider_id, listing_slug, reason, created_at)
       VALUES (?, ?, 'max_sms_attempts_exceeded', ?)`
    ).bind(provider.id, slug, now).run();

    // Create or update claim as pending
    const existingClaim = await env.LEADS_DB.prepare(
      `SELECT id FROM claimed_listings WHERE listing_slug = ? AND provider_id = ?`
    ).bind(slug, provider.id).first();

    if (existingClaim) {
      await env.LEADS_DB.prepare(
        `UPDATE claimed_listings SET verification_status = 'pending_review', verification_method = 'pending' WHERE id = ?`
      ).bind(existingClaim.id).run();
    } else {
      await env.LEADS_DB.prepare(
        `INSERT INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json, verification_status, verification_method)
         VALUES (?, ?, ?, '{}', 'pending_review', 'pending')`
      ).bind(provider.id, slug, now).run();
    }

    try {
      await notifyAdminPendingClaim(env, provider.email, slug, 'Max SMS verification attempts exceeded');
    } catch {}

    return jsonResponse({
      error: 'Too many attempts. Your claim has been submitted for manual review.',
      max_attempts_exceeded: true,
    }, 429, origin);
  }

  // Verify code
  if (code !== record.code) {
    const remaining = MAX_ATTEMPTS - newAttempts;
    return jsonResponse({
      error: `Invalid code. ${remaining} attempt${remaining !== 1 ? 's' : ''} remaining.`,
      attempts_remaining: remaining,
    }, 400, origin);
  }

  // Code is correct!
  await env.LEADS_DB.prepare(
    `UPDATE verification_codes SET verified = 1 WHERE id = ?`
  ).bind(record.id).run();

  // Claim the listing as verified
  const existingClaim = await env.LEADS_DB.prepare(
    `SELECT id FROM claimed_listings WHERE listing_slug = ? AND provider_id = ?`
  ).bind(slug, provider.id).first();

  if (existingClaim) {
    await env.LEADS_DB.prepare(
      `UPDATE claimed_listings SET verification_status = 'verified', verification_method = 'sms' WHERE id = ?`
    ).bind(existingClaim.id).run();
  } else {
    await env.LEADS_DB.prepare(
      `INSERT INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json, verification_status, verification_method)
       VALUES (?, ?, ?, '{}', 'verified', 'sms')`
    ).bind(provider.id, slug, now).run();
  }

  return jsonResponse({
    ok: true,
    redirect: `/provider/dashboard?listing=${slug}`,
  }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

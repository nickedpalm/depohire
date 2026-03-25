/**
 * POST /api/auth/manual-review
 * Request manual review for a listing claim when SMS verification fails.
 *
 * Body: { listing_slug: string }
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';
import { notifyAdminPendingClaim } from '../../_admin';

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

  // Check if already has a pending claim
  const existing = await env.LEADS_DB.prepare(
    `SELECT id FROM pending_claims WHERE provider_id = ? AND listing_slug = ? AND decision IS NULL`
  ).bind(provider.id, slug).first();

  if (existing) {
    return jsonResponse({ ok: true, message: 'Your claim is already under review.' }, 200, origin);
  }

  // Create pending claim
  await env.LEADS_DB.prepare(
    `INSERT INTO pending_claims (provider_id, listing_slug, reason, created_at)
     VALUES (?, ?, 'manual_review_requested', ?)`
  ).bind(provider.id, slug, now).run();

  // Create or update claimed_listings entry
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

  // Notify admin
  try {
    await notifyAdminPendingClaim(env, provider.email, slug, 'Provider requested manual review');
  } catch {}

  return jsonResponse({ ok: true, message: 'Your claim has been submitted for manual review.' }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

/**
 * POST /api/provider/claim — claim an unclaimed listing
 * Body: { listing_slug: string }
 * Requires authenticated session.
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse, SLUG_RE } from '../../_auth';

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const slug = (payload.listing_slug || '').trim();
  if (!slug || !SLUG_RE.test(slug)) return jsonResponse({ error: 'Valid listing_slug is required' }, 400, origin);

  // Verify authorization: a magic link must have been issued for this provider+listing
  const magicLink = await env.LEADS_DB.prepare(
    `SELECT id FROM magic_links WHERE email = ? AND listing_slug = ?`
  ).bind(provider.email, slug).first();

  if (!magicLink) {
    return jsonResponse({ error: 'You are not authorized to claim this listing' }, 403, origin);
  }

  // Atomic claim: INSERT OR IGNORE + check if we got it
  const result = await env.LEADS_DB.prepare(
    `INSERT OR IGNORE INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json)
     VALUES (?, ?, ?, '{}')`
  ).bind(provider.id, slug, new Date().toISOString()).run();

  if (result.meta.changes === 0) {
    // Listing was already claimed — check by whom
    const existing = await env.LEADS_DB.prepare(
      `SELECT provider_id FROM claimed_listings WHERE listing_slug = ?`
    ).bind(slug).first<{ provider_id: number }>();

    if (existing && existing.provider_id === provider.id) {
      return jsonResponse({ ok: true, message: 'Already claimed by you' }, 200, origin);
    }
    return jsonResponse({ error: 'This listing has already been claimed by another provider' }, 409, origin);
  }

  return jsonResponse({ ok: true, message: 'Listing claimed successfully' }, 200, origin);
};

export const onRequestDelete: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const slug = (payload.listing_slug || '').trim();
  if (!slug || !SLUG_RE.test(slug)) return jsonResponse({ error: 'Valid listing_slug is required' }, 400, origin);

  // Only allow unclaiming your own listing
  const existing = await env.LEADS_DB.prepare(
    `SELECT id FROM claimed_listings WHERE listing_slug = ? AND provider_id = ?`
  ).bind(slug, provider.id).first<{ id: number }>();

  if (!existing) {
    return jsonResponse({ error: 'Listing not claimed by you' }, 403, origin);
  }

  // Delete photos metadata (R2 objects remain but are orphaned — acceptable)
  await env.LEADS_DB.prepare(
    `DELETE FROM provider_photos WHERE listing_slug = ? AND provider_id = ?`
  ).bind(slug, provider.id).run();

  // Delete the claim
  await env.LEADS_DB.prepare(
    `DELETE FROM claimed_listings WHERE id = ?`
  ).bind(existing.id).run();

  // Cancel any active subscriptions for this listing
  await env.LEADS_DB.prepare(
    `UPDATE subscriptions SET status = 'canceled', canceled_at = ? WHERE listing_slug = ? AND status = 'active'`
  ).bind(new Date().toISOString(), slug).run();

  return jsonResponse({ ok: true, message: 'Listing unclaimed' }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

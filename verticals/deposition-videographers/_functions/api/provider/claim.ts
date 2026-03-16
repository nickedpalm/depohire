/**
 * POST /api/provider/claim — claim an unclaimed listing
 * Body: { listing_slug: string }
 * Requires authenticated session.
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';

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
  if (!slug) return jsonResponse({ error: 'listing_slug is required' }, 400, origin);

  // Check if already claimed
  const existing = await env.LEADS_DB.prepare(
    `SELECT id, provider_id FROM claimed_listings WHERE listing_slug = ?`
  ).bind(slug).first<{ id: number; provider_id: number }>();

  if (existing) {
    if (existing.provider_id === provider.id) {
      return jsonResponse({ ok: true, message: 'Already claimed by you' }, 200, origin);
    }
    return jsonResponse({ error: 'This listing has already been claimed by another provider' }, 409, origin);
  }

  await env.LEADS_DB.prepare(
    `INSERT INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json)
     VALUES (?, ?, ?, '{}')`
  ).bind(provider.id, slug, new Date().toISOString()).run();

  return jsonResponse({ ok: true, message: 'Listing claimed successfully' }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

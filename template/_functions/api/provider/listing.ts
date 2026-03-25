/**
 * GET /api/provider/listing?slug=xxx — load claimed listing data
 * PUT /api/provider/listing — update listing fields
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';

const ALLOWED_FIELDS = [
  'name', 'phone', 'website', 'email', 'description',
  'services', 'certifications', 'coverage_area', 'years_experience',
  'demo_reel_url',
  // Settings & visibility
  'visible', 'accept_quotes',
  'notify_new_quotes', 'notify_reminders', 'notify_monthly_report', 'notify_marketing',
  // Service area
  'service_radius', 'availability_days', 'rush_available', 'travel_policy',
];

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  const url = new URL(request.url);
  const slug = url.searchParams.get('slug');
  if (!slug) return jsonResponse({ error: 'slug parameter required' }, 400, origin);

  const claim = await env.LEADS_DB.prepare(
    `SELECT id, listing_slug, claimed_at, data_json, verification_status FROM claimed_listings
     WHERE provider_id = ? AND listing_slug = ?`
  ).bind(provider.id, slug).first<{ id: number; listing_slug: string; claimed_at: string; data_json: string; verification_status: string }>();

  if (!claim) return jsonResponse({ error: 'Listing not claimed by you' }, 403, origin);
  if (claim.verification_status !== 'verified') {
    return jsonResponse({ error: 'Listing claim is pending verification', status: claim.verification_status }, 403, origin);
  }

  let data = {};
  try { data = JSON.parse(claim.data_json || '{}'); } catch {}

  return jsonResponse({
    slug: claim.listing_slug,
    claimed_at: claim.claimed_at,
    data,
  }, 200, origin);
};

export const onRequestPut: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const slug = payload.slug;
  if (!slug) return jsonResponse({ error: 'slug is required' }, 400, origin);

  const claim = await env.LEADS_DB.prepare(
    `SELECT id, data_json, verification_status FROM claimed_listings WHERE provider_id = ? AND listing_slug = ?`
  ).bind(provider.id, slug).first<{ id: number; data_json: string; verification_status: string }>();

  if (!claim) return jsonResponse({ error: 'Listing not claimed by you' }, 403, origin);
  if (claim.verification_status !== 'verified') {
    return jsonResponse({ error: 'Listing claim is pending verification', status: claim.verification_status }, 403, origin);
  }

  // Merge only allowed fields
  let existing: Record<string, any> = {};
  try { existing = JSON.parse(claim.data_json || '{}'); } catch {}

  for (const field of ALLOWED_FIELDS) {
    if (field in payload) {
      existing[field] = payload[field];
    }
  }

  await env.LEADS_DB.prepare(
    `UPDATE claimed_listings SET data_json = ? WHERE id = ?`
  ).bind(JSON.stringify(existing), claim.id).run();

  // Also update provider name if provided
  if (payload.provider_name) {
    await env.LEADS_DB.prepare(
      `UPDATE providers SET name = ? WHERE id = ?`
    ).bind(payload.provider_name, provider.id).run();
  }

  return jsonResponse({ ok: true, data: existing }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

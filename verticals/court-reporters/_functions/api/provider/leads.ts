/**
 * GET /api/provider/leads?slug=xxx — get quote requests for a claimed listing
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse, SLUG_RE } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;

  try {
    const provider = await getProvider(env.LEADS_DB, request);
    if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

    const url = new URL(request.url);
    const slug = url.searchParams.get('slug');
    if (!slug || !SLUG_RE.test(slug)) return jsonResponse({ error: 'Valid slug parameter required' }, 400, origin);

    // Verify ownership
    const claim = await env.LEADS_DB.prepare(
      `SELECT id FROM claimed_listings WHERE provider_id = ? AND listing_slug = ?`
    ).bind(provider.id, slug).first();

    if (!claim) return jsonResponse({ error: 'Listing not claimed by you' }, 403, origin);

    // Get leads that include this listing slug in providers_json
    const leads = await env.LEADS_DB.prepare(
      `SELECT id, created_at, attorney_name, attorney_email, attorney_phone, case_details, city
       FROM leads
       WHERE INSTR(providers_json, ?) > 0
       ORDER BY created_at DESC
       LIMIT 50`
    ).bind(`"slug":"${slug}"`).all();

    return jsonResponse({
      leads: leads.results || [],
    }, 200, origin);
  } catch (err: any) {
    console.error('Leads endpoint error:', err?.message, err?.stack);
    return jsonResponse({ error: 'Internal error' }, 500, origin);
  }
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

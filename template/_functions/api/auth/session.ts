/**
 * GET /api/auth/session — check current session
 * DELETE /api/auth/session — logout (clear session)
 */
import type { Env } from '../../_types';
import { getProvider, getSessionToken, jsonResponse, optionsResponse, sessionCookie, corsHeaders } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);

  if (!provider) {
    return jsonResponse({ authenticated: false }, 401, origin);
  }

  // Get claimed listings for this provider (with verification status)
  const claims = await env.LEADS_DB.prepare(
    `SELECT listing_slug, verification_status FROM claimed_listings WHERE provider_id = ?`
  ).bind(provider.id).all<{ listing_slug: string; verification_status: string }>();

  return jsonResponse({
    authenticated: true,
    provider: {
      id: provider.id,
      email: provider.email,
      name: provider.name,
    },
    // Backwards-compatible: listings is still a string array of verified slugs
    listings: claims.results?.filter(c => c.verification_status === 'verified').map(c => c.listing_slug) || [],
    // Full claim details for dashboard UI
    claims: claims.results?.map(c => ({ slug: c.listing_slug, status: c.verification_status })) || [],
  }, 200, origin);
};

export const onRequestDelete: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const token = getSessionToken(request);

  if (token) {
    await env.LEADS_DB.prepare(`DELETE FROM sessions WHERE token = ?`).bind(token).run();
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': sessionCookie('deleted', 0),
      ...corsHeaders(origin),
    },
  });
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

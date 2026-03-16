/**
 * GET /api/auth/session — check current session
 * DELETE /api/auth/session — logout (clear session)
 */
import type { Env } from '../../_types';
import { getProvider, getSessionToken, jsonResponse, optionsResponse, sessionCookie } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);

  if (!provider) {
    return jsonResponse({ authenticated: false }, 401, origin);
  }

  // Get claimed listings for this provider
  const claims = await env.LEADS_DB.prepare(
    `SELECT listing_slug FROM claimed_listings WHERE provider_id = ?`
  ).bind(provider.id).all<{ listing_slug: string }>();

  return jsonResponse({
    authenticated: true,
    provider: {
      id: provider.id,
      email: provider.email,
      name: provider.name,
    },
    listings: claims.results?.map(c => c.listing_slug) || [],
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
      ...(origin ? { 'Access-Control-Allow-Origin': origin } : {}),
    },
  });
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

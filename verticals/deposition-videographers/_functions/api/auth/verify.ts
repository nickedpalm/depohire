/**
 * GET /api/auth/verify?token=xxx
 * Verify magic link, create session, redirect to dashboard.
 */
import type { Env } from '../../_types';
import { generateToken, sessionCookie } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const token = url.searchParams.get('token');

  if (!token) {
    return redirectWithError('Missing token');
  }

  const now = new Date().toISOString();

  // Look up magic link
  const link = await env.LEADS_DB.prepare(
    `SELECT id, email, listing_slug, expires_at, used FROM magic_links WHERE token = ?`
  ).bind(token).first<{ id: number; email: string; listing_slug: string | null; expires_at: string; used: number }>();

  if (!link) {
    return redirectWithError('Invalid or expired link');
  }

  if (link.used) {
    return redirectWithError('This link has already been used');
  }

  if (link.expires_at < now) {
    return redirectWithError('This link has expired. Please request a new one.');
  }

  // Mark link as used
  await env.LEADS_DB.prepare(
    `UPDATE magic_links SET used = 1 WHERE id = ?`
  ).bind(link.id).run();

  // Find or create provider
  let provider = await env.LEADS_DB.prepare(
    `SELECT id, email, name FROM providers WHERE email = ?`
  ).bind(link.email).first<{ id: number; email: string; name: string }>();

  if (!provider) {
    const result = await env.LEADS_DB.prepare(
      `INSERT INTO providers (email, name, created_at) VALUES (?, '', ?)`
    ).bind(link.email, now).run();

    provider = { id: result.meta.last_row_id as number, email: link.email, name: '' };
  }

  // If there's a listing_slug, auto-claim it
  if (link.listing_slug) {
    const existing = await env.LEADS_DB.prepare(
      `SELECT id FROM claimed_listings WHERE listing_slug = ?`
    ).bind(link.listing_slug).first();

    if (!existing) {
      await env.LEADS_DB.prepare(
        `INSERT INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json)
         VALUES (?, ?, ?, '{}')`
      ).bind(provider.id, link.listing_slug, now).run();
    }
  }

  // Create session (30 days)
  const sessionToken = generateToken();
  const expiresAt = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();

  await env.LEADS_DB.prepare(
    `INSERT INTO sessions (provider_id, token, created_at, expires_at)
     VALUES (?, ?, ?, ?)`
  ).bind(provider.id, sessionToken, now, expiresAt).run();

  // Redirect to dashboard
  const dashboardUrl = link.listing_slug
    ? `/provider/dashboard?listing=${link.listing_slug}`
    : '/provider/dashboard';

  return new Response(null, {
    status: 302,
    headers: {
      'Location': dashboardUrl,
      'Set-Cookie': sessionCookie(sessionToken),
    },
  });
};

function redirectWithError(message: string) {
  return new Response(null, {
    status: 302,
    headers: {
      'Location': `/provider/login?error=${encodeURIComponent(message)}`,
    },
  });
}

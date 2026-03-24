import type { Env } from '../_types';
import { SLUG_RE, corsHeaders, optionsResponse, jsonResponse, verifyTurnstile } from '../_auth';

export const onRequestOptions: PagesFunction<Env> = async ({ request }) => {
  const origin = request.headers.get('Origin') || undefined;
  return optionsResponse(origin);
};

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;

  let body: { email?: string; listing_slug?: string; business_name?: string; reason?: string };
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const email = (body.email || '').trim().toLowerCase();
  const listing_slug = (body.listing_slug || '').trim().toLowerCase();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return jsonResponse({ error: 'Invalid email' }, 400, origin);
  }

  if (!listing_slug || !SLUG_RE.test(listing_slug)) {
    return jsonResponse({ error: 'Invalid listing slug' }, 400, origin);
  }

  // Turnstile CSRF verification
  const turnstileToken = (body as any).turnstile_token || '';
  const ip = request.headers.get('CF-Connecting-IP') || '';
  if (env.TURNSTILE_SECRET_KEY) {
    const valid = await verifyTurnstile(turnstileToken, env.TURNSTILE_SECRET_KEY, ip);
    if (!valid) {
      return jsonResponse({ error: 'Bot verification failed. Please try again.' }, 403, origin);
    }
  }

  try {
    await env.LEADS_DB.prepare(
      `INSERT INTO removal_requests (listing_slug, email, business_name, reason, created_at)
       VALUES (?, ?, ?, ?, ?)`
    ).bind(
      listing_slug,
      email,
      body.business_name || null,
      body.reason || null,
      new Date().toISOString()
    ).run();
  } catch (err) {
    console.error('Removal request insert failed:', err);
    return jsonResponse({ error: 'Failed to submit request' }, 500, origin);
  }

  return jsonResponse({ ok: true, message: 'Removal request submitted. We will review it within 5 business days.' }, 200, origin);
};

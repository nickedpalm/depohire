import type { Env } from '../_types';
import { SLUG_RE, corsHeaders, optionsResponse, jsonResponse, verifyTurnstile } from '../_auth';

function esc(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function sendRemovalConfirmation(env: Env, email: string, businessName: string, slug: string) {
  const url = env.LISTMONK_URL || 'https://mail.firestick.io';
  const user = env.LISTMONK_USER || 'admin';
  const pass = env.LISTMONK_PASS || '';
  const siteName = env.SITE_NAME || 'DepoHire';
  const domain = env.SITE_DOMAIN || 'depohire.com';
  const authHeader = 'Basic ' + btoa(`${user}:${pass}`);

  // Ensure subscriber exists
  await fetch(`${url}/api/subscribers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': authHeader },
    body: JSON.stringify({ email, name: '', status: 'enabled' }),
  });

  const html = `<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:480px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">${siteName}</h1>
  </div>
  <div style="padding:32px">
    <h2 style="color:#1a1a1a;font-size:18px;margin:0 0 16px">Removal Request Received</h2>
    <p style="color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 16px">
      We've received your request to remove <strong>${esc(businessName || slug)}</strong> from ${siteName}.
    </p>
    <p style="color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 16px">
      Our team will review your request within <strong>5 business days</strong>. You'll receive a follow-up email once the listing has been removed.
    </p>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      If you have any questions, reply to this email and we'll assist you.
    </p>
  </div>
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px">
    <p style="color:#d1d5db;font-size:11px;margin:0;line-height:1.5">
      ${siteName} &middot; PO Box 1547, Austin, TX 78767
    </p>
  </div>
</div></body></html>`;

  await fetch(`${url}/api/tx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': authHeader },
    body: JSON.stringify({
      subscriber_email: email,
      template_id: 8,
      subject: `Your removal request has been received — ${siteName}`,
      data: { body: html },
      content_type: 'html',
      messenger: 'email',
      from_email: env.SITE_FROM_EMAIL || `${siteName} <noreply@${domain}>`,
    }),
  });
}

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

  // Send confirmation email (don't fail the request if this fails)
  try {
    await sendRemovalConfirmation(env, email, body.business_name || '', listing_slug);
  } catch (err) {
    console.error('Removal confirmation email failed:', err);
  }

  return jsonResponse({ ok: true, message: 'Removal request submitted. We will review it within 5 business days.' }, 200, origin);
};

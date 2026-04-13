/**
 * POST /api/auth/magic-link
 * Send a magic link email to the provider.
 * Body: { email: string, listing_slug?: string }
 */
import type { Env } from '../../_types';
import { generateToken, generateShortCode, jsonResponse, optionsResponse, getSiteConfig } from '../../_auth';

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const email = (payload.email || '').trim().toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return jsonResponse({ error: 'Valid email is required' }, 400, origin);
  }

  // Rate limit: max 3 magic links per email per hour (counts all, not just unused)
  const recentCount = await env.LEADS_DB.prepare(
    `SELECT COUNT(*) as cnt FROM magic_links
     WHERE email = ? AND created_at > ?`
  ).bind(email, new Date(Date.now() - 3600000).toISOString()).first<{ cnt: number }>();

  if (recentCount && recentCount.cnt >= 3) {
    return jsonResponse({ error: 'Too many requests. Check your email for an existing link.' }, 429, origin);
  }

  const token = generateShortCode(12);
  const now = new Date().toISOString();
  const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(); // 24 hours

  const listingSlug = (payload.listing_slug || '').trim() || null;
  if (listingSlug && !/^[a-z0-9][a-z0-9-]*$/.test(listingSlug)) {
    return jsonResponse({ error: 'Invalid listing slug' }, 400, origin);
  }

  await env.LEADS_DB.prepare(
    `INSERT INTO magic_links (email, token, listing_slug, created_at, expires_at, used)
     VALUES (?, ?, ?, ?, ?, 0)`
  ).bind(email, token, listingSlug, now, expiresAt).run();

  // Send email via Listmonk transactional API
  const site = getSiteConfig(env);
  const domain = site.domain;
  const siteName = site.name;
  const tagline = site.tagline;
  const verifyUrl = `https://${domain}/provider/verify/${token}`;

  const emailBody = `
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:480px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">${siteName}</h1>
  </div>
  <div style="padding:32px">
    <h2 style="color:#1a1a1a;font-size:18px;margin:0 0 12px">Log in to your dashboard</h2>
    <p style="color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 24px">
      Click the button below to access your provider dashboard on ${siteName}. This link expires in 24 hours.
    </p>
    <a href="${verifyUrl}"
       style="display:inline-block;background:#2563eb;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
      Log In to Dashboard
    </a>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:24px 0 0">
      If you didn't request this link, you can safely ignore this email.
    </p>
  </div>
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px">
    <p style="color:#d1d5db;font-size:11px;margin:0;line-height:1.5">
      ${siteName}${site.address ? ` &middot; ${site.address}` : ''}<br>
      ${tagline}
    </p>
  </div>
</div>
</body>
</html>`.trim();

  try {
    const resp = await fetch(`${site.listmonkUrl}/api/tx`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + btoa(`${site.listmonkUser}:${site.listmonkPass}`),
      },
      body: JSON.stringify({
        subscriber_email: email,
        template_id: site.magicLinkTemplateId,
        subject: `Your ${siteName} login link`,
        content_type: 'html',
        data: { body: emailBody },
        messenger: 'email',
        from_email: site.fromEmail,
      }),
    });

    if (!resp.ok) {
      console.error('Listmonk tx failed:', resp.status, await resp.text());
      return jsonResponse({ error: 'Failed to send email. Please try again.' }, 500, origin);
    }
  } catch (err) {
    console.error('Listmonk request failed:', err);
    return jsonResponse({ error: 'Failed to send email. Please try again.' }, 500, origin);
  }

  return jsonResponse({ ok: true, message: 'Check your email for a login link.' }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};

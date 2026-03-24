import type { Env } from '../_types';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const email = (url.searchParams.get('email') || '').trim().toLowerCase();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return new Response('Invalid email', { status: 400 });
  }

  try {
    if (env.LEADS_DB) {
      await env.LEADS_DB.prepare(
        `INSERT OR IGNORE INTO suppression_list (email, created_at, reason) VALUES (?, ?, 'unsubscribe')`
      ).bind(email, new Date().toISOString()).run();
    }
  } catch (err) {
    console.error('Suppression insert failed:', err);
  }

  const domain = env.SITE_DOMAIN || 'depohire.com';
  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Unsubscribed — DepoHire</title>
<style>body{font-family:system-ui,-apple-system,sans-serif;background:#f9fafb;margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#fff;border-radius:12px;border:1px solid #e5e7eb;padding:48px;max-width:420px;text-align:center}
h1{font-size:24px;color:#1a1a1a;margin:0 0 12px}p{color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 24px}
a{color:#2563eb;text-decoration:none;font-weight:500}</style></head>
<body><div class="card">
<h1>You've been unsubscribed</h1>
<p>You will no longer receive notification emails from DepoHire. If this was a mistake, you can re-enable notifications from your <a href="https://${domain}/provider/dashboard/">provider dashboard</a>.</p>
<a href="https://${domain}/">&larr; Back to DepoHire</a>
</div></body></html>`;

  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html' },
  });
};

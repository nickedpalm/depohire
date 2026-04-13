/**
 * GET  /api/unsubscribe?email=xxx — show confirmation page (safe from link prefetchers)
 * POST /api/unsubscribe — actually perform the unsubscribe
 */
import type { Env } from '../_types';
import { getSiteConfig } from '../_auth';

function esc(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** GET: Show confirmation page — does NOT unsubscribe (prevents link-prefetcher auto-unsub) */
export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const email = (url.searchParams.get('email') || '').trim().toLowerCase();
  const site = getSiteConfig(env);
  const domain = site.domain;
  const siteName = site.name;

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return new Response('Invalid email', { status: 400 });
  }

  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Unsubscribe — ${esc(siteName)}</title>
<style>body{font-family:system-ui,-apple-system,sans-serif;background:#f9fafb;margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#fff;border-radius:12px;border:1px solid #e5e7eb;padding:48px;max-width:420px;text-align:center}
h1{font-size:24px;color:#1a1a1a;margin:0 0 12px}p{color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 24px}
button{background:#dc2626;color:#fff;border:none;padding:14px 28px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
button:hover{background:#b91c1c}
a{color:#2563eb;text-decoration:none;font-weight:500}
.done{display:none}.done h1{color:#059669}</style></head>
<body><div class="card">
<div id="confirm-view">
  <h1>Unsubscribe from notifications?</h1>
  <p>You will no longer receive lead notification emails for <strong>${esc(email)}</strong>.</p>
  <button id="unsub-btn">Confirm Unsubscribe</button>
  <br><br>
  <a href="https://${esc(domain)}/">&larr; Back to ${esc(siteName)}</a>
</div>
<div id="done-view" class="done">
  <h1>You've been unsubscribed</h1>
  <p>You will no longer receive notification emails from ${esc(siteName)}. If this was a mistake, you can re-enable notifications from your <a href="https://${esc(domain)}/provider/dashboard/">provider dashboard</a>.</p>
  <a href="https://${esc(domain)}/">&larr; Back to ${esc(siteName)}</a>
</div>
<script>
document.getElementById('unsub-btn').addEventListener('click', async function() {
  this.disabled = true;
  this.textContent = 'Processing...';
  try {
    const resp = await fetch('/api/unsubscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: ${JSON.stringify(email)} }),
    });
    if (resp.ok) {
      document.getElementById('confirm-view').style.display = 'none';
      var done = document.getElementById('done-view');
      done.style.display = 'block';
      done.classList.remove('done');
    } else {
      this.textContent = 'Error — try again';
      this.disabled = false;
    }
  } catch {
    this.textContent = 'Error — try again';
    this.disabled = false;
  }
});
</script>
</div></body></html>`;

  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html' },
  });
};

/** POST: Actually perform the unsubscribe */
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: { email?: string };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const email = (body.email || '').trim().toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return new Response(JSON.stringify({ error: 'Invalid email' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
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

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};

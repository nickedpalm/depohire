/**
 * Cloudflare Pages Function: Lead Capture + Email Notifications
 *
 * POST /api/leads
 * 1. Saves the lead to D1
 * 2. Sends notification email to each provider via Listmonk
 * 3. Sends confirmation email to the attorney via Listmonk
 * 4. Returns 200 to the attorney no matter what (zero lead loss)
 */

import type { Env } from '../_types';
import { verifyTurnstile, isAllowedOrigin, getSiteConfig as _getSiteConfig } from '../_auth';

let _reqOrigin: string | null = null;
let _siteDomain: string | undefined;

function getCorsHeaders(origin?: string | null) {
  const allowed = isAllowedOrigin(origin, _siteDomain) || (_siteDomain ? `https://${_siteDomain}` : '');
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
}

function jsonResp(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...getCorsHeaders(_reqOrigin) },
  });
}

function esc(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escUrl(str: string): string {
  return encodeURI(str).replace(/'/g, '%27').replace(/"/g, '%22');
}

type SiteConfig = ReturnType<typeof _getSiteConfig>;

function providerEmailHtml(p: { name: string; email: string }, attorney: { name: string; email: string; phone: string; caseDetails: string; city: string }, site: SiteConfig) {
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">${site.name}</h1>
  </div>
  <div style="padding:32px">
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin-bottom:24px">
      <p style="color:#1e40af;font-size:14px;font-weight:600;margin:0 0 4px">New Quote Request</p>
      <p style="color:#3b82f6;font-size:13px;margin:0">A client wants to connect with you.</p>
    </div>

    <h2 style="color:#1a1a1a;font-size:18px;margin:0 0 16px">Quote request for ${esc(p.name)}</h2>

    <table style="width:100%;border-collapse:collapse">
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;width:110px;vertical-align:top">Attorney</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px;font-weight:500">${esc(attorney.name)}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Email</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">
          <a href="mailto:${escUrl(attorney.email)}" style="color:#2563eb;text-decoration:none">${esc(attorney.email)}</a>
        </td>
      </tr>
      ${attorney.phone ? `<tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Phone</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">
          <a href="tel:${escUrl(attorney.phone)}" style="color:#2563eb;text-decoration:none">${esc(attorney.phone)}</a>
        </td>
      </tr>` : ''}
      ${attorney.city ? `<tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Location</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">${esc(attorney.city)}</td>
      </tr>` : ''}
      ${attorney.caseDetails ? `<tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Details</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">${esc(attorney.caseDetails)}</td>
      </tr>` : ''}
    </table>

    <div style="margin-top:24px">
      <a href="mailto:${escUrl(attorney.email)}?subject=Re:%20Deposition%20Videography%20Quote%20Request&body=Hi%20${escUrl(attorney.name)},%0A%0AThank%20you%20for%20your%20interest.%20"
         style="display:inline-block;background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Reply to ${esc(attorney.name)}
      </a>
    </div>

    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:24px 0 0">
      Respond quickly — attorneys often contact multiple providers. The first reply usually wins the job.
    </p>
  </div>
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px;background:#fafafa">
    <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6">
      <a href="https://${site.domain}/provider/login?listing=${encodeURIComponent(p.slug)}" style="color:#6b7280;text-decoration:none">Manage your listing</a> &middot;
      <a href="https://${site.domain}/api/unsubscribe?email=${encodeURIComponent(p.email)}" style="color:#6b7280;text-decoration:none">Unsubscribe</a>
    </p>
    <p style="color:#d1d5db;font-size:11px;margin:8px 0 0;line-height:1.5">
      ${site.name}${site.address ? ` &middot; ${esc(site.address)}` : ''}<br>
      This email was sent because your business is listed on ${site.domain}. You can <a href="https://${site.domain}/api/unsubscribe?email=${encodeURIComponent(p.email)}" style="color:#d1d5db">unsubscribe</a> at any time.
    </p>
  </div>
</div>
</body>
</html>`;
}

function attorneyConfirmationHtml(attorney: { name: string }, providers: { name: string }[], site: SiteConfig) {
  const providerList = providers.map(p => `<li style="padding:4px 0;color:#1a1a1a;font-size:14px">${esc(p.name)}</li>`).join('');
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:480px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  <div style="background:#1e3a5f;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">${site.name}</h1>
  </div>
  <div style="padding:32px">
    <h2 style="color:#1a1a1a;font-size:18px;margin:0 0 12px">Your quote request has been sent!</h2>
    <p style="color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 20px">
      Hi ${esc(attorney.name)}, your request has been forwarded to:
    </p>
    <ul style="margin:0 0 20px;padding-left:20px">${providerList}</ul>
    <p style="color:#6b7280;font-size:15px;line-height:1.6;margin:0 0 20px">
      Providers typically respond within 1 business day. Keep an eye on your inbox for a direct reply.
    </p>
    <p style="color:#9ca3af;font-size:13px;line-height:1.5;margin:0">
      Need help? Reply to this email and we'll assist you.
    </p>
  </div>
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px">
    <p style="color:#d1d5db;font-size:11px;margin:0;line-height:1.5">
      ${site.name}${site.address ? ` &middot; ${esc(site.address)}` : ''}<br>
      ${site.tagline}
    </p>
  </div>
</div>
</body>
</html>`;
}

async function sendListmonkEmail(env: Env, to: string, subject: string, body: string, site: SiteConfig) {
  const authHeader = 'Basic ' + btoa(`${site.listmonkUser}:${site.listmonkPass}`);

  // Ensure subscriber exists in Listmonk (required for tx API)
  await fetch(`${site.listmonkUrl}/api/subscribers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': authHeader,
    },
    body: JSON.stringify({ email: to, name: '', status: 'enabled' }),
  }); // 409 if exists — that's fine

  const resp = await fetch(`${site.listmonkUrl}/api/tx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': authHeader,
    },
    body: JSON.stringify({
      subscriber_email: to,
      template_id: site.passthroughTemplateId,
      subject,
      data: { body },
      content_type: 'html',
      messenger: 'email',
      from_email: site.fromEmail,
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    console.error(`Listmonk email to ${to} failed: ${resp.status} ${text}`);
    return false;
  }
  return true;
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  _reqOrigin = request.headers.get('Origin');
  _siteDomain = env.SITE_DOMAIN;

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResp({ error: 'Invalid JSON' }, 400);
  }

  // Honeypot check — silently accept
  if (payload.honeypot) {
    return jsonResp({ status: 'ok' });
  }

  // Turnstile CSRF verification
  const turnstileToken = payload.turnstile_token || '';
  const ip = request.headers.get('CF-Connecting-IP') || '';
  if (env.TURNSTILE_SECRET_KEY) {
    const valid = await verifyTurnstile(turnstileToken, env.TURNSTILE_SECRET_KEY, ip);
    if (!valid) {
      return jsonResp({ error: 'Bot verification failed. Please try again.' }, 403);
    }
  }

  const providers: { name: string; email: string; slug: string }[] = payload.providers || [];
  const attorney = {
    name: payload.attorney_name || '',
    email: payload.attorney_email || '',
    phone: payload.attorney_phone || '',
    caseDetails: payload.case_details || '',
    city: payload.city || '',
  };

  // Rate limiting: max 5 leads per email per hour, max 20 per IP per hour
  if (env.LEADS_DB && (attorney.email || ip)) {
    try {
      const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString();
      if (attorney.email) {
        const emailCount = await env.LEADS_DB.prepare(
          `SELECT COUNT(*) as cnt FROM leads WHERE attorney_email = ? AND created_at > ?`
        ).bind(attorney.email, oneHourAgo).first<{ cnt: number }>();
        if (emailCount && emailCount.cnt >= 5) {
          return jsonResp({ error: 'Too many requests. Please wait before submitting again.' }, 429);
        }
      }
    } catch {}
  }

  // 1. Always save to D1
  try {
    if (env.LEADS_DB) {
      await env.LEADS_DB.prepare(
        `INSERT INTO leads (created_at, attorney_name, attorney_email, attorney_phone, case_details, city, providers_json, forwarded)
         VALUES (?, ?, ?, ?, ?, ?, ?, 1)`
      ).bind(
        new Date().toISOString(),
        attorney.name,
        attorney.email,
        attorney.phone,
        attorney.caseDetails,
        attorney.city,
        JSON.stringify(providers),
      ).run();
    }
  } catch (err) {
    console.error('D1 lead insert failed:', err);
  }

  // 2. Send notification to each provider
  const site = _getSiteConfig(env);
  let emailsSent = 0;
  for (const p of providers) {
    if (!p.email) continue;

    // Check suppression list and notification preferences
    if (env.LEADS_DB) {
      try {
        const suppressed = await env.LEADS_DB.prepare(
          `SELECT id FROM suppression_list WHERE email = ?`
        ).bind(p.email.toLowerCase()).first();
        if (suppressed) {
          console.log(`Skipping email for ${p.email}: on suppression list`);
          continue;
        }
      } catch {}

      if (p.slug) {
        try {
          const claim = await env.LEADS_DB.prepare(
            `SELECT data_json FROM claimed_listings WHERE listing_slug = ?`
          ).bind(p.slug).first<{ data_json: string }>();
          if (claim) {
            const prefs = JSON.parse(claim.data_json || '{}');
            if (prefs.notify_new_quotes === false) {
              console.log(`Skipping email for ${p.slug}: notifications disabled`);
              continue;
            }
          }
        } catch {}
      }
    }

    try {
      const ok = await sendListmonkEmail(
        env,
        p.email,
        `New quote request for ${p.name} on ${site.name}`,
        providerEmailHtml(p, attorney, site),
        site,
      );
      if (ok) emailsSent++;
    } catch (err) {
      console.error(`Provider email to ${p.email} failed:`, err);
    }
  }

  // 3. Send confirmation to attorney
  if (attorney.email) {
    try {
      await sendListmonkEmail(
        env,
        attorney.email,
        `Your ${site.name} quote request has been sent`,
        attorneyConfirmationHtml(attorney, providers, site),
        site,
      );
    } catch (err) {
      console.error('Attorney confirmation email failed:', err);
    }
  }

  // 4. Always return success
  return jsonResp({
    status: 'ok',
    message: 'Your request has been received. Providers will respond to your email.',
    emailed: emailsSent,
  });
};

// Handle CORS preflight
export const onRequestOptions: PagesFunction = async ({ request }) => {
  const origin = request.headers.get('Origin');
  return new Response(null, {
    status: 204,
    headers: {
      ...getCorsHeaders(origin),
      'Access-Control-Max-Age': '86400',
    },
  });
};

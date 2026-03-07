/**
 * FILE LOCATION: functions/subscribe.ts
 * Cloudflare Pages Function — handles POST /subscribe from all forms
 *
 * Uses Listmonk v6 public subscription form endpoint (/subscription/form)
 * which requires list UUIDs (not numeric IDs) and no authentication.
 *
 * LISTMONK LIST UUIDs (mail.firestick.io):
 *   6  → 1574cfb0-e6d2-4e02-b7db-684b252f7178  DepoHire Newsletter
 *   30 → 1c82963b-310b-4af5-bf89-a7fb96132dd8  DepoHire Leads
 *   31 → 4f72411e-2d6c-4ddb-af06-674b502393d7  DepoHire Blog
 *   33 → b8c38467-94a1-4e6a-aeb4-c14a72bd11a8  DepoHire Provider Interest
 *   34 → c7be263f-1308-4b7a-a65e-594809e728ad  Lead Magnet Downloads
 *
 * CLOUDFLARE PAGES ENV VARS (set per project in Cloudflare dashboard):
 *   LISTMONK_URL  = https://mail.firestick.io
 *
 * SOURCE → LIST UUID ROUTING:
 *   city-quote-form      → 30 (DepoHire Leads)
 *   listing-quote-form   → 30 (DepoHire Leads)
 *   blog-sidebar         → 31 (DepoHire Blog)
 *   exit-intent          → 34 (Lead Magnet Downloads)
 *   provider-signup      → 33 (DepoHire Provider Interest)
 *   advertise-form       → 33 (DepoHire Provider Interest)
 *   default              → 6  (DepoHire Newsletter)
 */

interface Env {
  LISTMONK_URL: string;
  RESEND_API_KEY: string;
}

// Source → list UUID mapping (lists must be type='public' in Listmonk)
const SOURCE_TO_UUID: Record<string, string> = {
  'city-quote-form':    '1c82963b-310b-4af5-bf89-a7fb96132dd8', // list 30
  'listing-quote-form': '1c82963b-310b-4af5-bf89-a7fb96132dd8', // list 30
  'blog-sidebar':       '4f72411e-2d6c-4ddb-af06-674b502393d7', // list 31
  'exit-intent':        'c7be263f-1308-4b7a-a65e-594809e728ad', // list 34
  'provider-signup':    'b8c38467-94a1-4e6a-aeb4-c14a72bd11a8', // list 33
  'advertise-form':     'b8c38467-94a1-4e6a-aeb4-c14a72bd11a8', // list 33
};
const DEFAULT_UUID = '1574cfb0-e6d2-4e02-b7db-684b252f7178'; // list 6 — DepoHire Newsletter

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
  };

  try {
    const contentType = request.headers.get('Content-Type') || '';

    let email = '', name = '', source = '', providerEmail = '', listingName = '', caseType = '', preferredDate = '', details = '', city = '';

    if (contentType.includes('application/json')) {
      const body = await request.json() as Record<string, string>;
      email         = body.email         || '';
      name          = body.name          || '';
      source        = body.source        || '';
      providerEmail = body.providerEmail || '';
      listingName   = body.listingName   || '';
      caseType      = body.caseType      || '';
      preferredDate = body.preferredDate || '';
      details       = body.details       || '';
      city          = body.city          || '';
    } else {
      // application/x-www-form-urlencoded (from advertise page)
      const formData = await request.formData();
      email         = (formData.get('email')         as string) || '';
      name          = (formData.get('name')          as string) || '';
      source        = (formData.get('source')        as string) || '';
      providerEmail = (formData.get('providerEmail') as string) || '';
      listingName   = (formData.get('listingName')   as string) || '';
      caseType      = (formData.get('caseType')      as string) || '';
      preferredDate = (formData.get('preferredDate') as string) || '';
      details       = (formData.get('details')       as string) || '';
      city          = (formData.get('city')          as string) || '';
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid email' }), { status: 400, headers: cors });
    }

    const base = env.LISTMONK_URL?.replace(/\/$/, '');
    if (!base) {
      console.error('Missing LISTMONK_URL');
      return new Response(JSON.stringify({ ok: false, error: 'Server config error' }), { status: 500, headers: cors });
    }

    const listUUID = SOURCE_TO_UUID[source] ?? DEFAULT_UUID;

    // Use the public /subscription/form endpoint — no auth required in Listmonk v6
    const payload = new URLSearchParams({
      email,
      name: name || email.split('@')[0],
      l: listUUID,
    });

    const res = await fetch(`${base}/subscription/form`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload.toString(),
    });

    const responseText = await res.text();

    // Public form returns HTML — check for success/duplicate indicators
    const isAlreadySubscribed = responseText.toLowerCase().includes('already subscribed')
      || responseText.toLowerCase().includes('unsubscribed');
    const isSuccess = res.ok || responseText.toLowerCase().includes('subscribed successfully') || isAlreadySubscribed;

    if (isSuccess) {
      // Fire transactional emails for listing quote requests
      if (source === 'listing-quote-form' && providerEmail && env.RESEND_API_KEY) {
        await sendTransactionalEmails({
          resendKey: env.RESEND_API_KEY,
          providerEmail,
          listingName,
          attorneyName: name,
          attorneyEmail: email,
          caseType,
          preferredDate,
          details,
          city,
        });
      }
      return new Response(JSON.stringify({ ok: true, already: isAlreadySubscribed }), { headers: cors });
    }

    console.error('Listmonk subscription error:', res.status, responseText.slice(0, 200));
    return new Response(JSON.stringify({ ok: false, error: 'Subscription failed' }), { status: 500, headers: cors });

  } catch (err) {
    console.error('Subscribe function error:', err);
    return new Response(JSON.stringify({ ok: false, error: 'Server error' }), { status: 500, headers: cors });
  }
};

export const onRequestOptions: PagesFunction = async () =>
  new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });

// ─── Transactional email via Resend ─────────────────────────────────────────

interface TransactionalPayload {
  resendKey: string;
  providerEmail: string;
  listingName: string;
  attorneyName: string;
  attorneyEmail: string;
  caseType: string;
  preferredDate: string;
  details: string;
  city: string;
}

async function sendTransactionalEmails(p: TransactionalPayload): Promise<void> {
  const dateLabel = p.preferredDate
    ? new Date(p.preferredDate).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    : 'Not specified';

  const caseLabel = p.caseType
    ? p.caseType.charAt(0).toUpperCase() + p.caseType.slice(1).replace(/-/g, ' ')
    : 'Not specified';

  // 1. Provider notification — new lead
  const providerHtml = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a2e; margin: 0; padding: 0; background: #f5f5f5; }
  .wrap { max-width: 560px; margin: 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .header { background: #1a1a2e; padding: 24px 32px; }
  .header h1 { color: #fff; margin: 0; font-size: 20px; font-weight: 700; }
  .header p { color: #94a3b8; margin: 4px 0 0; font-size: 14px; }
  .body { padding: 28px 32px; }
  .badge { display: inline-block; background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; border-radius: 99px; font-size: 12px; font-weight: 600; padding: 3px 10px; margin-bottom: 16px; }
  .row { display: flex; margin-bottom: 12px; gap: 12px; }
  .label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #94a3b8; letter-spacing: .04em; min-width: 110px; padding-top: 2px; }
  .value { font-size: 14px; color: #1a1a2e; }
  hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }
  .cta { display: block; background: #1a1a2e; color: #fff !important; text-decoration: none; text-align: center; border-radius: 8px; padding: 12px 24px; font-size: 15px; font-weight: 600; margin: 24px 0 8px; }
  .footer { padding: 16px 32px; background: #f9fafb; border-top: 1px solid #e5e7eb; font-size: 12px; color: #94a3b8; text-align: center; }
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>New Lead from DepoHire</h1>
    <p>An attorney is looking for a videographer in ${p.city}</p>
  </div>
  <div class="body">
    <span class="badge">&#128276; New Quote Request</span>
    <div class="row"><span class="label">From</span><span class="value"><strong>${p.attorneyName}</strong></span></div>
    <div class="row"><span class="label">Email</span><span class="value"><a href="mailto:${p.attorneyEmail}" style="color:#2563eb">${p.attorneyEmail}</a></span></div>
    <div class="row"><span class="label">Case Type</span><span class="value">${caseLabel}</span></div>
    <div class="row"><span class="label">Preferred Date</span><span class="value">${dateLabel}</span></div>
    ${p.details ? `<div class="row"><span class="label">Notes</span><span class="value">${p.details}</span></div>` : ''}
    <hr>
    <p style="font-size:14px;color:#374151;">Reply directly to <strong>${p.attorneyEmail}</strong> to respond to this lead. Attorneys expect a response within 4 business hours.</p>
    <a class="cta" href="mailto:${p.attorneyEmail}?subject=Re: Deposition Videography Quote&body=Hi ${p.attorneyName},%0D%0A%0D%0AThank you for reaching out through DepoHire.">Reply to ${p.attorneyName} &rarr;</a>
  </div>
  <div class="footer">You received this because your listing appears on DepoHire.com &mdash; <a href="https://depohire.com" style="color:#2563eb">depohire.com</a></div>
</div>
</body></html>`;

  // 2. Attorney confirmation — your request was sent
  const attorneyHtml = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a2e; margin: 0; padding: 0; background: #f5f5f5; }
  .wrap { max-width: 560px; margin: 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .header { background: #1a1a2e; padding: 24px 32px; }
  .header h1 { color: #fff; margin: 0; font-size: 20px; font-weight: 700; }
  .header p { color: #94a3b8; margin: 4px 0 0; font-size: 14px; }
  .body { padding: 28px 32px; }
  .box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }
  .box p { margin: 0; font-size: 14px; color: #166534; }
  .row { display: flex; margin-bottom: 10px; gap: 12px; }
  .label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #94a3b8; letter-spacing: .04em; min-width: 110px; padding-top: 2px; }
  .value { font-size: 14px; color: #1a1a2e; }
  .footer { padding: 16px 32px; background: #f9fafb; border-top: 1px solid #e5e7eb; font-size: 12px; color: #94a3b8; text-align: center; }
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Quote Request Sent</h1>
    <p>We've forwarded your request to ${p.listingName}</p>
  </div>
  <div class="body">
    <div class="box"><p>&#10003; <strong>${p.listingName}</strong> has been notified and will follow up with you directly at <strong>${p.attorneyEmail}</strong>.</p></div>
    <p style="font-size:14px;color:#374151;">Here's what you submitted:</p>
    <div class="row"><span class="label">Provider</span><span class="value">${p.listingName}</span></div>
    <div class="row"><span class="label">Case Type</span><span class="value">${caseLabel}</span></div>
    <div class="row"><span class="label">Preferred Date</span><span class="value">${dateLabel}</span></div>
    ${p.details ? `<div class="row"><span class="label">Notes</span><span class="value">${p.details}</span></div>` : ''}
    <p style="font-size:13px;color:#6b7280;margin-top:20px;">Most featured providers respond within 4 business hours. If you don't hear back, <a href="https://depohire.com" style="color:#2563eb">search for other providers</a> in your city.</p>
  </div>
  <div class="footer">Sent via <a href="https://depohire.com" style="color:#2563eb">DepoHire.com</a> &mdash; the free deposition videographer directory</div>
</div>
</body></html>`;

  const sends = [
    // To provider
    fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${p.resendKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: 'DepoHire Leads <contact@depohire.com>',
        to: [p.providerEmail],
        reply_to: p.attorneyEmail,
        subject: `New lead: ${p.attorneyName} needs a videographer in ${p.city}`,
        html: providerHtml,
      }),
    }),
    // To attorney
    fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${p.resendKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: 'DepoHire <contact@depohire.com>',
        to: [p.attorneyEmail],
        reply_to: p.providerEmail,
        subject: `Your quote request was sent to ${p.listingName}`,
        html: attorneyHtml,
      }),
    }),
  ];

  const results = await Promise.allSettled(sends);
  for (const r of results) {
    if (r.status === 'rejected') {
      console.error('Resend error:', r.reason);
    } else {
      const body = await r.value.json() as { id?: string; statusCode?: number; message?: string };
      if (!r.value.ok) console.error('Resend API error:', body);
    }
  }
}
